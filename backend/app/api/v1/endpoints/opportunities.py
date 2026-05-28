"""
Opportunities API.

Free plan:  delayed data (last hour), limited to 10 results
Pro plan:   live data, unlimited results, all fields
Premium:    same + details field with strategy internals
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Query
from sqlalchemy import desc

from backend.app.api.deps import CurrentUser, DbSession, OptionalUser
from backend.app.core.cache import _cache
from backend.app.models.market import Opportunity, ScanRun
from backend.app.schemas.opportunity import (
    OpportunityListResponse,
    OpportunityOut,
    ScannerStatusResponse,
)

router = APIRouter(prefix="/opportunities", tags=["opportunities"])

PLAN_PAGE_SIZE = {"free": 10, "pro": 100, "premium": 100}
FREE_DELAY_MINUTES = 60


@router.get("", response_model=OpportunityListResponse)
def list_opportunities(
    user: OptionalUser,
    db: DbSession,
    opp_type: Optional[str] = Query(None, description="VALUE|SPREAD|HIGH_VIG|TOURNAMENT_ARB"),
    min_edge: float = Query(0.0),
    min_confidence: float = Query(0.0),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    """
    List opportunities. Free users get delayed + limited data.
    """
    plan = user.plan if user else "free"
    max_results = PLAN_PAGE_SIZE.get(plan, 10)
    page_size = min(page_size, max_results)

    q = db.query(Opportunity).filter(
        Opportunity.edge_pct >= min_edge,
        Opportunity.confidence >= min_confidence,
    )

    if opp_type:
        q = q.filter(Opportunity.opportunity_type.ilike(f"%{opp_type}%"))

    # Free plan: only show data older than FREE_DELAY_MINUTES
    if plan == "free":
        cutoff = datetime.utcnow() - timedelta(minutes=FREE_DELAY_MINUTES)
        q = q.filter(Opportunity.timestamp <= cutoff)

    total = q.count()
    items = (
        q.order_by(desc(Opportunity.timestamp), desc(Opportunity.edge_pct))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    # Non-premium: hide strategy internals in details
    results = []
    for opp in items:
        out = OpportunityOut.model_validate(opp)
        if plan not in ("premium",):
            out.details = {k: v for k, v in out.details.items()
                           if k not in ("strategy", "r_squared", "velocity_per_hour")}
        results.append(out)

    return OpportunityListResponse(
        items=results, total=total, page=page, page_size=page_size
    )


@router.get("/latest", response_model=list[OpportunityOut])
def latest_opportunities(
    user: OptionalUser,
    db: DbSession,
    limit: int = Query(20, ge=1, le=50),
):
    """Top opportunities from the most recent scan."""
    plan = user.plan if user else "free"
    cache_key = f"latest:{plan}:{limit}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    # Get latest scan_id
    latest_scan = db.query(ScanRun).order_by(desc(ScanRun.id)).first()
    if not latest_scan:
        return []

    q = db.query(Opportunity).filter(
        Opportunity.scan_id == latest_scan.id
    )

    if plan == "free":
        # Free: latest scan must be > 60 min old
        if latest_scan.started_at and (
            datetime.utcnow() - latest_scan.started_at
        ) < timedelta(minutes=FREE_DELAY_MINUTES):
            # Return previous scan instead
            prev = (
                db.query(ScanRun)
                .filter(ScanRun.id < latest_scan.id)
                .order_by(desc(ScanRun.id))
                .first()
            )
            if prev:
                q = db.query(Opportunity).filter(Opportunity.scan_id == prev.id)
            else:
                return []
        limit = min(limit, 10)

    items = (
        q.order_by(desc(Opportunity.edge_pct))
        .limit(limit)
        .all()
    )
    result = [OpportunityOut.model_validate(o) for o in items]
    _cache.set(cache_key, result, ttl=15.0)
    return result


@router.get("/scanner/status", response_model=ScannerStatusResponse)
def scanner_status(db: DbSession):
    """Scanner health — public endpoint."""
    cached = _cache.get("scanner:status")
    if cached is not None:
        return cached

    latest = db.query(ScanRun).order_by(desc(ScanRun.id)).first()
    if not latest:
        result = ScannerStatusResponse(
            last_scan_id=None, last_scan_at=None, duration_seconds=None,
            markets_fetched=0, markets_priced=0, opportunities_found=0,
            is_running=False, error=None,
        )
        _cache.set("scanner:status", result, ttl=15.0)
        return result

    # Consider scanner "running" if last scan finished < SCAN_INTERVAL * 3 ago
    from backend.app.core.config import settings
    elapsed = (datetime.utcnow() - latest.finished_at).total_seconds() if latest.finished_at else None
    is_running = elapsed is not None and elapsed < settings.SCAN_INTERVAL_SECONDS * 3

    result = ScannerStatusResponse(
        last_scan_id=latest.id,
        last_scan_at=latest.started_at,
        duration_seconds=latest.duration_seconds,
        markets_fetched=latest.markets_fetched,
        markets_priced=latest.markets_priced,
        opportunities_found=latest.opportunities_found,
        is_running=is_running,
        error=latest.error,
    )
    _cache.set("scanner:status", result, ttl=15.0)
    return result
