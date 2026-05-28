"""
Auth endpoints: register, login, /me, refresh, forgot/reset password.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, status

from backend.app.api.deps import CurrentUser, DbSession
from backend.app.core.email import send_password_reset
from backend.app.core.security import create_access_token, hash_password, verify_password
from backend.app.models.user import User
from backend.app.schemas.auth import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: DbSession):
    """Create new account. Returns JWT immediately."""
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        plan="free",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)
    return TokenResponse(access_token=token, plan=user.plan)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: DbSession):
    """Email/password login. Returns JWT."""
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")

    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account disabled")

    user.last_login = datetime.utcnow()
    db.commit()

    token = create_access_token(user.id)
    return TokenResponse(access_token=token, plan=user.plan)


@router.get("/me", response_model=UserResponse)
def get_me(user: CurrentUser):
    """Return current authenticated user."""
    return user


@router.patch("/me", response_model=UserResponse)
def update_me(body: dict, user: CurrentUser, db: DbSession):
    """Update full_name."""
    if "full_name" in body:
        user.full_name = body["full_name"]
        db.commit()
        db.refresh(user)
    return user


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(body: ForgotPasswordRequest, db: DbSession):
    """Request a password reset link. Always returns 200 to prevent email enumeration."""
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not user.is_active:
        return ForgotPasswordResponse(message="If that email is registered, a reset link has been sent.")

    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    user.reset_token_hash = token_hash
    user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
    db.commit()

    sent = send_password_reset(user.email, token)

    from backend.app.core.config import settings
    dev_token = token if (not sent or settings.is_dev) and not settings.SMTP_HOST else None

    return ForgotPasswordResponse(
        message="If that email is registered, a reset link has been sent.",
        dev_token=dev_token,
    )


@router.post("/reset-password")
def reset_password(body: ResetPasswordRequest, db: DbSession):
    """Validate reset token and set new password."""
    token_hash = hashlib.sha256(body.token.encode()).hexdigest()
    user = db.query(User).filter(User.reset_token_hash == token_hash).first()

    if not user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired reset token")

    now = datetime.now(timezone.utc)
    expires = user.reset_token_expires
    if expires is None or (expires.tzinfo is None and expires.replace(tzinfo=timezone.utc) < now) or \
       (expires.tzinfo is not None and expires < now):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Reset token has expired")

    user.hashed_password = hash_password(body.new_password)
    user.reset_token_hash = None
    user.reset_token_expires = None
    db.commit()

    return {"message": "Password updated successfully"}
