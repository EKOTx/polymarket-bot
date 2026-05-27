"""
arbitrage.py - Detect pricing opportunities in Polymarket markets.

Two main opportunity types:
  1. UNDERPRICED: YES ask + NO ask < 1.0
     → Buy both sides for less than $1, collect $1 at resolution.
     → Profit = 1 - yes_ask - no_ask

  2. OVERPRICED: YES bid + NO bid > 1.0
     → Sell both sides for more than $1, pay $1 at resolution.
     → Profit = yes_bid + no_bid - 1

All prices are in range [0, 1] representing probability / USDC per share.
"""

from typing import Optional
import config
from src.utils import safe_float


# Flags attached to opportunities to explain warnings or confidence
WARNING_GAMMA_PRICES = "prices from gamma (no real bid/ask)"
WARNING_WIDE_SPREAD = "wide spread — slippage risk"
WARNING_LOW_LIQUIDITY = "low liquidity"


def analyze_market(market: dict) -> Optional[dict]:
    """
    Analyze one market for arbitrage opportunities.

    Returns opportunity dict if profit >= MIN_PROFIT_PERCENT, else None.
    Returns None if prices are missing or invalid.
    """
    yes_bid = market.get("yes_bid")
    yes_ask = market.get("yes_ask")
    no_bid = market.get("no_bid")
    no_ask = market.get("no_ask")

    # Reject if any price is missing
    if any(p is None for p in [yes_bid, yes_ask, no_bid, no_ask]):
        return None

    # Reject clearly invalid prices
    for price in [yes_bid, yes_ask, no_bid, no_ask]:
        if not (0.0 < price < 1.0):
            return None

    # Bid must be <= ask (sanity check)
    if yes_bid > yes_ask or no_bid > no_ask:
        return None

    warnings = []
    source = market.get("price_source", "unknown")

    # Flag gamma prices as less reliable (mid price, not real bid/ask)
    if source == "gamma":
        warnings.append(WARNING_GAMMA_PRICES)

    # Flag markets with very wide spreads (slippage risk)
    yes_spread = yes_ask - yes_bid
    no_spread = no_ask - no_bid
    if yes_spread > 0.05 or no_spread > 0.05:
        warnings.append(WARNING_WIDE_SPREAD)

    # Flag low liquidity
    liquidity = market.get("liquidity", 0)
    if liquidity < 5000:
        warnings.append(WARNING_LOW_LIQUIDITY)

    # ── Check opportunity types ─────────────────────────────────────────────────

    opportunity = None

    # Type 1: UNDERPRICED - buy both sides cheaper than $1
    total_ask = yes_ask + no_ask
    if total_ask < 1.0:
        profit = 1.0 - total_ask
        profit_pct = profit * 100

        if profit_pct >= config.MIN_PROFIT_PERCENT:
            opportunity = _build_opportunity(
                market=market,
                opp_type="UNDERPRICED",
                description="Buy YES + NO for less than $1",
                yes_bid=yes_bid,
                yes_ask=yes_ask,
                no_bid=no_bid,
                no_ask=no_ask,
                total_cost=total_ask,
                profit_pct=profit_pct,
                warnings=warnings,
            )

    # Type 2: OVERPRICED - sell both sides for more than $1
    total_bid = yes_bid + no_bid
    if total_bid > 1.0 and opportunity is None:
        profit = total_bid - 1.0
        profit_pct = profit * 100

        if profit_pct >= config.MIN_PROFIT_PERCENT:
            opportunity = _build_opportunity(
                market=market,
                opp_type="OVERPRICED",
                description="Sell YES + NO for more than $1",
                yes_bid=yes_bid,
                yes_ask=yes_ask,
                no_bid=no_bid,
                no_ask=no_ask,
                total_cost=total_bid,
                profit_pct=profit_pct,
                warnings=warnings,
            )

    return opportunity


def _build_opportunity(
    market: dict,
    opp_type: str,
    description: str,
    yes_bid: float,
    yes_ask: float,
    no_bid: float,
    no_ask: float,
    total_cost: float,
    profit_pct: float,
    warnings: list[str],
) -> dict:
    """Build standardized opportunity dict."""
    return {
        # Market info
        "market_id": market.get("id", ""),
        "title": market.get("question", "Unknown"),
        "event_title": market.get("event_title", ""),
        "liquidity": market.get("liquidity", 0),
        "volume": market.get("volume", 0),
        # Prices
        "yes_bid": yes_bid,
        "yes_ask": yes_ask,
        "no_bid": no_bid,
        "no_ask": no_ask,
        # Analysis
        "total_cost": total_cost,
        "profit_pct": profit_pct,
        "opportunity_type": opp_type,
        "description": description,
        "price_source": market.get("price_source", "unknown"),
        # Quality flags
        "warnings": warnings,
        "confidence": _confidence_score(profit_pct, warnings, market),
    }


def _confidence_score(profit_pct: float, warnings: list[str], market: dict) -> str:
    """
    Simple confidence label based on profit size, warnings, and liquidity.

    HIGH   = good profit, real CLOB prices, decent liquidity, no spread issues
    MEDIUM = some warnings but still worth watching
    LOW    = gamma prices or wide spread (not trustworthy for real trading)
    """
    if WARNING_GAMMA_PRICES in warnings:
        return "LOW"
    if WARNING_WIDE_SPREAD in warnings:
        return "LOW"
    if profit_pct >= 3.0 and not warnings:
        return "HIGH"
    if profit_pct >= 1.5:
        return "MEDIUM"
    return "LOW"


def scan_for_opportunities(markets: list[dict]) -> list[dict]:
    """
    Run arbitrage analysis across all scanned markets.
    Returns list of opportunities sorted by profit % descending.
    """
    opportunities = []

    for market in markets:
        opp = analyze_market(market)
        if opp:
            opportunities.append(opp)

    # Sort best opportunities first
    opportunities.sort(key=lambda x: x["profit_pct"], reverse=True)

    return opportunities
