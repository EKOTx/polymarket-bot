"""
Webhook senders for Discord and Slack.

Thin HTTP layer — just sends payloads.
No retry logic here; caller handles errors.
"""

from __future__ import annotations

import httpx
from utils.logging import get_logger

logger = get_logger(__name__)

TIMEOUT = 8.0


async def send_discord(url: str, payload: dict, client: httpx.AsyncClient) -> bool:
    """POST embed payload to Discord webhook. Returns True on success."""
    try:
        resp = await client.post(url, json=payload, timeout=TIMEOUT)
        if resp.status_code in (200, 204):
            return True
        logger.warning("discord_webhook_failed", status=resp.status_code, body=resp.text[:200])
        return False
    except Exception as e:
        logger.warning("discord_webhook_error", error=str(e))
        return False


async def send_slack(url: str, payload: dict, client: httpx.AsyncClient) -> bool:
    """POST blocks payload to Slack webhook. Returns True on success."""
    try:
        resp = await client.post(url, json=payload, timeout=TIMEOUT)
        if resp.status_code == 200:
            return True
        logger.warning("slack_webhook_failed", status=resp.status_code, body=resp.text[:200])
        return False
    except Exception as e:
        logger.warning("slack_webhook_error", error=str(e))
        return False


# ── Payload builders ──────────────────────────────────────────────────────────

def discord_opportunity(opp_dict: dict) -> dict:
    """Build Discord embed for a VALUE/ARB opportunity."""
    edge  = opp_dict.get("edge_pct", 0)
    conf  = opp_dict.get("confidence", 0)
    title = opp_dict.get("title", "")[:80]
    typ   = opp_dict.get("type", "VALUE")
    platform = opp_dict.get("external_platform", "")
    pm_ask   = opp_dict.get("pm_ask", "")
    ext_fair = opp_dict.get("external_fair", "")
    size     = opp_dict.get("suggested_size_usd", 0)

    color = 0x00ff88 if edge >= 3.0 else 0xf77f00

    fields = [
        {"name": "Edge",       "value": f"`{edge:.2f}%`",        "inline": True},
        {"name": "Confidence", "value": f"`{conf:.2f}`",          "inline": True},
        {"name": "Type",       "value": f"`{typ}`",               "inline": True},
    ]
    if pm_ask:
        fields.append({"name": "PM Ask",       "value": f"`{pm_ask:.3f}`",  "inline": True})
    if ext_fair:
        fields.append({"name": "Ext Fair",     "value": f"`{ext_fair:.3f}`","inline": True})
    if platform:
        fields.append({"name": "Source",       "value": f"`{platform}`",    "inline": True})
    if size:
        fields.append({"name": "Kelly Size",   "value": f"`${size:.0f}`",   "inline": True})

    return {
        "embeds": [{
            "title": f"🎯 {typ} Signal",
            "description": title,
            "color": color,
            "fields": fields,
            "footer": {"text": "Polymarket Quant Bot • paper trading only"},
        }]
    }


def discord_trade_closed(record: dict) -> dict:
    """Build Discord embed for a closed paper trade."""
    pnl       = record.get("realized_pnl", 0)
    won       = pnl > 0
    resolution= record.get("resolution", "?")
    question  = record.get("question", "")[:80]
    entry     = record.get("entry", 0)
    exit_p    = record.get("exit", 0)

    color = 0x00ff88 if won else 0xff4444
    icon  = "✅" if won else "❌"

    return {
        "embeds": [{
            "title": f"{icon} Trade Closed — {resolution}",
            "description": question,
            "color": color,
            "fields": [
                {"name": "Realized PnL", "value": f"`${pnl:+.2f}`",    "inline": True},
                {"name": "Entry → Exit", "value": f"`{entry:.3f} → {exit_p:.3f}`", "inline": True},
            ],
            "footer": {"text": "Polymarket Quant Bot • paper trading only"},
        }]
    }


def discord_daily_digest(stats: dict, balance: float, open_count: int) -> dict:
    """Build Discord embed for daily summary."""
    pnl        = balance - 10000
    win_rate   = stats.get("win_rate", 0)
    realized   = stats.get("total_realized_pnl", 0)
    total_cl   = stats.get("total_closed", 0)
    pf         = stats.get("profit_factor", 0)

    color = 0x00ff88 if pnl >= 0 else 0xff4444

    return {
        "embeds": [{
            "title": "📊 Daily Digest — Polymarket Bot",
            "color": color,
            "fields": [
                {"name": "Balance",        "value": f"`${balance:,.2f}`",      "inline": True},
                {"name": "Total PnL",      "value": f"`${pnl:+,.2f}`",         "inline": True},
                {"name": "Open Positions", "value": f"`{open_count}`",          "inline": True},
                {"name": "Closed Trades",  "value": f"`{total_cl}`",            "inline": True},
                {"name": "Win Rate",       "value": f"`{win_rate:.0%}`",        "inline": True},
                {"name": "Profit Factor",  "value": f"`{pf:.2f}`",             "inline": True},
                {"name": "Realized PnL",   "value": f"`${realized:+,.2f}`",    "inline": True},
            ],
            "footer": {"text": "Polymarket Quant Bot • paper trading only"},
        }]
    }


def slack_opportunity(opp_dict: dict) -> dict:
    """Build Slack blocks for an opportunity alert."""
    edge  = opp_dict.get("edge_pct", 0)
    conf  = opp_dict.get("confidence", 0)
    title = opp_dict.get("title", "")[:80]
    typ   = opp_dict.get("type", "VALUE")
    platform = opp_dict.get("external_platform", "")
    size  = opp_dict.get("suggested_size_usd", 0)

    icon = "🎯" if edge >= 3.0 else "📡"
    details = f"Edge: *{edge:.2f}%* | Conf: *{conf:.2f}* | Size: *${size:.0f}*"
    if platform:
        details += f" | Source: *{platform}*"

    return {
        "blocks": [
            {"type": "section", "text": {"type": "mrkdwn",
             "text": f"{icon} *{typ} Signal*\n{title}"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": details}},
            {"type": "divider"},
        ]
    }


def slack_trade_closed(record: dict) -> dict:
    """Build Slack blocks for a closed trade."""
    pnl  = record.get("realized_pnl", 0)
    icon = "✅" if pnl > 0 else "❌"
    q    = record.get("question", "")[:80]
    res  = record.get("resolution", "?")
    return {
        "blocks": [
            {"type": "section", "text": {"type": "mrkdwn",
             "text": f"{icon} *Trade Closed ({res})* — {q}\nPnL: *${pnl:+.2f}*"}},
            {"type": "divider"},
        ]
    }


def slack_daily_digest(stats: dict, balance: float, open_count: int) -> dict:
    """Build Slack blocks for daily digest."""
    pnl      = balance - 10000
    win_rate = stats.get("win_rate", 0)
    realized = stats.get("total_realized_pnl", 0)
    return {
        "blocks": [
            {"type": "section", "text": {"type": "mrkdwn",
             "text": f"📊 *Daily Digest*\nBalance: *${balance:,.2f}* ({pnl:+,.2f}) | "
                     f"Open: *{open_count}* | Win Rate: *{win_rate:.0%}* | "
                     f"Realized: *${realized:+,.2f}*"}},
            {"type": "divider"},
        ]
    }
