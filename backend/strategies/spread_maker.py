"""
Spread Market Maker Strategy.

Identifies markets with wide bid-ask spreads where posting limit orders
at the midpoint would earn the spread. Informational signal only in paper
mode — no actual limit orders, but sized as if posting at mid.

Different from the basic SPREAD detector:
- Ranks by spread_pct × liquidity (wider AND liquid = better)
- Calculates theoretical edge from half-spread capture
- Tags with SPREAD opportunity type (not traded in paper mode, tracked for analysis)
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from models.opportunity import Opportunity, OpportunityType
from strategies.base import Strategy
from utils.math_utils import confidence_score
from utils.logging import get_logger

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from integrations.normalizer import ExternalMarketOdds
    from models.market import MarketData, TournamentGroup

logger = get_logger(__name__)

MIN_SPREAD_PCT = float(os.getenv("SPREAD_MIN_PCT", "5.0"))
MIN_ABS_SPREAD = float(os.getenv("SPREAD_MIN_ABS", "0.015"))
MIN_MID = float(os.getenv("SPREAD_MIN_MID", "0.03"))
MAX_MID = float(os.getenv("SPREAD_MAX_MID", "0.97"))
MIN_LIQUIDITY = float(os.getenv("SPREAD_MIN_LIQUIDITY", "200"))
# Top N markets to surface (avoid flooding)
TOP_N = int(os.getenv("SPREAD_TOP_N", "10"))

MIN_CONFIDENCE = float(os.getenv("MIN_CONFIDENCE", "0.4"))
PAPER_MAX_POSITION_SIZE = float(os.getenv("PAPER_MAX_POSITION_SIZE", "500"))


class SpreadMakerStrategy(Strategy):
    """
    Ranks wide-spread markets by expected spread capture.

    Expected edge = half-spread × capture_prob (assume 50% fill rate).
    Higher liquidity → more reliable spread, higher confidence.
    """

    name = "spread_maker"

    def analyze(
        self,
        markets: list["MarketData"],
        groups: list["TournamentGroup"],
        external_odds: list["ExternalMarketOdds"],
        session: "Session",
        scan_id: int,
    ) -> list["Opportunity"]:
        candidates = []

        for m in markets:
            if not m.yes_book or not m.yes_book.spread_pct:
                continue

            sp_pct = m.yes_book.spread_pct
            abs_sp = m.yes_book.spread or 0
            mid = m.yes_mid or 0

            if sp_pct < MIN_SPREAD_PCT:
                continue
            if abs_sp < MIN_ABS_SPREAD:
                continue
            if not (MIN_MID < mid < MAX_MID):
                continue
            if m.liquidity < MIN_LIQUIDITY:
                continue

            # Theoretical edge: if we post at mid, capture half-spread on fill
            half_spread = abs_sp / 2
            # Scale by bid/ask depth balance (symmetric depth = easier fill)
            bid_d = m.yes_book.bid_depth_usd or 0
            ask_d = m.yes_book.ask_depth_usd or 0
            depth_total = bid_d + ask_d
            depth_balance = 1.0 - abs(bid_d - ask_d) / (depth_total + 1)
            capture_prob = 0.5 * depth_balance

            edge_pct = round(half_spread * capture_prob * 100, 3)

            conf = confidence_score(
                edge=edge_pct,
                liquidity=m.liquidity,
                spread_pct=sp_pct,
            )
            if conf < MIN_CONFIDENCE:
                continue

            # Position size: scaled by depth available
            size = min(
                PAPER_MAX_POSITION_SIZE,
                min(bid_d, ask_d) * 0.05,  # 5% of thinner side
            )
            size = max(size, 10.0)

            candidates.append(Opportunity(
                scan_id=scan_id,
                opportunity_type=OpportunityType.SPREAD,
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
                    "spread_pct": sp_pct,
                    "abs_spread": abs_sp,
                    "half_spread": half_spread,
                    "capture_prob": round(capture_prob, 3),
                    "bid_depth_usd": bid_d,
                    "ask_depth_usd": ask_d,
                    "mid": mid,
                },
            ))

        # Sort by edge × liquidity score
        candidates.sort(key=lambda o: -(o.edge_pct * min(o.liquidity / 10_000, 1.0)))
        top = candidates[:TOP_N]
        logger.debug("spread_maker_signals", total=len(candidates), surfaced=len(top))
        return top
