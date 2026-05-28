"""Opportunity response schemas."""

import json
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, field_validator


class OpportunityOut(BaseModel):
    id: int
    opportunity_type: str

    @field_validator("opportunity_type", mode="before")
    @classmethod
    def strip_enum_prefix(cls, v):
        """DB stores 'OpportunityType.VALUE' — return just 'VALUE'."""
        if isinstance(v, str) and "." in v:
            return v.rsplit(".", 1)[-1]
        return v
    title: str
    event_title: str
    market_id: Optional[str]
    edge_pct: float
    confidence: float
    expected_value: float
    suggested_size_usd: float
    yes_bid: Optional[float]
    yes_ask: Optional[float]
    no_bid: Optional[float] = None
    no_ask: Optional[float] = None
    vig_pct: Optional[float]
    liquidity: float
    market_count: int
    warnings: list[str]
    details: dict[str, Any]
    timestamp: datetime

    @field_validator("warnings", mode="before")
    @classmethod
    def parse_warnings(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return []
        return v or []

    @field_validator("details", mode="before")
    @classmethod
    def parse_details(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return {}
        return v or {}

    model_config = {"from_attributes": True}


class OpportunityListResponse(BaseModel):
    items: list[OpportunityOut]
    total: int
    page: int
    page_size: int


class ScannerStatusResponse(BaseModel):
    last_scan_id: Optional[int]
    last_scan_at: Optional[datetime]
    duration_seconds: Optional[float]
    markets_fetched: int
    markets_priced: int
    opportunities_found: int
    is_running: bool
    error: Optional[str]
