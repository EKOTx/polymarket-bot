"""
Momentum Strategy.

Detects markets with sustained directional price movement over recent scans.
Strong momentum = price accelerating toward 0 or 1 = event approaching resolution.

Signal: buy YES if strong upward momentum + price not yet near ceiling.
        buy NO  if strong downward momentum + price not near floor.

Uses price_snapshots table for historical data.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Optional

from models.opportunity import Opportunity, OpportunityType
from strategies.base import Strategy
from utils.math_utils import confidence_score, half_kelly
from utils.logging import get_logger

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from integrations.normalizer import ExternalMarketOdds
    from models.market import MarketData, TournamentGroup

logger = get_logger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────

# Minimum number of historical snapshots to calculate momentum
MIN_HISTORY_POINTS = int(os.getenv("MOMENTUM_MIN_POINTS", "4"))
# Look back window (minutes)
LOOKBACK_MINUTES = int(os.getenv("MOMENTUM_LOOKBACK_MINUTES", "120"))
# Minimum price velocity (absolute price change per hour) to flag
MIN_VELOCITY_PER_HOUR = float(os.getenv("MOMENTUM_MIN_VELOCITY", "0.04"))
# Minimum R² of linear trend to ensure signal isn't noise
MIN_R_SQUARED = float(os.getenv("MOMENTUM_MIN_R2", "0.70"))
# Max mid price ceiling (skip near-resolved markets)
MAX_MID_BUY_YES = float(os.getenv("MOMENTUM_MAX_MID", "0.88"))
MIN_MID_BUY_NO = float(os.getenv("MOMENTUM_MIN_MID_NO", "0.12"))

PAPER_MAX_POSITION_SIZE = float(os.getenv("PAPER_MAX_POSITION_SIZE", "500"))
MIN_CONFIDENCE = float(os.getenv("MIN_CONFIDENCE", "0.4"))


# ── Math helpers ──────────────────────────────────────────────────────────────

def _linear_regression(x: list[float], y: list[float]) -> tuple[float, float, float]:
    """
    Simple linear regression: y = slope * x + intercept.
    Returns (slope, intercept, r_squared).
    """
    n = len(x)
    if n < 2:
        return 0.0, 0.0, 0.0

    sx = sum(x)
    sy = sum(y)
    sx2 = sum(xi ** 2 for xi in x)
    sxy = sum(xi * yi for xi, yi in zip(x, y))

    denom = n * sx2 - sx ** 2
    if abs(denom) < 1e-10:
        return 0.0, sum(y) / n, 0.0

    slope = (n * sxy - sx * sy) / denom
    intercept = (sy - slope * sx) / n

    # R²
    y_mean = sy / n
    ss_tot = sum((yi - y_mean) ** 2 for yi in y)
    ss_res = sum((yi - (slope * xi + intercept)) ** 2 for xi, yi in zip(x, y))

    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 1e-10 else 0.0
    return slope, intercept, max(0.0, r2)


# ── Momentum query ────────────────────────────────────────────────────────────

def _fetch_price_history(
    session: "Session",
    market_id: str,
    lookback_minutes: int,
) -> list[tuple[datetime, float]]:
    """
    Fetch (timestamp, mid) tuples for YES outcome, newest first.
    Returns empty list if not enough data.
    """
    from sqlalchemy import text

    cutoff = datetime.utcnow() - timedelta(minutes=lookback_minutes)
    rows = session.execute(
        text("""
            SELECT timestamp, mid
            FROM price_snapshots
            WHERE market_id = :mid
              AND outcome = 'Yes'
              AND mid IS NOT NULL
              AND timestamp >= :cutoff
            ORDER BY timestamp ASC
        """),
        {"mid": market_id, "cutoff": cutoff.isoformat()},
    ).fetchall()

    return [(r[0], float(r[1])) for r in rows if r[1] is not None]


def _compute_momentum(
    history: list[tuple[datetime, float]],
) -> Optional[dict]:
    """
    Fit linear trend to (time_hours, price) series.

    Returns dict with velocity_per_hour, r_squared, direction, current_mid,
    or None if not enough data / below thresholds.
    """
    if len(history) < MIN_HISTORY_POINTS:
        return None

    # Convert timestamps to hours relative to first point
    t0 = history[0][0]
    xs = [(t - t0).total_seconds() / 3600.0 for t, _ in history]
    ys = [p for _, p in history]

    # Skip if price hasn't moved much (flat market)
    price_range = max(ys) - min(ys)
    if price_range < 0.005:
        return None

    slope, intercept, r2 = _linear_regression(xs, ys)

    if r2 < MIN_R_SQUARED:
        return None
    if abs(slope) < MIN_VELOCITY_PER_HOUR:
        return None

    current_mid = ys[-1]
    direction = "UP" if slope > 0 else "DOWN"

    return {
        "velocity_per_hour": round(slope, 5),
        "r_squared": round(r2, 4),
        "direction": direction,
        "current_mid": round(current_mid, 4),
        "price_range": round(price_range, 4),
        "n_points": len(history),
        "hours_span": round(xs[-1], 2),
    }


# ── Strategy ──────────────────────────────────────────────────────────────────

class MomentumStrategy(Strategy):
    """
    Momentum signal: sustained directional price move with high R².

    BUY_YES: slope > MIN_VELOCITY, R² > MIN_R2, mid < MAX_MID_BUY_YES
    BUY_NO:  slope < -MIN_VELOCITY, R² > MIN_R2, mid > MIN_MID_BUY_NO

    Uses last LOOKBACK_MINUTES of price history.
    Requires MIN_HISTORY_POINTS data points (one per scan = ~30s each).
    """

    name = "momentum"

    def analyze(
        self,
        markets: list["MarketData"],
        groups: list["TournamentGroup"],
        external_odds: list["ExternalMarketOdds"],
        session: "Session",
        scan_id: int,
    ) -> list["Opportunity"]:
        opps: list[Opportunity] = []

        for m in markets:
            if m.yes_mid is None or not (0.02 < m.yes_mid < 0.98):
                continue
            if m.liquidity < 500:
                continue

            history = _fetch_price_history(session, m.market_id, LOOKBACK_MINUTES)
            mom = _compute_momentum(history)
            if mom is None:
                continue

            direction = mom["direction"]
            mid = mom["current_mid"]
            velocity = mom["velocity_per_hour"]
            r2 = mom["r_squared"]

            # Determine trade direction and entry price
            if direction == "UP":
                if mid > MAX_MID_BUY_YES:
                    continue  # too close to ceiling
                trade_dir = "BUY_YES"
                entry_price = m.yes_ask or mid
                # Edge estimate: how much price likely moves in next hour
                edge_pct = abs(velocity) * 50  # rough: 0.04/hr → 2% edge
            else:
                if mid < MIN_MID_BUY_NO:
                    continue  # too close to floor
                trade_dir = "BUY_NO"
                entry_price = m.no_ask or (1.0 - (m.yes_bid or mid))
                edge_pct = abs(velocity) * 50

            if entry_price <= 0 or entry_price >= 1.0:
                continue

            # Scale edge by R² confidence
            edge_pct = round(edge_pct * r2, 3)
            if edge_pct < 0.5:
                continue

            conf = confidence_score(
                edge=edge_pct,
                liquidity=m.liquidity,
                spread_pct=m.yes_spread_pct or 5.0,
                source_quality=r2,  # use R² as source quality
            )
            if conf < MIN_CONFIDENCE:
                continue

            # Kelly sizing
            fair_prob = min(mid + abs(velocity), 0.95)
            size = min(
                PAPER_MAX_POSITION_SIZE,
                half_kelly(fair_prob, 1.0 / entry_price) * 10_000,
            )

            opps.append(Opportunity(
                scan_id=scan_id,
                opportunity_type=OpportunityType.VALUE,
                title=m.question,
                event_title=m.event_title,
                market_id=m.market_id,
                edge_pct=edge_pct,
                confidence=conf,
                expected_value=round(edge_pct / 100 * size, 4),
                yes_bid=m.yes_bid,
                yes_ask=m.yes_ask,
                no_bid=m.no_bid,
                no_ask=m.no_ask,
                liquidity=m.liquidity,
                suggested_size_usd=round(size, 2),
                details={
                    "strategy": self.name,
                    "direction": trade_dir,
                    "velocity_per_hour": velocity,
                    "r_squared": r2,
                    "current_mid": mid,
                    "n_points": mom["n_points"],
                    "hours_span": mom["hours_span"],
                    "price_range": mom["price_range"],
                },
            ))

        opps.sort(key=lambda o: -(o.confidence * o.edge_pct))
        logger.debug("momentum_signals", count=len(opps))
        return opps
