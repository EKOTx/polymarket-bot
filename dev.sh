#!/usr/bin/env bash
# ── Polymarket Bot — local dev launcher ──────────────────────────────────────
# Usage:
#   ./dev.sh          — start API + frontend
#   ./dev.sh api      — API only
#   ./dev.sh front    — frontend only
#   ./dev.sh scanner  — scanner only
#   ./dev.sh all      — everything (API + frontend + scanner)

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

# Load .env if present
if [[ -f .env ]]; then
  set -a && source .env && set +a
fi

# Create data dir
mkdir -p data logs

MODE="${1:-}"

start_api() {
  echo "▶ Starting FastAPI on :8000"
  uvicorn backend.app.main:app --reload --port 8000 &
  API_PID=$!
  echo "  PID $API_PID"
}

start_frontend() {
  echo "▶ Starting Next.js on :3000"
  cd frontend && npm run dev &
  FRONT_PID=$!
  cd "$ROOT"
  echo "  PID $FRONT_PID"
}

start_scanner() {
  echo "▶ Starting scanner"
  python scanner.py &
  SCAN_PID=$!
  echo "  PID $SCAN_PID"
}

cleanup() {
  echo ""
  echo "Stopping all processes…"
  kill "$API_PID" "$FRONT_PID" "$SCAN_PID" 2>/dev/null || true
}

case "$MODE" in
  api)
    start_api
    wait $API_PID
    ;;
  front|frontend)
    start_frontend
    wait $FRONT_PID
    ;;
  scanner)
    start_scanner
    wait $SCAN_PID
    ;;
  all)
    trap cleanup EXIT INT TERM
    start_api
    start_frontend
    start_scanner
    echo ""
    echo "All services running. Ctrl+C to stop."
    wait
    ;;
  ""|default)
    trap cleanup EXIT INT TERM
    start_api
    start_frontend
    echo ""
    echo "API → http://localhost:8000/docs"
    echo "App → http://localhost:3000"
    echo ""
    echo "Ctrl+C to stop."
    wait
    ;;
esac
