"""Pydantic models for detected opportunities and strategy signals."""

from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class OpportunityType(str, Enum):
    VALUE = "VALUE"                     # PM price < fair value
    HIGH_VIG = "HIGH_VIG"               # Tournament vig > 5%
    ELEVATED_VIG = "ELEVATED_VIG"       # Tournament vig 2-5%
    TOURNAMENT_ARB = "TOURNAMENT_ARB"   # sum_ask < 1.0 (clean)
    TOURNAMENT_ARB_RISKY = "TOURNAMENT_ARB_RISKY"  # sum_ask < 1.0 (with warnings)
    SPREAD = "SPREAD"                   # Wide spread anomaly
    STALE = "STALE"                     # Price hasn't moved, possible stale quote


class SignalStrength(str, Enum):
    STRONG = "STRONG"
    MEDIUM = "MEDIUM"
    WEAK = "WEAK"


class Opportunity(BaseModel):
    """One detected opportunity from any scanner/strategy."""
    opportunity_type: OpportunityType
    title: str                          # Human-readable title
    event_title: str = ""
    market_id: Optional[str] = None
    scan_id: int = 0

    # Core metrics
    edge_pct: float                     # Estimated edge %
    confidence: float                   # 0-1 confidence score
    expected_value: float               # EV in USD per $100 risked

    # Market data
    yes_bid: Optional[float] = None
    yes_ask: Optional[float] = None
    no_bid: Optional[float] = None
    no_ask: Optional[float] = None
    sum_yes_mid: Optional[float] = None
    vig_pct: Optional[float] = None
    liquidity: float = 0.0
    market_count: int = 1

    # Risk
    suggested_size_usd: float = 0.0
    warnings: list[str] = Field(default_factory=list)
    details: dict = Field(default_factory=dict)

    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @property
    def signal_strength(self) -> SignalStrength:
        if self.confidence >= 0.7 and self.edge_pct >= 3.0:
            return SignalStrength.STRONG
        elif self.confidence >= 0.4 and self.edge_pct >= 1.0:
            return SignalStrength.MEDIUM
        return SignalStrength.WEAK

    @property
    def is_actionable(self) -> bool:
        """True if worth paper trading."""
        return (
            self.confidence >= 0.4
            and self.edge_pct >= 0.5
            and not any("CUMULATIVE" in w for w in self.warnings)
        )
