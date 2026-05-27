"""
Cross-platform Value Strategy.

Finds markets where Polymarket price diverges from external fair value
(Kalshi + PredictIt after devigging).

Wraps integrations.matcher logic into the Strategy interface.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from integrations.matcher import match_markets, filter_actionable
from scanners.opportunity_detector import analyze_cross_platform_value
from strategies.base import Strategy

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from integrations.normalizer import ExternalMarketOdds
    from models.market import MarketData, TournamentGroup
    from models.opportunity import Opportunity

MIN_SIMILARITY = float(os.getenv("VALUE_MIN_SIMILARITY", "0.68"))
MIN_EDGE = float(os.getenv("MIN_EDGE_PCT", "1.5"))


class CrossPlatformValueStrategy(Strategy):
    """
    VALUE signal: PM ask price < external devigged fair probability.

    Entry logic:
    - Match PM market title to external market title (fuzzy)
    - Compute edge = external_fair - pm_ask
    - Signal if edge >= MIN_EDGE (default 1.5%)
    """

    name = "cross_platform_value"

    def analyze(
        self,
        markets: list["MarketData"],
        groups: list["TournamentGroup"],
        external_odds: list["ExternalMarketOdds"],
        session: "Session",
        scan_id: int,
    ) -> list["Opportunity"]:
        if not external_odds:
            return []

        matches = match_markets(markets, external_odds)
        opps = analyze_cross_platform_value(matches, scan_id=scan_id)

        for o in opps:
            if o.details is None:
                o.details = {}
            o.details["strategy"] = self.name

        return opps
