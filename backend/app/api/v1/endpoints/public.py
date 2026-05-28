"""
Public endpoints (no auth): waitlist signup, contact form.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status

from backend.app.api.deps import DbSession
from backend.app.core.email import send_email, send_waitlist_confirmation
from backend.app.core.config import settings
from backend.app.models.public import ContactMessage, WaitlistEntry
from backend.app.schemas.public import (
    ContactRequest,
    ContactResponse,
    WaitlistRequest,
    WaitlistResponse,
)

router = APIRouter(tags=["public"])
logger = logging.getLogger(__name__)


@router.post("/waitlist", response_model=WaitlistResponse, status_code=status.HTTP_200_OK)
def join_waitlist(body: WaitlistRequest, db: DbSession):
    existing = db.query(WaitlistEntry).filter(WaitlistEntry.email == body.email).first()
    if existing:
        return WaitlistResponse(
            message="You're already on the waitlist.",
            already_registered=True,
        )

    entry = WaitlistEntry(email=body.email, marketing_consent=body.marketing_consent)
    db.add(entry)
    db.commit()

    send_waitlist_confirmation(body.email)

    if settings.WAITLIST_NOTIFY_EMAIL:
        send_email(
            settings.WAITLIST_NOTIFY_EMAIL,
            f"New waitlist signup: {body.email}",
            f"<p>{body.email} joined the waitlist. Marketing consent: {body.marketing_consent}</p>",
        )

    return WaitlistResponse(message="You're on the waitlist! We'll be in touch.")


@router.post("/contact", response_model=ContactResponse, status_code=status.HTTP_200_OK)
def submit_contact(body: ContactRequest, db: DbSession):
    if len(body.message) < 10:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Message too short")

    msg = ContactMessage(
        name=body.name,
        email=body.email,
        subject=body.subject,
        message=body.message,
    )
    db.add(msg)
    db.commit()

    if settings.WAITLIST_NOTIFY_EMAIL:
        send_email(
            settings.WAITLIST_NOTIFY_EMAIL,
            f"[Contact] {body.subject} — {body.name}",
            f"<p><b>From:</b> {body.name} ({body.email})<br/>"
            f"<b>Subject:</b> {body.subject}<br/><br/>{body.message}</p>",
        )

    return ContactResponse(message="Message received. We aim to respond within 2 business days.")
