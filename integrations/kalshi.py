"""
Kalshi async API client.

Uses: https://api.elections.kalshi.com/trade-api/v2/
No auth needed for public market data (GET requests).

Prices returned as yes_ask_dollars / yes_bid_dollars in [0, 1] range.
Each Kalshi market = one binary outcome (unlike PredictIt where one market has many contracts).
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

KALSHI_BASE = "https://api.elections.kalshi.com/trade-api/v2"
PAGE_SIZE = 200
MAX_PAGES = 15     # max 3,000 markets
REQUEST_TIMEOUT = 12.0


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8), reraise=True)
async def _get(client: httpx.AsyncClient, url: str, params: dict | None = None) -> dict:
    resp = await client.get(url, params=params, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


async def fetch_all_markets(client: httpx.AsyncClient) -> list[dict]:
    """
    Fetch all open Kalshi markets with pagination.
    Returns raw market dicts normalized to standard format.
    """
    markets = []
    cursor: Optional[str] = None

    for _ in range(MAX_PAGES):
        params: dict = {"status": "open", "limit": PAGE_SIZE}
        if cursor:
            params["cursor"] = cursor

        try:
            data = await _get(client, f"{KALSHI_BASE}/markets", params)
        except Exception as e:
            print(f"[kalshi] fetch error: {e}")
            break

        batch = data.get("markets", [])
        markets.extend(batch)
        cursor = data.get("cursor")
        if not cursor or len(batch) < PAGE_SIZE:
            break

    return [_normalize(m) for m in markets if _is_usable(m)]


async def fetch_events(client: httpx.AsyncClient, limit: int = 200) -> list[dict]:
    """Fetch Kalshi events (one event can have multiple binary markets)."""
    try:
        data = await _get(client, f"{KALSHI_BASE}/events",
                          {"status": "open", "limit": limit})
        return data.get("events", [])
    except Exception as e:
        print(f"[kalshi] events error: {e}")
        return []


def _to_float(v) -> float:
    """Safely coerce string or None price to float."""
    try:
        return float(v) if v is not None else 0.0
    except (TypeError, ValueError):
        return 0.0


def _is_usable(raw: dict) -> bool:
    """Skip markets with no prices or non-binary types."""
    ask = _to_float(raw.get("yes_ask_dollars"))
    return ask > 0.001


def _normalize(raw: dict) -> dict:
    """Normalize raw Kalshi market to internal format."""
    ask = _to_float(raw.get("yes_ask_dollars"))
    bid = _to_float(raw.get("yes_bid_dollars"))
    mid = (ask + bid) / 2 if (ask + bid) > 0 else ask

    return {
        "platform": "kalshi",
        "platform_market_id": raw.get("ticker", ""),
        "event_ticker": raw.get("event_ticker", ""),
        "title": raw.get("title", ""),
        "yes_ask": round(ask, 4),
        "yes_bid": round(bid, 4),
        "mid": round(mid, 4),
        "volume": raw.get("volume_fp") or raw.get("volume_24h_fp") or 0,
        "liquidity": raw.get("liquidity_dollars") or 0,
        "status": raw.get("status", ""),
        "close_time": raw.get("close_time", ""),
        "fetched_at": datetime.utcnow().isoformat(),
    }
