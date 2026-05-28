"""Billing endpoint tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import auth_headers, register_user


def test_billing_status_requires_auth(client: TestClient):
    res = client.get("/api/v1/billing/status")
    assert res.status_code == 401


def test_billing_status_returns_free_plan(client: TestClient):
    token = register_user(client, "billing@example.com", "password123")["access_token"]
    res = client.get("/api/v1/billing/status", headers=auth_headers(token))
    assert res.status_code == 200
    data = res.json()
    assert data["plan"] == "free"
    assert data["stripe_customer_id"] is None
    assert data["subscription"] is None


def test_checkout_503_when_stripe_not_configured(client: TestClient):
    token = register_user(client, "checkout@example.com", "password123")["access_token"]
    res = client.post(
        "/api/v1/billing/checkout",
        json={"plan": "pro"},
        headers=auth_headers(token),
    )
    assert res.status_code == 503


def test_portal_503_when_stripe_not_configured(client: TestClient):
    token = register_user(client, "portal@example.com", "password123")["access_token"]
    res = client.post("/api/v1/billing/portal", headers=auth_headers(token))
    assert res.status_code == 503


def test_webhook_503_when_stripe_not_configured(client: TestClient):
    res = client.post("/api/v1/billing/webhook", content=b"{}", headers={"stripe-signature": "t=1,v1=abc"})
    assert res.status_code == 503
