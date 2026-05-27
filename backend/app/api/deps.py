"""
FastAPI dependencies: auth, DB session, plan gating.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import decode_access_token
from backend.app.models.user import User

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Require valid JWT. Returns User or raises 401."""
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")

    user_id = int(payload.get("sub", 0))
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or inactive")

    return user


def get_current_user_optional(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    db: Annotated[Session, Depends(get_db)],
) -> User | None:
    """Like get_current_user but returns None for unauthenticated requests."""
    if credentials is None:
        return None
    try:
        return get_current_user(credentials, db)
    except HTTPException:
        return None


def require_plan(min_plan: str):
    """
    Dependency factory: require user to have at least `min_plan`.
    Plan hierarchy: free < pro < premium
    """
    PLAN_RANK = {"free": 0, "pro": 1, "premium": 2}

    def check(user: Annotated[User, Depends(get_current_user)]) -> User:
        user_rank = PLAN_RANK.get(user.plan, 0)
        required_rank = PLAN_RANK.get(min_plan, 0)
        if user_rank < required_rank:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"This feature requires {min_plan} plan. You are on {user.plan}.",
            )
        return user

    return check


# Convenient type aliases
CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_current_user_optional)]
ProUser = Annotated[User, Depends(require_plan("pro"))]
PremiumUser = Annotated[User, Depends(require_plan("premium"))]
DbSession = Annotated[Session, Depends(get_db)]
