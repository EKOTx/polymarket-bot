"""
Auth endpoints: register, login, /me, refresh.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, status

from backend.app.api.deps import CurrentUser, DbSession
from backend.app.core.security import create_access_token, hash_password, verify_password
from backend.app.models.user import User
from backend.app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
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
