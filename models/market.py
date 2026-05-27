"""Pydantic models for market data (not ORM — these are data transfer objects)."""

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field, computed_field


class OrderBook(BaseModel):
    """Normalized order book for one token."""
    token_id: str
    outcome: str                          # "Yes" | "No"
    bids: list[dict] = Field(default_factory=list)   # [{"price": float, "size": float}]
    asks: list[dict] = Field(default_factory=list)
    best_bid: Optional[float] = None
    best_ask: Optional[float] = None
    price_source: str = "clob"           # "clob" | "gamma"

    @computed_field
    @property
    def mid(self) -> Optional[float]:
        if self.best_bid and self.best_ask:
            return (self.best_bid + self.best_ask) / 2
        return self.best_bid or self.best_ask

    @computed_field
    @property
    def spread(self) -> Optional[float]:
        if self.best_bid and self.best_ask:
            return self.best_ask - self.best_bid
        return None

    @computed_field
    @property
    def spread_pct(self) -> Optional[float]:
        if self.spread and self.mid and self.mid > 0:
            return (self.spread / self.mid) * 100
        return None

    @computed_field
    @property
    def bid_depth_usd(self) -> float:
        """Total USD value available at all bid levels."""
        return sum(b["price"] * b["size"] for b in self.bids)

    @computed_field
    @property
    def ask_depth_usd(self) -> float:
        """Total USD value available at all ask levels."""
        return sum(a["price"] * a["size"] for a in self.asks)


class MarketData(BaseModel):
    """Fully enriched market with both YES and NO order books."""
    market_id: str
    question: str
    event_title: str = ""
    event_id: str = ""
    volume: float = 0.0
    liquidity: float = 0.0

    yes_book: Optional[OrderBook] = None
    no_book: Optional[OrderBook] = None

    # Convenience accessors (populated from books)
    yes_bid: Optional[float] = None
    yes_ask: Optional[float] = None
    no_bid: Optional[float] = None
    no_ask: Optional[float] = None
    yes_mid: Optional[float] = None
    no_mid: Optional[float] = None

    price_source: str = "gamma"

    def enrich_from_books(self) -> None:
        """Populate flat price fields from order books."""
        if self.yes_book:
            self.yes_bid = self.yes_book.best_bid
            self.yes_ask = self.yes_book.best_ask
            self.yes_mid = self.yes_book.mid
        if self.no_book:
            self.no_bid = self.no_book.best_bid
            self.no_ask = self.no_book.best_ask
            self.no_mid = self.no_book.mid

    @computed_field
    @property
    def ask_sum(self) -> Optional[float]:
        """Cost to buy both YES and NO."""
        if self.yes_ask and self.no_ask:
            return self.yes_ask + self.no_ask
        return None

    @computed_field
    @property
    def bid_sum(self) -> Optional[float]:
        if self.yes_bid and self.no_bid:
            return self.yes_bid + self.no_bid
        return None

    @computed_field
    @property
    def mid_sum(self) -> Optional[float]:
        if self.yes_mid and self.no_mid:
            return self.yes_mid + self.no_mid
        return None

    @computed_field
    @property
    def yes_spread_pct(self) -> Optional[float]:
        if self.yes_book:
            return self.yes_book.spread_pct
        return None

    @computed_field
    @property
    def has_prices(self) -> bool:
        return all(v is not None for v in [self.yes_bid, self.yes_ask, self.no_bid, self.no_ask])


class TournamentGroup(BaseModel):
    """A group of related mutually-exclusive markets (e.g. FIFA winner)."""
    event_title: str
    event_id: str = ""
    market_count: int
    markets: list[MarketData]

    sum_yes_mid: float
    sum_yes_ask: float
    sum_yes_bid: float
    vig_pct: float                    # (sum_mid - 1.0) * 100
    buy_all_profit_pct: float         # (1 - sum_ask) * 100
    field_probability: float          # 1 - sum_mid (missing outcomes)
    total_liquidity: float

    is_cumulative: bool = False       # Nested markets (false positive)
    warnings: list[str] = Field(default_factory=list)
    opportunity_type: str = "NORMAL_VIG"  # BUY_ALL|BUY_ALL_RISKY|HIGH_VIG|ELEVATED_VIG|NORMAL_VIG
    confidence: float = 0.0
