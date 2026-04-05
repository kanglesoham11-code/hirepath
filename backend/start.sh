#!/bin/bash
# HIREPATH Quick Start Script
set -e

echo "⬡ HIREPATH — Starting up..."

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
  echo "⚠️  Created .env from template."
  echo "   Please add your GROQ_API_KEY to backend/.env before continuing."
  echo "   Get a free key at: https://console.groq.com"
  echo ""
  read -p "Press Enter once you've added your API key..."
fi

# Check postgres
echo "Checking database connection..."
python3 -c "
import asyncio, asyncpg
async def check():
    try:
        conn = await asyncpg.connect('postgresql://hirepath:hirepath@localhost:5432/hirepath')
        await conn.close()
        print('✓ Database connected')
    except Exception as e:
        print(f'✗ Database error: {e}')
        print('  Start PostgreSQL with: docker run -d --name hirepath-db -e POSTGRES_USER=hirepath -e POSTGRES_PASSWORD=hirepath -e POSTGRES_DB=hirepath -p 5432:5432 postgres:16-alpine')
        exit(1)
asyncio.run(check())
"

echo "Seeding demo data..."
python3 seed.py

echo ""
echo "🚀 Starting HIREPATH backend on http://localhost:8000"
echo "   API docs: http://localhost:8000/docs"
echo "   Open frontend/index.html in your browser"
echo ""

python3 main.py
