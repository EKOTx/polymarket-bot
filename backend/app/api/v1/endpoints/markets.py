"""
Markets API — market detail with price history, opportunities, and trades.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import desc

from backend.app.api.deps import CurrentUser, DbSession
from backend.app.models.market import Market, Opportunity, PaperTrade, PriceSnapshot
from backend.app.schemas.opportunity import OpportunityOut

router = APIRouter(prefix="/markets", tags=["markets"])


class PricePoint(BaseModel):
    timestamp: datetime
    outcome: str
    bid: Optional[float]
    ask: Optional[float]
    mid: Optional[float]
    spread: Optional[float]
    bid_depth_usd: Optional[float]
    ask_depth_usd: Optional[float]


class MarketDetailResponse(BaseModel):
    id: str
    question: str
    event_title: str
    volume: float
    liquidity: float
    active: bool
    outcomes: list[str]
    outcome_prices: list[float]
    first_seen: datetime
    last_updated: datetime
    price_history: list[PricePoint]
    recent_opportunities: list[OpportunityOut]
    open_trades: list[dict]


def _parse_json_list(raw: str, cast=None) -> list:
    try:
        result = json.loads(raw or "[]")
        if cast:
            return [cast(x) for x in result]
        return result
    except Exception:
        return []


@router.get("/{market_id}", response_model=MarketDetailResponse)
def get_market_detail(
    market_id: str,
    user: CurrentUser,
    db: DbSession,
    history_limit: int = 200,
):
    market = db.query(Market).filter(Market.id == market_id).first()
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")

    snapshots = (
        db.query(PriceSnapshot)
        .filter(PriceSnapshot.market_id == market_id)
        .order_by(desc(PriceSnapshot.timestamp))
        .limit(history_limit)
        .all()
    )
    price_history = [
        PricePoint(
            timestamp=s.timestamp,
            outcome=s.outcome,
            bid=s.bid,
            ask=s.ask,
            mid=s.mid,
            spread=s.spread,
            bid_depth_usd=s.bid_depth_usd,
            ask_depth_usd=s.ask_depth_usd,
        )
        for s in reversed(snapshots)
    ]

    opps = (
        db.query(Opportunity)
        .filter(Opportunity.market_id == market_id)
        .order_by(desc(Opportunity.timestamp))
        .limit(10)
        .all()
    )
    recent_opportunities = [OpportunityOut.model_validate(o) for o in opps]

    trades = (
        db.query(PaperTrade)
        .filter(PaperTrade.market_id == market_id)
        .order_by(desc(PaperTrade.opened_at))
        .limit(20)
        .all()
    )
    open_trades = [
        {
            "id": t.id,
            "question": t.question,
            "outcome": t.outcome,
            "strategy": t.strategy,
            "status": t.status,
            "entry_price": t.entry_price,
            "exit_price": t.exit_price,
            "size_shares": t.size_shares,
            "cost_usd": t.cost_usd,
            "realized_pnl": t.realized_pnl,
            "unrealized_pnl": t.unrealized_pnl,
            "resolution": t.resolution,
            "opened_at": t.opened_at,
            "closed_at": t.closed_at,
        }
        for t in trades
    ]

    return MarketDetailResponse(
        id=market.id,
        question=market.question,
        event_title=market.event_title,
        volume=market.volume,
        liquidity=market.liquidity,
        active=market.active,
        outcomes=_parse_json_list(market.outcomes),
        outcome_prices=_parse_json_list(market.outcome_prices, float),
        first_seen=market.first_seen,
        last_updated=market.last_updated,
        price_history=price_history,
        recent_opportunities=recent_opportunities,
        open_trades=open_trades,
    )
