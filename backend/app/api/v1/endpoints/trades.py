"""Paper trades API — user's simulated portfolio."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, field_validator
from sqlalchemy import desc, func

from backend.app.api.deps import CurrentUser, DbSession
from backend.app.core.config import settings
from backend.app.models.market import Opportunity, PaperTrade, Portfolio
from backend.app.schemas.opportunity import ScannerStatusResponse

router = APIRouter(prefix="/trades", tags=["trades"])

SLIPPAGE = 0.002
FEE_PCT  = 0.01


class PlaceTradeIn(BaseModel):
    opportunity_id: int
    outcome: str = "YES"
    size_usd: float

    @field_validator("outcome")
    @classmethod
    def validate_outcome(cls, v: str) -> str:
        if v.upper() not in ("YES", "NO"):
            raise ValueError("outcome must be YES or NO")
        return v.upper()

    @field_validator("size_usd")
    @classmethod
    def validate_size(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("size_usd must be positive")
        return v


def _portfolio_snap(db, user_id: int) -> tuple[float, float]:
    """Return (balance, starting_balance) for user, defaulting to config."""
    snap = (
        db.query(Portfolio)
        .filter(Portfolio.user_id == user_id)
        .order_by(desc(Portfolio.timestamp))
        .first()
    )
    if snap:
        return snap.balance, snap.starting_balance
    return settings.PAPER_STARTING_BALANCE, settings.PAPER_STARTING_BALANCE


def _save_portfolio(db, user_id: int, new_balance: float, starting: float) -> None:
    open_trades = (
        db.query(PaperTrade)
        .filter(PaperTrade.user_id == user_id, PaperTrade.status == "OPEN")
        .all()
    )
    realized = db.query(
        func.coalesce(func.sum(PaperTrade.realized_pnl), 0)
    ).filter(PaperTrade.user_id == user_id, PaperTrade.status == "CLOSED").scalar() or 0.0

    snap = Portfolio(
        user_id=user_id,
        balance=round(new_balance, 4),
        starting_balance=starting,
        total_invested=round(sum(t.cost_usd for t in open_trades), 4),
        realized_pnl=round(float(realized), 4),
        unrealized_pnl=round(sum(t.unrealized_pnl or 0 for t in open_trades), 4),
        open_positions=len(open_trades),
        total_trades=db.query(PaperTrade).filter(PaperTrade.user_id == user_id).count(),
        timestamp=datetime.utcnow(),
    )
    db.add(snap)


@router.post("", status_code=201)
def place_trade(body: PlaceTradeIn, user: CurrentUser, db: DbSession):
    """Place a manual paper trade on an opportunity."""
    opp = db.query(Opportunity).filter(Opportunity.id == body.opportunity_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    balance, starting = _portfolio_snap(db, user.id)
    cost = min(body.size_usd, settings.PAPER_MAX_POSITION_SIZE)

    # Risk checks
    if cost > balance:
        raise HTTPException(400, f"Insufficient balance: ${balance:.2f} available")

    open_trades = (
        db.query(PaperTrade)
        .filter(PaperTrade.user_id == user.id, PaperTrade.status == "OPEN")
        .all()
    )
    if len(open_trades) >= settings.PAPER_MAX_OPEN_POSITIONS:
        raise HTTPException(400, f"Max open positions reached ({settings.PAPER_MAX_OPEN_POSITIONS})")

    total_invested = sum(t.cost_usd for t in open_trades)
    max_exposure = starting * settings.PAPER_MAX_EXPOSURE_PCT
    if total_invested + cost > max_exposure:
        raise HTTPException(
            400,
            f"Exposure limit: ${total_invested:.0f} + ${cost:.0f} > ${max_exposure:.0f}",
        )

    if opp.market_id:
        dup = db.query(PaperTrade).filter(
            PaperTrade.user_id == user.id,
            PaperTrade.market_id == opp.market_id,
            PaperTrade.status == "OPEN",
        ).first()
        if dup:
            raise HTTPException(400, "Already have an open position on this market")

    # Pricing
    if body.outcome == "NO":
        raw_ask = opp.no_ask or (1.0 - (opp.yes_bid or 0.5))
    else:
        raw_ask = opp.yes_ask or 0.5

    entry_price = min(raw_ask * (1 + SLIPPAGE), 0.999)
    fee = cost * FEE_PCT
    total_cost = cost + fee
    shares = cost / entry_price

    trade = PaperTrade(
        user_id=user.id,
        opportunity_id=opp.id,
        market_id=opp.market_id or "",
        question=opp.title[:200],
        event_title=opp.event_title[:200],
        outcome=body.outcome,
        side="BUY",
        strategy=str(opp.opportunity_type).rsplit(".", 1)[-1],
        entry_price=round(entry_price, 6),
        size_shares=round(shares, 4),
        cost_usd=round(total_cost, 4),
        unrealized_pnl=0.0,
        status="OPEN",
        notes=json.dumps({"slippage_pct": SLIPPAGE * 100, "fee_usd": round(fee, 4), "edge_pct": opp.edge_pct}),
        opened_at=datetime.utcnow(),
    )
    db.add(trade)
    db.flush()

    new_balance = balance - total_cost
    _save_portfolio(db, user.id, new_balance, starting)
    db.commit()
    db.refresh(trade)

    return {
        "id": trade.id,
        "market_id": trade.market_id,
        "question": trade.question,
        "outcome": trade.outcome,
        "strategy": trade.strategy,
        "entry_price": trade.entry_price,
        "size_shares": trade.size_shares,
        "cost_usd": trade.cost_usd,
        "unrealized_pnl": trade.unrealized_pnl,
        "status": trade.status,
        "opened_at": trade.opened_at,
        "new_balance": round(new_balance, 2),
    }


@router.get("")
def list_trades(
    user: CurrentUser,
    db: DbSession,
    status: str | None = Query(None, description="OPEN|CLOSED"),
    limit: int = Query(50, ge=1, le=200),
):
    """List user's paper trades."""
    q = db.query(PaperTrade).filter(PaperTrade.user_id == user.id)
    if status:
        q = q.filter(PaperTrade.status == status.upper())
    trades = q.order_by(desc(PaperTrade.opened_at)).limit(limit).all()
    return [
        {
            "id": t.id,
            "market_id": t.market_id,
            "question": t.question,
            "outcome": t.outcome,
            "strategy": t.strategy,
            "entry_price": t.entry_price,
            "exit_price": t.exit_price,
            "size_shares": t.size_shares,
            "cost_usd": t.cost_usd,
            "realized_pnl": t.realized_pnl,
            "unrealized_pnl": t.unrealized_pnl,
            "status": t.status,
            "resolution": t.resolution,
            "opened_at": t.opened_at,
            "closed_at": t.closed_at,
        }
        for t in trades
    ]


@router.get("/portfolio")
def get_portfolio(user: CurrentUser, db: DbSession):
    """Current portfolio snapshot."""
    snap = (
        db.query(Portfolio)
        .filter(Portfolio.user_id == user.id)
        .order_by(desc(Portfolio.timestamp))
        .first()
    )
    if not snap:
        return {
            "balance": 10000.0,
            "starting_balance": 10000.0,
            "total_invested": 0.0,
            "realized_pnl": 0.0,
            "unrealized_pnl": 0.0,
            "open_positions": 0,
            "total_trades": 0,
        }
    return {
        "balance": snap.balance,
        "starting_balance": snap.starting_balance,
        "total_invested": snap.total_invested,
        "realized_pnl": snap.realized_pnl,
        "unrealized_pnl": snap.unrealized_pnl,
        "open_positions": snap.open_positions,
        "total_trades": snap.total_trades,
        "timestamp": snap.timestamp,
    }


@router.get("/portfolio/history")
def get_portfolio_history(
    user: CurrentUser,
    db: DbSession,
    limit: int = Query(200, ge=10, le=1000),
):
    """Portfolio balance over time."""
    snaps = (
        db.query(Portfolio)
        .filter(Portfolio.user_id == user.id)
        .order_by(desc(Portfolio.timestamp))
        .limit(limit)
        .all()
    )
    return [
        {"timestamp": s.timestamp, "balance": s.balance,
         "realized_pnl": s.realized_pnl, "unrealized_pnl": s.unrealized_pnl}
        for s in reversed(snaps)
    ]
