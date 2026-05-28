"""
Admin-only endpoints. All routes require is_superuser=True.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.api.deps import CurrentUser, DbSession, get_current_user
from backend.app.models.public import ContactMessage, WaitlistEntry
from backend.app.models.user import User

router = APIRouter(prefix="/admin", tags=["admin"])


def require_superuser(user: Annotated[User, Depends(get_current_user)]) -> User:
    if not user.is_superuser:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin access required")
    return user


SuperUser = Annotated[User, Depends(require_superuser)]


# ── Users ────────────────────────────────────────────────────────────────────

@router.get("/users")
def list_users(
    _: SuperUser,
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    total = db.query(User).count()
    users = (
        db.query(User)
        .order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": u.id,
                "email": u.email,
                "full_name": u.full_name,
                "plan": u.plan,
                "is_verified": u.is_verified,
                "is_active": u.is_active,
                "is_superuser": u.is_superuser,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "last_login": u.last_login.isoformat() if u.last_login else None,
            }
            for u in users
        ],
    }


@router.patch("/users/{user_id}")
def update_user(
    user_id: int,
    body: dict,
    _: SuperUser,
    db: DbSession,
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    allowed = {"plan", "is_active", "is_verified", "is_superuser"}
    for key, value in body.items():
        if key in allowed:
            setattr(user, key, value)

    db.commit()
    return {"message": "User updated", "id": user_id}


# ── Waitlist ─────────────────────────────────────────────────────────────────

@router.get("/waitlist")
def list_waitlist(
    _: SuperUser,
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    total = db.query(WaitlistEntry).count()
    entries = (
        db.query(WaitlistEntry)
        .order_by(WaitlistEntry.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": e.id,
                "email": e.email,
                "marketing_consent": e.marketing_consent,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in entries
        ],
    }


# ── Contact messages ─────────────────────────────────────────────────────────

@router.get("/contact")
def list_contact(
    _: SuperUser,
    db: DbSession,
    unread_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    q = db.query(ContactMessage)
    if unread_only:
        q = q.filter(ContactMessage.is_read == False)  # noqa: E712
    total = q.count()
    messages = (
        q.order_by(ContactMessage.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": m.id,
                "name": m.name,
                "email": m.email,
                "subject": m.subject,
                "message": m.message,
                "is_read": m.is_read,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in messages
        ],
    }


@router.patch("/contact/{message_id}/read")
def mark_contact_read(
    message_id: int,
    _: SuperUser,
    db: DbSession,
):
    msg = db.get(ContactMessage, message_id)
    if not msg:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Message not found")
    msg.is_read = True
    db.commit()
    return {"message": "Marked as read"}
