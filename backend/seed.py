"""
seed.py — Populate HIREPATH with realistic demo data for the hackathon demo.
Uses real GitHub profiles sourced from actual open-source contributors.
Run: python seed.py
"""
import asyncio
from datetime import datetime, timedelta
from database import init_db, AsyncSessionLocal, Role, Candidate, CandidateStage, RoleStatus
from utils.logger import log_event

ROLES = [
    {
        "title": "Senior Backend Engineer",
        "description": "We're building the next generation of our data platform. You'll own the backend architecture, design high-throughput APIs, and mentor junior engineers. The team works on real-time event processing, serving 50M+ API calls/day.",
        "requirements": "Python, FastAPI, PostgreSQL, Redis, Docker, 4+ years experience, experience with async systems, CI/CD pipelines, system design",
        "status": RoleStatus.ACTIVE,
    },
    {
        "title": "ML Engineer — LLM Platform",
        "description": "Join our AI team to build and deploy large language model pipelines. You'll work on fine-tuning, RAG systems, and production inference infrastructure. We process 10M+ documents daily through our ML pipeline.",
        "requirements": "Python, PyTorch, LangChain, HuggingFace, RAG, vector databases, 3+ years ML experience, production deployment experience",
        "status": RoleStatus.ACTIVE,
    },
    {
        "title": "Frontend Engineer — React",
        "description": "Build beautiful, fast, accessible interfaces for our B2B SaaS product. You'll work closely with design and product to ship pixel-perfect features used by 500+ enterprise customers.",
        "requirements": "React, TypeScript, Tailwind CSS, REST/GraphQL, performance optimization, 3+ years, component architecture",
        "status": RoleStatus.ACTIVE,
    },
]

# Real GitHub profiles — these are actual open-source contributors
# Emails are left as None where not publicly available (SCOUT will fetch real ones)
CANDIDATES = [
    # Role 1 — Senior Backend Engineer
    {
        "role_idx": 0,
        "name": "Sebastián Ramírez",
        "email": None,
        "github_url": "https://github.com/tiangolo",
        "source": "github_contributor",
        "stage": CandidateStage.SCREENED,
        "score": 95.0,
        "screen_brief": {
            "overall_score": 95,
            "years_experience": 10,
            "top_skills": ["Python", "FastAPI", "Docker", "PostgreSQL", "Async"],
            "skill_gaps": [],
            "strengths": [
                "Creator of FastAPI — the most starred Python web framework on GitHub",
                "Deep expertise in async Python, Pydantic, and OpenAPI standards",
                "Proven track record of building production-grade developer tools",
                "Active maintainer with 60k+ GitHub stars across projects"
            ],
            "concerns": [],
            "red_flags": [],
            "suggested_interview_questions": [
                "How did you approach the async architecture decisions in FastAPI's core?",
                "What trade-offs did you make when designing the dependency injection system?",
                "How do you handle backwards compatibility across major releases?",
                "Describe the most complex performance bottleneck you've solved in FastAPI."
            ],
            "one_line_verdict": "Creator of FastAPI — exceptional fit, world-class backend engineer.",
            "hire_recommendation": "strong_yes"
        }
    },
    {
        "role_idx": 0,
        "name": "Marcelo Trylesinski",
        "email": None,
        "github_url": "https://github.com/Kludex",
        "source": "github_contributor",
        "stage": CandidateStage.SCREENED,
        "score": 82.0,
        "screen_brief": {
            "overall_score": 82,
            "years_experience": 5,
            "top_skills": ["Python", "FastAPI", "Uvicorn", "Starlette", "Docker"],
            "skill_gaps": ["Redis"],
            "strengths": [
                "Core maintainer of Uvicorn — the ASGI server powering FastAPI",
                "500+ contributions to FastAPI ecosystem",
                "Strong async Python and ASGI protocol expertise"
            ],
            "concerns": [
                "Redis experience not evidenced in GitHub profile"
            ],
            "red_flags": [],
            "suggested_interview_questions": [
                "How do you approach ASGI middleware performance optimization?",
                "Describe the most challenging bug you've debugged in Uvicorn.",
                "How would you design a Redis caching layer for high-throughput APIs?",
                "What's your approach to load testing async Python services?"
            ],
            "one_line_verdict": "Uvicorn core maintainer — strong async Python expertise, great fit.",
            "hire_recommendation": "strong_yes"
        }
    },
    {
        "role_idx": 0,
        "name": "Hasan Ramezani",
        "email": None,
        "github_url": "https://github.com/hramezani",
        "source": "github",
        "stage": CandidateStage.SOURCED,
        "score": 68.0
    },
    {
        "role_idx": 0,
        "name": "Amin Alaee",
        "email": None,
        "github_url": "https://github.com/aminalaee",
        "source": "github_contributor",
        "stage": CandidateStage.SOURCED,
        "score": 72.0,
    },

    # Role 2 — ML Engineer
    {
        "role_idx": 1,
        "name": "Harrison Chase",
        "email": None,
        "github_url": "https://github.com/hwchase17",
        "source": "github_contributor",
        "stage": CandidateStage.SCREENED,
        "score": 93.0,
        "screen_brief": {
            "overall_score": 93,
            "years_experience": 6,
            "top_skills": ["Python", "LangChain", "LLM", "RAG", "Vector Databases"],
            "skill_gaps": [],
            "strengths": [
                "Creator of LangChain — the most adopted LLM orchestration framework",
                "Deep expertise in RAG architectures and production LLM deployment",
                "Built and scaled LangChain to 70k+ GitHub stars",
                "Pioneered agent-based LLM architectures"
            ],
            "concerns": [],
            "red_flags": [],
            "suggested_interview_questions": [
                "How did you design LangChain's agent execution model?",
                "What are the key challenges in production RAG system accuracy?",
                "How do you approach LLM evaluation and testing at scale?",
                "Describe the architecture decisions behind LangGraph."
            ],
            "one_line_verdict": "LangChain creator — unmatched LLM expertise, perfect fit.",
            "hire_recommendation": "strong_yes"
        }
    },
    {
        "role_idx": 1,
        "name": "Nils Reimers",
        "email": None,
        "github_url": "https://github.com/nreimers",
        "source": "github",
        "stage": CandidateStage.SOURCED,
        "score": 78.0,
    },
    {
        "role_idx": 1,
        "name": "Niels Bantilan",
        "email": None,
        "github_url": "https://github.com/cosmicBboy",
        "source": "github",
        "stage": CandidateStage.SOURCED,
        "score": 61.0,
    },

    # Role 3 — Frontend Engineer
    {
        "role_idx": 2,
        "name": "Kent C. Dodds",
        "email": None,
        "github_url": "https://github.com/kentcdodds",
        "source": "github",
        "stage": CandidateStage.SCREENED,
        "score": 90.0,
        "screen_brief": {
            "overall_score": 90,
            "years_experience": 10,
            "top_skills": ["React", "TypeScript", "Testing", "JavaScript", "Performance"],
            "skill_gaps": [],
            "strengths": [
                "Creator of Testing Library — industry standard for React testing",
                "Prolific React educator and open-source contributor",
                "Deep expertise in React patterns, hooks, and performance optimization",
                "Built remix.run — production-grade React meta-framework"
            ],
            "concerns": [],
            "red_flags": [],
            "suggested_interview_questions": [
                "How do you approach component design for maintainability at scale?",
                "What testing patterns do you recommend for complex React applications?",
                "How do you handle state management in large enterprise React apps?",
                "Describe your approach to web performance optimization."
            ],
            "one_line_verdict": "Testing Library creator — world-class React expert.",
            "hire_recommendation": "strong_yes"
        }
    },
    {
        "role_idx": 2,
        "name": "Tanner Linsley",
        "email": None,
        "github_url": "https://github.com/tannerlinsley",
        "source": "github_contributor",
        "stage": CandidateStage.SOURCED,
        "score": 85.0,
    },
]

async def seed():
    print("Initializing database...")
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

    base_time = datetime.utcnow() - timedelta(hours=6)
    async with AsyncSessionLocal() as session:
        for i, c_data in enumerate(CANDIDATES):
            role_idx = c_data.pop("role_idx")
            c_data["role_id"] = role_ids[role_idx]
            c_data.setdefault("last_activity_at", base_time + timedelta(hours=i))
            c_data.setdefault("outreach_count", 0)
            c = Candidate(**c_data)
            session.add(c)
        await session.commit()

    print(f"Created {len(CANDIDATES)} candidates across {len(ROLES)} roles.")
    print(f"\n✅ Seed complete! All candidates use real GitHub profiles.")
    print(f"\nDemo flow:")
    print(f"  1. Select 'Senior Backend Engineer'")
    print(f"  2. Click SCOUT to source more real candidates from GitHub")
    print(f"  3. Click SCREEN All to generate AI evaluation briefs")
    print(f"  4. Click 'Engage Top' to send outreach to qualified candidates")
    print(f"  5. Click TRACK to see pipeline health analytics")

if __name__ == "__main__":
    asyncio.run(seed())
