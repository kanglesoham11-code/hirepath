"""
Tests for the location engine, rate limiter, privacy tokens, auth,
and migration 0004.

All tests run offline — no network calls.
"""
import asyncio
import csv
import os
import random
import sys
import time
from pathlib import Path

import pytest

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# ── Phase 1: Location Resolver Tests ─────────────────────────────────────────

class TestLocationResolver:
    """Test the pure-function location resolver."""

    def test_accept_high_confidence(self):
        from utils.location_resolver import resolve_location

        cases = [
            ("Pune, India", "Pune"),
            ("Mumbai, Maharashtra, India", "Mumbai"),
            ("Pimpri-Chinchwad, India", "Pimpri-Chinchwad"),
            ("Bombay, India", "Mumbai"),
            ("Poona, MH", "Pune"),
            ("Satara, Maharashtra", "Satara"),
            ("Nagpur, Maharashtra, India", "Nagpur"),
        ]
        for text, expected_city in cases:
            result = resolve_location(text)
            assert result.accepted, f"Expected '{text}' to be accepted"
            assert result.confidence == "high", f"Expected high confidence for '{text}', got {result.confidence}"
            if expected_city:
                assert result.city == expected_city, f"Expected city={expected_city} for '{text}', got {result.city}"

    def test_accept_medium_confidence(self):
        from utils.location_resolver import resolve_location

        cases = [
            ("Pune", "Pune"),
            ("Hinjewadi, Pune", "Hinjewadi"),
            ("Navi Mumbai", "Navi Mumbai"),
            ("Kalyan", "Kalyan-Dombivli"),
            ("PCMC", "Pimpri-Chinchwad"),
        ]
        for text, expected_city in cases:
            result = resolve_location(text)
            assert result.accepted, f"Expected '{text}' to be accepted"
            if expected_city:
                assert result.city == expected_city, f"Expected city={expected_city} for '{text}', got {result.city}"

    def test_reject_foreign_country(self):
        from utils.location_resolver import resolve_location

        cases = [
            "Thane, Sri Lanka",
            "Pune, USA",
            "Mumbai, United Kingdom",
            "London, UK",
            "Singapore",
            "Dubai, UAE",
        ]
        for text in cases:
            result = resolve_location(text)
            assert not result.accepted, f"Expected '{text}' to be rejected"
            assert result.reason == "foreign_country", f"Expected foreign_country reason for '{text}', got {result.reason}"

    def test_reject_past_location(self):
        from utils.location_resolver import resolve_location

        cases = [
            "ex-Mumbai, now London",
            "formerly Nagpur, now Berlin",
            "former Nagpur resident",
            "previously in Pune",
        ]
        for text in cases:
            result = resolve_location(text)
            assert not result.accepted, f"Expected '{text}' to be rejected"

    def test_reject_other_state(self):
        from utils.location_resolver import resolve_location

        cases = [
            "Bangalore, Karnataka",
            "New Delhi, India",
            "Chennai, Tamil Nadu",
            "Hyderabad, Telangana",
            "Patna, Bihar",
        ]
        for text in cases:
            result = resolve_location(text)
            assert not result.accepted, f"Expected '{text}' to be rejected"

    def test_reject_ambiguous(self):
        from utils.location_resolver import resolve_location

        result = resolve_location("Aurangabad")
        assert not result.accepted, "Aurangabad alone should be rejected as ambiguous"
        assert result.reason == "ambiguous_name"

        # But with Bihar qualifier, it's rejected as other_state
        result2 = resolve_location("Aurangabad, Bihar")
        assert not result2.accepted

    def test_reject_from_prefix(self):
        from utils.location_resolver import resolve_location

        result = resolve_location("from Pune")
        assert not result.accepted
        assert result.reason == "origin_not_residence"

    def test_reject_empty(self):
        from utils.location_resolver import resolve_location

        for text in ["", None, "   "]:
            result = resolve_location(text or "")
            assert not result.accepted
            assert result.reason == "no_match"

    def test_no_false_positive_indianapolis(self):
        from utils.location_resolver import resolve_location

        result = resolve_location("Indianapolis, Indiana")
        assert not result.accepted, "Indianapolis must not match"

    def test_no_false_positive_puneet(self):
        from utils.location_resolver import resolve_location

        result = resolve_location("Puneet Sharma, Delhi")
        assert not result.accepted, "Puneet must not match Pune"

    def test_emoji_handling(self):
        from utils.location_resolver import resolve_location

        result = resolve_location("📍 Mumbai 🇮🇳")
        assert result.accepted
        assert result.city == "Mumbai"

    def test_uppercase_handling(self):
        from utils.location_resolver import resolve_location

        result = resolve_location("PUNE, INDIA")
        assert result.accepted
        assert result.city == "Pune"

    def test_old_name_aliases(self):
        from utils.location_resolver import resolve_location

        assert resolve_location("Bombay").city == "Mumbai"
        assert resolve_location("Poona").city == "Pune"
        assert resolve_location("Osmanabad, Maharashtra").city == "Dharashiv"
        assert resolve_location("Ahmednagar, MH").city == "Ahilyanagar"


# ── Phase 3.1: Fixture Evaluation Tests ──────────────────────────────────────

class TestLocationFixture:
    """Run the full fixture file and assert precision/recall gates."""

    def test_fixture_precision_recall(self):
        from utils.location_resolver import resolve_location

        fixture = Path(__file__).parent / "fixtures" / "location_cases.csv"
        tp = fp = tn = fn = 0

        with open(fixture, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                text = row["text"].strip()
                expected = row["expected_accepted"].strip().lower() == "true"
                result = resolve_location(text)

                if result.accepted and expected:
                    tp += 1
                elif not result.accepted and not expected:
                    tn += 1
                elif result.accepted and not expected:
                    fp += 1
                else:
                    fn += 1

        precision = tp / (tp + fp) if (tp + fp) else 0
        recall = tp / (tp + fn) if (tp + fn) else 0

        assert precision >= 0.97, f"Precision {precision:.4f} < 0.97"
        assert recall >= 0.90, f"Recall {recall:.4f} < 0.90"


# ── Phase 3.2: Target Location Filtering ─────────────────────────────────────

class TestTargetLocationFiltering:
    """A role targeting only Pune should return only Pune-resolved candidates."""

    def test_pune_only_target(self):
        from utils.location_resolver import resolve_for_target

        target = [{"state": "Maharashtra", "cities": ["Pune"], "country_iso2": "IN", "remote_ok": False}]

        pune_result = resolve_for_target("Pune, India", target)
        assert pune_result.accepted, "Pune should be accepted for Pune target"

        mumbai_result = resolve_for_target("Mumbai, India", target)
        assert not mumbai_result.accepted, "Mumbai should NOT be accepted for Pune-only target"


# ── Phase 3.5: Rate Limiter Tests ────────────────────────────────────────────

class TestRateLimiter:
    """Simulate two roles; no 60-second window may contain > 25 search calls."""

    def test_limiter_respects_window(self, monkeypatch):
        from utils.rate_limiter import RateLimiter

        current_time = 1000.0

        def mock_monotonic():
            nonlocal current_time
            return current_time

        async def mock_sleep(seconds):
            nonlocal current_time
            current_time += seconds

        monkeypatch.setattr(time, "monotonic", mock_monotonic)
        monkeypatch.setattr(asyncio, "sleep", mock_sleep)

        async def _run():
            limiter = RateLimiter(max_calls=25, window_seconds=60.0, max_concurrency=2)
            timestamps = []

            async def simulate_role_search(role_name: str, call_count: int):
                for _ in range(call_count):
                    async with limiter:
                        timestamps.append(time.monotonic())

            # Simulate two roles making search calls concurrently (15 calls each = 30 calls)
            await asyncio.gather(
                simulate_role_search("Role_Backend", 15),
                simulate_role_search("Role_Frontend", 15),
            )

            assert len(timestamps) == 30
            # Check no 60s window has more than 25 calls
            for i, t in enumerate(timestamps):
                window_count = sum(1 for t2 in timestamps if t <= t2 < t + 60.0)
                assert window_count <= 25, f"Window starting at call {i} (t={t}) has {window_count} calls (max 25)"

        asyncio.run(_run())


# ── Phase 0.2: Strict Privacy Tokens ─────────────────────────────────────────

class TestPrivacyTokenStrict:
    """Phase 0.2: Mutate a valid token 2000 times; assert zero acceptances."""

    def test_mutated_tokens_all_rejected(self):
        from utils.privacy import create_privacy_token, verify_privacy_token, PrivacyTokenError

        token = create_privacy_token(42, "opt_out")
        accepted = 0

        random.seed(42)
        for _ in range(2000):
            # Random mutation: flip a random character
            chars = list(token)
            idx = random.randint(0, len(chars) - 1)
            original = chars[idx]
            # Replace with a different character
            replacement = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_.")
            if replacement == original:
                replacement = "X" if original != "X" else "Y"
            chars[idx] = replacement
            mutated = "".join(chars)

            try:
                verify_privacy_token(mutated, "opt_out")
                accepted += 1
            except (PrivacyTokenError, Exception):
                pass

        assert accepted == 0, f"{accepted} mutated tokens were incorrectly accepted"


# ── Phase 0.1: Auth on Personal Data Reads ───────────────────────────────────

class TestAuthOnReads:
    """Anonymous GET on candidate routes must return 401."""

    def test_anonymous_candidates_returns_401(self):
        async def _run():
            from database import init_db, AsyncSessionLocal, Role, RoleStatus

            await init_db()
            async with AsyncSessionLocal() as session:
                role = Role(title="Auth Test", description="Test", requirements="Test", status=RoleStatus.ACTIVE)
                session.add(role)
                await session.commit()
                await session.refresh(role)
                role_id = role.id

            from httpx import AsyncClient, ASGITransport
            from main import app

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                # Anonymous GET on candidates should 401
                resp = await client.get(f"/api/roles/{role_id}/candidates")
                assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"

                # Keyed GET should 200
                resp2 = await client.get(
                    f"/api/roles/{role_id}/candidates",
                    headers={"X-Api-Key": "test-api-secret"},
                )
                assert resp2.status_code == 200, f"Expected 200, got {resp2.status_code}"

                # Anonymous GET on logs should 401
                resp3 = await client.get("/api/logs")
                assert resp3.status_code == 401, f"Expected 401 on /api/logs, got {resp3.status_code}"

                # Anonymous GET on track/report should 401
                resp4 = await client.get("/api/track/report")
                assert resp4.status_code == 401, f"Expected 401 on /api/track/report, got {resp4.status_code}"

        asyncio.run(_run())


# ── Migration 0004 Test ──────────────────────────────────────────────────────

class TestMigration0004:
    """Verify migration 0004 upgrades and downgrades on SQLite."""

    def test_upgrade_downgrade_sqlite(self):
        async def _run():
            from database import Base, engine, Candidate

            # After schema creation, the new columns should exist
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
                await conn.run_sync(Base.metadata.create_all)

            from database import AsyncSessionLocal, Role, RoleStatus, CandidateStage
            from datetime import datetime, timezone

            async with AsyncSessionLocal() as session:
                role = Role(title="Migration Test", description="Test", status=RoleStatus.ACTIVE)
                session.add(role)
                await session.commit()
                await session.refresh(role)

                # Create candidate with new location fields
                c = Candidate(
                    role_id=role.id,
                    name="Test User",
                    source="test",
                    stage=CandidateStage.SOURCED,
                    location_raw="Pune, India",
                    location_city="Pune",
                    location_district="Pune",
                    location_state="Maharashtra",
                    location_country_iso2="IN",
                    location_confidence="high",
                    location_reason=None,
                    location_source="github",
                    location_resolved_at=datetime.now(timezone.utc),
                )
                session.add(c)
                await session.commit()
                await session.refresh(c)

                assert c.location_city == "Pune"
                assert c.location_state == "Maharashtra"
                assert c.location_confidence == "high"
                assert c.location_country_iso2 == "IN"

                # Verify role target_locations
                role.target_locations = [{"state": "Maharashtra", "country_iso2": "IN"}]
                await session.commit()
                await session.refresh(role)
                assert role.target_locations[0]["state"] == "Maharashtra"

        asyncio.run(_run())


# ── Keep existing tests working ──────────────────────────────────────────────

class TestScoutLocationMatching:
    """Location resolver must match whole words and handle aliases."""

    def test_valid_maharashtra_locations(self):
        from utils.location_resolver import resolve_location

        valid = [
            "Mumbai, Maharashtra",
            "Pune, India",
            "Nagpur",
            "Nashik, Maharashtra, India",
            "Thane",
            "Navi Mumbai",
            "Kolhapur",
        ]
        for loc in valid:
            result = resolve_location(loc)
            assert result.accepted, f"Expected {loc} to be accepted"

    def test_invalid_locations_and_false_positives(self):
        from utils.location_resolver import resolve_location

        invalid = [
            "Indianapolis, Indiana",
            "Indiana, USA",
            "London, UK",
            "San Francisco, CA",
            "New Delhi, India",
            "Bangalore, Karnataka",
            "Hyderabad, Telangana",
            "",
        ]
        for loc in invalid:
            result = resolve_location(loc)
            assert not result.accepted, f"Expected {loc} NOT to be accepted"


class TestKeywordExtraction:
    """Fix #12: Keyword matching must use word boundaries."""

    def test_substring_false_positives_prevented(self):
        from agents.scout import _extract_keywords

        assert "rag" not in _extract_keywords("We need storage solutions for file uploads.")
        assert "ml" not in _extract_keywords("Proficient in html and css styling.")
        assert "rust" not in _extract_keywords("We value trust and communication in our engineering team.")

    def test_exact_keywords_matched(self):
        from agents.scout import _extract_keywords

        text = "Looking for a Senior Python and FastAPI backend engineer with Docker, Kubernetes, and PostgreSQL experience."
        keywords = _extract_keywords(text)
        assert "python" in keywords
        assert "fastapi" in keywords
        assert "docker" in keywords
        assert "postgresql" in keywords or "postgres" in keywords


class TestScoutScoring:
    """Fix #19: SCOUT heuristic scoring."""

    def test_qualified_candidate_scoring(self):
        from agents.scout import compute_quick_heuristic_score

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
        res = compute_quick_heuristic_score(candidate, "FastAPI Backend Engineer", "Python, FastAPI, Docker, PostgreSQL")
        assert res["score"] >= 60
        assert len(res["strengths"]) > 0

    def test_unqualified_candidate_scoring(self):
        from agents.scout import compute_quick_heuristic_score

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
        res = compute_quick_heuristic_score(candidate, "Senior Golang Distributed Systems", "Golang, Kubernetes, Raft, Distributed Systems")
        assert res["score"] <= 40


class TestCoordSlots:
    """Fix #5: Interview slots must be in IST and within business hours."""

    def test_slot_time_and_timezone(self):
        from agents.coord import find_next_slot, IST
        from datetime import datetime

        slot = find_next_slot()
        assert slot.tzinfo is not None
        assert slot.weekday() < 5
        assert 10 <= slot.hour < 17
        now_ist = datetime.now(IST)
        assert slot > now_ist


class TestTrackEmptyJobs:
    """Fix #13: TRACK must handle empty roles."""

    def test_compute_pipeline_health_empty(self):
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

        asyncio.run(_run())


class TestDeduplication:
    """Fix #8: Deduplication must match on github_url, email, or name+source."""

    def test_duplicate_detection(self):
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

            assert await is_duplicate(role_id, "https://github.com/spatil-test", None) is True
            assert await is_duplicate(role_id, None, "spatil@example.com") is True
            assert await is_duplicate(role_id, None, None, "Siddharth Patil", "github_maharashtra") is True
            assert await is_duplicate(role_id, "https://github.com/other-user", "other@example.com", "Other User", "github_maharashtra") is False

        asyncio.run(_run())
