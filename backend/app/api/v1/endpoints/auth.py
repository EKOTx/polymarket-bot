"""
Auth endpoints: register, login, /me, forgot/reset password, change password, delete account.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Request, status

from backend.app.api.deps import CurrentUser, DbSession
from backend.app.core.email import send_password_reset, send_verification_email
from backend.app.core.limiter import limiter
from backend.app.core.security import create_access_token, hash_password, verify_password
from backend.app.models.user import User
from backend.app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    RegisterRequest,
    ResendVerificationResponse,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
    VerifyEmailRequest,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/hour")
def register(request: Request, body: RegisterRequest, db: DbSession):
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

    ver_token = secrets.token_urlsafe(32)
    ver_token_hash = hashlib.sha256(ver_token.encode()).hexdigest()

    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        plan="free",
        verification_token_hash=ver_token_hash,
        verification_token_expires=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    send_verification_email(user.email, ver_token)

    token = create_access_token(user.id)
    return TokenResponse(access_token=token, plan=user.plan)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("20/hour")
def login(request: Request, body: LoginRequest, db: DbSession):
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
    return user


@router.patch("/me", response_model=UserResponse)
def update_me(body: dict, user: CurrentUser, db: DbSession):
    if "full_name" in body:
        user.full_name = body["full_name"]
        db.commit()
        db.refresh(user)
    return user


@router.post("/me/change-password")
def change_password(body: ChangePasswordRequest, user: CurrentUser, db: DbSession):
    if not verify_password(body.current_password, user.hashed_password):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Current password is incorrect")
    user.hashed_password = hash_password(body.new_password)
    user.reset_token_hash = None
    user.reset_token_expires = None
    db.commit()
    return {"message": "Password changed successfully"}


@router.delete("/me")
def delete_account(body: dict, user: CurrentUser, db: DbSession):
    """
    Permanently delete account and all associated data.
    Requires email confirmation in body: {"confirm_email": "user@example.com"}
    """
    confirm = body.get("confirm_email", "")
    if confirm.lower() != user.email.lower():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email confirmation does not match")

    from backend.app.models.market import PaperTrade, Portfolio

    db.query(PaperTrade).filter(PaperTrade.user_id == user.id).delete()
    db.query(Portfolio).filter(Portfolio.user_id == user.id).delete()
    db.delete(user)
    db.commit()

    return {"message": "Account deleted"}


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
@limiter.limit("5/hour")
def forgot_password(request: Request, body: ForgotPasswordRequest, db: DbSession):
    """Always returns 200 to prevent email enumeration."""
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


@router.post("/verify-email")
def verify_email(body: VerifyEmailRequest, db: DbSession):
    token_hash = hashlib.sha256(body.token.encode()).hexdigest()
    user = db.query(User).filter(User.verification_token_hash == token_hash).first()

    if not user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired verification token")

    now = datetime.now(timezone.utc)
    expires = user.verification_token_expires
    if expires is not None:
        exp_aware = expires if expires.tzinfo else expires.replace(tzinfo=timezone.utc)
        if exp_aware < now:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Verification token has expired")

    user.is_verified = True
    user.verification_token_hash = None
    user.verification_token_expires = None
    db.commit()

    return {"message": "Email verified successfully"}


@router.post("/resend-verification", response_model=ResendVerificationResponse)
@limiter.limit("3/hour")
def resend_verification(request: Request, user: CurrentUser, db: DbSession):
    if user.is_verified:
        return ResendVerificationResponse(message="Email is already verified")

    ver_token = secrets.token_urlsafe(32)
    ver_token_hash = hashlib.sha256(ver_token.encode()).hexdigest()
    user.verification_token_hash = ver_token_hash
    user.verification_token_expires = datetime.now(timezone.utc) + timedelta(hours=24)
    db.commit()

    sent = send_verification_email(user.email, ver_token)

    from backend.app.core.config import settings
    dev_token = ver_token if (not sent or settings.is_dev) and not settings.SMTP_HOST else None

    return ResendVerificationResponse(
        message="Verification email sent",
        dev_token=dev_token,
    )
