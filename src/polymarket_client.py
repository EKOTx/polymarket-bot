"""
polymarket_client.py - Fetch and normalize Polymarket data.

Uses public endpoints - no auth needed for scanning.
Authenticated trading endpoints stubbed out for later.
"""

import json
import requests
from typing import Optional
import config
from src.utils import safe_float


# Shared session for connection reuse
_session = requests.Session()
_session.headers.update({"User-Agent": "polymarket-bot/1.0"})

# Request timeout in seconds
TIMEOUT = 10


def _get(url: str, params: dict = None) -> Optional[dict | list]:
    """
    GET request with error handling. Returns parsed JSON or None.
    Never raises - prints error and returns None instead.
    """
    try:
        resp = _session.get(url, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        print(f"[client] Connection error: {url}")
    except requests.exceptions.Timeout:
        print(f"[client] Timeout after {TIMEOUT}s: {url}")
    except requests.exceptions.HTTPError as e:
        print(f"[client] HTTP {e.response.status_code}: {url}")
    except requests.exceptions.RequestException as e:
        print(f"[client] Request error: {e}")
    except json.JSONDecodeError:
        print(f"[client] Bad JSON response from: {url}")
    return None


def fetch_markets(limit: int = 50) -> list[dict]:
    """
    Fetch active markets from Gamma API with pagination.

    Gamma API caps each page at 100. If limit > 100, fetches multiple pages.

    Returns list of normalized market dicts. Each dict has:
      - id, question, event_title
      - volume, liquidity (floats)
      - outcomes: list of str ["Yes", "No"]
      - outcome_prices: list of float (mid prices)
      - clob_token_ids: list of str (for order book lookup)
      - active: bool
    """
    url = f"{config.GAMMA_API_BASE}/markets"
    page_size = 100  # API maximum per page
    all_raw = []
    offset = 0

    while len(all_raw) < limit:
        batch_size = min(page_size, limit - len(all_raw))
        params = {
            "active": "true",
            "closed": "false",
            "limit": batch_size,
            "offset": offset,
        }
        raw = _get(url, params=params)
        if not raw:
            break
        all_raw.extend(raw)
        if len(raw) < batch_size:
            break  # no more pages
        offset += len(raw)

    markets = []
    for item in all_raw:
        normalized = _normalize_market(item)
        if normalized:
            markets.append(normalized)

    return markets


def _normalize_market(raw: dict) -> Optional[dict]:
    """
    Convert raw Gamma API market dict to clean internal format.
    Returns None if market is missing critical fields.
    """
    # Parse JSON string fields
    try:
        outcomes = json.loads(raw.get("outcomes", "[]"))
        outcome_prices = json.loads(raw.get("outcomePrices", "[]"))
        clob_token_ids = json.loads(raw.get("clobTokenIds", "[]"))
    except (json.JSONDecodeError, TypeError):
        return None

    # Need at least outcomes and prices
    if not outcomes or not outcome_prices:
        return None

    # Get event title
    events = raw.get("events", [])
    event_title = events[0].get("title", "") if events else ""

    return {
        "id": raw.get("id", ""),
        "question": raw.get("question", "Unknown"),
        "event_title": event_title,
        "volume": safe_float(raw.get("volume", 0)),
        "liquidity": safe_float(raw.get("liquidity", 0)),
        "outcomes": outcomes,
        "outcome_prices": [safe_float(p) for p in outcome_prices],
        "clob_token_ids": clob_token_ids,
        "active": raw.get("active", False),
        "closed": raw.get("closed", True),
    }


def fetch_order_book(token_id: str) -> Optional[dict]:
    """
    Fetch order book for a single token from CLOB API.

    Returns dict with:
      - bids: list of {"price": float, "size": float}
      - asks: list of {"price": float, "size": float}
      - best_bid: float or None
      - best_ask: float or None

    Returns None if fetch fails.
    """
    url = f"{config.CLOB_API_BASE}/book"
    params = {"token_id": token_id}

    raw = _get(url, params=params)
    if not raw:
        return None

    return _normalize_order_book(raw)


def _normalize_order_book(raw: dict) -> dict:
    """Convert raw CLOB order book to clean format."""
    bids = []
    for b in raw.get("bids", []):
        price = safe_float(b.get("price"))
        size = safe_float(b.get("size"))
        if price > 0 and size > 0:
            bids.append({"price": price, "size": size})

    asks = []
    for a in raw.get("asks", []):
        price = safe_float(a.get("price"))
        size = safe_float(a.get("size"))
        if price > 0 and size > 0:
            asks.append({"price": price, "size": size})

    # Best bid = highest price someone is willing to buy at
    best_bid = max((b["price"] for b in bids), default=None)
    # Best ask = lowest price someone is willing to sell at
    best_ask = min((a["price"] for a in asks), default=None)

    return {
        "bids": bids,
        "asks": asks,
        "best_bid": best_bid,
        "best_ask": best_ask,
    }


def fetch_market_prices(market: dict) -> Optional[dict]:
    """
    Get YES/NO bid-ask prices for a market.

    Tries CLOB order book first (accurate bid/ask).
    Falls back to outcome_prices from gamma (mid price only).

    Returns dict with:
      - yes_bid, yes_ask, no_bid, no_ask (all floats or None)
      - source: "clob" or "gamma"
    """
    token_ids = market.get("clob_token_ids", [])
    outcomes = market.get("outcomes", [])

    # Find YES and NO token IDs
    yes_token_id = None
    no_token_id = None
    for token_id, outcome in zip(token_ids, outcomes):
        name = outcome.lower()
        if name == "yes":
            yes_token_id = token_id
        elif name == "no":
            no_token_id = token_id

    # Try CLOB first for real bid/ask data
    if yes_token_id and no_token_id:
        yes_book = fetch_order_book(yes_token_id)
        no_book = fetch_order_book(no_token_id)

        if yes_book and no_book:
            yes_bid = yes_book["best_bid"]
            yes_ask = yes_book["best_ask"]
            no_bid = no_book["best_bid"]
            no_ask = no_book["best_ask"]

            # Only use CLOB data if we have all 4 values
            if all(v is not None for v in [yes_bid, yes_ask, no_bid, no_ask]):
                return {
                    "yes_bid": yes_bid,
                    "yes_ask": yes_ask,
                    "no_bid": no_bid,
                    "no_ask": no_ask,
                    "source": "clob",
                }

    # Fallback: use gamma outcome prices (these are mid prices, not bid/ask)
    prices = market.get("outcome_prices", [])
    outcomes_list = market.get("outcomes", [])

    yes_mid = None
    no_mid = None
    for outcome, price in zip(outcomes_list, prices):
        name = outcome.lower()
        if name == "yes":
            yes_mid = price
        elif name == "no":
            no_mid = price

    if yes_mid is not None and no_mid is not None:
        # Estimate bid/ask from mid price with a small synthetic spread
        # This is approximate - real spread from CLOB is much better
        spread = 0.01  # 1% synthetic spread
        return {
            "yes_bid": yes_mid - spread / 2,
            "yes_ask": yes_mid + spread / 2,
            "no_bid": no_mid - spread / 2,
            "no_ask": no_mid + spread / 2,
            "source": "gamma",
        }

    return None


# ── Authenticated trading (NOT IMPLEMENTED) ─────────────────────────────────────

def place_order(token_id: str, side: str, price: float, size: float) -> dict:
    """
    Place a real order. NOT IMPLEMENTED - raises error to prevent accidents.

    This function exists as a placeholder for future authenticated trading.
    Only callable when DRY_RUN=false and credentials are configured.
    """
    raise NotImplementedError(
        "Real trading is not implemented. Set DRY_RUN=true or use paper_trader."
    )
