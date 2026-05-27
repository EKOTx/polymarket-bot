"""
tournament_scanner.py - Detect mispricing across related tournament markets.

Strategy: In a tournament (FIFA, election, etc.), exactly ONE outcome wins.
Sum of all YES prices should equal 1.0.

  sum(yes_ask) < 1.0  → BUY ALL outcomes, profit guaranteed when resolved
  sum(yes_mid) > 1.0  → Market is overpriced overall (vig too high)

Groups markets by event_title + event_id. Filters to mutually-exclusive groups
by checking that sum of mid prices falls in [0.5, 1.5].
Groups where sum >> 1.5 are independent events (e.g. "Will X happen before Y?")
and are skipped.

Each detected opportunity includes:
  - event_title, market_count
  - sum_yes_ask   (cost to buy all outcomes)
  - sum_yes_bid   (revenue if you could sell all)
  - sum_yes_mid   (theoretical fair sum, should = 1.0)
  - buy_all_profit_pct  (if sum_yes_ask < 1.0)
  - vig_pct       (excess over 1.0 in mid prices = market maker take)
  - markets       (sorted list of individual markets with prices)
  - outliers      (markets whose mid deviates most from fair share)
"""

import requests
import json
from typing import Optional
import config
from src import polymarket_client as client
from src.utils import safe_float, truncate


# A group is "mutually exclusive" (tournament-style) if mid sum is in this range.
# Sum <<1.0 means markets missing. Sum >>1.5 means independent events.
MUTUAL_EXCLUSIVE_SUM_MIN = 0.50
MUTUAL_EXCLUSIVE_SUM_MAX = 1.50

# Minimum number of markets to consider a valid tournament group
MIN_GROUP_SIZE = 2

# Only flag groups where vig or gap exceeds this (in percent)
MIN_DEVIATION_PCT = 0.5


def fetch_all_markets_grouped(limit: int = 500) -> dict[str, list[dict]]:
    """
    Fetch markets and group by (event_id, event_title).

    Returns dict: event_title → list of market dicts (normalized).
    """
    markets = client.fetch_markets(limit=limit)

    groups: dict[str, list[dict]] = {}
    for m in markets:
        key = m.get("event_title", "").strip()
        if not key:
            key = "__no_event__"
        if key not in groups:
            groups[key] = []
        groups[key].append(m)

    return groups


def enrich_group_with_prices(markets: list[dict]) -> list[dict]:
    """
    Fetch CLOB bid/ask for every market in a group.
    Returns enriched market list (markets that failed price fetch are excluded).
    """
    enriched = []
    for m in markets:
        prices = client.fetch_market_prices(m)
        if prices is None:
            continue
        enriched.append({
            **m,
            "yes_bid": prices["yes_bid"],
            "yes_ask": prices["yes_ask"],
            "no_bid": prices["no_bid"],
            "no_ask": prices["no_ask"],
            "yes_mid": (prices["yes_bid"] + prices["yes_ask"]) / 2,
            "price_source": prices["source"],
        })
    return enriched


def _is_cumulative_group(markets: list[dict]) -> bool:
    """
    Detect "staircase" / cumulative market groups.

    Example: "FDV above $500M", "FDV above $1B", "FDV above $3B"
    These are nested, NOT mutually exclusive — buying all doesn't guarantee $1.

    Heuristic: if >50% of questions share the same phrase pattern with a
    numeric threshold that varies ("above X", "exceed X", "more than X"),
    treat as cumulative.
    """
    import re
    threshold_patterns = [
        r"above\s+\$?[\d,.]+[kmbt]?",
        r"exceed\s+\$?[\d,.]+[kmbt]?",
        r"more than\s+\$?[\d,.]+[kmbt]?",
        r"over\s+\$?[\d,.]+[kmbt]?",
        r"greater than\s+\$?[\d,.]+[kmbt]?",
        r"below\s+\$?[\d,.]+[kmbt]?",
        r"less than\s+\$?[\d,.]+[kmbt]?",
        r"under\s+\$?[\d,.]+[kmbt]?",
        r"at least\s+\$?[\d,.]+[kmbt]?",
    ]
    combined = "|".join(threshold_patterns)
    matches = sum(
        1 for m in markets
        if re.search(combined, m.get("question", ""), re.IGNORECASE)
    )
    return matches > len(markets) * 0.5


def _field_probability(sum_mid: float) -> float:
    """
    Implied probability of an outcome NOT listed in this group.

    E.g. sum_mid=0.96 means 4% chance that an unlisted candidate wins.
    This prevents "buy all" from being truly risk-free.
    """
    return max(0.0, 1.0 - sum_mid)


def analyze_group(event_title: str, markets: list[dict]) -> Optional[dict]:
    """
    Analyze one event group for tournament mispricing.

    Returns opportunity dict or None if group is not interesting.
    """
    if len(markets) < MIN_GROUP_SIZE:
        return None

    # Filter markets where prices are valid
    valid = [
        m for m in markets
        if m.get("yes_ask") is not None
        and m.get("yes_bid") is not None
        and 0 < m["yes_ask"] < 1
        and 0 < m["yes_bid"] < 1
    ]

    if len(valid) < MIN_GROUP_SIZE:
        return None

    # Sum of mid prices — tells us if this is mutually exclusive
    sum_mid = sum(m["yes_mid"] for m in valid)

    # Skip if not a mutually-exclusive tournament
    if not (MUTUAL_EXCLUSIVE_SUM_MIN <= sum_mid <= MUTUAL_EXCLUSIVE_SUM_MAX):
        return None

    # Detect false positive patterns
    warnings = []
    is_cumulative = _is_cumulative_group(valid)
    if is_cumulative:
        warnings.append("CUMULATIVE: nested markets — BUY_ALL profit is not real arb")

    field_prob = _field_probability(sum_mid)
    if field_prob > 0.03:
        warnings.append(
            f"INCOMPLETE: ~{field_prob*100:.1f}% chance unlisted outcome wins — "
            f"'buy all' carries field risk"
        )

    # Core metrics
    sum_ask = sum(m["yes_ask"] for m in valid)
    sum_bid = sum(m["yes_bid"] for m in valid)

    # Buy-all: pay sum_ask, receive $1 when winner resolves
    buy_all_profit = 1.0 - sum_ask
    buy_all_profit_pct = buy_all_profit * 100

    # Vig = excess above fair value (market maker's take on mid prices)
    vig_pct = (sum_mid - 1.0) * 100

    # Overall deviation from 1.0
    mid_deviation_pct = abs(sum_mid - 1.0) * 100

    # Only flag if deviation is interesting
    if mid_deviation_pct < MIN_DEVIATION_PCT and buy_all_profit_pct < MIN_DEVIATION_PCT:
        return None

    # Find outlier markets: which outcomes deviate most from "fair share"
    # Fair share = 1.0 / len(valid) is naive (teams aren't equal)
    # Better: compare each market's mid vs its proportional share of sum_mid
    outliers = _find_outliers(valid, sum_mid)

    # Sort markets by mid price descending (favorites first)
    sorted_markets = sorted(valid, key=lambda m: m["yes_mid"], reverse=True)

    # Total liquidity in this group
    total_liquidity = sum(m.get("liquidity", 0) for m in valid)

    return {
        "event_title": event_title,
        "market_count": len(valid),
        "sum_yes_ask": sum_ask,
        "sum_yes_bid": sum_bid,
        "sum_yes_mid": sum_mid,
        "buy_all_profit_pct": buy_all_profit_pct,
        "vig_pct": vig_pct,
        "mid_deviation_pct": mid_deviation_pct,
        "field_probability": field_prob,
        "total_liquidity": total_liquidity,
        "markets": sorted_markets,
        "outliers": outliers,
        "warnings": warnings,
        "is_cumulative": is_cumulative,
        "opportunity_type": _classify(buy_all_profit_pct, vig_pct, warnings),
    }


def _classify(buy_all_profit_pct: float, vig_pct: float, warnings: list[str]) -> str:
    """Classify what kind of opportunity this group represents."""
    if buy_all_profit_pct > 0 and not warnings:
        return "BUY_ALL"          # sum_ask < 1.0, no false-positive flags
    elif buy_all_profit_pct > 0 and warnings:
        return "BUY_ALL_RISKY"    # looks like arb but has warnings
    elif vig_pct > 5.0:
        return "HIGH_VIG"         # market maker taking > 5%
    elif vig_pct > 2.0:
        return "ELEVATED_VIG"
    else:
        return "NORMAL_VIG"


def _find_outliers(markets: list[dict], sum_mid: float) -> list[dict]:
    """
    Find markets that are most mispriced relative to the group.

    For each market: expected_share = yes_mid / sum_mid (its portion of 1.0).
    If sum_mid ≠ 1.0, some markets are contributing disproportionately.

    We find markets where (yes_mid - expected_fair_price) is largest.
    expected_fair_price = yes_mid / sum_mid  (rescaled to sum=1.0)
    """
    if sum_mid == 0:
        return []

    results = []
    for m in markets:
        mid = m["yes_mid"]
        # What this market's price would be if the group summed to exactly 1.0
        fair_price = mid / sum_mid
        deviation = mid - fair_price  # positive = overpriced in group context
        deviation_pct = deviation * 100

        results.append({
            "question": m["question"],
            "yes_mid": mid,
            "yes_ask": m["yes_ask"],
            "yes_bid": m["yes_bid"],
            "fair_price": fair_price,
            "deviation_pct": deviation_pct,
            "direction": "OVER" if deviation > 0 else "UNDER",
        })

    # Sort by absolute deviation
    results.sort(key=lambda x: abs(x["deviation_pct"]), reverse=True)
    return results[:5]  # top 5 most mispriced


def scan_tournaments(market_limit: int = 500) -> list[dict]:
    """
    Main entry point. Scans all events for tournament mispricing.

    Returns list of opportunities sorted by:
      1. BUY_ALL opportunities first (rare, most actionable)
      2. Then by vig_pct descending (shows biggest mispricings)
    """
    print(f"[tournament] Fetching markets (limit={market_limit})...")
    groups = fetch_all_markets_grouped(limit=market_limit)

    # Filter to groups worth analyzing (3+ markets)
    candidates = {
        title: mlist
        for title, mlist in groups.items()
        if len(mlist) >= MIN_GROUP_SIZE and title != "__no_event__"
    }

    print(f"[tournament] {len(groups)} events found, {len(candidates)} with {MIN_GROUP_SIZE}+ markets")
    print(f"[tournament] Fetching CLOB prices for candidate groups...")

    opportunities = []
    for event_title, markets in candidates.items():
        # Enrich with real CLOB prices
        enriched = enrich_group_with_prices(markets)

        opp = analyze_group(event_title, enriched)
        if opp:
            opportunities.append(opp)

    # Sort: BUY_ALL first, then by deviation size
    def sort_key(o):
        type_rank = 0 if o["opportunity_type"] == "BUY_ALL" else 1
        return (type_rank, -o["mid_deviation_pct"])

    opportunities.sort(key=sort_key)

    print(f"[tournament] {len(opportunities)} groups with notable mispricing")
    return opportunities
