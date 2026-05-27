"""
paper_trader.py - Simulate trades without real money.

Tracks a fake balance and logs simulated trades.
Never sends real orders. Used to evaluate strategy performance.
"""

from datetime import datetime
import config
from src.utils import now_str


class PaperTrader:
    """
    Simulates executing arbitrage trades on paper.

    Tracks balance and trade history. All trades are fake.
    """

    def __init__(self, starting_balance: float = None):
        self.balance = starting_balance or config.PAPER_STARTING_BALANCE
        self.starting_balance = self.balance
        self.trades: list[dict] = []
        self.total_invested = 0.0
        self.total_profit = 0.0

    def simulate_arbitrage(self, opportunity: dict, size_usd: float = 10.0) -> dict:
        """
        Simulate buying both sides of an arbitrage opportunity.

        For UNDERPRICED: buy YES + buy NO
        For OVERPRICED: sell YES + sell NO (buying the other side)

        Args:
            opportunity: From arbitrage.scan_for_opportunities()
            size_usd: How much to invest (in USD)

        Returns:
            Trade record dict.
        """
        opp_type = opportunity.get("opportunity_type", "UNKNOWN")
        cost = opportunity.get("total_cost", 1.0)
        profit_pct = opportunity.get("profit_pct", 0.0)

        # Expected profit on this trade
        expected_profit = size_usd * (profit_pct / 100.0)

        # Check we have enough fake balance
        if size_usd > self.balance:
            return {
                "status": "REJECTED",
                "reason": f"Insufficient paper balance (${self.balance:.2f} < ${size_usd:.2f})",
            }

        # Deduct cost from paper balance
        self.balance -= size_usd

        trade = {
            "timestamp": now_str(),
            "market": opportunity.get("title", "Unknown"),
            "market_id": opportunity.get("market_id", ""),
            "action": f"PAPER_{opp_type}",
            "cost": size_usd,
            "expected_profit": expected_profit,
            "yes_ask": opportunity.get("yes_ask"),
            "no_ask": opportunity.get("no_ask"),
            "yes_bid": opportunity.get("yes_bid"),
            "no_bid": opportunity.get("no_bid"),
            "profit_pct": profit_pct,
            "confidence": opportunity.get("confidence", "?"),
            "status": "SIMULATED",
        }

        self.trades.append(trade)
        self.total_invested += size_usd
        self.total_profit += expected_profit  # optimistic estimate

        return trade

    def execute_real_trade(self, opportunity: dict) -> None:
        """
        Real trading - NOT IMPLEMENTED.

        This method exists to mark where real trading would go.
        It will always raise to prevent accidental live trading.
        """
        raise NotImplementedError(
            "Real trading is disabled. "
            "Set DRY_RUN=false and implement authenticated order placement "
            "in polymarket_client.place_order() when ready."
        )

    @property
    def pnl(self) -> float:
        """Paper profit/loss vs starting balance."""
        return self.balance - self.starting_balance + self.total_profit

    @property
    def roi_pct(self) -> float:
        """Return on investment %."""
        if self.total_invested == 0:
            return 0.0
        return (self.total_profit / self.total_invested) * 100

    def summary(self) -> dict:
        """Return summary stats for display."""
        return {
            "starting_balance": self.starting_balance,
            "current_balance": self.balance,
            "total_invested": self.total_invested,
            "expected_profit": self.total_profit,
            "pnl": self.pnl,
            "roi_pct": self.roi_pct,
            "trade_count": len(self.trades),
        }

    def print_summary(self):
        """Print summary to stdout."""
        s = self.summary()
        print(f"\n--- Paper Trader Summary ---")
        print(f"  Starting balance:  ${s['starting_balance']:,.2f}")
        print(f"  Current balance:   ${s['current_balance']:,.2f}")
        print(f"  Total invested:    ${s['total_invested']:,.2f}")
        print(f"  Expected profit:   ${s['expected_profit']:,.2f}")
        print(f"  Estimated ROI:     {s['roi_pct']:.2f}%")
        print(f"  Total trades:      {s['trade_count']}")
        print(f"----------------------------\n")
