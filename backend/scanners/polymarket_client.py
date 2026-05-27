"""
Async Polymarket API client.

Uses httpx.AsyncClient with:
- Semaphore-based rate limiting (CLOB_CONCURRENCY concurrent requests)
- Tenacity retry on transient errors
- Pagination support for market list
- Concurrent order book fetching

Public endpoints — no auth needed for scanning.
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Optional

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)
import logging

from models.market import MarketData, OrderBook, TournamentGroup

logger = logging.getLogger(__name__)

# API base URLs
GAMMA_API = os.getenv("GAMMA_API_BASE", "https://gamma-api.polymarket.com")
CLOB_API = os.getenv("CLOB_API_BASE", "https://clob.polymarket.com")

# Max concurrent CLOB requests (avoids rate limiting)
CLOB_CONCURRENCY = int(os.getenv("CLOB_CONCURRENCY", "15"))
_semaphore: Optional[asyncio.Semaphore] = None


def _get_semaphore() -> asyncio.Semaphore:
    global _semaphore
    if _semaphore is None:
        _semaphore = asyncio.Semaphore(CLOB_CONCURRENCY)
    return _semaphore


# ── Retry decorator ──────────────────────────────────────────────────────────

_RETRYABLE = (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError)

retry_transient = retry(
    retry=retry_if_exception_type(_RETRYABLE),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    reraise=True,
)


# ── Core HTTP helpers ────────────────────────────────────────────────────────

@retry_transient
async def _get(
    client: httpx.AsyncClient,
    url: str,
    params: dict | None = None,
) -> dict | list | None:
    """GET with retry. Returns parsed JSON or None on non-retryable error."""
    try:
        resp = await client.get(url, params=params, timeout=12.0)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code in (429, 503):
            raise  # retryable
        logger.warning(f"HTTP {e.response.status_code} from {url}")
        return None
    except Exception as e:
        logger.warning(f"Request failed {url}: {e}")
        return None


# ── Market list ──────────────────────────────────────────────────────────────

async def fetch_markets_page(
    client: httpx.AsyncClient,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    """Fetch one page of active markets."""
    data = await _get(client, f"{GAMMA_API}/markets", params={
        "active": "true",
        "closed": "false",
        "limit": limit,
        "offset": offset,
    })
    return data if isinstance(data, list) else []


async def fetch_all_markets(
    client: httpx.AsyncClient,
    total_limit: int = 500,
) -> list[MarketData]:
    """
    Fetch all active markets with pagination.
    Returns normalized MarketData list (no order book yet).
    """
    page_size = 100
    raw_markets: list[dict] = []
    offset = 0

    while len(raw_markets) < total_limit:
        batch = await fetch_markets_page(client, page_size, offset)
        if not batch:
            break
        raw_markets.extend(batch)
        if len(batch) < page_size:
            break  # last page
        offset += len(batch)

    markets = []
    for raw in raw_markets[:total_limit]:
        m = _normalize_market(raw)
        if m:
            markets.append(m)

    return markets


def _normalize_market(raw: dict) -> Optional[MarketData]:
    """Convert raw Gamma API dict to MarketData. Returns None if invalid."""
    try:
        outcomes = json.loads(raw.get("outcomes", "[]"))
        outcome_prices = json.loads(raw.get("outcomePrices", "[]"))
        clob_ids = json.loads(raw.get("clobTokenIds", "[]"))
    except (json.JSONDecodeError, TypeError):
        return None

    if not outcomes:
        return None

    events = raw.get("events", [])
    event_title = events[0].get("title", "") if events else ""
    event_id = str(events[0].get("id", "")) if events else ""

    m = MarketData(
        market_id=str(raw.get("id", "")),
        question=raw.get("question", "Unknown"),
        event_title=event_title,
        event_id=event_id,
        volume=float(raw.get("volume") or 0),
        liquidity=float(raw.get("liquidity") or 0),
    )

    # Attach gamma mid prices as fallback (no real bid/ask from gamma)
    for outcome, price_str, token_id in zip(
        outcomes, outcome_prices, clob_ids + [""] * len(outcomes)
    ):
        mid = float(price_str) if price_str else None
        if mid is None:
            continue
        spread = 0.01
        book = OrderBook(
            token_id=token_id,
            outcome=outcome,
            best_bid=max(0.001, mid - spread / 2),
            best_ask=min(0.999, mid + spread / 2),
            price_source="gamma",
        )
        if outcome.lower() == "yes":
            m.yes_book = book
        elif outcome.lower() == "no":
            m.no_book = book

    m.enrich_from_books()
    m.price_source = "gamma"

    return m


# ── Order book ───────────────────────────────────────────────────────────────

async def fetch_order_book(
    client: httpx.AsyncClient,
    token_id: str,
    outcome: str,
) -> Optional[OrderBook]:
    """Fetch CLOB order book for one token. Rate-limited by semaphore."""
    async with _get_semaphore():
        data = await _get(client, f"{CLOB_API}/book", params={"token_id": token_id})

    if not data or not isinstance(data, dict):
        return None

    bids = _parse_levels(data.get("bids", []))
    asks = _parse_levels(data.get("asks", []))

    if not bids and not asks:
        return None

    best_bid = max((b["price"] for b in bids), default=None)
    best_ask = min((a["price"] for a in asks), default=None)

    return OrderBook(
        token_id=token_id,
        outcome=outcome,
        bids=bids,
        asks=asks,
        best_bid=best_bid,
        best_ask=best_ask,
        price_source="clob",
    )


def _parse_levels(levels: list) -> list[dict]:
    """Parse raw bid/ask levels. Filter invalid."""
    result = []
    for lvl in levels:
        try:
            p = float(lvl.get("price", 0))
            s = float(lvl.get("size", 0))
            if 0 < p < 1 and s > 0:
                result.append({"price": p, "size": s})
        except (TypeError, ValueError):
            continue
    return result


async def enrich_market_with_clob(
    client: httpx.AsyncClient,
    market: MarketData,
) -> MarketData:
    """
    Fetch real CLOB order books for YES and NO tokens.
    Falls back to gamma prices if CLOB fails.
    """
    # Gather token IDs from gamma-populated books
    yes_token = market.yes_book.token_id if market.yes_book else ""
    no_token = market.no_book.token_id if market.no_book else ""

    async def _noop() -> None:
        return None

    tasks = []
    tasks.append(fetch_order_book(client, yes_token, "Yes") if yes_token else _noop())
    tasks.append(fetch_order_book(client, no_token, "No") if no_token else _noop())

    results = await asyncio.gather(*tasks, return_exceptions=True)

    yes_book = results[0] if not isinstance(results[0], Exception) else None
    no_book = results[1] if not isinstance(results[1], Exception) else None

    if yes_book and isinstance(yes_book, OrderBook):
        market.yes_book = yes_book
        market.price_source = "clob"
    if no_book and isinstance(no_book, OrderBook):
        market.no_book = no_book

    market.enrich_from_books()
    return market


async def enrich_markets_concurrent(
    client: httpx.AsyncClient,
    markets: list[MarketData],
    only_binary: bool = True,
    min_liquidity: float = 500.0,
) -> list[MarketData]:
    """
    Concurrently enrich all markets with CLOB order books.
    Filters to binary YES/NO markets above min_liquidity.
    """
    candidates = [
        m for m in markets
        if m.liquidity >= min_liquidity
        and _is_binary(m)
    ]

    tasks = [enrich_market_with_clob(client, m) for m in candidates]
    enriched = await asyncio.gather(*tasks, return_exceptions=True)

    result = []
    for m in enriched:
        if isinstance(m, Exception):
            continue
        if m.has_prices:
            result.append(m)

    return result


def _is_binary(market: MarketData) -> bool:
    """Check if market has YES and NO books."""
    has_yes = market.yes_book is not None
    has_no = market.no_book is not None
    return has_yes and has_no
