"""
Group markets by event and detect tournament-style pricing anomalies.
"""

from __future__ import annotations
import re
from typing import Optional

from models.market import MarketData, TournamentGroup
from utils.math_utils import vig_pct as calc_vig


MUTUAL_EXCLUSIVE_SUM_MIN = 0.40   # lowered: partial groups still useful
MUTUAL_EXCLUSIVE_SUM_MAX = 1.50
MIN_GROUP_SIZE = 2

_CUMULATIVE_RE = re.compile(
    r"(above|exceed|more than|over|greater than|below|less than|under|at least)\s+\$?[\d,.]+[kmbt]?",
    re.IGNORECASE,
)


def group_by_event(markets: list[MarketData]) -> dict[str, list[MarketData]]:
    """Group markets by event_title. Returns dict event_title → markets."""
    groups: dict[str, list[MarketData]] = {}
    for m in markets:
        key = m.event_title.strip() or "__no_event__"
        groups.setdefault(key, []).append(m)
    return groups


def is_cumulative(markets: list[MarketData]) -> bool:
    """True if markets look like nested threshold questions (false positive for arb)."""
    matches = sum(
        1 for m in markets
        if _CUMULATIVE_RE.search(m.question or "")
    )
    return matches > len(markets) * 0.5


def analyze_group(
    event_title: str,
    markets: list[MarketData],
) -> Optional[TournamentGroup]:
    """
    Analyze one event group.

    Returns TournamentGroup if the group shows notable mispricing,
    or None if the group is skipped (not mutually exclusive, too small, etc.)
    """
    if len(markets) < MIN_GROUP_SIZE:
        return None

    # Only use markets with valid YES mid prices
    valid = [
        m for m in markets
        if m.yes_mid is not None
        and 0.0 < m.yes_mid < 1.0
        and m.yes_ask is not None
        and m.yes_bid is not None
    ]

    if len(valid) < MIN_GROUP_SIZE:
        return None

    sum_mid = sum(m.yes_mid for m in valid)

    # Skip if not mutually exclusive
    if not (MUTUAL_EXCLUSIVE_SUM_MIN <= sum_mid <= MUTUAL_EXCLUSIVE_SUM_MAX):
        return None

    sum_ask = sum(m.yes_ask for m in valid)
    sum_bid = sum(m.yes_bid for m in valid)

    buy_all_profit_pct = (1.0 - sum_ask) * 100
    vig = calc_vig([m.yes_mid for m in valid])
    field_prob = max(0.0, 1.0 - sum_mid)

    # Detect false positive patterns
    warnings: list[str] = []
    cumulative = is_cumulative(valid)
    if cumulative:
        warnings.append("CUMULATIVE: nested threshold markets — not real arb")
    if field_prob > 0.03:
        warnings.append(
            f"INCOMPLETE: {field_prob*100:.1f}% field probability "
            f"(unlisted winners possible)"
        )

    opp_type = _classify(buy_all_profit_pct, vig, warnings)
    confidence = _group_confidence(vig, field_prob, sum(m.liquidity for m in valid), len(valid))

    return TournamentGroup(
        event_title=event_title,
        market_count=len(valid),
        markets=sorted(valid, key=lambda m: m.yes_mid or 0, reverse=True),
        sum_yes_mid=round(sum_mid, 6),
        sum_yes_ask=round(sum_ask, 6),
        sum_yes_bid=round(sum_bid, 6),
        vig_pct=round(vig, 4),
        buy_all_profit_pct=round(buy_all_profit_pct, 4),
        field_probability=round(field_prob, 4),
        total_liquidity=sum(m.liquidity for m in valid),
        is_cumulative=cumulative,
        warnings=warnings,
        opportunity_type=opp_type,
        confidence=confidence,
    )


def _classify(buy_all_profit_pct: float, vig: float, warnings: list[str]) -> str:
    if buy_all_profit_pct > 0 and not warnings:
        return "BUY_ALL"
    if buy_all_profit_pct > 0 and warnings:
        return "BUY_ALL_RISKY"
    if vig > 5.0:
        return "HIGH_VIG"
    if vig > 2.0:
        return "ELEVATED_VIG"
    return "NORMAL_VIG"


def _group_confidence(
    vig: float,
    field_prob: float,
    total_liquidity: float,
    n_markets: int,
) -> float:
    """
    Confidence score for a tournament group opportunity.
    HIGH vig + LOW field risk + HIGH liquidity = high confidence.
    """
    vig_score = min(abs(vig) / 10.0, 1.0)
    liq_score = min(total_liquidity / 1_000_000, 1.0)
    field_penalty = min(field_prob * 5, 1.0)
    size_score = min(n_markets / 20, 1.0)

    score = (vig_score * 0.4 + liq_score * 0.3 + size_score * 0.3) * (1 - field_penalty * 0.5)
    return round(min(1.0, max(0.0, score)), 3)


def scan_all_groups(markets: list[MarketData]) -> list[TournamentGroup]:
    """Run group analysis on all markets. Returns notable groups, sorted by vig."""
    groups = group_by_event(markets)
    results: list[TournamentGroup] = []

    for event_title, mlist in groups.items():
        if event_title == "__no_event__":
            continue
        group = analyze_group(event_title, mlist)
        if group:
            results.append(group)

    # Sort: BUY_ALL first, then by absolute vig descending
    results.sort(key=lambda g: (
        0 if g.opportunity_type == "BUY_ALL" else 1,
        -abs(g.vig_pct),
    ))

    return results
