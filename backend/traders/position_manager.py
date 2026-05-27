"""
Position Manager — mark-to-market and resolution handling.

Each scan cycle:
  1. mark_to_market()  — update unrealized_pnl for all OPEN trades
  2. close_resolved()  — detect resolved markets, book realized PnL

Resolution detection:
  - YES wins:  yes_mid > 0.95 (market settled YES)
  - YES loses: yes_mid < 0.05 (market settled NO)
  - Market inactive: active=False AND price near 0 or 1
  - Also catches markets no longer in enriched set (delisted/expired)

PnL formula (YES BUY position):
  unrealized = (current_mid - entry_price) * size_shares
  realized   = (exit_price - entry_price) * size_shares  [at close]
  fee already paid at entry; no exit fee modeled
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from database.db import get_session
from database.models import PaperTrade as DBTrade, Portfolio as DBPortfolio
from models.market import MarketData
from utils.logging import get_logger

logger = get_logger(__name__)

# Resolution thresholds
YES_WIN_THRESHOLD  = 0.95   # yes_mid above this → YES resolved
YES_LOSE_THRESHOLD = 0.05   # yes_mid below this → NO resolved (YES loses)


# ── Mark to market ────────────────────────────────────────────────────────────

def mark_to_market(
    enriched_markets: list[MarketData],
    balance: float,
) -> tuple[float, int]:
    """
    Update unrealized_pnl for all OPEN trades based on current mid prices.

    Returns (total_unrealized_pnl, trades_updated).
    """
    mid_by_market: dict[str, float] = {
        m.market_id: m.yes_mid
        for m in enriched_markets
        if m.yes_mid is not None
    }

    updated = 0
    total_unrealized = 0.0

    with get_session() as session:
        open_trades = (
            session.query(DBTrade)
            .filter(DBTrade.status == "OPEN")
            .all()
        )

        for trade in open_trades:
            current_mid = mid_by_market.get(trade.market_id)
            if current_mid is None:
                # Market not in current enriched set — skip (not delisted yet)
                total_unrealized += trade.unrealized_pnl or 0.0
                continue

            # PnL: for YES BUY, profit when price rises
            if trade.outcome == "Yes":
                unrealized = (current_mid - trade.entry_price) * trade.size_shares
            elif trade.outcome == "No":
                # NO position profits when yes_mid falls
                no_mid = 1.0 - current_mid
                no_entry = 1.0 - trade.entry_price
                unrealized = (no_mid - no_entry) * trade.size_shares
            else:
                unrealized = 0.0

            trade.unrealized_pnl = round(unrealized, 4)
            total_unrealized += unrealized
            updated += 1

        if updated > 0:
            session.commit()

    return round(total_unrealized, 4), updated


# ── Resolution detection ──────────────────────────────────────────────────────

def _detect_resolution(
    trade: DBTrade,
    mid_by_market: dict[str, float],
    active_market_ids: set[str],
) -> Optional[tuple[str, float]]:
    """
    Determine if a trade's market has resolved.

    Returns (resolution, exit_price) or None if still open.
    resolution: "YES" | "NO"
    exit_price: price at which we close (1.0 for YES win, 0.0 for YES lose)
    """
    current_mid = mid_by_market.get(trade.market_id)

    if current_mid is not None:
        if trade.outcome == "Yes":
            if current_mid >= YES_WIN_THRESHOLD:
                return "YES", min(current_mid, 0.999)
            if current_mid <= YES_LOSE_THRESHOLD:
                return "NO", max(current_mid, 0.001)
        elif trade.outcome == "No":
            no_mid = 1.0 - current_mid
            if no_mid >= YES_WIN_THRESHOLD:
                return "YES", min(no_mid, 0.999)
            if no_mid <= YES_LOSE_THRESHOLD:
                return "NO", max(no_mid, 0.001)
    elif trade.market_id not in active_market_ids:
        # Market vanished from enriched set with no price update
        # Conservative: treat as expired/cancelled if held > 7 days
        if trade.opened_at:
            age_days = (datetime.utcnow() - trade.opened_at).days
            if age_days > 7:
                logger.warning(
                    "trade_market_missing",
                    trade_id=trade.id,
                    market_id=trade.market_id,
                    age_days=age_days,
                )
                return "NO", 0.001  # worst case

    return None


def close_resolved(
    enriched_markets: list[MarketData],
    paper_trader,   # PaperTrader instance (to update balance)
) -> list[dict]:
    """
    Find and close all trades whose markets have resolved.

    Returns list of close records for logging.
    """
    mid_by_market: dict[str, float] = {
        m.market_id: m.yes_mid
        for m in enriched_markets
        if m.yes_mid is not None
    }
    active_ids = {m.market_id for m in enriched_markets}

    closed_records = []

    with get_session() as session:
        open_trades = (
            session.query(DBTrade)
            .filter(DBTrade.status == "OPEN")
            .all()
        )

        for trade in open_trades:
            result = _detect_resolution(trade, mid_by_market, active_ids)
            if result is None:
                continue

            resolution, exit_price = result
            realized = (exit_price - trade.entry_price) * trade.size_shares

            trade.status = "CLOSED"
            trade.resolution = resolution
            trade.exit_price = round(exit_price, 4)
            trade.realized_pnl = round(realized, 4)
            trade.unrealized_pnl = 0.0
            trade.closed_at = datetime.utcnow()

            # Return proceeds to balance: cost + realized PnL
            proceeds = trade.cost_usd + realized
            paper_trader.balance += proceeds
            paper_trader.daily_loss -= min(realized, 0)  # track losses

            closed_records.append({
                "trade_id": trade.id,
                "market_id": trade.market_id,
                "question": trade.question[:60],
                "resolution": resolution,
                "entry": trade.entry_price,
                "exit": exit_price,
                "realized_pnl": round(realized, 4),
                "proceeds": round(proceeds, 4),
            })

            logger.info(
                "trade_closed",
                trade_id=trade.id,
                resolution=resolution,
                realized_pnl=round(realized, 4),
                question=trade.question[:50],
            )

        if closed_records:
            session.commit()

    return closed_records


# ── Performance stats ─────────────────────────────────────────────────────────

def get_performance_stats() -> dict:
    """
    Compute strategy performance metrics from all closed trades.

    Returns:
      - win_rate, avg_win, avg_loss, profit_factor
      - realized_pnl total
      - per-strategy breakdown
      - sharpe (approximate, from portfolio snapshots)
    """
    with get_session() as session:
        closed = (
            session.query(DBTrade)
            .filter(DBTrade.status == "CLOSED")
            .all()
        )

        if not closed:
            return {"message": "No closed trades yet"}

        wins   = [t for t in closed if (t.realized_pnl or 0) > 0]
        losses = [t for t in closed if (t.realized_pnl or 0) <= 0]

        total_pnl   = sum(t.realized_pnl or 0 for t in closed)
        gross_profit = sum(t.realized_pnl for t in wins if t.realized_pnl)
        gross_loss   = sum(abs(t.realized_pnl) for t in losses if t.realized_pnl)

        # Per-strategy breakdown
        by_strategy: dict[str, dict] = {}
        for t in closed:
            strat = t.strategy or "unknown"
            if strat not in by_strategy:
                by_strategy[strat] = {"trades": 0, "wins": 0, "pnl": 0.0, "cost": 0.0}
            by_strategy[strat]["trades"] += 1
            by_strategy[strat]["pnl"] += t.realized_pnl or 0
            by_strategy[strat]["cost"] += t.cost_usd or 0
            if (t.realized_pnl or 0) > 0:
                by_strategy[strat]["wins"] += 1

        for strat, d in by_strategy.items():
            d["win_rate"] = round(d["wins"] / max(d["trades"], 1), 3)
            d["roi_pct"] = round(d["pnl"] / max(d["cost"], 1) * 100, 2)

        # Sharpe from daily portfolio snapshots
        sharpe = _compute_sharpe(session)

        return {
            "total_closed": len(closed),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": round(len(wins) / max(len(closed), 1), 3),
            "total_realized_pnl": round(total_pnl, 2),
            "gross_profit": round(gross_profit, 2),
            "gross_loss": round(gross_loss, 2),
            "profit_factor": round(gross_profit / max(gross_loss, 0.01), 3),
            "avg_win": round(gross_profit / max(len(wins), 1), 2),
            "avg_loss": round(gross_loss / max(len(losses), 1), 2),
            "sharpe": sharpe,
            "by_strategy": by_strategy,
        }


def _compute_sharpe(session) -> Optional[float]:
    """
    Approximate Sharpe from daily portfolio balance changes.
    Annualized, risk-free rate = 0.
    """
    from sqlalchemy import text, func
    import math

    rows = session.execute(
        text("""
            SELECT DATE(timestamp) as day, AVG(balance) as avg_bal
            FROM portfolio
            GROUP BY DATE(timestamp)
            ORDER BY day ASC
        """)
    ).fetchall()

    if len(rows) < 3:
        return None

    balances = [float(r[1]) for r in rows]
    returns = [
        (balances[i] - balances[i - 1]) / balances[i - 1]
        for i in range(1, len(balances))
    ]

    if not returns:
        return None

    n = len(returns)
    mean_r = sum(returns) / n
    variance = sum((r - mean_r) ** 2 for r in returns) / max(n - 1, 1)
    std_r = math.sqrt(variance)

    if std_r < 1e-10:
        return None

    sharpe = (mean_r / std_r) * math.sqrt(252)  # annualized
    return round(sharpe, 3)
