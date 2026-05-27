"""
market_scanner.py - Scan markets and gather price data.

Fetches markets, filters for liquid YES/NO markets,
retrieves bid/ask prices, and returns clean market data
for arbitrage analysis.
"""

from typing import Optional
import config
from src import polymarket_client as client
from src.utils import truncate


def is_binary_market(market: dict) -> bool:
    """Check if market is a simple YES/NO binary market."""
    outcomes = market.get("outcomes", [])
    if len(outcomes) != 2:
        return False
    names = [o.lower() for o in outcomes]
    return "yes" in names and "no" in names


def is_liquid_enough(market: dict) -> bool:
    """Filter out markets with too little liquidity."""
    liquidity = market.get("liquidity", 0)
    return liquidity >= config.MIN_LIQUIDITY


def scan_markets() -> list[dict]:
    """
    Main scan function. Fetches markets and returns enriched data.

    Each returned item is a dict with:
      - All original market fields
      - yes_bid, yes_ask, no_bid, no_ask
      - price_source: "clob" or "gamma"
      - scan_ok: bool (True if prices retrieved successfully)
    """
    print(f"[scanner] Fetching up to {config.MARKET_LIMIT} markets...")

    markets = client.fetch_markets(limit=config.MARKET_LIMIT)

    if not markets:
        print("[scanner] No markets returned. Check API connection.")
        return []

    # Filter to binary yes/no markets with enough liquidity
    candidates = [
        m for m in markets
        if is_binary_market(m) and is_liquid_enough(m)
    ]

    print(f"[scanner] {len(markets)} total → {len(candidates)} binary + liquid")

    enriched = []
    for market in candidates:
        title = truncate(market.get("question", "?"), 50)
        prices = client.fetch_market_prices(market)

        if prices is None:
            print(f"[scanner] No prices for: {title}")
            continue

        enriched_market = {
            **market,
            "yes_bid": prices["yes_bid"],
            "yes_ask": prices["yes_ask"],
            "no_bid": prices["no_bid"],
            "no_ask": prices["no_ask"],
            "price_source": prices["source"],
            "scan_ok": True,
        }
        enriched.append(enriched_market)

    print(f"[scanner] Prices retrieved for {len(enriched)}/{len(candidates)} markets")
    return enriched
