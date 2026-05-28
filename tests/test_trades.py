"""Paper trading plan limit tests."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.conftest import auth_headers, register_user
from backend.app.models.market import Opportunity, ScanRun
from backend.app.models.market import Portfolio


def _seed_opportunity(db: Session) -> int:
    """Insert a minimal ScanRun + Opportunity so place_trade has something to reference."""
    run = ScanRun(
        started_at=__import__("datetime").datetime.utcnow(),
        finished_at=__import__("datetime").datetime.utcnow(),
        markets_fetched=1,
        markets_priced=1,
        opportunities_found=1,
        duration_seconds=1.0,
    )
    db.add(run)
    db.flush()

    opp = Opportunity(
        scan_id=run.id,
        market_id="test-market-001",
        opportunity_type="VALUE",
        title="Test Market",
        event_title="Test Event",
        edge_pct=5.0,
        confidence=0.8,
        expected_value=0.05,
        suggested_size_usd=50.0,
        yes_bid=0.45,
        yes_ask=0.50,
        no_bid=0.45,
        no_ask=0.50,
        vig_pct=0.1,
        liquidity=10000.0,
        market_count=1,
    )
    db.add(opp)
    db.commit()
    return opp.id


def _seed_portfolio(db: Session, user_id: int):
    portfolio = Portfolio(
        user_id=user_id,
        balance=10000.0,
        starting_balance=10000.0,
        total_invested=0.0,
        realized_pnl=0.0,
        unrealized_pnl=0.0,
        open_positions=0,
        total_trades=0,
    )
    db.add(portfolio)
    db.commit()


def test_free_plan_position_size_capped(client: TestClient, db: Session):
    """Free plan: $200 trade is capped at $100 (plan max), not rejected."""
    token = register_user(client, "freelimit@example.com", "password123")["access_token"]

    from backend.app.models.user import User
    user = db.query(User).filter(User.email == "freelimit@example.com").first()
    _seed_portfolio(db, user.id)
    opp_id = _seed_opportunity(db)

    res = client.post(
        "/api/v1/trades",
        json={"opportunity_id": opp_id, "outcome": "YES", "size_usd": 200.0},
        headers=auth_headers(token),
    )
    assert res.status_code == 201
    assert res.json()["cost_usd"] < 200.0  # capped at plan max + slippage, not the full $200


def test_free_plan_within_position_size(client: TestClient, db: Session):
    """Free plan: $50 trade should succeed."""
    token = register_user(client, "freesmall@example.com", "password123")["access_token"]

    from backend.app.models.user import User
    user = db.query(User).filter(User.email == "freesmall@example.com").first()
    _seed_portfolio(db, user.id)
    opp_id = _seed_opportunity(db)

    res = client.post(
        "/api/v1/trades",
        json={"opportunity_id": opp_id, "outcome": "YES", "size_usd": 50.0},
        headers=auth_headers(token),
    )
    assert res.status_code == 201


def test_scanner_status_endpoint(client: TestClient):
    res = client.get("/api/v1/opportunities/scanner/status")
    assert res.status_code == 200
    data = res.json()
    assert "is_running" in data
    assert data["is_running"] is False
