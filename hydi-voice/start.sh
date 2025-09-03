#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export PYTHONUNBUFFERED=1
if [ -f .env ]; then
  set -a; source .env; set +a
fi
exec uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload