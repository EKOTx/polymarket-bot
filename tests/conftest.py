"""
Pytest fixtures: in-memory SQLite DB, TestClient, user helpers.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from backend.app.core.database import Base, get_db
from backend.app.main import app

# Import all models so Base knows every table before create_all
from backend.app.models import user as _um, market as _mm, public as _pm  # noqa: F401, E402


@pytest.fixture()
def db() -> Session:
    # Fresh in-memory DB per test — zero leakage between tests
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = SessionLocal()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture()
def client(db: Session) -> TestClient:
    from unittest.mock import patch

    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    def _no_rate_limit(request, *args, **kwargs):
        if hasattr(request, "state"):
            request.state.view_rate_limit = None

    # Disable rate limiting so tests don't interfere with each other
    with patch("slowapi.extension.Limiter._check_request_limit", side_effect=_no_rate_limit):
        with TestClient(app, raise_server_exceptions=True) as c:
            yield c
    app.dependency_overrides.clear()


# ── User helpers ─────────────────────────────────────────────────────────────

def register_user(client: TestClient, email: str, password: str) -> dict:
    res = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert res.status_code == 201, res.text
    return res.json()


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
