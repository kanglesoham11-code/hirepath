"""
seed.py — Initialize HIREPATH with roles only.
NO hardcoded candidate data — all candidates are sourced LIVE via SCOUT agent.
Run: python seed.py
"""
import asyncio
from datetime import datetime
from database import init_db, AsyncSessionLocal, Role, Candidate, CandidateStage, RoleStatus
from utils.logger import log_event

# Roles define what we're hiring for — these are NOT hardcoded candidates
ROLES = [
    {
        "title": "Senior Backend Engineer",
        "description": "We're building the next generation of our data platform based in Pune, Maharashtra. You'll own the backend architecture, design high-throughput APIs, and mentor junior engineers. The team works on real-time event processing, serving 50M+ API calls/day. Location: Maharashtra, India.",
        "requirements": "Python, FastAPI, PostgreSQL, Redis, Docker, 4+ years experience, experience with async systems, CI/CD pipelines, system design. Candidates must be based in or willing to relocate to Maharashtra.",
        "status": RoleStatus.ACTIVE,
    },
    {
        "title": "ML Engineer — LLM Platform",
        "description": "Join our AI team in Mumbai, Maharashtra to build and deploy large language model pipelines. You'll work on fine-tuning, RAG systems, and production inference infrastructure. We process 10M+ documents daily through our ML pipeline. Office: Mumbai, Maharashtra.",
        "requirements": "Python, PyTorch, LangChain, HuggingFace, RAG, vector databases, 3+ years ML experience, production deployment experience. Based in Maharashtra or remote India.",
        "status": RoleStatus.ACTIVE,
    },
    {
        "title": "Frontend Engineer — React",
        "description": "Build beautiful, fast, accessible interfaces for our B2B SaaS product from our Pune office. You'll work closely with design and product to ship pixel-perfect features used by 500+ enterprise customers. Location: Pune, Maharashtra.",
        "requirements": "React, TypeScript, Tailwind CSS, REST/GraphQL, performance optimization, 3+ years, component architecture. Maharashtra-based candidates preferred.",
        "status": RoleStatus.ACTIVE,
    },
]


async def seed():
    print("[*] Initializing HIREPATH database...")
    await init_db()

    async with AsyncSessionLocal() as session:
        # Check if already seeded
        from sqlalchemy import select, func
        result = await session.execute(select(func.count()).select_from(Role))
        count = result.scalar()
        if count > 0:
            print(f"Database already has {count} roles. Skipping seed.")
            print("To reseed: delete hirepath.db and run again.")
            return

    role_ids = []
    async with AsyncSessionLocal() as session:
        for r in ROLES:
            role = Role(**r)
            session.add(role)
        await session.flush()
        await session.commit()

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            __import__("sqlalchemy").select(Role).order_by(Role.id)
        )
        roles = result.scalars().all()
        role_ids = [r.id for r in roles]
        print(f"Created {len(role_ids)} roles: {[r.title for r in roles]}")

    print(f"\n[OK] Seed complete! Roles created -- NO hardcoded candidates.")
    print(f"\n[SCOUT] All candidates will be sourced LIVE via the SCOUT agent.")
    print(f"[LOCATION] Filter: Maharashtra, India")
    print(f"\nDemo flow:")
    print(f"  1. Select a role (e.g., 'Senior Backend Engineer')")
    print(f"  2. Click SCOUT -> Sources LIVE candidates from GitHub/StackOverflow in Maharashtra")
    print(f"  3. Click SCREEN All -> AI evaluates each candidate's profile in real-time")
    print(f"  4. Click 'Engage Top' -> Sends personalized outreach")
    print(f"  5. Click TRACK -> See pipeline health analytics")

if __name__ == "__main__":
    asyncio.run(seed())
