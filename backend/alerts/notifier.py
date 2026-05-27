"""
AlertManager — decides when and what to alert.

Deduplication: tracks alerted (market_id, type) pairs with TTL.
Won't re-alert the same opportunity within ALERT_COOLDOWN_MINUTES.

Triggers:
  1. New VALUE opportunity above ALERT_MIN_EDGE_PCT
  2. Tournament ARB detected
  3. Position closed (win or loss)
  4. Daily digest (once per day at first scan after ALERT_DIGEST_HOUR UTC)
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import httpx

from alerts import webhook as wh
from models.opportunity import Opportunity, OpportunityType
from traders.position_manager import get_performance_stats
from utils.logging import get_logger

if TYPE_CHECKING:
    from traders.paper_trader import PaperTrader

logger = get_logger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL", "")
SLACK_WEBHOOK   = os.getenv("SLACK_WEBHOOK_URL", "")

ALERT_MIN_EDGE_PCT      = float(os.getenv("ALERT_MIN_EDGE_PCT", "3.0"))
ALERT_COOLDOWN_MINUTES  = int(os.getenv("ALERT_COOLDOWN_MINUTES", "60"))
ALERT_DIGEST_HOUR       = int(os.getenv("ALERT_DIGEST_HOUR", "8"))   # UTC hour for daily digest
ALERT_ON_CLOSE          = os.getenv("ALERT_ON_CLOSE", "true").lower() == "true"
ALERT_ON_OPPORTUNITY    = os.getenv("ALERT_ON_OPPORTUNITY", "true").lower() == "true"
ALERT_ON_DIGEST         = os.getenv("ALERT_ON_DIGEST", "true").lower() == "true"

ENABLED = bool(DISCORD_WEBHOOK or SLACK_WEBHOOK)


class AlertManager:
    """
    Stateful alert manager. One instance lives for the scanner lifetime.

    Tracks:
      - _seen: dict[(market_id, alert_type) → last_alerted_at]
      - _last_digest_date: date of last daily digest sent
    """

    def __init__(self):
        self._seen: dict[tuple[str, str], datetime] = {}
        self._last_digest_date: datetime | None = None

        if not ENABLED:
            logger.info("alerts_disabled",
                        reason="No DISCORD_WEBHOOK_URL or SLACK_WEBHOOK_URL set")
        else:
            targets = []
            if DISCORD_WEBHOOK:
                targets.append("discord")
            if SLACK_WEBHOOK:
                targets.append("slack")
            logger.info("alerts_enabled", targets=targets,
                        min_edge=ALERT_MIN_EDGE_PCT,
                        cooldown_min=ALERT_COOLDOWN_MINUTES)

    def _cooldown_ok(self, key: tuple[str, str]) -> bool:
        """True if we haven't alerted this key recently."""
        last = self._seen.get(key)
        if last is None:
            return True
        return datetime.utcnow() - last > timedelta(minutes=ALERT_COOLDOWN_MINUTES)

    def _mark_seen(self, key: tuple[str, str]) -> None:
        self._seen[key] = datetime.utcnow()

    # ── Async send helpers ────────────────────────────────────────────────────

    async def _send(
        self,
        client: httpx.AsyncClient,
        discord_payload: dict | None,
        slack_payload: dict | None,
    ) -> None:
        """Fire webhooks (whichever are configured)."""
        if DISCORD_WEBHOOK and discord_payload:
            await wh.send_discord(DISCORD_WEBHOOK, discord_payload, client)
        if SLACK_WEBHOOK and slack_payload:
            await wh.send_slack(SLACK_WEBHOOK, slack_payload, client)

    # ── Public alert methods ──────────────────────────────────────────────────

    async def alert_opportunities(
        self,
        opportunities: list[Opportunity],
        client: httpx.AsyncClient,
    ) -> int:
        """
        Alert on high-edge VALUE / ARB opportunities.
        Returns number of alerts sent.
        """
        if not ENABLED or not ALERT_ON_OPPORTUNITY:
            return 0

        sent = 0
        for opp in opportunities:
            if opp.edge_pct < ALERT_MIN_EDGE_PCT:
                continue

            opp_type = str(opp.opportunity_type)
            # Only alert VALUE and ARB — not VIG/SPREAD (informational)
            if not any(t in opp_type for t in ("VALUE", "ARB")):
                continue

            key = (opp.market_id or opp.title[:60], opp_type)
            if not self._cooldown_ok(key):
                continue

            details = opp.details or {}
            if isinstance(details, str):
                try:
                    details = json.loads(details)
                except Exception:
                    details = {}

            opp_dict = {
                "type":             opp_type.split(".")[-1],
                "title":            opp.title,
                "edge_pct":         opp.edge_pct,
                "confidence":       opp.confidence,
                "suggested_size_usd": opp.suggested_size_usd,
                "pm_ask":           opp.yes_ask,
                "external_fair":    details.get("fair_prob"),
                "external_platform": details.get("external_platform", ""),
            }

            await self._send(
                client,
                discord_payload=wh.discord_opportunity(opp_dict),
                slack_payload=wh.slack_opportunity(opp_dict),
            )
            self._mark_seen(key)
            sent += 1

            # Max 3 opportunity alerts per scan to avoid spam
            if sent >= 3:
                break

        if sent:
            logger.info("opportunity_alerts_sent", count=sent)
        return sent

    async def alert_closed_trades(
        self,
        closed_records: list[dict],
        client: httpx.AsyncClient,
    ) -> int:
        """Alert on each closed trade. Always fires (no cooldown — close is a one-time event)."""
        if not ENABLED or not ALERT_ON_CLOSE:
            return 0

        sent = 0
        for record in closed_records:
            await self._send(
                client,
                discord_payload=wh.discord_trade_closed(record),
                slack_payload=wh.slack_trade_closed(record),
            )
            sent += 1

        if sent:
            logger.info("close_alerts_sent", count=sent)
        return sent

    async def alert_daily_digest(
        self,
        paper_trader: "PaperTrader",
        client: httpx.AsyncClient,
    ) -> bool:
        """
        Send daily digest once per day at ALERT_DIGEST_HOUR UTC.
        Returns True if digest was sent.
        """
        if not ENABLED or not ALERT_ON_DIGEST:
            return False

        now = datetime.utcnow()
        if now.hour != ALERT_DIGEST_HOUR:
            return False
        if self._last_digest_date and self._last_digest_date.date() == now.date():
            return False  # already sent today

        stats = get_performance_stats()
        open_count = sum(
            1 for _ in []  # populated below
        )
        from database.db import get_session
        from database.models import PaperTrade as DBTrade
        with get_session() as session:
            open_count = session.query(DBTrade).filter(DBTrade.status == "OPEN").count()

        if not isinstance(stats, dict) or "win_rate" not in stats:
            stats = {}

        await self._send(
            client,
            discord_payload=wh.discord_daily_digest(stats, paper_trader.balance, open_count),
            slack_payload=wh.slack_daily_digest(stats, paper_trader.balance, open_count),
        )
        self._last_digest_date = now
        logger.info("daily_digest_sent", balance=paper_trader.balance)
        return True
