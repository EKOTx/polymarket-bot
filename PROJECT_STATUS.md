# Project Status

Last updated: May 2026

## What works on localhost

| Feature | Status | Notes |
|---------|--------|-------|
| Polymarket scanner | ✅ Working | Scans every 30s, stores to SQLite |
| Opportunity detection | ✅ Working | VALUE, SPREAD, HIGH_VIG, TOURNAMENT_ARB signal types |
| External odds comparison | ✅ Working | Kalshi + PredictIt cross-market signals |
| Dashboard (React) | ✅ Working | Real-time via 10s polling |
| Paper trading | ✅ Working | Plan-gated limits, slippage + fee simulation |
| Paper trade close | ✅ Working | Auto-price from latest snapshot or manual override |
| Portfolio tracking | ✅ Working | Balance, PnL, win rate, history chart |
| User auth | ✅ Working | JWT, register, login, change/reset password, delete account |
| Alert webhooks | ✅ Working | Discord + Slack on new opportunities |
| Market detail view | ✅ Working | Price history chart, recent signals, open positions |
| Landing page | ✅ Working | Hero, features, pricing, waitlist, FAQ, cookie banner |
| 8 legal pages | ✅ Draft | Privacy, terms, cookies, disclaimer, etc. — need legal review |
| Waitlist + contact forms | ✅ Working | DB-backed, email notifications |
| Rate limiting | ✅ Working | slowapi on auth + public endpoints |
| Settings page | ✅ Working | Profile, change password, plan info, delete account |
| Security headers | ✅ Working | X-Frame-Options, CSP, HSTS, etc. via next.config.ts |
| Error boundaries | ✅ Working | Global + dashboard-level error pages |

## What is NOT ready for production

| Item | Blocker | Priority |
|------|---------|----------|
| Real trading | Disabled by hard guard — `ENABLE_REAL_TRADING=false` | N/A (intentional) |
| Stripe billing | Keys not configured, no webhook handler wired | P1 |
| Email sending | SMTP not configured (console-only in dev) | P1 |
| Email verification | `is_verified` field exists, flow not built | P1 |
| Test suite | No pytest or Jest tests | P1 |
| Response caching | Scanner results hit DB on every request | P1 |
| PostgreSQL | Schema works in theory, needs real migration run | P0 before prod |
| Secret key | Must change `SECRET_KEY` from default before deploying | P0 before prod |
| Legal review | All legal pages are drafts, not reviewed by lawyer | P0 before public |
| Admin panel | No way to manage users, view waitlist, or read contact messages | P2 |
| Sentry / error tracking | TODO comments in error boundaries | P2 |

## How to run locally

See README.md for full instructions.

```bash
# Backend
source .venv/bin/activate
uvicorn backend.app.main:app --reload --port 8000

# Scanner (separate terminal)
python -m backend.scanner

# Frontend
cd frontend && npm run dev
```
