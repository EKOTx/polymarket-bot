"""Paper trades API — user's simulated portfolio."""

from __future__ import annotations

from fastapi import APIRouter, Query
from sqlalchemy import desc

from backend.app.api.deps import CurrentUser, DbSession
from backend.app.models.market import PaperTrade, Portfolio
from backend.app.schemas.opportunity import ScannerStatusResponse

router = APIRouter(prefix="/trades", tags=["trades"])


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
