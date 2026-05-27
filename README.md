# Polymarket Quant Trading System

Professional-grade Polymarket scanner and paper trading framework.

> ⚠️ **Paper trading only by default. No real money involved.**
> Prediction markets carry real financial risk. Never risk more than you can afford to lose.

---

## Architecture

```
scanner.py          ← async scanner loop (writes to SQLite)
dashboard/app.py    ← Streamlit dashboard (reads from SQLite)
app.py              ← FastAPI REST API (optional)

scanners/
  polymarket_client.py    ← async httpx client, paginated + CLOB order books
  event_grouper.py        ← tournament group analysis, vig detection
  opportunity_detector.py ← spread, value, tournament arb detection

strategies/
  base.py           ← abstract Strategy class
  registry.py       ← build_registry(), run_all_strategies() dispatcher
  value.py          ← cross-platform VALUE (Kalshi/PredictIt fair prob vs PM ask)
  momentum.py       ← price velocity detection (linear regression on snapshots)
  spread_maker.py   ← market maker ranking (spread × depth × liquidity)

integrations/
  kalshi.py         ← Kalshi async client (cursor pagination, 2600+ markets)
  predictit.py      ← PredictIt async client (281 markets → 920 contracts)
  normalizer.py     ← ExternalMarketOdds, devig_group, load_all_external
  matcher.py        ← fuzzy title matching (SequenceMatcher + Jaccard token overlap)

traders/
  paper_trader.py   ← simulated fills, portfolio tracking, kill switch

database/
  models.py              ← SQLAlchemy ORM (Market, Snapshot, Opportunity, Trade)
  db.py                  ← SQLite engine, session factory

models/
  market.py              ← Pydantic MarketData, OrderBook, TournamentGroup
  opportunity.py         ← Pydantic Opportunity, OpportunityType

utils/
  math_utils.py          ← vig, devig, kelly, edge%, slippage, confidence
  logging.py             ← structlog + rich console + rotating file
```

## Quick Start

### 1. Setup

```bash
cd polymarket-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### 2. Start Scanner

```bash
# Terminal 1
python scanner.py
```

Scanner runs every 30 seconds (configurable). Fetches 500 markets, enriches all with CLOB order books, detects opportunities, saves to `data/polymarket.db`.

### 3. Launch Dashboard

```bash
# Terminal 2
streamlit run dashboard/app.py
```

Opens at **http://localhost:8501**

Dashboard pages:
- **Dashboard** — live KPIs, opportunity table, scanner health, portfolio PnL
- **Opportunities** — full filterable table with edge %, confidence, vig
- **Tournament Analysis** — vig by event, buy-all arb detection
- **Paper Trades** — open/closed positions, PnL chart, strategy breakdown
- **Market Analysis** — spread rankings, liquidity, price history charts
- **Logs** — live log viewer with level filtering
- **Settings** — config display (no secrets shown)

---

## Configuration (.env)

| Variable | Default | Description |
|---|---|---|
| `ENABLE_REAL_TRADING` | `false` | ⛔ Never change without full implementation |
| `DRY_RUN` | `true` | Paper mode toggle |
| `SCAN_INTERVAL_SECONDS` | `30` | Seconds between scans |
| `MARKET_LIMIT` | `500` | Markets to fetch per scan |
| `MIN_LIQUIDITY` | `500` | Min USD liquidity for CLOB enrichment |
| `CLOB_CONCURRENCY` | `15` | Max concurrent CLOB API requests |
| `MIN_EDGE_PCT` | `0.5` | Min edge % to surface an opportunity |
| `MIN_VIG_PCT` | `2.0` | Min vig % for tournament group alert |
| `MIN_CONFIDENCE` | `0.4` | Confidence threshold (0-1) |
| `PAPER_STARTING_BALANCE` | `10000` | Paper USD starting balance |
| `PAPER_MAX_POSITION_SIZE` | `500` | Max USD per paper trade |
| `PAPER_MAX_DAILY_LOSS` | `1000` | Daily loss kill switch |

---

## Opportunity Types

| Type | Meaning | Action |
|---|---|---|
| `TOURNAMENT_ARB` | sum_ask < 1.0, no warnings | Buy all outcomes for guaranteed profit |
| `TOURNAMENT_ARB_RISKY` | sum_ask < 1.0, has warnings | Apparent arb but field risk or cumulative |
| `HIGH_VIG` | Tournament vig > 5% | Expensive market; watch for value opportunities |
| `ELEVATED_VIG` | Tournament vig 2-5% | Moderately expensive market |
| `VALUE` | PM price < external fair value | Buy underpriced outcome (Phase 2) |
| `SPREAD` | Wide bid-ask spread | Potential market maker opportunity |

---

## Scanner Metrics

Each scan outputs:
- **Markets fetched**: from Gamma API (paginated)
- **CLOB enriched**: markets with real order book bid/ask
- **Groups analyzed**: tournament event groups
- **Opportunities**: detected signals saved to DB
- **Duration**: typically 7-15 seconds for 500 markets

---

## Data Model

```
SQLite: data/polymarket.db

markets          — market metadata, updated each scan
price_snapshots  — bid/ask/mid/spread per outcome per scan (time series)
opportunities    — detected signals, one row per opportunity per scan
paper_trades     — simulated trades with PnL tracking
portfolio        — portfolio state snapshots (balance, PnL)
scan_runs        — scan metadata (timing, error tracking)
```

---

## Roadmap

- [x] Phase 1: Core scanner + dashboard
- [x] Phase 2: External odds (Kalshi 2600+ markets, PredictIt 920 contracts)
- [x] Phase 3: Strategy engine (cross-platform value, momentum, spread-maker)
- [ ] Phase 4: Enhanced paper trading (mark-to-market, proper PnL)
- [ ] Phase 5: FastAPI REST layer for external consumption
- [ ] Phase 6: Real trading execution (when explicitly enabled)

---

## Safety

- `ENABLE_REAL_TRADING=false` by default (hardcoded check in paper_trader.py)
- `place_order()` raises `NotImplementedError` until implemented
- Private keys never logged (log sanitization in utils/logging.py)
- Daily loss kill switch stops paper trading when threshold hit
- `.env` in `.gitignore` — secrets never committed
