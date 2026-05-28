"""Auth endpoint tests."""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.conftest import auth_headers, register_user
from backend.app.models.user import User


def test_register_creates_user(client: TestClient, db: Session):
    res = client.post("/api/v1/auth/register", json={
        "email": "new@example.com",
        "password": "password123",
    })
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert data["plan"] == "free"

    user = db.query(User).filter(User.email == "new@example.com").first()
    assert user is not None
    assert not user.is_verified
    assert user.verification_token_hash is not None


def test_register_duplicate_email(client: TestClient):
    client.post("/api/v1/auth/register", json={"email": "dup@example.com", "password": "password123"})
    res = client.post("/api/v1/auth/register", json={"email": "dup@example.com", "password": "password123"})
    assert res.status_code == 409


def test_register_short_password(client: TestClient):
    res = client.post("/api/v1/auth/register", json={"email": "pw@example.com", "password": "short"})
    assert res.status_code == 422


def test_login_success(client: TestClient):
    register_user(client, "login@example.com", "goodpassword")
    res = client.post("/api/v1/auth/login", json={"email": "login@example.com", "password": "goodpassword"})
    assert res.status_code == 200
    assert "access_token" in res.json()


def test_login_wrong_password(client: TestClient):
    register_user(client, "badpw@example.com", "correctpassword")
    res = client.post("/api/v1/auth/login", json={"email": "badpw@example.com", "password": "wrongpassword"})
    assert res.status_code == 401


def test_get_me(client: TestClient):
    token = register_user(client, "me@example.com", "password123")["access_token"]
    res = client.get("/api/v1/auth/me", headers=auth_headers(token))
    assert res.status_code == 200
    assert res.json()["email"] == "me@example.com"
    assert res.json()["is_verified"] is False


def test_verify_email(client: TestClient, db: Session):
    register_user(client, "verify@example.com", "password123")

    user = db.query(User).filter(User.email == "verify@example.com").first()
    assert user is not None

    # Generate a fresh token and store its hash
    import secrets
    token = secrets.token_urlsafe(32)
    user.verification_token_hash = hashlib.sha256(token.encode()).hexdigest()
    user.verification_token_expires = datetime.now(timezone.utc) + timedelta(hours=24)
    db.commit()

    res = client.post("/api/v1/auth/verify-email", json={"token": token})
    assert res.status_code == 200

    db.refresh(user)
    assert user.is_verified is True
    assert user.verification_token_hash is None


def test_verify_email_bad_token(client: TestClient):
    res = client.post("/api/v1/auth/verify-email", json={"token": "notavalidtoken"})
    assert res.status_code == 400


def test_forgot_password_always_200(client: TestClient):
    res = client.post("/api/v1/auth/forgot-password", json={"email": "nobody@example.com"})
    assert res.status_code == 200
    assert "message" in res.json()


def test_reset_password(client: TestClient, db: Session):
    register_user(client, "reset@example.com", "oldpassword")
    user = db.query(User).filter(User.email == "reset@example.com").first()

    import secrets
    token = secrets.token_urlsafe(32)
    user.reset_token_hash = hashlib.sha256(token.encode()).hexdigest()
    user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
    db.commit()

    res = client.post("/api/v1/auth/reset-password", json={"token": token, "new_password": "newpassword123"})
    assert res.status_code == 200

    # Old password should no longer work
    login = client.post("/api/v1/auth/login", json={"email": "reset@example.com", "password": "oldpassword"})
    assert login.status_code == 401

    # New password works
    login = client.post("/api/v1/auth/login", json={"email": "reset@example.com", "password": "newpassword123"})
    assert login.status_code == 200


def test_change_password(client: TestClient):
    token = register_user(client, "changepw@example.com", "original123")["access_token"]
    res = client.post(
        "/api/v1/auth/me/change-password",
        json={"current_password": "original123", "new_password": "updated123"},
        headers=auth_headers(token),
    )
    assert res.status_code == 200

    # Old password no longer works
    login = client.post("/api/v1/auth/login", json={"email": "changepw@example.com", "password": "original123"})
    assert login.status_code == 401


def test_change_password_wrong_current(client: TestClient):
    token = register_user(client, "wrongcurrent@example.com", "realpass123")["access_token"]
    res = client.post(
        "/api/v1/auth/me/change-password",
        json={"current_password": "wrong", "new_password": "newpass123"},
        headers=auth_headers(token),
    )
    assert res.status_code == 400


def test_delete_account(client: TestClient, db: Session):
    token = register_user(client, "delete@example.com", "password123")["access_token"]
    res = client.request(
        "DELETE",
        "/api/v1/auth/me",
        json={"confirm_email": "delete@example.com"},
        headers=auth_headers(token),
    )
    assert res.status_code == 200
    assert db.query(User).filter(User.email == "delete@example.com").first() is None


def test_delete_account_wrong_email(client: TestClient):
    token = register_user(client, "keepme@example.com", "password123")["access_token"]
    res = client.request(
        "DELETE",
        "/api/v1/auth/me",
        json={"confirm_email": "wrong@example.com"},
        headers=auth_headers(token),
    )
    assert res.status_code == 400
