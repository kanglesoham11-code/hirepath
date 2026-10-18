"""Test configuration that keeps all tests away from the application database."""
import asyncio
import os
from pathlib import Path
import sys

import pytest


BACKEND_DIR = Path(__file__).resolve().parents[1]
TEST_DATABASE = BACKEND_DIR / "test_hirepath.db"

# This runs before test modules import config/database. Environment values take
# priority over a developer's backend/.env file.
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DATABASE.as_posix()}"
os.environ["API_SECRET_KEY"] = "test-api-secret"
os.environ["GROQ_API_KEY"] = ""
os.environ["GITHUB_TOKEN"] = ""
sys.path.insert(0, str(BACKEND_DIR))


@pytest.fixture(autouse=True)
def isolated_database():
    """Recreate the schema for each test without touching hirepath.db."""
    from database import Base, engine

    async def reset():
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)
            await connection.run_sync(Base.metadata.create_all)

    asyncio.run(reset())
    yield
    asyncio.run(reset())


def pytest_sessionfinish(session, exitstatus):
    """Dispose the async engine before deleting the isolated SQLite file."""
    try:
        from database import engine

        asyncio.run(engine.dispose())
    finally:
        TEST_DATABASE.unlink(missing_ok=True)
