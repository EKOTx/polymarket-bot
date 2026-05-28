# Procfile — for Railway, Render, Heroku, or any Procfile-based host
#
# Two processes:
#   web    → FastAPI REST API (receives HTTP traffic)
#   worker → Background scanner loop (writes to DB, no HTTP traffic)
#
# On Railway/Render: deploy this repo, set start command to one of the lines below.
# The platform assigns $PORT automatically.

web: uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}
worker: python -m backend.scanner
