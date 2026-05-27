"""
Strategy registry.

All active strategies listed here. Scanner iterates this list.
Disable a strategy by setting its enabled=False or removing from ACTIVE.

Order matters: strategies run sequentially, later strategies see earlier
results only if they query DB (they don't share in-memory state).
"""

from __future__ import annotations

import os

from strategies.base import Strategy
from strategies.momentum import MomentumStrategy
from strategies.spread_maker import SpreadMakerStrategy
from strategies.value import CrossPlatformValueStrategy


def build_registry() -> list[Strategy]:
    """Instantiate and return all enabled strategies."""
    strategies: list[Strategy] = [
        CrossPlatformValueStrategy(),
        MomentumStrategy(),
        SpreadMakerStrategy(),
    ]

    # Allow disabling via env: DISABLE_STRATEGIES=momentum,spread_maker
    disabled = set(
        s.strip()
        for s in os.getenv("DISABLE_STRATEGIES", "").split(",")
        if s.strip()
    )

    active = [s for s in strategies if s.name not in disabled]
    return active


def run_all_strategies(
    markets,
    groups,
    external_odds,
    session,
    scan_id: int,
    registry: list[Strategy] | None = None,
) -> list:
    """
    Run all strategies and return merged Opportunity list.
    Deduplicates by (market_id, opportunity_type) — keeps highest confidence.
    """
    from models.opportunity import Opportunity

    if registry is None:
        registry = build_registry()

    all_opps: list[Opportunity] = []
    seen: dict[tuple, Opportunity] = {}

    for strategy in registry:
        try:
            opps = strategy.analyze(
                markets=markets,
                groups=groups,
                external_odds=external_odds,
                session=session,
                scan_id=scan_id,
            )
            for opp in opps:
                key = (opp.market_id or opp.title[:60], str(opp.opportunity_type))
                existing = seen.get(key)
                if existing is None or opp.confidence > existing.confidence:
                    seen[key] = opp

        except Exception as e:
            from utils.logging import get_logger
            get_logger(__name__).error(
                "strategy_error", strategy=strategy.name, error=str(e)
            )

    all_opps = list(seen.values())
    all_opps.sort(key=lambda o: -(o.confidence * o.edge_pct))
    return all_opps
