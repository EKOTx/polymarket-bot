# Contributing

This is a personal project in active development. Notes for contributors and future-me.

## Prerequisites

- Python 3.11+
- Node.js 20+
- Git

## Local setup

```bash
# 1. Clone
git clone https://github.com/EKOTx/polymarket-bot.git
cd polymarket-bot

# 2. Python environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

# 3. Environment
cp .env.example .env
# Edit .env — at minimum set SECRET_KEY to a random value

# 4. Database (auto-created on first run)
# SQLite DB created at data/polymarket.db automatically

# 5. Frontend
cd frontend
npm install
cd ..
```

## Running locally

```bash
# Terminal 1 — API server
source .venv/bin/activate
uvicorn backend.app.main:app --reload --port 8000

# Terminal 2 — Scanner background worker
source .venv/bin/activate
python -m backend.scanner

# Terminal 3 — Frontend dev server
cd frontend && npm run dev
```

Open http://localhost:3000

## Checks before committing

```bash
# Backend — import check
python -c "from backend.app.main import app; print('OK')"

# Frontend
cd frontend
npm run typecheck   # TypeScript check
npm run lint        # ESLint
npm run build       # Verify production build passes
```

## Database migrations

New column or table? Use Alembic:

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "describe your change"

# Apply
alembic upgrade head

# Rollback one step
alembic downgrade -1
```

Do NOT add new columns by editing `_migrate_sqlite()` in `main.py` — that hack is only
for the one-time column additions that predate the migration. New changes go through Alembic.

## Key constraints

- `ENABLE_REAL_TRADING` must remain `false` by default — there is a validator enforcing this
- Never put secrets in frontend code
- All paper trade routes must filter by `user_id` — no cross-user data leakage
- Legal pages are drafts — do not publish them as final without a legal review

## Branch strategy

- `main` — stable, deployable
- Feature branches: `feat/description`
- Bugfix branches: `fix/description`

## Project structure

```
backend/app/          FastAPI application (routes, models, auth)
backend/scanners/     Polymarket API clients
backend/strategies/   Signal detection strategies
backend/traders/      Paper trading engine
frontend/src/app/     Next.js pages (App Router)
frontend/src/components/  UI components
frontend/src/lib/     API client, auth store, utilities
alembic/versions/     Database migrations
```
