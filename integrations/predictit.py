"""
PredictIt async API client.

Uses: https://www.predictit.org/api/marketdata/all/
Fully public, no auth needed.

One PredictIt market = multiple binary contracts (unlike Kalshi).
Each contract: bestBuyYesCost = ask, bestSellYesCost = bid (both in [0, 1]).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

PREDICTIT_URL = "https://www.predictit.org/api/marketdata/all/"
REQUEST_TIMEOUT = 15.0


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8), reraise=True)
async def _get(client: httpx.AsyncClient, url: str) -> dict:
    resp = await client.get(url, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


async def fetch_all_markets(client: httpx.AsyncClient) -> list[dict]:
    """
    Fetch all PredictIt markets and expand to individual contracts.

    One PI market → N contracts (one per candidate/outcome).
    Returns flat list of normalized contract dicts.
    """
    try:
        data = await _get(client, PREDICTIT_URL)
    except Exception as e:
        print(f"[predictit] fetch error: {e}")
        return []

    pi_markets = data.get("markets", [])
    contracts: list[dict] = []

    for market in pi_markets:
        market_id = market.get("id", "")
        market_name = market.get("name", "")
        market_url = market.get("url", "")
        status = market.get("status", "")

        if status.lower() not in ("open", ""):
            continue

        for contract in market.get("contracts", []):
            normalized = _normalize_contract(
                contract,
                market_id=market_id,
                market_name=market_name,
                market_url=market_url,
            )
            if normalized:
                contracts.append(normalized)

    return contracts


def _normalize_contract(
    contract: dict,
    market_id: int | str,
    market_name: str,
    market_url: str,
) -> Optional[dict]:
    """Normalize one PredictIt contract to internal format."""
    ask = contract.get("bestBuyYesCost")   # price to BUY YES
    bid = contract.get("bestSellYesCost")  # price to SELL YES (= bid)
    last = contract.get("lastTradePrice")

    # Skip if no price data
    if ask is None and bid is None and last is None:
        return None

    ask = float(ask) if ask is not None else None
    bid = float(bid) if bid is not None else None
    last = float(last) if last is not None else None

    # Use last trade as fallback mid
    if ask is not None and bid is not None:
        mid = (ask + bid) / 2
    elif ask is not None:
        mid = ask
    elif bid is not None:
        mid = bid
    else:
        mid = last

    if mid is None or mid <= 0.001:
        return None

    contract_id = contract.get("id", "")
    contract_name = contract.get("name", "")

    # Build composite title: "Market Name — Contract Name"
    if contract_name and contract_name.lower() != "yes":
        full_title = f"{market_name} — {contract_name}"
        outcome_label = contract_name
    else:
        full_title = market_name
        outcome_label = "Yes"

    return {
        "platform": "predictit",
        "platform_market_id": f"pi_{market_id}_{contract_id}",
        "parent_market_id": str(market_id),
        "parent_market_name": market_name,
        "contract_id": str(contract_id),
        "contract_name": contract_name,
        "outcome_label": outcome_label,
        "title": full_title,
        "yes_ask": round(ask, 4) if ask is not None else None,
        "yes_bid": round(bid, 4) if bid is not None else None,
        "mid": round(mid, 4),
        "last_trade": round(last, 4) if last is not None else None,
        "volume": contract.get("volume") or 0,
        "open_interest": contract.get("openInterest") or 0,
        "status": contract.get("status", ""),
        "url": market_url,
        "fetched_at": datetime.utcnow().isoformat(),
    }
