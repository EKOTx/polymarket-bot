"""
Alerts API — config status and webhook test.
"""

from __future__ import annotations

import httpx
from fastapi import APIRouter

from backend.app.api.deps import CurrentUser
from backend.app.core.config import settings

router = APIRouter(prefix="/alerts", tags=["alerts"])

_TEST_DISCORD = {
    "embeds": [{
        "title": "🔔 Test Alert",
        "description": "Polymarket Intel webhook is configured correctly.",
        "color": 0x00FF88,
        "footer": {"text": "Polymarket Intelligence"},
    }]
}

_TEST_SLACK = {
    "blocks": [{
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "🔔 *Test Alert* — Polymarket Intel webhook is configured correctly.",
        },
    }]
}


@router.get("/config")
def get_alert_config(user: CurrentUser):
    return {
        "discord_configured": bool(settings.DISCORD_WEBHOOK_URL),
        "slack_configured": bool(settings.SLACK_WEBHOOK_URL),
        "min_edge_pct": settings.ALERT_MIN_EDGE_PCT,
        "cooldown_minutes": settings.ALERT_COOLDOWN_MINUTES,
        "digest_hour": settings.ALERT_DIGEST_HOUR,
    }


@router.post("/test")
async def test_alert(user: CurrentUser):
    """Send test message to all configured webhooks. Returns per-channel result."""
    results: dict[str, bool | None] = {"discord": None, "slack": None}

    async with httpx.AsyncClient(timeout=8.0) as client:
        if settings.DISCORD_WEBHOOK_URL:
            try:
                r = await client.post(settings.DISCORD_WEBHOOK_URL, json=_TEST_DISCORD)
                results["discord"] = r.status_code in (200, 204)
            except Exception:
                results["discord"] = False

        if settings.SLACK_WEBHOOK_URL:
            try:
                r = await client.post(settings.SLACK_WEBHOOK_URL, json=_TEST_SLACK)
                results["slack"] = r.status_code == 200
            except Exception:
                results["slack"] = False

    return results
