"""
Paper trading engine.
Simulates fills with slippage, tracks positions and PnL.
Writes to SQLite via SQLAlchemy.

NEVER sends real orders. Real trading path raises NotImplementedError.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, date
from typing import Optional

from database.db import get_session
from database.models import PaperTrade as DBTrade, Portfolio as DBPortfolio
from models.opportunity import Opportunity
from utils.logging import get_logger

logger = get_logger(__name__)

PAPER_STARTING_BALANCE = float(os.getenv("PAPER_STARTING_BALANCE", "10000"))
PAPER_MAX_POSITION_SIZE = float(os.getenv("PAPER_MAX_POSITION_SIZE", "500"))
PAPER_MAX_DAILY_LOSS = float(os.getenv("PAPER_MAX_DAILY_LOSS", "1000"))
PAPER_MAX_OPEN_POSITIONS = int(os.getenv("PAPER_MAX_OPEN_POSITIONS", "10"))
# Max % of balance deployed at once
PAPER_MAX_EXPOSURE_PCT = float(os.getenv("PAPER_MAX_EXPOSURE_PCT", "0.40"))

# Simulated fee: 1% of trade cost
SIMULATED_FEE_PCT = 0.01


class PaperTrader:
    """
    Stateful paper trading engine.

    Maintains in-memory balance and position tracking.
    Persists all trades and portfolio snapshots to DB.
    """

    def __init__(self):
        self.balance = PAPER_STARTING_BALANCE
        self.starting_balance = PAPER_STARTING_BALANCE
        self.daily_loss = 0.0
        self.daily_loss_date: Optional[date] = None
        self._load_state()

    def _load_state(self) -> None:
        """Restore balance from last portfolio snapshot."""
        try:
            with get_session() as session:
                latest = (
                    session.query(DBPortfolio)
                    .order_by(DBPortfolio.timestamp.desc())
                    .first()
                )
                if latest:
                    self.balance = latest.balance
                    self.starting_balance = latest.starting_balance
                    logger.info("paper_trader_state_loaded", balance=self.balance)
        except Exception as e:
            logger.warning("paper_trader_load_failed", error=str(e))

    # ── Risk checks ──────────────────────────────────────────────────────────

    def _check_daily_loss_reset(self) -> None:
        """Reset daily loss counter on new day."""
        today = date.today()
        if self.daily_loss_date != today:
            self.daily_loss = 0.0
            self.daily_loss_date = today

    def _can_trade(self, cost_usd: float) -> tuple[bool, str]:
        """Check all risk limits before executing a paper trade."""
        self._check_daily_loss_reset()

        if cost_usd > self.balance:
            return False, f"Insufficient balance: ${self.balance:.2f} < ${cost_usd:.2f}"

        if cost_usd > PAPER_MAX_POSITION_SIZE:
            return False, f"Size ${cost_usd:.2f} > max ${PAPER_MAX_POSITION_SIZE:.2f}"

        # Max open positions
        try:
            with get_session() as session:
                open_count = (
                    session.query(DBTrade)
                    .filter(DBTrade.status == "OPEN")
                    .count()
                )
                if open_count >= PAPER_MAX_OPEN_POSITIONS:
                    return False, f"Max open positions reached: {open_count}/{PAPER_MAX_OPEN_POSITIONS}"

                # Max total exposure (% of starting balance)
                total_invested = sum(
                    t.cost_usd for t in
                    session.query(DBTrade).filter(DBTrade.status == "OPEN").all()
                )
                max_exposure = self.starting_balance * PAPER_MAX_EXPOSURE_PCT
                if total_invested + cost_usd > max_exposure:
                    return False, (
                        f"Exposure limit: ${total_invested:.0f}+${cost_usd:.0f} "
                        f"> ${max_exposure:.0f} ({PAPER_MAX_EXPOSURE_PCT*100:.0f}% of balance)"
                    )
        except Exception as e:
            logger.warning("paper_trade_risk_check_failed", error=str(e))

        if self.daily_loss >= PAPER_MAX_DAILY_LOSS:
            return False, f"Daily loss limit hit: ${self.daily_loss:.2f}"

        return True, "ok"

    # ── Execution ────────────────────────────────────────────────────────────

    def execute(
        self,
        opportunity: Opportunity,
        size_usd: Optional[float] = None,
    ) -> Optional[DBTrade]:
        """
        Simulate buying the best outcome for an opportunity.

        For VALUE opportunities: buys YES at yes_ask.
        For TOURNAMENT_ARB: buys all outcomes (one trade per outcome logged).
        For VIG opportunities: no trade (informational only).

        Returns the created DBTrade or None if rejected.
        """
        opp_type = str(opportunity.opportunity_type)

        if "VIG" in opp_type or "SPREAD" in opp_type:
            # These are informational, not direct trades
            return None

        # Don't double-up: skip if already have an OPEN position in this market
        if opportunity.market_id:
            try:
                with get_session() as session:
                    existing = (
                        session.query(DBTrade)
                        .filter(
                            DBTrade.market_id == opportunity.market_id,
                            DBTrade.status == "OPEN",
                        )
                        .first()
                    )
                    if existing:
                        logger.debug(
                            "paper_trade_skipped_duplicate",
                            market_id=opportunity.market_id,
                            title=opportunity.title[:40],
                        )
                        return None
            except Exception as e:
                logger.warning("paper_trade_dedup_check_failed", error=str(e))

        cost = size_usd or opportunity.suggested_size_usd
        if cost <= 0:
            cost = min(50.0, PAPER_MAX_POSITION_SIZE)

        ok, reason = self._can_trade(cost)
        if not ok:
            logger.warning("paper_trade_rejected", reason=reason, opp=opportunity.title[:40])
            return None

        # Simulate slippage (0.2% for now, depth-based later)
        slippage = 0.002
        entry_price = (opportunity.yes_ask or 0.5) * (1 + slippage)
        entry_price = min(entry_price, 0.999)

        fee = cost * SIMULATED_FEE_PCT
        total_cost = cost + fee
        shares = cost / entry_price if entry_price > 0 else 0

        self.balance -= total_cost

        trade = DBTrade(
            opportunity_id=opportunity.scan_id,
            market_id=opportunity.market_id or "",
            question=opportunity.title[:200],
            event_title=opportunity.event_title[:200],
            outcome="Yes",
            side="BUY",
            strategy=opp_type,
            entry_price=round(entry_price, 6),
            size_shares=round(shares, 4),
            cost_usd=round(total_cost, 4),
            unrealized_pnl=0.0,
            status="OPEN",
            notes=json.dumps({
                "slippage_pct": slippage * 100,
                "fee_usd": round(fee, 4),
                "edge_pct": opportunity.edge_pct,
                "confidence": opportunity.confidence,
            }),
            opened_at=datetime.utcnow(),
        )

        try:
            with get_session() as session:
                session.add(trade)
                session.flush()
                session.refresh(trade)
                trade_id = trade.id
                session.commit()
        except Exception as e:
            self.balance += total_cost  # rollback in-memory
            logger.error("paper_trade_db_error", error=str(e))
            return None

        logger.info(
            "paper_trade_executed",
            trade_id=trade_id,
            strategy=opp_type,
            cost=round(total_cost, 2),
            balance=round(self.balance, 2),
        )

        self._save_portfolio_snapshot()
        return trade

    def _save_portfolio_snapshot(self) -> None:
        """Write current portfolio state to DB."""
        try:
            with get_session() as session:
                open_trades = (
                    session.query(DBTrade)
                    .filter(DBTrade.status == "OPEN")
                    .all()
                )
                total_invested = sum(t.cost_usd for t in open_trades)
                unrealized = sum(t.unrealized_pnl or 0 for t in open_trades)

                # Sum realized PnL from closed trades
                from sqlalchemy import func
                realized = session.query(
                    func.coalesce(func.sum(DBTrade.realized_pnl), 0)
                ).filter(DBTrade.status == "CLOSED").scalar() or 0.0

                snap = DBPortfolio(
                    balance=round(self.balance, 4),
                    starting_balance=self.starting_balance,
                    total_invested=round(total_invested, 4),
                    realized_pnl=round(float(realized), 4),
                    unrealized_pnl=round(unrealized, 4),
                    open_positions=len(open_trades),
                    total_trades=session.query(DBTrade).count(),
                    timestamp=datetime.utcnow(),
                )
                session.add(snap)
                session.commit()
        except Exception as e:
            logger.warning("portfolio_snapshot_failed", error=str(e))

    # ── Statistics ───────────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """Return current portfolio statistics."""
        try:
            with get_session() as session:
                total = session.query(DBTrade).count()
                open_c = session.query(DBTrade).filter(DBTrade.status == "OPEN").count()
                closed = session.query(DBTrade).filter(DBTrade.status == "CLOSED").all()

                wins = sum(1 for t in closed if (t.realized_pnl or 0) > 0)
                realized = sum(t.realized_pnl or 0 for t in closed)

                return {
                    "balance": self.balance,
                    "starting_balance": self.starting_balance,
                    "pnl": self.balance - self.starting_balance + realized,
                    "realized_pnl": realized,
                    "total_trades": total,
                    "open_trades": open_c,
                    "closed_trades": len(closed),
                    "win_rate": wins / max(len(closed), 1),
                }
        except Exception:
            return {"balance": self.balance, "starting_balance": self.starting_balance}


# ── Real trading guard ────────────────────────────────────────────────────────

def execute_real_trade(opportunity: Opportunity) -> None:
    """
    Placeholder for real trade execution.
    ALWAYS raises unless ENABLE_REAL_TRADING=true (not yet implemented).
    """
    enable = os.getenv("ENABLE_REAL_TRADING", "false").lower()
    if enable != "true":
        raise RuntimeError(
            "Real trading is DISABLED. Set ENABLE_REAL_TRADING=true in .env "
            "and implement authenticated order placement to enable."
        )
    raise NotImplementedError(
        "Real trading execution not yet implemented. "
        "Implement polymarket_client.place_order() with proper auth."
    )
