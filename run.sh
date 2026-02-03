#!/usr/bin/env bash
set -euo pipefail
source .venv/bin/activate
export PVAPP_DB_URL=${PVAPP_DB_URL:-sqlite:///./db.sqlite3}
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
