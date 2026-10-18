#!/bin/bash
# HIREPATH Quick Start Script
set -e

echo "[*] HIREPATH -- Starting up..."

# Check Python
python3 --version || { echo "Python 3 required"; exit 1; }

# Setup virtualenv
if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv venv
fi

source venv/bin/activate

echo "Installing dependencies..."
pip install -q -r requirements.txt

# Check for .env
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo ""
  echo "WARNING: Created .env from template."
  echo "   Please add your GROQ_API_KEY and GITHUB_TOKEN to backend/.env before continuing."
  echo "   GROQ_API_KEY: Get a free key at https://console.groq.com"
  echo "   GITHUB_TOKEN: Create at https://github.com/settings/tokens"
  echo ""
  read -p "Press Enter once you've added your API keys..."
fi

require_env_value() {
  local key="$1"
  local value
  value=$(grep -E "^${key}=.+" .env | tail -n 1 | cut -d= -f2- || true)
  if [ -z "$value" ]; then
    echo "[FAIL] ${key} must be set in backend/.env before starting HIREPATH."
    exit 1
  fi
}

# Live sourcing, AI screening, and authenticated write routes each need these.
require_env_value "GROQ_API_KEY"
require_env_value "GITHUB_TOKEN"
require_env_value "API_SECRET_KEY"

# Fix #15: Only check Postgres when the DATABASE_URL actually points to Postgres
DB_URL=$(grep -E "^DATABASE_URL=" .env | cut -d= -f2-)
if echo "$DB_URL" | grep -qi "postgres"; then
  echo "Checking PostgreSQL connection..."
  # asyncpg expects a PostgreSQL URL, not SQLAlchemy's postgresql+asyncpg URL.
  HIREPATH_POSTGRES_URL="${DB_URL/postgresql+asyncpg:/postgresql:}" python3 - <<'PY'
import asyncio
import os
import asyncpg

async def check():
    try:
        conn = await asyncpg.connect(os.environ["HIREPATH_POSTGRES_URL"])
        await conn.close()
        print("[OK] Database connected")
    except Exception as exc:
        print(f"[FAIL] Database error: {exc}")
        print("  Start PostgreSQL with: docker compose up -d db")
        raise SystemExit(1)

asyncio.run(check())
PY
else
  echo "[OK] Using SQLite (default). No Postgres check needed."
fi

echo "Applying database migrations..."
alembic upgrade head

echo "Seeding role data..."
python3 seed.py

echo ""
echo "[*] Starting HIREPATH backend on http://localhost:8000"
echo "   API docs: http://localhost:8000/docs"
echo "   Open frontend/index.html in your browser"
echo ""

python3 main.py
