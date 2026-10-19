"""Regression coverage for authentication, outreach, scheduling, and privacy flows."""
import asyncio
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from agents import coord, engage, scout
from agents.coord import IST, find_next_slot, schedule_interview
from config import settings
from database import AsyncSessionLocal, Candidate, CandidateStage, Role, RoleStatus
from main import app, list_candidates, require_api_key
from schemas import ConsentRequest
from utils.privacy import PrivacyTokenError, create_privacy_token, verify_privacy_token


async def create_role_and_candidate(
    *,
    consent: bool = False,
    stage: CandidateStage = CandidateStage.SOURCED,
    verified: bool = True,
):
    async with AsyncSessionLocal() as session:
        role = Role(
            title="Backend Engineer",
            description="Build reliable Python services.",
            requirements="Python, FastAPI",
            status=RoleStatus.ACTIVE,
        )
        session.add(role)
        await session.flush()
        candidate = Candidate(
            role_id=role.id,
            name="Test Candidate",
            email="candidate@example.com",
            source="github_maharashtra",
            source_verified=verified,
            source_captured_at=datetime.now(timezone.utc) if verified else None,
            source_evidence=[
                {
                    "id": "E1",
                    "type": "github_profile",
                    "label": "GitHub profile",
                    "url": "https://github.com/test-candidate",
                }
            ] if verified else None,
            stage=stage,
            contact_consent_at=datetime.now(timezone.utc) if consent else None,
            contact_consent_source="Direct application" if consent else None,
            last_activity_at=datetime.utcnow(),
        )
        session.add(candidate)
        await session.commit()
        return role.id, candidate.id


class TestWriteAuthentication:
    def test_require_api_key_rejects_missing_or_wrong_key(self, monkeypatch):
        monkeypatch.setattr(settings, "API_SECRET_KEY", "test-api-secret")

        for value in (None, "wrong-key"):
            with pytest.raises(HTTPException) as error:
                asyncio.run(require_api_key(value))
            assert error.value.status_code == 401

    def test_require_api_key_fails_closed_when_unconfigured(self, monkeypatch):
        monkeypatch.setattr(settings, "API_SECRET_KEY", "")
        with pytest.raises(HTTPException) as error:
            asyncio.run(require_api_key("anything"))
        assert error.value.status_code == 503

    def test_consent_records_require_a_meaningful_source(self):
        with pytest.raises(ValueError):
            ConsentRequest(confirmed=True, source="   ")

    def test_direct_candidate_creation_is_not_an_application_route(self):
        assert "/api/candidates" not in app.openapi()["paths"]


class TestPrivacyTokens:
    def test_signed_token_is_action_bound(self):
        token = create_privacy_token(42, "opt_out")
        assert verify_privacy_token(token, "opt_out") == 42
        with pytest.raises(PrivacyTokenError):
            verify_privacy_token(token, "delete")

    def test_modified_signed_token_is_rejected(self):
        token = create_privacy_token(42, "delete")
        altered = f"{token[:-1]}{'A' if token[-1] != 'A' else 'B'}"
        with pytest.raises(PrivacyTokenError):
            verify_privacy_token(altered, "delete")


class TestOutreachSafety:
    def test_outreach_requires_recorded_consent(self, monkeypatch):
        async def run():
            _, candidate_id = await create_role_and_candidate(consent=False)
            called = False

            def fake_smtp(*args, **kwargs):
                nonlocal called
                called = True
                return True

            monkeypatch.setattr(engage, "send_email_smtp", fake_smtp)
            result = await engage.engage_candidate(candidate_id)
            assert result["success"] is False
            assert "consent" in result["error"].lower()
            assert called is False

        asyncio.run(run())

    def test_smtp_failure_does_not_advance_or_stamp_candidate(self, monkeypatch):
        async def run():
            _, candidate_id = await create_role_and_candidate(consent=True)
            monkeypatch.setattr(engage, "send_email_smtp", lambda *args, **kwargs: False)

            result = await engage.engage_candidate(candidate_id)
            assert result["success"] is False

            async with AsyncSessionLocal() as session:
                candidate = await session.get(Candidate, candidate_id)
                assert candidate.stage == CandidateStage.SOURCED
                assert candidate.outreach_count == 0
                assert candidate.last_contacted_at is None

        asyncio.run(run())


class TestScheduling:
    def test_long_interview_moves_to_next_business_day(self):
        monday = datetime(2026, 10, 19, 15, 30, tzinfo=IST)
        slot = find_next_slot(monday, duration_minutes=120)
        assert slot.weekday() == 1
        assert slot.hour == 10
        assert slot.tzinfo == IST

    def test_calendar_failure_does_not_schedule_candidate(self, monkeypatch):
        async def run():
            _, candidate_id = await create_role_and_candidate(consent=True)

            async def fake_prep(*args, **kwargs):
                return "<p>prep</p>"

            monkeypatch.setattr(coord, "generate_prep_doc", fake_prep)
            monkeypatch.setattr(coord, "_get_calendar_service", lambda: object())
            monkeypatch.setattr(coord, "create_calendar_event", lambda *args, **kwargs: None)

            result = await schedule_interview(candidate_id, "interviewer@example.com")
            assert result["success"] is False
            assert "could not create" in result["error"].lower()

            async with AsyncSessionLocal() as session:
                candidate = await session.get(Candidate, candidate_id)
                assert candidate.stage == CandidateStage.SOURCED
                assert candidate.calendar_event_id is None

        asyncio.run(run())


class TestScoutAndCandidateQueries:
    def test_scout_evidence_uses_only_safe_public_profile_and_repository_links(self):
        evidence = scout.build_source_evidence({
            "github_url": "https://github.com/public-user?tracking=remove-me",
            "stackoverflow_url": "https://stackoverflow.com/users/123/public-user",
            "top_repos": [
                {"name": "real-repo", "url": "https://github.com/public-user/real-repo", "language": "Python", "stars": 12},
                {"name": "unsafe", "url": "javascript:alert(1)"},
            ],
        })
        assert [item["url"] for item in evidence] == [
            "https://github.com/public-user",
            "https://stackoverflow.com/users/123/public-user",
            "https://github.com/public-user/real-repo",
        ]

    def test_scout_requires_github_token_before_network_work(self, monkeypatch):
        async def run():
            role_id, _ = await create_role_and_candidate()
            monkeypatch.setattr(settings, "GITHUB_TOKEN", "")
            events = [event async for event in scout.run_scout(role_id)]
            assert events == [{
                "event": "error",
                "agent": "SCOUT",
                "message": "GITHUB_TOKEN is required before SCOUT can run. Add it to backend/.env and restart the service.",
            }]

        asyncio.run(run())

    def test_candidate_stage_filter_uses_enum_value(self):
        async def run():
            role_id, candidate_id = await create_role_and_candidate()
            async with AsyncSessionLocal() as session:
                candidate = await session.get(Candidate, candidate_id)
                candidate.stage = CandidateStage.SCREENED
                await session.commit()

                screened = await list_candidates(role_id, stage="screened", db=session)
                sourced = await list_candidates(role_id, stage="sourced", db=session)

            # New frontend-compatible API returns string IDs like '#CAN-00001'
            assert [candidate.id for candidate in screened] == [f"#CAN-{candidate_id:05d}"]
            assert sourced == []

        asyncio.run(run())

    def test_unverified_legacy_candidates_are_hidden_and_cannot_be_contacted(self):
        async def run():
            role_id, candidate_id = await create_role_and_candidate(consent=True, verified=False)
            async with AsyncSessionLocal() as session:
                visible = await list_candidates(role_id, db=session)
            assert visible == []

            result = await engage.engage_candidate(candidate_id)
            assert result["success"] is False
            assert "evidence" in result["error"].lower()

        asyncio.run(run())
