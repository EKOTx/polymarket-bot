"""
Application configuration via pydantic-settings.
Reads from environment variables / .env file.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ───────────────────────────────────────────────────────────────────
    APP_NAME: str = "Polymarket Intelligence"
    APP_VERSION: str = "0.1.0"
    ENV: Literal["development", "production", "test"] = "development"
    DEBUG: bool = False

    # ── Security ──────────────────────────────────────────────────────────────
    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7   # 7 days

    # ── Database ──────────────────────────────────────────────────────────────
    # Supports SQLite (dev) and PostgreSQL (prod)
    DATABASE_URL: str = "sqlite:///./data/polymarket.db"

    # ── CORS ──────────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://polymarket-intel.vercel.app",  # update with real domain
    ]

    @property
    def CORS_ORIGINS(self) -> list[str]:
        return self.ALLOWED_ORIGINS

    # ── Scanner ───────────────────────────────────────────────────────────────
    SCAN_INTERVAL_SECONDS: int = 30
    MARKET_LIMIT: int = 500
    MIN_LIQUIDITY: float = 500.0
    CLOB_CONCURRENCY: int = 15
    ENABLE_EXTERNAL_ODDS: bool = True
    EXTERNAL_ODDS_EVERY_N: int = 3

    # ── Strategies ────────────────────────────────────────────────────────────
    MIN_EDGE_PCT: float = 0.5
    MIN_VIG_PCT: float = 2.0
    MIN_CONFIDENCE: float = 0.4
    DISABLE_STRATEGIES: str = ""

    # ── Paper trading ─────────────────────────────────────────────────────────
    ENABLE_REAL_TRADING: bool = False   # NEVER change without full implementation
    PAPER_STARTING_BALANCE: float = 10_000.0
    PAPER_MAX_POSITION_SIZE: float = 500.0
    PAPER_MAX_DAILY_LOSS: float = 1_000.0
    PAPER_MAX_OPEN_POSITIONS: int = 10
    PAPER_MAX_EXPOSURE_PCT: float = 0.40

    # ── Alerts ────────────────────────────────────────────────────────────────
    DISCORD_WEBHOOK_URL: str = ""
    SLACK_WEBHOOK_URL: str = ""
    ALERT_MIN_EDGE_PCT: float = 3.0
    ALERT_COOLDOWN_MINUTES: int = 60
    ALERT_DIGEST_HOUR: int = 8

    # ── Stripe ────────────────────────────────────────────────────────────────
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_PRO: str = ""       # price_xxx
    STRIPE_PRICE_PREMIUM: str = ""

    # ── Email ─────────────────────────────────────────────────────────────────
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@polymarket-intel.com"
    FRONTEND_URL: str = "http://localhost:3000"

    # ── Waitlist ──────────────────────────────────────────────────────────────
    WAITLIST_NOTIFY_EMAIL: str = ""  # email to notify on new waitlist signup

    # ── External APIs ─────────────────────────────────────────────────────────
    THE_ODDS_API_KEY: str = ""

    @field_validator("ENABLE_REAL_TRADING", mode="before")
    @classmethod
    def block_real_trading(cls, v):
        """Hard guard: real trading disabled unless explicitly enabled."""
        if str(v).lower() == "true":
            import os
            if os.getenv("I_UNDERSTAND_REAL_TRADING_RISKS") != "yes":
                raise ValueError(
                    "Set I_UNDERSTAND_REAL_TRADING_RISKS=yes to enable real trading"
                )
        return v

    @property
    def is_postgres(self) -> bool:
        return self.DATABASE_URL.startswith("postgresql")

    @property
    def is_dev(self) -> bool:
        return self.ENV == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
