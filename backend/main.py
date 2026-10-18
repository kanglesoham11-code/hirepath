"""
HIREPATH — Main FastAPI Application
All REST endpoints + Server-Sent Events for real-time agent activity.
Includes API key auth on write endpoints (Fix #3).
"""
import asyncio
import hmac
import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional, List, AsyncGenerator
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request, Header
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, delete, or_
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database import init_db, get_db, Candidate, Role, AgentLog, CandidateStage, RoleStatus
from schemas import (
    RoleCreate, RoleOut, CandidateOut,
    ConsentRequest, PrivacyRequest, ScoutRequest, EngageRequest, CoordRequest,
    TrackRequest, AgentLogOut,
)
from agents.scout import run_scout
from agents.screen import screen_candidate, screen_all_sourced
from agents.engage import engage_bulk, engage_candidate, mark_replied, run_followup_sweep
from agents.coord import schedule_interview, send_reminder, run_reminder_sweep
from agents.track import run_track, compute_pipeline_health, generate_weekly_report, mark_stale
from orchestrator import run_full_pipeline
from utils.logger import log_event
from utils.privacy import PrivacyTokenError, verify_privacy_token
from utils.evidence import candidate_has_verifiable_evidence
from config import settings

# ── SSE broadcaster ───────────────────────────────────────────────────────────

_sse_queues: list[asyncio.Queue] = []

async def broadcast(data: dict):
    dead = []
    for q in _sse_queues:
        try:
            q.put_nowait(data)
        except asyncio.QueueFull:
            dead.append(q)
    for q in dead:
        if q in _sse_queues:
            _sse_queues.remove(q)


# ── Auth dependency (Fix #3) ─────────────────────────────────────────────────

async def require_api_key(x_api_key: str = Header(None)):
    """Require a configured API key on every recruiter-controlled write route."""
    if not settings.API_SECRET_KEY:
        raise HTTPException(
            status_code=503,
            detail="API_SECRET_KEY is not configured. Set it in backend/.env before using write endpoints.",
        )
    if not x_api_key or not hmac.compare_digest(x_api_key, settings.API_SECRET_KEY):
        raise HTTPException(status_code=401, detail="Invalid or missing API key. Pass X-Api-Key header.")


def require_verifiable_candidate(candidate: Candidate) -> None:
    """Keep unverified or legacy records out of recruiter workflow actions."""
    if not candidate_has_verifiable_evidence(candidate):
        raise HTTPException(
            status_code=409,
            detail="Candidate is missing live, recruiter-verifiable public source evidence. Run SCOUT again.",
        )


# ── Scheduler ─────────────────────────────────────────────────────────────────

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job("interval", hours=6, id="followup_sweep")
async def scheduled_followup():
    await run_followup_sweep()

@scheduler.scheduled_job("interval", hours=12, id="track_all")
async def scheduled_track():
    await run_track()


@scheduler.scheduled_job("interval", hours=1, id="interview_reminders")
async def scheduled_interview_reminders():
    await run_reminder_sweep()


# ── App lifecycle ─────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    scheduler.start()
    await log_event("SYSTEM", "startup", "HIREPATH backend started")
    yield
    scheduler.shutdown(wait=False)

app = FastAPI(
    title="HIREPATH",
    description="Autonomous Recruitment Agent — 5-agent pipeline",
    version="1.1.0",
    lifespan=lifespan,
)

# Fix #3: Lock CORS to the dashboard URLs instead of accepting any website.
_allowed_origins = list(dict.fromkeys(
    origin.rstrip("/")
    for origin in (settings.FRONTEND_URL, "http://localhost:3000", "http://127.0.0.1:3000")
    if origin
))
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-Api-Key"],
)


# ── SSE endpoint ──────────────────────────────────────────────────────────────

@app.get("/api/events")
async def sse_endpoint(request: Request):
    """Server-Sent Events stream for real-time agent activity."""
    q: asyncio.Queue = asyncio.Queue(maxsize=100)
    _sse_queues.append(q)

    async def event_stream() -> AsyncGenerator[str, None]:
        yield f"data: {json.dumps({'event': 'connected', 'message': 'HIREPATH SSE connected'})}\n\n"
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    data = await asyncio.wait_for(q.get(), timeout=15)
                    yield f"data: {json.dumps(data, default=str)}\n\n"
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'event': 'heartbeat'})}\n\n"
        finally:
            if q in _sse_queues:
                _sse_queues.remove(q)

    return StreamingResponse(event_stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "HIREPATH", "timestamp": datetime.utcnow().isoformat()}


# ── Roles ─────────────────────────────────────────────────────────────────────

@app.get("/api/roles", response_model=List[RoleOut])
async def list_roles(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Role).order_by(desc(Role.created_at)))
    return result.scalars().all()


@app.post("/api/roles", response_model=RoleOut)
async def create_role(payload: RoleCreate, db: AsyncSession = Depends(get_db), _auth=Depends(require_api_key)):
    role = Role(**payload.model_dump())
    db.add(role)
    await db.commit()
    await db.refresh(role)
    await log_event("SYSTEM", "role_created", f"New role: {role.title}", role_id=role.id)
    return role


@app.get("/api/roles/{role_id}", response_model=RoleOut)
async def get_role(role_id: int, db: AsyncSession = Depends(get_db)):
    role = await db.get(Role, role_id)
    if not role:
        raise HTTPException(404, "Role not found")
    return role


@app.delete("/api/roles/{role_id}")
async def delete_role(role_id: int, db: AsyncSession = Depends(get_db), _auth=Depends(require_api_key)):
    role = await db.get(Role, role_id)
    if not role:
        raise HTTPException(404, "Role not found")
    # Fix #7: Delete dependent candidates and their logs before deleting the role.
    candidate_ids = list((await db.execute(select(Candidate.id).where(Candidate.role_id == role_id))).scalars())
    if candidate_ids:
        await db.execute(
            delete(AgentLog).where(or_(AgentLog.role_id == role_id, AgentLog.candidate_id.in_(candidate_ids)))
        )
    else:
        await db.execute(delete(AgentLog).where(AgentLog.role_id == role_id))
    await db.execute(delete(Candidate).where(Candidate.role_id == role_id))
    await db.delete(role)
    await db.commit()
    return {"deleted": True}


# ── Candidates ────────────────────────────────────────────────────────────────

@app.get("/api/roles/{role_id}/candidates", response_model=List[CandidateOut])
async def list_candidates(role_id: int, stage: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    q = select(Candidate).where(
        Candidate.role_id == role_id,
        Candidate.source_verified.is_(True),
    )
    if stage:
        try:
            q = q.where(Candidate.stage == CandidateStage(stage))
        except ValueError:
            raise HTTPException(400, f"Invalid stage: {stage}")
    q = q.order_by(desc(Candidate.score))
    result = await db.execute(q)
    return [candidate for candidate in result.scalars().all() if candidate_has_verifiable_evidence(candidate)]


@app.get("/api/candidates/{candidate_id}", response_model=CandidateOut)
async def get_candidate(candidate_id: int, db: AsyncSession = Depends(get_db)):
    c = await db.get(Candidate, candidate_id)
    if not c:
        raise HTTPException(404, "Candidate not found")
    require_verifiable_candidate(c)
    return c


@app.patch("/api/candidates/{candidate_id}/stage")
async def update_stage(candidate_id: int, stage: str, db: AsyncSession = Depends(get_db), _auth=Depends(require_api_key)):
    c = await db.get(Candidate, candidate_id)
    if not c:
        raise HTTPException(404, "Candidate not found")
    require_verifiable_candidate(c)
    try:
        c.stage = CandidateStage(stage)
    except ValueError:
        raise HTTPException(400, f"Invalid stage: {stage}")
    c.last_activity_at = datetime.utcnow()
    await db.commit()
    return {"updated": True, "stage": stage}


async def _candidate_from_privacy_token(
    payload: PrivacyRequest,
    expected_action: str,
    db: AsyncSession,
) -> Candidate | None:
    """Resolve a candidate from a signed privacy link without exposing identifiers."""
    try:
        candidate_id = verify_privacy_token(payload.token, expected_action)  # type: ignore[arg-type]
    except PrivacyTokenError as exc:
        raise HTTPException(400, str(exc))
    return await db.get(Candidate, candidate_id)


# Fix #18: Privacy actions use signed one-time-purpose links instead of a raw
# candidate id or email, which would let one person alter another profile.
@app.post("/api/privacy/opt-out")
async def opt_out_candidate(payload: PrivacyRequest, db: AsyncSession = Depends(get_db)):
    """Suppress future contact and remove nonessential profile data."""
    candidate = await _candidate_from_privacy_token(payload, "opt_out", db)
    if not candidate:
        return {"status": "ok", "message": "Your contact preference has been recorded."}

    now = datetime.now(timezone.utc)
    await db.execute(delete(AgentLog).where(AgentLog.candidate_id == candidate.id))
    candidate.stage = CandidateStage.REJECTED
    candidate.email = None
    candidate.linkedin_url = None
    candidate.resume_path = None
    candidate.notes = None
    candidate.raw_data = {"privacy": {"opted_out_at": now.isoformat()}}
    candidate.screen_brief = {"privacy": {"opted_out": True, "recorded_at": now.isoformat()}}
    candidate.contact_consent_at = None
    candidate.contact_consent_source = None
    candidate.last_activity_at = datetime.utcnow()
    await db.commit()
    await log_event("PRIVACY", "opt_out", "Candidate contact preference recorded", candidate_id=candidate.id)
    return {"status": "ok", "message": "You will not receive further HirePath outreach."}


@app.post("/api/privacy/delete")
async def delete_my_data(payload: PrivacyRequest, db: AsyncSession = Depends(get_db)):
    """Delete a candidate profile and its related activity records."""
    candidate = await _candidate_from_privacy_token(payload, "delete", db)
    if not candidate:
        return {"status": "ok", "message": "Your data has already been removed."}

    await db.execute(delete(AgentLog).where(AgentLog.candidate_id == candidate.id))
    await db.delete(candidate)
    await db.commit()
    await log_event("PRIVACY", "candidate_deleted", "A candidate data deletion request was completed")
    return {"status": "ok", "message": "Your HirePath candidate data has been deleted."}


@app.post("/api/candidates/{candidate_id}/contact-consent")
async def record_contact_consent(
    candidate_id: int,
    payload: ConsentRequest,
    db: AsyncSession = Depends(get_db),
    _auth=Depends(require_api_key),
):
    """Record a recruiter's confirmation that a candidate agreed to outreach."""
    if not payload.confirmed:
        raise HTTPException(400, "Confirmation is required before recording contact consent.")
    candidate = await db.get(Candidate, candidate_id)
    if not candidate:
        raise HTTPException(404, "Candidate not found")
    require_verifiable_candidate(candidate)

    candidate.contact_consent_at = datetime.now(timezone.utc)
    candidate.contact_consent_source = payload.source.strip()
    candidate.last_activity_at = datetime.utcnow()
    await db.commit()
    await log_event(
        "RECRUITER",
        "contact_consent_recorded",
        "Contact consent recorded by a recruiter",
        data={"source": candidate.contact_consent_source},
        candidate_id=candidate.id,
        role_id=candidate.role_id,
    )
    return {
        "recorded": True,
        "candidate_id": candidate.id,
        "contact_consent_at": candidate.contact_consent_at.isoformat(),
    }


@app.delete("/api/candidates/{candidate_id}")
async def delete_candidate(candidate_id: int, db: AsyncSession = Depends(get_db), _auth=Depends(require_api_key)):
    """Delete a candidate selected by an authenticated recruiter."""
    c = await db.get(Candidate, candidate_id)
    if not c:
        raise HTTPException(404, "Candidate not found")
    await db.execute(delete(AgentLog).where(AgentLog.candidate_id == candidate_id))
    await db.delete(c)
    await db.commit()
    return {"deleted": True, "candidate_id": candidate_id}


# ── SCOUT ─────────────────────────────────────────────────────────────────────

@app.post("/api/scout/stream")
async def scout_stream(payload: ScoutRequest, _auth=Depends(require_api_key)):
    """Streams SCOUT events as SSE."""
    async def gen():
        async for event in run_scout(payload.role_id, payload.keywords, payload.max_candidates):
            yield f"data: {json.dumps(event, default=str)}\n\n"
        yield "data: {\"event\": \"done\"}\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.post("/api/scout")
async def scout_run(payload: ScoutRequest, background_tasks: BackgroundTasks, _auth=Depends(require_api_key)):
    """Runs SCOUT in background."""
    async def _run():
        async for _ in run_scout(payload.role_id, payload.keywords, payload.max_candidates):
            pass
    background_tasks.add_task(_run)
    return {"status": "started", "role_id": payload.role_id}


# ── SCREEN ────────────────────────────────────────────────────────────────────

@app.post("/api/screen/{candidate_id}")
async def screen_one(candidate_id: int, _auth=Depends(require_api_key)):
    brief = await screen_candidate(candidate_id)
    if "error" in brief:
        raise HTTPException(400, brief["error"])
    return brief


@app.post("/api/screen/role/{role_id}")
async def screen_role(role_id: int, background_tasks: BackgroundTasks, _auth=Depends(require_api_key)):
    background_tasks.add_task(screen_all_sourced, role_id)
    return {"status": "started", "role_id": role_id}


# ── ENGAGE ────────────────────────────────────────────────────────────────────

@app.post("/api/engage")
async def engage(payload: EngageRequest, _auth=Depends(require_api_key)):
    results = await engage_bulk(payload.candidate_ids, payload.custom_message)
    return {"results": results, "sent": sum(1 for r in results if r.get("success"))}


# Fix #6: Move followup-sweep route ABOVE the {candidate_id} route
# so it is not caught by the path-parameter route first.
@app.post("/api/engage/followup-sweep")
async def followup_sweep(role_id: Optional[int] = None, _auth=Depends(require_api_key)):
    results = await run_followup_sweep(role_id)
    return {"swept": len(results), "results": results}


@app.post("/api/engage/{candidate_id}")
async def engage_one(candidate_id: int, _auth=Depends(require_api_key)):
    return await engage_candidate(candidate_id)


@app.post("/api/engage/reply/{candidate_id}")
async def webhook_reply(candidate_id: int, _auth=Depends(require_api_key)):
    """Call this when a candidate replies to outreach."""
    return await mark_replied(candidate_id)


# ── COORD ─────────────────────────────────────────────────────────────────────

@app.post("/api/coord/schedule")
async def coord_schedule(payload: CoordRequest, _auth=Depends(require_api_key)):
    result = await schedule_interview(
        candidate_id=payload.candidate_id,
        interviewer_email=payload.interviewer_email,
        duration_minutes=payload.duration_minutes,
    )
    if not result.get("success"):
        raise HTTPException(400, result.get("error", "Scheduling failed"))
    return result


@app.post("/api/coord/{candidate_id}/remind")
async def coord_remind(candidate_id: int, _auth=Depends(require_api_key)):
    """Fix #22: Wire up send_reminder."""
    result = await send_reminder(candidate_id)
    if not result.get("success"):
        raise HTTPException(400, result.get("error", "Failed to send reminder"))
    return result


# ── TRACK ─────────────────────────────────────────────────────────────────────

@app.post("/api/track")
async def track(payload: TrackRequest, _auth=Depends(require_api_key)):
    result = await run_track(payload.role_id)
    return result


@app.post("/api/track/mark-stale")
async def track_mark_stale(candidate_ids: List[int], _auth=Depends(require_api_key)):
    """Fix #22: Wire up mark_stale."""
    count = await mark_stale(candidate_ids)
    return {"marked_stale": count}


@app.get("/api/track/health/{role_id}")
async def pipeline_health(role_id: int):
    return await compute_pipeline_health(role_id)


@app.get("/api/track/report")
async def weekly_report():
    html = await generate_weekly_report()
    return {"report_html": html, "generated_at": datetime.utcnow().isoformat()}


# ── Orchestrator ──────────────────────────────────────────────────────────────

@app.post("/api/pipeline/run")
async def run_pipeline(role_id: int, background_tasks: BackgroundTasks, keywords: Optional[str] = None, max_candidates: int = 20, _auth=Depends(require_api_key)):
    kw = keywords.split(",") if keywords else None
    background_tasks.add_task(run_full_pipeline, role_id, kw, max_candidates)
    return {"status": "pipeline_started", "role_id": role_id}


# ── Agent Logs ────────────────────────────────────────────────────────────────

@app.get("/api/logs", response_model=List[AgentLogOut])
async def get_logs(
    agent: Optional[str] = None,
    role_id: Optional[int] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    q = select(AgentLog).order_by(desc(AgentLog.created_at)).limit(limit)
    if agent:
        q = q.where(AgentLog.agent == agent)
    if role_id:
        q = q.where(AgentLog.role_id == role_id)
    result = await db.execute(q)
    return result.scalars().all()


# ── Dashboard Stats ───────────────────────────────────────────────────────────

@app.get("/api/stats")
async def dashboard_stats(db: AsyncSession = Depends(get_db)):
    roles_result = await db.execute(select(Role))
    roles = roles_result.scalars().all()

    total_candidates = 0
    stage_totals = {}
    role_stats = []

    for role in roles:
        result = await db.execute(
            select(Candidate).where(
                Candidate.role_id == role.id,
                Candidate.source_verified.is_(True),
            )
        )
        cands = [candidate for candidate in result.scalars().all() if candidate_has_verifiable_evidence(candidate)]
        total_candidates += len(cands)
        for c in cands:
            stage_totals[c.stage.value] = stage_totals.get(c.stage.value, 0) + 1
        role_stats.append({
            "id": role.id,
            "title": role.title,
            "status": role.status.value,
            "candidates": len(cands),
            "top_score": max((c.score for c in cands if c.score), default=None),
        })

    return {
        "total_roles": len(roles),
        "total_candidates": total_candidates,
        "stage_breakdown": stage_totals,
        "roles": role_stats,
        "timestamp": datetime.utcnow().isoformat(),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=True)
