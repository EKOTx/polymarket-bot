"""
Stripe billing endpoints: checkout, portal, webhook, status.
"""

from __future__ import annotations

from datetime import datetime

import stripe
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from backend.app.api.deps import CurrentUser, DbSession
from backend.app.core.config import settings
from backend.app.models.user import Subscription, User

router = APIRouter(prefix="/billing", tags=["billing"])

# Price ID → plan name mapping (populated from env vars at call time, not import time)
def _price_to_plan() -> dict[str, str]:
    m: dict[str, str] = {}
    if settings.STRIPE_PRICE_PRO:
        m[settings.STRIPE_PRICE_PRO] = "pro"
    if settings.STRIPE_PRICE_PREMIUM:
        m[settings.STRIPE_PRICE_PREMIUM] = "premium"
    return m


def _stripe_configured() -> bool:
    return bool(settings.STRIPE_SECRET_KEY)


def _require_stripe() -> None:
    if not _stripe_configured():
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Stripe not configured")
    stripe.api_key = settings.STRIPE_SECRET_KEY


class CheckoutRequest(BaseModel):
    plan: str  # "pro" | "premium"


# ---------------------------------------------------------------------------
# GET /billing/status
# ---------------------------------------------------------------------------

@router.get("/status")
def billing_status(user: CurrentUser, db: DbSession):
    sub = (
        db.query(Subscription)
        .filter(Subscription.user_id == user.id)
        .order_by(Subscription.created_at.desc())
        .first()
    )
    return {
        "plan": user.plan,
        "stripe_customer_id": user.stripe_customer_id,
        "subscription": {
            "id": sub.id,
            "stripe_subscription_id": sub.stripe_subscription_id,
            "status": sub.status,
            "current_period_end": sub.current_period_end.isoformat() if sub.current_period_end else None,
        } if sub else None,
    }


# ---------------------------------------------------------------------------
# POST /billing/checkout
# ---------------------------------------------------------------------------

@router.post("/checkout")
def create_checkout(body: CheckoutRequest, user: CurrentUser, db: DbSession):
    _require_stripe()

    price_map = {"pro": settings.STRIPE_PRICE_PRO, "premium": settings.STRIPE_PRICE_PREMIUM}
    price_id = price_map.get(body.plan)
    if not price_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unknown plan: {body.plan}")

    # Create Stripe customer on first checkout
    if not user.stripe_customer_id:
        customer = stripe.Customer.create(
            email=user.email,
            metadata={"user_id": str(user.id)},
        )
        user.stripe_customer_id = customer.id
        db.commit()

    session = stripe.checkout.Session.create(
        customer=user.stripe_customer_id,
        line_items=[{"price": price_id, "quantity": 1}],
        mode="subscription",
        success_url=f"{settings.FRONTEND_URL}/settings?checkout=success",
        cancel_url=f"{settings.FRONTEND_URL}/settings?checkout=cancelled",
        metadata={"user_id": str(user.id)},
        allow_promotion_codes=True,
    )

    return {"url": session.url}


# ---------------------------------------------------------------------------
# POST /billing/portal
# ---------------------------------------------------------------------------

@router.post("/portal")
def create_portal(user: CurrentUser):
    _require_stripe()

    if not user.stripe_customer_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No billing account found")

    session = stripe.billing_portal.Session.create(
        customer=user.stripe_customer_id,
        return_url=f"{settings.FRONTEND_URL}/settings",
    )
    return {"url": session.url}


# ---------------------------------------------------------------------------
# POST /billing/webhook
# ---------------------------------------------------------------------------

@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(request: Request, db: DbSession):
    _require_stripe()

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.SignatureVerificationError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid Stripe signature")

    etype = event["type"]
    data = event["data"]["object"]

    if etype == "checkout.session.completed":
        _handle_checkout_completed(data, db)

    elif etype in ("customer.subscription.updated", "customer.subscription.created"):
        _handle_subscription_updated(data, db)

    elif etype == "customer.subscription.deleted":
        _handle_subscription_deleted(data, db)

    elif etype == "invoice.payment_failed":
        _handle_payment_failed(data, db)

    return {"received": True}


# ---------------------------------------------------------------------------
# Webhook helpers
# ---------------------------------------------------------------------------

def _user_by_customer(customer_id: str, db: DbSession) -> User | None:
    return db.query(User).filter(User.stripe_customer_id == customer_id).first()


def _handle_checkout_completed(session: dict, db: DbSession) -> None:
    customer_id = session.get("customer")
    user_id = int(session.get("metadata", {}).get("user_id", 0))

    user = db.query(User).filter(User.id == user_id).first() if user_id else None
    if not user and customer_id:
        user = _user_by_customer(customer_id, db)
    if not user:
        return

    if customer_id and not user.stripe_customer_id:
        user.stripe_customer_id = customer_id

    subscription_id = session.get("subscription")
    if subscription_id:
        _sync_subscription(subscription_id, user, db)
    db.commit()


def _handle_subscription_updated(sub: dict, db: DbSession) -> None:
    customer_id = sub.get("customer")
    user = _user_by_customer(customer_id, db) if customer_id else None
    if not user:
        return
    _sync_subscription_obj(sub, user, db)
    db.commit()


def _handle_subscription_deleted(sub: dict, db: DbSession) -> None:
    customer_id = sub.get("customer")
    user = _user_by_customer(customer_id, db) if customer_id else None
    if not user:
        return
    user.plan = "free"
    stripe_sub_id = sub.get("id")
    if stripe_sub_id:
        existing = (
            db.query(Subscription)
            .filter(Subscription.stripe_subscription_id == stripe_sub_id)
            .first()
        )
        if existing:
            existing.status = "canceled"
    db.commit()


def _handle_payment_failed(invoice: dict, db: DbSession) -> None:
    customer_id = invoice.get("customer")
    user = _user_by_customer(customer_id, db) if customer_id else None
    if not user:
        return
    sub_id = invoice.get("subscription")
    if sub_id:
        existing = (
            db.query(Subscription)
            .filter(Subscription.stripe_subscription_id == sub_id)
            .first()
        )
        if existing:
            existing.status = "past_due"
            db.commit()


def _sync_subscription(subscription_id: str, user: User, db: DbSession) -> None:
    sub_obj = stripe.Subscription.retrieve(subscription_id)
    _sync_subscription_obj(sub_obj, user, db)


def _sync_subscription_obj(sub: dict, user: User, db: DbSession) -> None:
    price_to_plan = _price_to_plan()
    items = sub.get("items", {}).get("data", [])
    price_id = items[0]["price"]["id"] if items else None
    plan_name = price_to_plan.get(price_id, "free") if price_id else "free"
    sub_status = sub.get("status", "active")

    user.plan = plan_name if sub_status == "active" else "free"

    stripe_sub_id = sub.get("id")
    period_end_ts = sub.get("current_period_end")
    period_start_ts = sub.get("current_period_start")

    existing = (
        db.query(Subscription)
        .filter(Subscription.stripe_subscription_id == stripe_sub_id)
        .first()
    ) if stripe_sub_id else None

    if existing:
        existing.plan = plan_name
        existing.status = sub_status
        existing.stripe_price_id = price_id
        if period_end_ts:
            existing.current_period_end = datetime.utcfromtimestamp(period_end_ts)
        if period_start_ts:
            existing.current_period_start = datetime.utcfromtimestamp(period_start_ts)
    else:
        new_sub = Subscription(
            user_id=user.id,
            stripe_subscription_id=stripe_sub_id,
            stripe_price_id=price_id,
            plan=plan_name,
            status=sub_status,
            current_period_start=datetime.utcfromtimestamp(period_start_ts) if period_start_ts else None,
            current_period_end=datetime.utcfromtimestamp(period_end_ts) if period_end_ts else None,
        )
        db.add(new_sub)
