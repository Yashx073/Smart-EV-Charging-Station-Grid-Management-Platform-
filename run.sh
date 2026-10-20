#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  echo ""
  echo "==> Stopping services..."
  if [ -n "$BACKEND_PID" ]; then kill "$BACKEND_PID" 2>/dev/null || true; fi
  if [ -n "$FRONTEND_PID" ]; then kill "$FRONTEND_PID" 2>/dev/null || true; fi
  wait 2>/dev/null || true
  echo "==> MongoDB data volume is preserved. To remove MongoDB too: docker compose down -v"
}
trap cleanup EXIT INT TERM

echo "==> Starting MongoDB (data persists in named volume smart_ev_mongodb_data)..."
docker compose up -d mongodb

echo "==> Waiting for MongoDB to be healthy..."
for i in $(seq 1 40); do
  status=$(docker inspect --format='{{.State.Health.Status}}' smart-ev-mongodb 2>/dev/null || echo "starting")
  if [ "$status" = "healthy" ]; then
    echo "==> MongoDB is healthy."
    break
  fi
  if [ "$i" -eq 40 ]; then
    echo "==> MongoDB did not become healthy in time." >&2
    exit 1
  fi
  sleep 2
done

echo "==> Setting up Python virtual environment (.venv)..."
if [ ! -d "$BACKEND_DIR/.venv" ]; then
  python3 -m venv "$BACKEND_DIR/.venv"
fi
"$BACKEND_DIR/.venv/bin/pip" install --upgrade pip -q
"$BACKEND_DIR/.venv/bin/pip" install -r "$BACKEND_DIR/requirements.txt"

echo "==> Seeding database with sample data (idempotent)..."
if [ -f "$BACKEND_DIR/.env" ]; then
  set -a; . "$BACKEND_DIR/.env"; set +a
fi
"$BACKEND_DIR/.venv/bin/python" "$ROOT_DIR/scripts/seed_database.py"

echo "==> Starting FastAPI backend on http://localhost:8000"
cd "$BACKEND_DIR"
"$BACKEND_DIR/.venv/bin/uvicorn" app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

echo "==> Installing frontend dependencies..."
cd "$FRONTEND_DIR"
npm install --no-audit --no-fund >/dev/null 2>&1 || npm install

echo "==> Starting Vite frontend on http://localhost:5173"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "=============================================="
echo " Smart EV Charging is running."
echo " Backend API : http://localhost:8000"
echo " API docs    : http://localhost:8000/docs"
echo " Frontend    : http://localhost:5173"
echo " MongoDB     : localhost:27017"
echo "=============================================="
echo "==> Press Ctrl+C to stop all services."
wait
