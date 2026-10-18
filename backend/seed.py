"""Initialize the HirePath database without inserting sample data.

Roles must come from a recruiter and candidates must enter only through the
live SCOUT flow. Keeping this command empty prevents demonstration records
from being mistaken for real hiring data.
"""
import asyncio

from database import init_db


async def seed() -> None:
    print("[*] Initializing HirePath database schema...")
    await init_db()
    print("[OK] Schema ready. No sample roles or candidates were created.")
    print("Create an actual role in the dashboard, then run SCOUT to retrieve public profiles with evidence links.")


if __name__ == "__main__":
    asyncio.run(seed())
