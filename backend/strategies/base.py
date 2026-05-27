"""
Abstract Strategy base class.

Each strategy receives the full scan context and returns Opportunity objects.
Scanner iterates registered strategies, merges results.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from integrations.normalizer import ExternalMarketOdds
    from models.market import MarketData, TournamentGroup
    from models.opportunity import Opportunity


class Strategy(ABC):
    """
    Base class for all trading strategies.

    Subclasses implement `analyze()` and return a list of Opportunity objects.
    Strategies must NOT mutate input data or write to DB themselves —
    that is the scanner's responsibility.
    """

    #: Short unique identifier shown in logs and opportunity details
    name: str = "base"

    #: Whether this strategy is active (can be toggled by env var)
    enabled: bool = True

    @abstractmethod
    def analyze(
        self,
        markets: list["MarketData"],
        groups: list["TournamentGroup"],
        external_odds: list["ExternalMarketOdds"],
        session: "Session",
        scan_id: int,
    ) -> list["Opportunity"]:
        """
        Run the strategy against the current scan context.

        Args:
            markets:       CLOB-enriched Polymarket markets
            groups:        Tournament event groups (gamma prices)
            external_odds: Normalized Kalshi + PredictIt odds (may be empty)
            session:       Read-only DB session for historical queries
            scan_id:       Current scan run ID

        Returns:
            List of Opportunity objects (unsaved — scanner saves them).
        """
        ...

    def __repr__(self) -> str:
        return f"<Strategy:{self.name} enabled={self.enabled}>"
