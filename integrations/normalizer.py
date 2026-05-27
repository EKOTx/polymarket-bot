"""
Cross-platform market normalizer.

Converts raw platform dicts → ExternalMarketOdds Pydantic objects.
Applies devigging to get fair probability from platform prices.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class ExternalMarketOdds(BaseModel):
    """Normalized external market odds — one row per outcome per platform."""

    platform: str                    # "kalshi" | "predictit"
    platform_market_id: str
    title: str                        # full display title
    outcome_label: str               # "Yes" or candidate name

    # Raw prices (0-1)
    yes_ask: Optional[float] = None  # cost to buy YES
    yes_bid: Optional[float] = None  # proceeds from selling YES
    mid: float                        # (ask+bid)/2 or best available

    # Derived
    fair_probability: Optional[float] = None  # devigged fair value (if group known)
    volume: float = 0.0
    fetched_at: str = ""

    # Grouping (for devig within a multi-outcome market)
    group_id: Optional[str] = None   # links contracts from same PI market

    @field_validator("yes_ask", "yes_bid", "mid", "fair_probability", mode="before")
    @classmethod
    def clamp_price(cls, v):
        if v is None:
            return v
        return max(0.0, min(1.0, float(v)))

    @property
    def spread(self) -> Optional[float]:
        if self.yes_ask is not None and self.yes_bid is not None:
            return round(self.yes_ask - self.yes_bid, 4)
        return None


def normalize_kalshi(raw: dict) -> ExternalMarketOdds:
    """Kalshi raw dict → ExternalMarketOdds."""
    return ExternalMarketOdds(
        platform="kalshi",
        platform_market_id=raw["platform_market_id"],
        title=raw["title"],
        outcome_label="Yes",
        yes_ask=raw.get("yes_ask"),
        yes_bid=raw.get("yes_bid"),
        mid=raw["mid"],
        volume=float(raw.get("volume") or 0),
        fetched_at=raw.get("fetched_at", datetime.utcnow().isoformat()),
        group_id=raw.get("event_ticker"),
    )


def normalize_predictit(raw: dict) -> ExternalMarketOdds:
    """PredictIt contract dict → ExternalMarketOdds."""
    return ExternalMarketOdds(
        platform="predictit",
        platform_market_id=raw["platform_market_id"],
        title=raw["title"],
        outcome_label=raw.get("outcome_label", "Yes"),
        yes_ask=raw.get("yes_ask"),
        yes_bid=raw.get("yes_bid"),
        mid=raw["mid"],
        volume=float(raw.get("volume") or 0),
        fetched_at=raw.get("fetched_at", datetime.utcnow().isoformat()),
        group_id=raw.get("parent_market_id"),
    )


def devig_group(odds_list: list[ExternalMarketOdds]) -> list[ExternalMarketOdds]:
    """
    Apply multiplicative devigging to a group of mutually exclusive outcomes.

    Returns new list with fair_probability populated.
    Only useful for PI multi-contract markets or Kalshi event groups.
    """
    mids = [o.mid for o in odds_list if o.mid > 0]
    if not mids or sum(mids) <= 0:
        return odds_list

    total = sum(mids)
    result = []
    for o in odds_list:
        fair = o.mid / total if total > 0 else o.mid
        result.append(o.model_copy(update={"fair_probability": round(fair, 4)}))
    return result


def devig_all(
    external: list[ExternalMarketOdds],
) -> list[ExternalMarketOdds]:
    """
    Devig all markets, grouping by group_id where possible.
    Single-outcome markets (no group or group of 1) use mid as fair_probability.
    """
    # Group by (platform, group_id)
    groups: dict[tuple[str, str], list[ExternalMarketOdds]] = {}
    no_group: list[ExternalMarketOdds] = []

    for o in external:
        if o.group_id:
            key = (o.platform, o.group_id)
            groups.setdefault(key, []).append(o)
        else:
            no_group.append(o)

    result: list[ExternalMarketOdds] = []

    for key, group in groups.items():
        if len(group) > 1:
            result.extend(devig_group(group))
        else:
            # Single market in group — use mid as fair prob
            o = group[0]
            result.append(o.model_copy(update={"fair_probability": o.mid}))

    # No-group items: fair_prob = mid
    for o in no_group:
        result.append(o.model_copy(update={"fair_probability": o.mid}))

    return result


def load_all_external(
    kalshi_raw: list[dict],
    predictit_raw: list[dict],
) -> list[ExternalMarketOdds]:
    """Convert raw platform dicts to normalized + devigged ExternalMarketOdds list."""
    normalized: list[ExternalMarketOdds] = []
    normalized.extend(normalize_kalshi(r) for r in kalshi_raw)
    normalized.extend(normalize_predictit(r) for r in predictit_raw)
    return devig_all(normalized)
