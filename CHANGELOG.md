# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Added
- GitHub Actions CI workflow (typecheck + lint + build)
- `/ready` endpoint for deployment health probes (DB connectivity check)
- Security headers in Next.js (X-Frame-Options, CSP, HSTS, etc.)
- Global and dashboard-level React error boundaries
- `npm run typecheck` script
- Alembic migration for waitlist_entries, contact_messages, reset token columns
- `PROJECT_STATUS.md` and `CONTRIBUTING.md`
- `Procfile` for Railway/Render deployment
- Updated `.env.example` with all current vars (SMTP, FRONTEND_URL, ENV, etc.)

---

## [0.3.0] — 2026-05-28

### Added
- Rate limiting (slowapi): auth endpoints 20/hour, public endpoints 3–5/hour
- Change password endpoint and settings UI
- Delete account (GDPR) — requires email re-entry to confirm
- Plan enforcement in paper trading: free (3 pos / $100), pro (10 / $500), premium (20 / $1000)
- `SECRET_KEY` startup validator (fails if default value used in production)

---

## [0.2.0] — 2026-05-28

### Added
- Waitlist signup form + backend endpoint (POST /api/v1/waitlist)
- Contact form + backend endpoint (POST /api/v1/contact)
- Forgot password / reset password flow (email or dev token)
- Next.js API route proxies for waitlist and contact
- WaitlistEntry + ContactMessage DB models
- SMTP email utility (console fallback in dev)

---

## [0.1.0] — 2026-05-27

### Added
- Full SaaS landing page: Hero, DashboardPreview (demo data), Features, HowItWorks, Pricing, FAQ, WaitlistCTA, Footer
- Cookie consent banner (GDPR, localStorage-backed)
- 8 legal pages: privacy, terms, cookies, disclaimer, accessibility, refund-policy, security, contact
- Marketing layout for /pricing + legal pages

---

## [0.0.3] — 2026-05-27

### Added
- Manual paper trading from opportunity list (TradeModal)
- Close open position from trades page (CloseModal with auto exit price)
- Market detail page with bid/mid/ask price history chart
- Alerts configuration page (Discord/Slack webhook status + test)
- Real-time scanner polling via Zustand (10s interval, refreshKey increments on new scan)
- Auth hydration fix (isMounted pattern in AuthGuard)

---

## [0.0.2] — 2026-05-27

### Added
- FastAPI backend: auth (JWT/bcrypt), opportunities, paper trades, portfolio, alerts, markets
- SQLAlchemy ORM with SQLite/PostgreSQL support
- Alembic initial migration
- Next.js frontend: dashboard, opportunities, trades, alerts, settings pages
- User authentication (register, login, JWT)
- Plan-based access control (free/pro/premium) in opportunities API

---

## [0.0.1] — 2026-05-26

### Added
- Async Polymarket scanner (GAMMA + CLOB API)
- Opportunity detection: VALUE, SPREAD, HIGH_VIG, TOURNAMENT_ARB
- Kalshi + PredictIt cross-platform value comparison
- Paper trading engine (slippage, fees, P&L tracking)
- Discord + Slack alert webhooks
- Streamlit dashboard (legacy, replaced by React)
- structlog + rotating file logger
