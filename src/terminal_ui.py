"""
terminal_ui.py - Rich terminal display for the bot.

Uses the `rich` library for colored tables and panels.
All display logic is here - keeps other modules clean.
"""

from datetime import datetime
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich import box
from rich.text import Text
from src.utils import truncate

console = Console()


def print_header(dry_run: bool, scan_count: int, market_count: int):
    """Print top status panel."""
    mode = (
        Text("🟡 DRY RUN (paper trading)", style="bold yellow")
        if dry_run
        else Text("🔴 LIVE MODE - REAL TRADES", style="bold red")
    )

    now = datetime.now().strftime("%H:%M:%S")

    header_text = Text()
    header_text.append("POLYMARKET ARBITRAGE SCANNER\n", style="bold white")
    header_text.append(f"Time: {now}  |  Scans: {scan_count}  |  Markets: {market_count}\n")
    header_text.append("Mode: ")
    header_text.append_text(mode)

    console.print(Panel(header_text, border_style="blue", expand=True))


def print_opportunities(opportunities: list[dict], max_display: int = 10):
    """Print table of detected arbitrage opportunities."""
    if not opportunities:
        console.print(
            Panel(
                "No opportunities found above threshold.",
                border_style="dim",
                title="Opportunities",
            )
        )
        return

    table = Table(
        title=f"Arbitrage Opportunities ({len(opportunities)} found)",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
        expand=True,
    )

    table.add_column("Market", style="white", max_width=40, no_wrap=False)
    table.add_column("Type", style="bold", width=12)
    table.add_column("YES Bid", justify="right", width=9)
    table.add_column("YES Ask", justify="right", width=9)
    table.add_column("NO Bid", justify="right", width=9)
    table.add_column("NO Ask", justify="right", width=9)
    table.add_column("Cost", justify="right", width=8)
    table.add_column("Profit%", justify="right", width=9)
    table.add_column("Conf", width=7)
    table.add_column("Source", width=7)

    for opp in opportunities[:max_display]:
        profit_pct = opp["profit_pct"]
        opp_type = opp["opportunity_type"]
        confidence = opp["confidence"]

        # Color profit based on size
        if profit_pct >= 3.0:
            profit_str = Text(f"{profit_pct:.2f}%", style="bold green")
        elif profit_pct >= 1.5:
            profit_str = Text(f"{profit_pct:.2f}%", style="green")
        else:
            profit_str = Text(f"{profit_pct:.2f}%", style="yellow")

        # Color type
        if opp_type == "UNDERPRICED":
            type_str = Text("UNDERPRICED", style="green")
        else:
            type_str = Text("OVERPRICED", style="red")

        # Color confidence
        if confidence == "HIGH":
            conf_str = Text("HIGH", style="bold green")
        elif confidence == "MEDIUM":
            conf_str = Text("MED", style="yellow")
        else:
            conf_str = Text("LOW", style="dim red")

        # Source indicator
        source = opp.get("price_source", "?")
        source_str = Text("CLOB", style="green") if source == "clob" else Text("GAMMA", style="dim yellow")

        table.add_row(
            truncate(opp["title"], 38),
            type_str,
            f"{opp['yes_bid']:.3f}",
            f"{opp['yes_ask']:.3f}",
            f"{opp['no_bid']:.3f}",
            f"{opp['no_ask']:.3f}",
            f"{opp['total_cost']:.3f}",
            profit_str,
            conf_str,
            source_str,
        )

    console.print(table)

    # Print warnings for top opportunity
    if opportunities:
        top = opportunities[0]
        if top.get("warnings"):
            console.print(
                f"[dim]⚠ Top opportunity warnings: {', '.join(top['warnings'])}[/dim]"
            )


def print_market_summary(markets: list[dict]):
    """Print a compact summary table of all scanned markets."""
    if not markets:
        return

    table = Table(
        title=f"Scanned Markets ({len(markets)})",
        box=box.SIMPLE,
        show_header=True,
        header_style="bold dim",
        expand=True,
    )

    table.add_column("Market", max_width=50)
    table.add_column("Liquidity", justify="right", width=12)
    table.add_column("YES", justify="right", width=8)
    table.add_column("NO", justify="right", width=8)
    table.add_column("Sum", justify="right", width=8)
    table.add_column("Src", width=6)

    for m in markets:
        yes_ask = m.get("yes_ask", 0) or 0
        no_ask = m.get("no_ask", 0) or 0
        total = yes_ask + no_ask

        # Flag sum anomalies
        if total < 0.98:
            sum_str = Text(f"{total:.3f}", style="green")
        elif total > 1.02:
            sum_str = Text(f"{total:.3f}", style="red")
        else:
            sum_str = Text(f"{total:.3f}", style="dim")

        src = m.get("price_source", "?")

        table.add_row(
            truncate(m.get("question", "?"), 48),
            f"${m.get('liquidity', 0):,.0f}",
            f"{yes_ask:.3f}",
            f"{no_ask:.3f}",
            sum_str,
            "clob" if src == "clob" else "γapi",
        )

    console.print(table)


def print_paper_trades(trades: list[dict], balance: float):
    """Print paper trading log."""
    if not trades:
        return

    console.print(
        Panel(
            f"[bold]Paper Balance: ${balance:,.2f}[/bold]\n"
            f"Total paper trades: {len(trades)}",
            title="Paper Trader",
            border_style="yellow",
        )
    )

    # Show last 5 trades
    recent = trades[-5:]
    for t in recent:
        console.print(
            f"  [dim]{t['timestamp']}[/dim] "
            f"[yellow]{t['action']}[/yellow] "
            f"{truncate(t['market'], 35)} "
            f"→ ${t['cost']:.2f} cost, "
            f"[green]${t['expected_profit']:.2f} expected profit[/green]"
        )


def print_tournament_opportunities(opportunities: list[dict], max_display: int = 15):
    """
    Print tournament mispricing opportunities.

    Shows each event group with sum deviation from 1.0,
    plus top outlier markets within each group.
    """
    if not opportunities:
        console.print(
            Panel(
                "No tournament mispricing found above threshold.",
                border_style="dim",
                title="Tournament Scanner",
            )
        )
        return

    # ── Summary table: one row per event group ──────────────────────────────────
    table = Table(
        title=f"Tournament Mispricing ({len(opportunities)} groups)",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
        expand=True,
    )

    table.add_column("Event / Tournament", max_width=38)
    table.add_column("Mkts", justify="right", width=5)
    table.add_column("Sum Mid", justify="right", width=9)
    table.add_column("Sum Ask", justify="right", width=9)
    table.add_column("Buy-All Profit", justify="right", width=14)
    table.add_column("Vig", justify="right", width=7)
    table.add_column("Liquidity", justify="right", width=12)
    table.add_column("Type", width=14)

    for opp in opportunities[:max_display]:
        opp_type = opp["opportunity_type"]
        buy_pct = opp["buy_all_profit_pct"]
        vig = opp["vig_pct"]

        # Color buy-all profit
        if buy_pct > 0:
            profit_str = Text(f"+{buy_pct:.2f}%", style="bold green")
        else:
            profit_str = Text(f"{buy_pct:.2f}%", style="dim")

        # Color vig
        if vig > 5:
            vig_str = Text(f"{vig:.1f}%", style="bold red")
        elif vig > 2:
            vig_str = Text(f"{vig:.1f}%", style="yellow")
        else:
            vig_str = Text(f"{vig:.1f}%", style="dim")

        # Color type
        type_colors = {
            "BUY_ALL": "bold green",
            "BUY_ALL_RISKY": "yellow",
            "HIGH_VIG": "bold red",
            "ELEVATED_VIG": "yellow",
            "NORMAL_VIG": "dim",
        }
        type_str = Text(opp_type, style=type_colors.get(opp_type, "white"))

        table.add_row(
            truncate(opp["event_title"], 36),
            str(opp["market_count"]),
            f"{opp['sum_yes_mid']:.4f}",
            f"{opp['sum_yes_ask']:.4f}",
            profit_str,
            vig_str,
            f"${opp['total_liquidity']:,.0f}",
            type_str,
        )

    console.print(table)

    # ── Detail view: top 3 groups with outlier markets ──────────────────────────
    console.print("\n[bold cyan]Top Group Details[/bold cyan]")

    for opp in opportunities[:3]:
        _print_tournament_detail(opp)


def _print_tournament_detail(opp: dict):
    """Print detailed breakdown for one tournament group."""
    buy_pct = opp["buy_all_profit_pct"]
    vig = opp["vig_pct"]

    if buy_pct > 0:
        header_style = "green"
        header_icon = "🟢"
    elif vig > 5:
        header_style = "red"
        header_icon = "🔴"
    else:
        header_style = "yellow"
        header_icon = "🟡"

    title = f"{header_icon} {opp['event_title']}"

    # Build detail text
    lines = []
    lines.append(
        f"Markets: {opp['market_count']}  |  "
        f"Sum-Mid: {opp['sum_yes_mid']:.4f}  |  "
        f"Sum-Ask: {opp['sum_yes_ask']:.4f}  |  "
        f"Vig: {vig:.2f}%"
    )

    if buy_pct > 0 and not opp.get("warnings"):
        lines.append(
            f"[bold green]BUY ALL OUTCOMES → est. profit {buy_pct:.3f}% per dollar invested[/bold green]"
        )
    elif buy_pct > 0 and opp.get("warnings"):
        lines.append(
            f"[yellow]BUY ALL (RISKY) → apparent profit {buy_pct:.3f}% — see warnings below[/yellow]"
        )

    field_prob = opp.get("field_probability", 0)
    if field_prob > 0.01:
        lines.append(
            f"[dim]Field risk: {field_prob*100:.1f}% implied prob of unlisted winner[/dim]"
        )

    for w in opp.get("warnings", []):
        lines.append(f"[bold yellow]⚠ {w}[/bold yellow]")

    # Show top outcomes
    lines.append("\n[bold]Outcomes (favorites first):[/bold]")
    for m in opp["markets"][:8]:
        mid = m["yes_mid"]
        ask = m["yes_ask"]
        bid = m["yes_bid"]
        q = truncate(m["question"], 50)
        lines.append(
            f"  {mid*100:5.1f}% mid  "
            f"(bid {bid:.3f} / ask {ask:.3f})  "
            f"{q}"
        )
    if len(opp["markets"]) > 8:
        lines.append(f"  ... +{len(opp['markets']) - 8} more outcomes")

    # Show outliers
    if opp.get("outliers"):
        lines.append("\n[bold]Most mispriced (vs group-rescaled fair price):[/bold]")
        for out in opp["outliers"][:3]:
            direction = "↑ OVER" if out["direction"] == "OVER" else "↓ UNDER"
            color = "red" if out["direction"] == "OVER" else "green"
            lines.append(
                f"  [{color}]{direction} {abs(out['deviation_pct']):.2f}%[/{color}]  "
                f"mid={out['yes_mid']*100:.1f}%  fair={out['fair_price']*100:.1f}%  "
                f"{truncate(out['question'], 40)}"
            )

    console.print(
        Panel(
            "\n".join(lines),
            title=title,
            border_style=header_style,
            expand=True,
        )
    )


def print_error(message: str):
    """Print error message."""
    console.print(f"[bold red]ERROR:[/bold red] {message}")


def print_warning(message: str):
    """Print warning message."""
    console.print(f"[yellow]WARNING:[/yellow] {message}")


def print_info(message: str):
    """Print info message."""
    console.print(f"[dim]{message}[/dim]")


def clear():
    """Clear terminal."""
    console.clear()
