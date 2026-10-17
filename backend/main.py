"""
HIREPATH — Main FastAPI Application
All REST endpoints + Server-Sent Events for real-time agent activity.
"""
import asyncio
import json
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional, List, AsyncGenerator
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database import init_db, get_db, Candidate, Role, AgentLog, CandidateStage, RoleStatus
from schemas import (
    RoleCreate, RoleOut, CandidateOut, CandidateCreate,
    ScoutRequest, ScreenRequest, EngageRequest, CoordRequest, TrackRequest,
    AgentLogOut, PipelineHealth,
)
from agents.scout import run_scout
from agents.screen import screen_candidate, screen_all_sourced
from agents.engage import engage_bulk, engage_candidate, mark_replied, run_followup_sweep
from agents.coord import schedule_interview
from agents.track import run_track, compute_pipeline_health, generate_weekly_report
from orchestrator import run_full_pipeline
from utils.logger import log_event
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


# ── Scheduler ─────────────────────────────────────────────────────────────────

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job("interval", hours=6, id="followup_sweep")
async def scheduled_followup():
    await run_followup_sweep()

@scheduler.scheduled_job("interval", hours=12, id="track_all")
async def scheduled_track():
    await run_track()


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
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
async def create_role(payload: RoleCreate, db: AsyncSession = Depends(get_db)):
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
async def delete_role(role_id: int, db: AsyncSession = Depends(get_db)):
    role = await db.get(Role, role_id)
    if not role:
        raise HTTPException(404, "Role not found")
    await db.delete(role)
    await db.commit()
    return {"deleted": True}


# ── Candidates ────────────────────────────────────────────────────────────────

@app.get("/api/roles/{role_id}/candidates", response_model=List[CandidateOut])
async def list_candidates(role_id: int, stage: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    q = select(Candidate).where(Candidate.role_id == role_id)
    if stage:
        q = q.where(Candidate.stage == stage)
    q = q.order_by(desc(Candidate.score))
    result = await db.execute(q)
    return result.scalars().all()


@app.post("/api/candidates", response_model=CandidateOut)
async def add_candidate(payload: CandidateCreate, db: AsyncSession = Depends(get_db)):
    c = Candidate(**payload.model_dump(), stage=CandidateStage.SOURCED, last_activity_at=datetime.utcnow())
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return c


@app.get("/api/candidates/{candidate_id}", response_model=CandidateOut)
async def get_candidate(candidate_id: int, db: AsyncSession = Depends(get_db)):
    c = await db.get(Candidate, candidate_id)
    if not c:
        raise HTTPException(404, "Candidate not found")
    return c


@app.patch("/api/candidates/{candidate_id}/stage")
async def update_stage(candidate_id: int, stage: str, db: AsyncSession = Depends(get_db)):
    c = await db.get(Candidate, candidate_id)
    if not c:
        raise HTTPException(404, "Candidate not found")
    try:
        c.stage = CandidateStage(stage)
    except ValueError:
        raise HTTPException(400, f"Invalid stage: {stage}")
    c.last_activity_at = datetime.utcnow()
    await db.commit()
    return {"updated": True, "stage": stage}


# ── SCOUT ─────────────────────────────────────────────────────────────────────

@app.post("/api/scout/stream")
async def scout_stream(payload: ScoutRequest):
    """Streams SCOUT events as SSE."""
    async def gen():
        async for event in run_scout(payload.role_id, payload.keywords, payload.max_candidates):
            yield f"data: {json.dumps(event, default=str)}\n\n"
        yield "data: {\"event\": \"done\"}\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.post("/api/scout")
async def scout_run(payload: ScoutRequest, background_tasks: BackgroundTasks):
    """Runs SCOUT in background."""
    async def _run():
        async for _ in run_scout(payload.role_id, payload.keywords, payload.max_candidates):
            pass
    background_tasks.add_task(_run)
    return {"status": "started", "role_id": payload.role_id}


# ── SCREEN ────────────────────────────────────────────────────────────────────

@app.post("/api/screen/{candidate_id}")
async def screen_one(candidate_id: int):
    brief = await screen_candidate(candidate_id)
    if "error" in brief:
        raise HTTPException(400, brief["error"])
    return brief


@app.post("/api/screen/role/{role_id}")
async def screen_role(role_id: int, background_tasks: BackgroundTasks):
    background_tasks.add_task(screen_all_sourced, role_id)
    return {"status": "started", "role_id": role_id}


# ── ENGAGE ────────────────────────────────────────────────────────────────────

@app.post("/api/engage")
async def engage(payload: EngageRequest):
    results = await engage_bulk(payload.candidate_ids, payload.custom_message)
    return {"results": results, "sent": sum(1 for r in results if r.get("success"))}


@app.post("/api/engage/{candidate_id}")
async def engage_one(candidate_id: int):
    return await engage_candidate(candidate_id)


@app.post("/api/engage/reply/{candidate_id}")
async def webhook_reply(candidate_id: int):
    """Call this when a candidate replies to outreach."""
    return await mark_replied(candidate_id)


@app.post("/api/engage/followup-sweep")
async def followup_sweep(role_id: Optional[int] = None):
    results = await run_followup_sweep(role_id)
    return {"swept": len(results), "results": results}


# ── COORD ─────────────────────────────────────────────────────────────────────

@app.post("/api/coord/schedule")
async def coord_schedule(payload: CoordRequest):
    result = await schedule_interview(
        candidate_id=payload.candidate_id,
        interviewer_email=payload.interviewer_email,
        duration_minutes=payload.duration_minutes,
    )
    if not result.get("success"):
        raise HTTPException(400, result.get("error", "Scheduling failed"))
    return result


# ── TRACK ─────────────────────────────────────────────────────────────────────

@app.post("/api/track")
async def track(payload: TrackRequest):
    result = await run_track(payload.role_id)
    return result


@app.get("/api/track/health/{role_id}")
async def pipeline_health(role_id: int):
    return await compute_pipeline_health(role_id)


@app.get("/api/track/report")
async def weekly_report():
    html = await generate_weekly_report()
    return {"report_html": html, "generated_at": datetime.utcnow().isoformat()}


# ── Orchestrator ──────────────────────────────────────────────────────────────

@app.post("/api/pipeline/run")
async def run_pipeline(role_id: int, keywords: Optional[str] = None, max_candidates: int = 20, background_tasks: BackgroundTasks = BackgroundTasks()):
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
        result = await db.execute(select(Candidate).where(Candidate.role_id == role.id))
        cands = result.scalars().all()
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
