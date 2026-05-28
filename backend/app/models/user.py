"""
User and subscription ORM models.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)

    plan: Mapped[str] = mapped_column(String(50), default="free")
    # free | pro | premium

    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    reset_token_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reset_token_expires: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    verification_token_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    verification_token_expires: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    subscriptions: Mapped[list["Subscription"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    alert_rules: Mapped[list["AlertRule"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.email} plan={self.plan}>"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    stripe_price_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    plan: Mapped[str] = mapped_column(String(50))           # free | pro | premium
    status: Mapped[str] = mapped_column(String(50))         # active | canceled | past_due
    current_period_start: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    current_period_end: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="subscriptions")


class AlertRule(Base):
    """User-defined alert conditions."""
    __tablename__ = "alert_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    alert_type: Mapped[str] = mapped_column(String(50))
    # edge_threshold | vig_threshold | price_move | liquidity_spike | external_divergence

    # Condition parameters (JSON-like columns)
    min_edge_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    min_vig_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    market_filter: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    platforms: Mapped[Optional[str]] = mapped_column(Text, nullable=True)      # JSON list

    # Delivery
    delivery_email: Mapped[bool] = mapped_column(Boolean, default=True)
    delivery_discord: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_fired: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    fire_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="alert_rules")
