"""
scanner.py — Main async scanner loop.

Orchestrates:
  1. Fetch markets from Polymarket (paginated)
  2. Enrich with CLOB order books (concurrent)
  3. Group by event
  4. Detect opportunities
  5. Save all data to SQLite
  6. Execute paper trades on high-confidence signals
  7. Sleep and repeat

Run:
    python scanner.py
"""

from __future__ import annotations

import asyncio
import json
import os
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()

# Setup paths before local imports
sys.path.insert(0, str(Path(__file__).parent))

from database.db import init_db, get_session
from database.models import (
    Market as DBMarket,
    PriceSnapshot,
    Opportunity as DBOpportunity,
    ExternalOddsSnapshot,
    ScanRun,
)
from models.market import MarketData
from models.opportunity import Opportunity
from scanners.polymarket_client import fetch_all_markets, enrich_markets_concurrent
from scanners.event_grouper import scan_all_groups
from scanners.opportunity_detector import analyze_spreads, analyze_tournament_vig
from strategies.registry import build_registry, run_all_strategies
from traders.paper_trader import PaperTrader
from utils.logging import setup_logging, get_logger
import integrations.kalshi as kalshi_client
import integrations.predictit as predictit_client
from integrations.normalizer import load_all_external
from integrations.matcher import match_summary

# ── Config ───────────────────────────────────────────────────────────────────

SCAN_INTERVAL = int(os.getenv("SCAN_INTERVAL_SECONDS", "30"))
MARKET_LIMIT = int(os.getenv("MARKET_LIMIT", "500"))
MIN_LIQUIDITY = float(os.getenv("MIN_LIQUIDITY", "500"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "logs/scanner.log")
ENABLE_EXTERNAL_ODDS = os.getenv("ENABLE_EXTERNAL_ODDS", "true").lower() == "true"
# Fetch external odds every N scans (not every scan — Kalshi/PI are slower)
EXTERNAL_ODDS_EVERY_N = int(os.getenv("EXTERNAL_ODDS_EVERY_N", "3"))

setup_logging(LOG_LEVEL, LOG_FILE)
logger = get_logger("scanner")

_shutdown = False


def _handle_signal(sig, frame):
    global _shutdown
    logger.info("shutdown_signal_received", signal=sig)
    _shutdown = True


signal.signal(signal.SIGINT, _handle_signal)
signal.signal(signal.SIGTERM, _handle_signal)


# ── Persistence ───────────────────────────────────────────────────────────────

def save_markets(markets: list[MarketData], scan_id: int) -> None:
    """Upsert markets + price snapshots to DB."""
    with get_session() as session:
        for m in markets:
            # Upsert market record
            db_m = session.get(DBMarket, m.market_id)
            if db_m is None:
                db_m = DBMarket(
                    id=m.market_id,
                    question=m.question,
                    event_title=m.event_title,
                    event_id=m.event_id,
                )
                session.add(db_m)
            db_m.volume = m.volume
            db_m.liquidity = m.liquidity
            db_m.active = True
            db_m.last_updated = datetime.utcnow()

            # Snapshot YES prices
            for outcome, book in [("Yes", m.yes_book), ("No", m.no_book)]:
                if book is None:
                    continue
                snap = PriceSnapshot(
                    market_id=m.market_id,
                    outcome=outcome,
                    token_id=book.token_id,
                    bid=book.best_bid,
                    ask=book.best_ask,
                    mid=book.mid,
                    spread=book.spread,
                    spread_pct=book.spread_pct,
                    bid_depth_usd=book.bid_depth_usd,
                    ask_depth_usd=book.ask_depth_usd,
                    price_source=book.price_source,
                    scan_id=scan_id,
                    timestamp=datetime.utcnow(),
                )
                session.add(snap)

        session.commit()
    logger.debug("markets_saved", count=len(markets))


def save_opportunities(opps: list[Opportunity], scan_id: int) -> None:
    """Save detected opportunities to DB."""
    with get_session() as session:
        for opp in opps:
            db_opp = DBOpportunity(
                scan_id=scan_id,
                opportunity_type=str(opp.opportunity_type),
                event_title=opp.event_title or "",
                market_id=opp.market_id,
                title=opp.title[:250],
                edge_pct=opp.edge_pct,
                confidence=opp.confidence,
                expected_value=opp.expected_value,
                suggested_size_usd=opp.suggested_size_usd,
                yes_bid=opp.yes_bid,
                yes_ask=opp.yes_ask,
                no_bid=opp.no_bid,
                no_ask=opp.no_ask,
                sum_yes_mid=opp.sum_yes_mid,
                vig_pct=opp.vig_pct,
                liquidity=opp.liquidity,
                market_count=opp.market_count,
                warnings=json.dumps(opp.warnings),
                details=json.dumps(opp.details),
                timestamp=datetime.utcnow(),
            )
            session.add(db_opp)
        session.commit()
    logger.debug("opportunities_saved", count=len(opps))


def save_external_odds(odds_list: list, scan_id: int) -> None:
    """Persist external odds snapshots to DB."""
    if not odds_list:
        return
    with get_session() as session:
        for o in odds_list:
            snap = ExternalOddsSnapshot(
                scan_id=scan_id,
                platform=o.platform,
                platform_market_id=o.platform_market_id,
                title=o.title[:300],
                outcome_label=o.outcome_label,
                yes_ask=o.yes_ask,
                yes_bid=o.yes_bid,
                mid=o.mid,
                fair_probability=o.fair_probability,
                volume=o.volume,
                group_id=o.group_id,
                timestamp=datetime.utcnow(),
            )
            session.add(snap)
        session.commit()
    logger.debug("external_odds_saved", count=len(odds_list))


def create_scan_run() -> int:
    """Create a ScanRun record and return its ID."""
    with get_session() as session:
        run = ScanRun(started_at=datetime.utcnow())
        session.add(run)
        session.flush()
        session.refresh(run)
        run_id = run.id
        session.commit()
    return run_id


def finish_scan_run(
    scan_id: int,
    markets_fetched: int,
    markets_priced: int,
    opportunities_found: int,
    duration: float,
    error: str | None = None,
) -> None:
    with get_session() as session:
        run = session.get(ScanRun, scan_id)
        if run:
            run.markets_fetched = markets_fetched
            run.markets_priced = markets_priced
            run.opportunities_found = opportunities_found
            run.duration_seconds = round(duration, 2)
            run.error = error
            run.finished_at = datetime.utcnow()
            session.commit()


# ── Main scan cycle ───────────────────────────────────────────────────────────

async def fetch_external_odds(client: httpx.AsyncClient) -> list:
    """Fetch Kalshi + PredictIt markets and return normalized ExternalMarketOdds list."""
    kalshi_raw, predictit_raw = await asyncio.gather(
        kalshi_client.fetch_all_markets(client),
        predictit_client.fetch_all_markets(client),
        return_exceptions=True,
    )

    if isinstance(kalshi_raw, Exception):
        logger.warning("kalshi_fetch_failed", error=str(kalshi_raw))
        kalshi_raw = []
    if isinstance(predictit_raw, Exception):
        logger.warning("predictit_fetch_failed", error=str(predictit_raw))
        predictit_raw = []

    logger.info(
        "external_fetched",
        kalshi=len(kalshi_raw),
        predictit=len(predictit_raw),
    )
    return load_all_external(kalshi_raw, predictit_raw)


async def run_scan_cycle(
    client: httpx.AsyncClient,
    paper_trader: PaperTrader,
    scan_num: int,
    external_odds: list | None = None,
    strategy_registry: list | None = None,
) -> list:
    """
    Execute one full scan cycle.
    Returns updated external_odds (refreshed every EXTERNAL_ODDS_EVERY_N scans).
    """
    scan_id = create_scan_run()
    t_start = time.perf_counter()
    error_msg = None

    try:
        logger.info("scan_start", scan_num=scan_num, scan_id=scan_id)

        # 1. Fetch markets (gamma prices — fast, all markets)
        all_markets = await fetch_all_markets(client, total_limit=MARKET_LIMIT)
        logger.info("markets_fetched", count=len(all_markets))

        # 2. Group by event FIRST using gamma data (full picture)
        groups = scan_all_groups(all_markets)
        logger.info("groups_analyzed", count=len(groups))

        # 3. Enrich liquid markets with real CLOB order books
        enriched = await enrich_markets_concurrent(
            client, all_markets, min_liquidity=MIN_LIQUIDITY
        )
        logger.info("markets_enriched", clob_count=len(enriched))

        # 4. Save market data (enriched subset)
        save_markets(enriched, scan_id)

        # 5. Fetch external odds (throttled — not every scan)
        if ENABLE_EXTERNAL_ODDS and scan_num % EXTERNAL_ODDS_EVERY_N == 1:
            external_odds = await fetch_external_odds(client)
            save_external_odds(external_odds, scan_id)

        # 6. Run strategy engine
        #    Strategies: cross-platform value, momentum, spread-maker
        #    Plus hard-coded tournament vig/arb from event groups
        with get_session() as session:
            strategy_opps = run_all_strategies(
                markets=enriched,
                groups=groups,
                external_odds=external_odds or [],
                session=session,
                scan_id=scan_id,
                registry=strategy_registry,
            )

        # Tournament vig/arb still via legacy detector (no DB needed)
        vig_opps = analyze_tournament_vig(groups, scan_id)
        spread_opps = analyze_spreads(enriched, scan_id)

        # Merge: strategy engine owns VALUE/MOMENTUM; legacy owns VIG/SPREAD
        from models.opportunity import OpportunityType
        strategy_types = {OpportunityType.VALUE}
        vig_types = {
            OpportunityType.TOURNAMENT_ARB, OpportunityType.TOURNAMENT_ARB_RISKY,
            OpportunityType.HIGH_VIG, OpportunityType.ELEVATED_VIG,
        }

        # Strategy results: filter to VALUE only (spread/spread_maker deduped below)
        value_opps = [o for o in strategy_opps if o.opportunity_type in strategy_types]

        # Merge spread from strategy engine + legacy (strategy engine takes precedence)
        spread_market_ids = {o.market_id for o in strategy_opps
                             if o.opportunity_type == OpportunityType.SPREAD}
        legacy_spread = [o for o in spread_opps if o.market_id not in spread_market_ids]
        final_spread = [o for o in strategy_opps
                        if o.opportunity_type == OpportunityType.SPREAD] + legacy_spread

        opportunities = value_opps + vig_opps + final_spread
        opportunities.sort(key=lambda o: -(o.confidence * o.edge_pct))

        logger.info(
            "opportunities_found",
            count=len(opportunities),
            value=len(value_opps),
            vig=len(vig_opps),
            spread=len(final_spread),
        )

        # 8. Save opportunities
        save_opportunities(opportunities, scan_id)

        # 9. Paper trade actionable signals
        traded = 0
        for opp in opportunities:
            if opp.is_actionable and opp.suggested_size_usd > 0:
                trade = paper_trader.execute(opp)
                if trade:
                    traded += 1
                    if traded >= 3:  # max 3 paper trades per scan
                        break

        duration = time.perf_counter() - t_start

        logger.info(
            "scan_complete",
            scan_num=scan_num,
            duration=round(duration, 1),
            markets=len(enriched),
            opportunities=len(opportunities),
            paper_trades=traded,
        )

        finish_scan_run(scan_id, len(all_markets), len(enriched), len(opportunities), duration)

    except Exception as e:
        duration = time.perf_counter() - t_start
        error_msg = str(e)
        logger.error("scan_error", error=error_msg, scan_num=scan_num)
        finish_scan_run(scan_id, 0, 0, 0, duration, error_msg)

    return external_odds or []


# ── Entry point ───────────────────────────────────────────────────────────────

async def main() -> None:
    """Main scanner loop."""
    logger.info("scanner_starting", interval=SCAN_INTERVAL, limit=MARKET_LIMIT)

    init_db()
    paper_trader = PaperTrader()
    strategy_registry = build_registry()
    logger.info(
        "strategies_loaded",
        strategies=[s.name for s in strategy_registry],
    )
    scan_num = 0

    external_odds: list = []

    async with httpx.AsyncClient(
        headers={"User-Agent": "polymarket-quant-bot/2.0"},
        follow_redirects=True,
    ) as client:
        while not _shutdown:
            scan_num += 1
            external_odds = await run_scan_cycle(
                client, paper_trader, scan_num, external_odds, strategy_registry
            )

            if not _shutdown:
                logger.info("scan_sleeping", seconds=SCAN_INTERVAL)
                # Sleep in 1s chunks to allow clean shutdown
                for _ in range(SCAN_INTERVAL):
                    if _shutdown:
                        break
                    await asyncio.sleep(1)

    stats = paper_trader.get_stats()
    logger.info("scanner_stopped", paper_stats=stats)
    print(f"\n✓ Scanner stopped after {scan_num} scans.")
    print(f"  Paper balance: ${stats.get('balance', 0):,.2f}")
    print(f"  Total trades:  {stats.get('total_trades', 0)}")


if __name__ == "__main__":
    asyncio.run(main())
