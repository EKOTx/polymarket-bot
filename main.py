"""
main.py - Polymarket Arbitrage Scanner Bot

Runs two scanners in alternating cycles:
  1. YES/NO same-market scanner  (arbitrage.py)
  2. Tournament cross-market scanner  (tournament_scanner.py)

Stop with Ctrl+C.
"""

import time
import sys
import argparse

import config
from src import market_scanner, arbitrage, terminal_ui
from src.tournament_scanner import scan_tournaments
from src.paper_trader import PaperTrader


def parse_args():
    p = argparse.ArgumentParser(description="Polymarket scanner bot")
    p.add_argument(
        "--mode",
        choices=["all", "market", "tournament"],
        default="all",
        help="Scanner mode: all (default), market (YES/NO arb), tournament",
    )
    return p.parse_args()


def run_market_scan(scan_count: int, paper_trader: PaperTrader):
    """Run same-market YES/NO arbitrage scan."""
    markets = market_scanner.scan_markets()
    opportunities = arbitrage.scan_for_opportunities(markets)

    terminal_ui.print_header(
        dry_run=config.DRY_RUN,
        scan_count=scan_count,
        market_count=len(markets),
    )
    terminal_ui.print_opportunities(opportunities)
    terminal_ui.print_market_summary(markets)

    if opportunities and config.DRY_RUN:
        best = opportunities[0]
        if best["confidence"] in ("HIGH", "MEDIUM"):
            paper_trader.simulate_arbitrage(best, size_usd=10.0)
            terminal_ui.print_paper_trades(paper_trader.trades, paper_trader.balance)


def run_tournament_scan():
    """Run cross-market tournament mispricing scan."""
    tournament_opps = scan_tournaments(market_limit=config.MARKET_LIMIT)
    terminal_ui.print_tournament_opportunities(tournament_opps, max_display=15)


def main():
    args = parse_args()

    if config.DRY_RUN:
        terminal_ui.console.print(
            "\n[bold yellow]🟡 DRY RUN MODE: No real trades will be placed.[/bold yellow]\n"
        )
    else:
        terminal_ui.console.print(
            "\n[bold red]🔴 WARNING: DRY_RUN=false. Real trading NOT yet implemented.[/bold red]\n"
        )

    terminal_ui.console.print("[bold]Configuration:[/bold]")
    config.print_config_summary()
    terminal_ui.console.print(f"  Mode:                 {args.mode}\n")

    paper_trader = PaperTrader()
    scan_count = 0

    terminal_ui.console.print("[dim]Starting scanner. Press Ctrl+C to stop.[/dim]\n")
    time.sleep(1)

    try:
        while True:
            scan_count += 1
            terminal_ui.clear()

            if args.mode == "tournament":
                terminal_ui.print_header(
                    dry_run=config.DRY_RUN,
                    scan_count=scan_count,
                    market_count=0,
                )
                run_tournament_scan()

            elif args.mode == "market":
                run_market_scan(scan_count, paper_trader)

            else:  # all — alternate every other scan
                if scan_count % 2 == 1:
                    # Odd scans: tournament (slower, more insightful)
                    terminal_ui.print_header(
                        dry_run=config.DRY_RUN,
                        scan_count=scan_count,
                        market_count=0,
                    )
                    terminal_ui.console.print(
                        "[bold cyan]═══ TOURNAMENT SCANNER ═══[/bold cyan]\n"
                    )
                    run_tournament_scan()
                else:
                    # Even scans: market arb (fast)
                    terminal_ui.console.print(
                        "[bold cyan]═══ MARKET SCANNER ═══[/bold cyan]\n"
                    )
                    run_market_scan(scan_count, paper_trader)

            terminal_ui.print_info(
                f"\nNext scan in {config.SCAN_INTERVAL_SECONDS}s... (Ctrl+C to stop)"
            )
            time.sleep(config.SCAN_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        terminal_ui.console.print("\n\n[bold]Stopping scanner...[/bold]")
        paper_trader.print_summary()
        terminal_ui.console.print("[green]Goodbye.[/green]")
        sys.exit(0)


if __name__ == "__main__":
    main()
