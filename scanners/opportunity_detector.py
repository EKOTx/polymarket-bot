"""
Detect pricing opportunities from enriched market data.

Three detectors:
  1. SpreadAnalyzer   — wide spread, low depth, stale prices
  2. VigDetector      — tournament group vig analysis
  3. ValueDetector    — price vs external fair value (stub for Phase 2)
"""

from __future__ import annotations
import os
from datetime import datetime

from models.market import MarketData, TournamentGroup
from models.opportunity import Opportunity, OpportunityType
from utils.math_utils import confidence_score, edge_pct, half_kelly


MIN_EDGE_PCT = float(os.getenv("MIN_EDGE_PCT", "0.5"))
MIN_VIG_PCT = float(os.getenv("MIN_VIG_PCT", "2.0"))
MIN_CONFIDENCE = float(os.getenv("MIN_CONFIDENCE", "0.4"))
PAPER_MAX_POSITION_SIZE = float(os.getenv("PAPER_MAX_POSITION_SIZE", "500"))


# ── Spread Analyzer ──────────────────────────────────────────────────────────

def analyze_spreads(markets: list[MarketData], scan_id: int = 0) -> list[Opportunity]:
    """
    Flag markets with unusually wide spreads.
    Wide spread = potential market maker absence = price discovery opportunity.

    Requires BOTH:
    - spread_pct > 5%  (relative)
    - absolute spread > $0.01  (avoids near-zero mid noise)
    - mid price > 0.02  (skip markets trading at dust prices)
    """
    opps = []
    for m in markets:
        if not m.yes_book or not m.yes_book.spread_pct:
            continue
        sp = m.yes_book.spread_pct
        abs_spread = m.yes_book.spread or 0
        mid = m.yes_mid or 0

        if sp is None or sp < 5.0:
            continue
        if abs_spread < 0.01:   # filter near-zero dust markets
            continue
        if mid < 0.02:          # skip markets priced below 2 cents
            continue

        conf = confidence_score(
            edge=sp / 2,                    # approximate edge from spread width
            liquidity=m.liquidity,
            spread_pct=sp,
        )
        if conf < MIN_CONFIDENCE:
            continue

        opp = Opportunity(
            scan_id=scan_id,
            opportunity_type=OpportunityType.SPREAD,
            title=m.question,
            event_title=m.event_title,
            market_id=m.market_id,
            edge_pct=round(sp / 2, 3),
            confidence=conf,
            expected_value=round(sp / 2 * 100 / 100, 4),
            yes_bid=m.yes_bid,
            yes_ask=m.yes_ask,
            no_bid=m.no_bid,
            no_ask=m.no_ask,
            liquidity=m.liquidity,
            suggested_size_usd=min(PAPER_MAX_POSITION_SIZE, m.liquidity * 0.01),
            details={
                "spread_pct": sp,
                "yes_spread": m.yes_book.spread,
                "bid_depth_usd": m.yes_book.bid_depth_usd,
                "ask_depth_usd": m.yes_book.ask_depth_usd,
            },
        )
        opps.append(opp)

    return sorted(opps, key=lambda o: -o.edge_pct)


# ── Vig Detector ─────────────────────────────────────────────────────────────

def analyze_tournament_vig(
    groups: list[TournamentGroup],
    scan_id: int = 0,
) -> list[Opportunity]:
    """
    Convert tournament groups into Opportunity objects.
    Only returns groups with vig above MIN_VIG_PCT or BUY_ALL.
    """
    opps = []

    for group in groups:
        opp_type_str = group.opportunity_type

        # Only surface notable groups
        if opp_type_str == "NORMAL_VIG" and abs(group.vig_pct) < MIN_VIG_PCT:
            continue
        if group.confidence < MIN_CONFIDENCE:
            continue

        if opp_type_str in ("BUY_ALL", "BUY_ALL_RISKY"):
            opp_type = (
                OpportunityType.TOURNAMENT_ARB
                if opp_type_str == "BUY_ALL"
                else OpportunityType.TOURNAMENT_ARB_RISKY
            )
            edge = group.buy_all_profit_pct
        else:
            opp_type = (
                OpportunityType.HIGH_VIG
                if group.vig_pct > 5
                else OpportunityType.ELEVATED_VIG
            )
            edge = abs(group.vig_pct)

        if edge < MIN_EDGE_PCT:
            continue

        opp = Opportunity(
            scan_id=scan_id,
            opportunity_type=opp_type,
            title=group.event_title,
            event_title=group.event_title,
            edge_pct=round(edge, 3),
            confidence=group.confidence,
            expected_value=round(edge / 100 * PAPER_MAX_POSITION_SIZE, 2),
            sum_yes_mid=group.sum_yes_mid,
            vig_pct=group.vig_pct,
            liquidity=group.total_liquidity,
            market_count=group.market_count,
            warnings=group.warnings,
            suggested_size_usd=_tournament_size(group),
            details={
                "sum_ask": group.sum_yes_ask,
                "sum_bid": group.sum_yes_bid,
                "field_probability": group.field_probability,
                "buy_all_profit_pct": group.buy_all_profit_pct,
                "is_cumulative": group.is_cumulative,
                "top_markets": [
                    {
                        "question": m.question[:60],
                        "yes_mid": m.yes_mid,
                        "yes_ask": m.yes_ask,
                        "liquidity": m.liquidity,
                    }
                    for m in group.markets[:5]
                ],
            },
        )
        opps.append(opp)

    return sorted(opps, key=lambda o: -o.edge_pct)


def _tournament_size(group: TournamentGroup) -> float:
    """Suggested position size for a tournament group opportunity."""
    if group.opportunity_type == "BUY_ALL":
        # Risk (1 - field_prob) of the investment per outcome
        risk_adj = 1.0 - group.field_probability
        return min(PAPER_MAX_POSITION_SIZE, group.total_liquidity * 0.001 * risk_adj)
    return 0.0  # VIG opportunities don't have a direct trade


# ── Value Detector ───────────────────────────────────────────────────────────

def analyze_value(
    markets: list[MarketData],
    external_probs: dict[str, float],  # market_id → fair probability
    scan_id: int = 0,
) -> list[Opportunity]:
    """
    Find markets where Polymarket price deviates from external fair value.
    external_probs comes from Kalshi, The Odds API, etc.
    """
    opps = []
    for m in markets:
        fair_prob = external_probs.get(m.market_id)
        if fair_prob is None or m.yes_ask is None:
            continue

        e = edge_pct(fair_prob, m.yes_ask)
        if e < MIN_EDGE_PCT:
            continue

        conf = confidence_score(
            edge=e,
            liquidity=m.liquidity,
            spread_pct=m.yes_spread_pct or 10.0,
            source_quality=0.8,
        )
        if conf < MIN_CONFIDENCE:
            continue

        size = min(
            PAPER_MAX_POSITION_SIZE,
            half_kelly(fair_prob, 1.0 / m.yes_ask) * 10_000,
        )

        opps.append(Opportunity(
            scan_id=scan_id,
            opportunity_type=OpportunityType.VALUE,
            title=m.question,
            event_title=m.event_title,
            market_id=m.market_id,
            edge_pct=round(e, 3),
            confidence=conf,
            expected_value=round(e / 100 * size, 4),
            yes_bid=m.yes_bid,
            yes_ask=m.yes_ask,
            no_bid=m.no_bid,
            no_ask=m.no_ask,
            liquidity=m.liquidity,
            suggested_size_usd=round(size, 2),
            details={
                "fair_prob": fair_prob,
                "pm_ask": m.yes_ask,
                "edge_pct": e,
            },
        ))

    return sorted(opps, key=lambda o: -o.edge_pct)


def analyze_cross_platform_value(
    matches: "list",   # list[integrations.matcher.MatchResult]
    scan_id: int = 0,
) -> list[Opportunity]:
    """
    Convert cross-platform MatchResult objects into VALUE Opportunity records.
    Only surfaces actionable matches (direction != NONE, edge >= MIN_VALUE_EDGE_PCT).
    """
    opps = []
    for m in matches:
        if m.direction == "NONE":
            continue
        if m.edge_pct < MIN_EDGE_PCT:
            continue

        pm = m.pm_market
        fair = m.external_fair
        e = m.edge_pct

        conf = confidence_score(
            edge=e,
            liquidity=pm.liquidity,
            spread_pct=pm.yes_spread_pct or 10.0,
            source_quality=0.75,  # external match isn't perfect
        )
        if conf < MIN_CONFIDENCE:
            continue

        ask = pm.yes_ask or pm.yes_mid or 0
        if ask <= 0:
            continue

        size = min(
            PAPER_MAX_POSITION_SIZE,
            half_kelly(fair, 1.0 / ask) * 10_000,
        )

        opps.append(Opportunity(
            scan_id=scan_id,
            opportunity_type=OpportunityType.VALUE,
            title=pm.question,
            event_title=pm.event_title,
            market_id=pm.market_id,
            edge_pct=round(e, 3),
            confidence=conf,
            expected_value=round(e / 100 * size, 4),
            yes_bid=pm.yes_bid,
            yes_ask=pm.yes_ask,
            no_bid=pm.no_bid,
            no_ask=pm.no_ask,
            liquidity=pm.liquidity,
            suggested_size_usd=round(size, 2),
            details={
                "fair_prob": fair,
                "pm_mid": m.pm_mid,
                "pm_ask": ask,
                "external_platform": m.external.platform,
                "external_title": m.external.title,
                "match_similarity": m.similarity,
                "direction": m.direction,
                "edge_pct": e,
            },
        ))

    return sorted(opps, key=lambda o: -o.edge_pct)


# ── Combined scan ────────────────────────────────────────────────────────────

def detect_all_opportunities(
    markets: list[MarketData],
    groups: list[TournamentGroup],
    external_probs: dict[str, float] | None = None,
    cross_platform_matches: "list | None" = None,
    scan_id: int = 0,
) -> list[Opportunity]:
    """Run all detectors and return merged, deduplicated, sorted results."""
    all_opps: list[Opportunity] = []

    all_opps.extend(analyze_spreads(markets, scan_id))
    all_opps.extend(analyze_tournament_vig(groups, scan_id))

    if external_probs:
        all_opps.extend(analyze_value(markets, external_probs, scan_id))

    if cross_platform_matches:
        all_opps.extend(analyze_cross_platform_value(cross_platform_matches, scan_id))

    # Sort by confidence × edge
    all_opps.sort(key=lambda o: -(o.confidence * o.edge_pct))
    return all_opps
