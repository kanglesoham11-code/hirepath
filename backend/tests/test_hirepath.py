"""
Unit and integration tests for HirePath (Fix #25).
Covers:
1. Location matching and word boundaries (Fix #11)
2. Keyword extraction without substring false positives (Fix #12)
3. SCOUT heuristic scoring and rubric clamping (Fix #19)
4. Duplicate candidate detection logic (Fix #8)
5. COORD slot selection in IST business hours (Fix #5)
6. TRACK empty job handling (Fix #13)
"""
import os
import sys
from datetime import datetime, timezone

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from agents.scout import (
    _is_maharashtra_location,
    _extract_keywords,
    compute_quick_heuristic_score,
)
from agents.coord import find_next_slot, IST


class TestScoutLocationMatching:
    """Fix #11: Location filter must match whole words and exclude loose 'india'."""

    def test_valid_maharashtra_locations(self):
        valid = [
            "Mumbai, Maharashtra",
            "Pune, India",
            "Nagpur",
            "Nashik, Maharashtra, India",
            "Thane West",
            "Navi Mumbai",
            "Aurangabad, India",
            "Kolhapur",
        ]
        for loc in valid:
            assert _is_maharashtra_location(loc) is True, f"Expected {loc} to match"

    def test_invalid_locations_and_false_positives(self):
        invalid = [
            "Indianapolis, Indiana",
            "Indiana, USA",
            "London, UK",
            "San Francisco, CA",
            "New Delhi, India",
            "Bangalore, Karnataka",
            "Hyderabad, Telangana",
            "India",  # Fix #11: 'india' alone is dropped from Maharashtra match list
            "",
            None,
        ]
        for loc in invalid:
            assert _is_maharashtra_location(loc) is False, f"Expected {loc} NOT to match"


class TestKeywordExtraction:
    """Fix #12: Keyword matching must use word boundaries to avoid substring false positives."""

    def test_substring_false_positives_prevented(self):
        # 'storage' should NOT match 'rag'
        assert "rag" not in _extract_keywords("We need storage solutions for file uploads.")

        # 'html' should NOT match 'ml'
        assert "ml" not in _extract_keywords("Proficient in html and css styling.")

        # 'trust' should NOT match 'rust'
        assert "rust" not in _extract_keywords("We value trust and communication in our engineering team.")

    def test_exact_keywords_matched(self):
        text = "Looking for a Senior Python and FastAPI backend engineer with Docker, Kubernetes, and PostgreSQL experience."
        keywords = _extract_keywords(text)
        assert "python" in keywords
        assert "fastapi" in keywords
        assert "docker" in keywords
        assert "postgresql" in keywords or "postgres" in keywords


class TestScoutScoring:
    """Fix #19: SCOUT heuristic scoring evaluates signals and clamps score 0-100."""

    def test_qualified_candidate_scoring(self):
        candidate = {
            "name": "Aarav Sharma",
            "source": "github_maharashtra",
            "location": "Pune, Maharashtra",
            "bio": "Senior Python and FastAPI developer building scalable microservices.",
            "public_repos": 12,
            "followers": 25,
            "contributions": 150,
            "top_repos": [
                {"name": "fastapi-service", "stars": 35, "language": "Python", "description": "FastAPI async microservice template"},
                {"name": "docker-tools", "stars": 20, "language": "Shell", "description": "Docker automation helpers"},
            ],
            "skills": ["python", "fastapi", "docker"],
        }
        res = compute_quick_heuristic_score(
            candidate,
            role_description="FastAPI Backend Engineer",
            role_requirements="Python, FastAPI, Docker, PostgreSQL",
        )
        assert res["score"] >= 60, f"Expected score >= 60, got {res['score']}"
        assert len(res["strengths"]) > 0
        assert "score" in res
        assert "summary" in res

    def test_unqualified_candidate_scoring(self):
        candidate = {
            "name": "Random User",
            "source": "github_maharashtra",
            "location": "Mumbai",
            "bio": "Beginner programmer learning HTML.",
            "public_repos": 1,
            "followers": 0,
            "top_repos": [],
            "skills": [],
        }
        res = compute_quick_heuristic_score(
            candidate,
            role_description="Senior Golang Distributed Systems",
            role_requirements="Golang, Kubernetes, Raft, Distributed Systems",
        )
        assert res["score"] <= 40, f"Expected low score, got {res['score']}"


class TestCoordSlots:
    """Fix #5: Interview slots must be in IST and within business hours on weekdays."""

    def test_slot_time_and_timezone(self):
        slot = find_next_slot()
        # Verify slot has IST timezone
        assert slot.tzinfo is not None
        # Check weekday is Monday-Friday (0-4)
        assert slot.weekday() < 5, f"Slot day {slot.weekday()} is a weekend"
        # Check the slot fully fits in the 10 AM–5 PM IST business window.
        assert 10 <= slot.hour < 17, f"Slot hour {slot.hour} is outside business hours"
        # Check slot is in the future
        now_ist = datetime.now(IST)
        assert slot > now_ist, "Slot is in the past"


class TestTrackEmptyJobs:
    """Fix #13: TRACK must handle empty roles without crashing or generating false alerts."""

    def test_compute_pipeline_health_empty(self):
        import asyncio

        async def _run():
            from agents.track import compute_pipeline_health
            from database import init_db, AsyncSessionLocal, Role, RoleStatus

            await init_db()
            async with AsyncSessionLocal() as session:
                role = Role(title="Test Empty Role", description="No candidates", requirements="Python", status=RoleStatus.ACTIVE)
                session.add(role)
                await session.commit()
                await session.refresh(role)
                role_id = role.id

            health = await compute_pipeline_health(role_id)
            assert health["total_candidates"] == 0
            assert health["role_id"] == role_id
            assert len(health["stale_candidates"]) == 0
            assert health["health_score"] == 0.0  # 0.0 when no candidates yet

        asyncio.run(_run())


class TestDeduplication:
    """Fix #8: Deduplication must match on github_url, email, or name+source."""

    def test_duplicate_detection(self):
        import asyncio

        async def _run():
            from agents.scout import is_duplicate
            from database import init_db, AsyncSessionLocal, Role, Candidate, CandidateStage, RoleStatus

            await init_db()
            async with AsyncSessionLocal() as session:
                role = Role(title="Dedup Test Role", description="Test", requirements="Test", status=RoleStatus.ACTIVE)
                session.add(role)
                await session.commit()
                await session.refresh(role)
                role_id = role.id

                cand = Candidate(
                    role_id=role_id,
                    name="Siddharth Patil",
                    github_url="https://github.com/spatil-test",
                    email="spatil@example.com",
                    source="github_maharashtra",
                    stage=CandidateStage.SOURCED,
                )
                session.add(cand)
                await session.commit()

            # Duplicate by GitHub URL
            assert await is_duplicate(role_id, "https://github.com/spatil-test", None) is True
            # Duplicate by email
            assert await is_duplicate(role_id, None, "spatil@example.com") is True
            # Duplicate by name + source (Fix #8)
            assert await is_duplicate(role_id, None, None, "Siddharth Patil", "github_maharashtra") is True
            # Not duplicate
            assert await is_duplicate(role_id, "https://github.com/other-user", "other@example.com", "Other User", "github_maharashtra") is False

        asyncio.run(_run())
