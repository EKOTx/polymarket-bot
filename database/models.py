"""
SQLAlchemy ORM models.
All timestamps are UTC.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    String, Float, Boolean, Integer, DateTime, Text, ForeignKey, Index
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Market(Base):
    """One Polymarket market (YES/NO question)."""
    __tablename__ = "markets"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    question: Mapped[str] = mapped_column(String, nullable=False)
    event_title: Mapped[str] = mapped_column(String, default="")
    event_id: Mapped[str] = mapped_column(String, default="", index=True)
    volume: Mapped[float] = mapped_column(Float, default=0.0)
    liquidity: Mapped[float] = mapped_column(Float, default=0.0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    outcomes: Mapped[str] = mapped_column(String, default="[]")        # JSON list
    clob_token_ids: Mapped[str] = mapped_column(String, default="[]")  # JSON list
    outcome_prices: Mapped[str] = mapped_column(String, default="[]")  # JSON list
    first_seen: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    snapshots: Mapped[list["PriceSnapshot"]] = relationship(
        back_populates="market", cascade="all, delete-orphan"
    )


class PriceSnapshot(Base):
    """
    Point-in-time bid/ask for one outcome (YES or NO) of a market.
    One row per outcome per scan cycle.
    """
    __tablename__ = "price_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    market_id: Mapped[str] = mapped_column(
        String, ForeignKey("markets.id", ondelete="CASCADE"), index=True
    )
    outcome: Mapped[str] = mapped_column(String)          # "Yes" | "No"
    token_id: Mapped[str] = mapped_column(String, default="")
    bid: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ask: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    mid: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    spread: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    spread_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bid_depth_usd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ask_depth_usd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    price_source: Mapped[str] = mapped_column(String, default="gamma")  # "clob"|"gamma"
    scan_id: Mapped[int] = mapped_column(Integer, index=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )

    market: Mapped["Market"] = relationship(back_populates="snapshots")

    __table_args__ = (
        Index("ix_snapshot_market_time", "market_id", "timestamp"),
    )


class Opportunity(Base):
    """
    Detected pricing opportunity. One row per opportunity per scan.
    """
    __tablename__ = "opportunities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scan_id: Mapped[int] = mapped_column(Integer, index=True)
    opportunity_type: Mapped[str] = mapped_column(String, index=True)
    # VALUE | HIGH_VIG | TOURNAMENT_ARB | TOURNAMENT_ARB_RISKY | SPREAD
    event_title: Mapped[str] = mapped_column(String, default="")
    market_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    title: Mapped[str] = mapped_column(String)
    edge_pct: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float)
    expected_value: Mapped[float] = mapped_column(Float)
    suggested_size_usd: Mapped[float] = mapped_column(Float, default=0.0)
    yes_bid: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    yes_ask: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    no_bid: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    no_ask: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sum_yes_mid: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    vig_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    liquidity: Mapped[float] = mapped_column(Float, default=0.0)
    market_count: Mapped[int] = mapped_column(Integer, default=1)
    warnings: Mapped[str] = mapped_column(Text, default="[]")       # JSON list
    details: Mapped[str] = mapped_column(Text, default="{}")        # JSON dict
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )


class PaperTrade(Base):
    """Simulated trade for strategy evaluation."""
    __tablename__ = "paper_trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    opportunity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    market_id: Mapped[str] = mapped_column(String)
    question: Mapped[str] = mapped_column(String)
    event_title: Mapped[str] = mapped_column(String, default="")
    outcome: Mapped[str] = mapped_column(String)     # "Yes" | "No" | "ALL"
    side: Mapped[str] = mapped_column(String)        # "BUY" | "SELL"
    strategy: Mapped[str] = mapped_column(String)    # strategy name
    entry_price: Mapped[float] = mapped_column(Float)
    size_shares: Mapped[float] = mapped_column(Float)
    cost_usd: Mapped[float] = mapped_column(Float)
    exit_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    realized_pnl: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    unrealized_pnl: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String, default="OPEN")  # OPEN|CLOSED|CANCELLED
    notes: Mapped[str] = mapped_column(Text, default="")
    opened_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class ScanRun(Base):
    """Metadata for each scan cycle."""
    __tablename__ = "scan_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    markets_fetched: Mapped[int] = mapped_column(Integer, default=0)
    markets_priced: Mapped[int] = mapped_column(Integer, default=0)
    opportunities_found: Mapped[int] = mapped_column(Integer, default=0)
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    error: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class Portfolio(Base):
    """Snapshot of paper trading portfolio state after each scan."""
    __tablename__ = "portfolio"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    balance: Mapped[float] = mapped_column(Float)
    starting_balance: Mapped[float] = mapped_column(Float)
    total_invested: Mapped[float] = mapped_column(Float, default=0.0)
    realized_pnl: Mapped[float] = mapped_column(Float, default=0.0)
    unrealized_pnl: Mapped[float] = mapped_column(Float, default=0.0)
    open_positions: Mapped[int] = mapped_column(Integer, default=0)
    total_trades: Mapped[int] = mapped_column(Integer, default=0)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class ExternalOddsSnapshot(Base):
    """
    Point-in-time external market odds from Kalshi / PredictIt.
    Stored per scan for historical comparison and drift analysis.
    """
    __tablename__ = "external_odds_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scan_id: Mapped[int] = mapped_column(Integer, index=True)
    platform: Mapped[str] = mapped_column(String, index=True)       # "kalshi"|"predictit"
    platform_market_id: Mapped[str] = mapped_column(String, index=True)
    title: Mapped[str] = mapped_column(String)
    outcome_label: Mapped[str] = mapped_column(String, default="Yes")
    yes_ask: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    yes_bid: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    mid: Mapped[float] = mapped_column(Float)
    fair_probability: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    volume: Mapped[float] = mapped_column(Float, default=0.0)
    group_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("ix_ext_odds_platform_time", "platform", "timestamp"),
    )
