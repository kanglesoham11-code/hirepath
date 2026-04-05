"""
HIREPATH — Main FastAPI Application (v2 — $10K Edition)
REST API + SSE + Email Discovery + Analytics + CSV/JSON Export
"""
import asyncio, json, csv, io
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional, List, AsyncGenerator
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database import init_db, get_db, Candidate, Role, AgentLog, CandidateStage, AsyncSessionLocal
from schemas import (RoleCreate, RoleOut, CandidateOut, CandidateCreate, ScoutRequest,
    ScreenRequest, EngageRequest, CoordRequest, TrackRequest, AgentLogOut, PipelineHealth)
from agents.scout import run_scout
from agents.screen import screen_candidate, screen_all_sourced
from agents.engage import engage_bulk, engage_candidate, mark_replied, run_followup_sweep
from agents.coord import schedule_interview
from agents.track import run_track, compute_pipeline_health, generate_weekly_report
from orchestrator import run_full_pipeline
from utils.logger import log_event
from utils.email_hunter import discover_email, hunter_domain_search
from config import settings

_sse_queues: list = []

async def broadcast(data: dict):
    dead = []
    for q in _sse_queues:
        try: q.put_nowait(data)
        except asyncio.QueueFull: dead.append(q)
    for q in dead:
        if q in _sse_queues: _sse_queues.remove(q)

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job("interval", hours=6, id="followup_sweep")
async def scheduled_followup(): await run_followup_sweep()

@scheduler.scheduled_job("interval", hours=12, id="track_all")
async def scheduled_track(): await run_track()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    scheduler.start()
    await log_event("SYSTEM", "startup", "HIREPATH v2 started")
    yield
    scheduler.shutdown(wait=False)

app = FastAPI(title="HIREPATH", description="Autonomous Recruitment + Email Discovery", version="2.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# ── SSE ────────────────────────────────────────────────────────────────────────
@app.get("/api/events")
async def sse_endpoint(request: Request):
    q = asyncio.Queue(maxsize=100)
    _sse_queues.append(q)
    async def stream():
        yield f"data: {json.dumps({'event':'connected'})}\n\n"
        try:
            while True:
                if await request.is_disconnected(): break
                try:
                    data = await asyncio.wait_for(q.get(), timeout=15)
                    yield f"data: {json.dumps(data, default=str)}\n\n"
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'event':'heartbeat'})}\n\n"
        finally:
            if q in _sse_queues: _sse_queues.remove(q)
    return StreamingResponse(stream(), media_type="text/event-stream", headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"})

# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/api/health")
async def health(): return {"status":"ok","version":"2.0.0","timestamp":datetime.utcnow().isoformat()}

# ── Roles ─────────────────────────────────────────────────────────────────────
@app.get("/api/roles", response_model=List[RoleOut])
async def list_roles(db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Role).order_by(desc(Role.created_at)))
    return r.scalars().all()

@app.post("/api/roles", response_model=RoleOut)
async def create_role(payload: RoleCreate, db: AsyncSession = Depends(get_db)):
    role = Role(**payload.model_dump()); db.add(role); await db.commit(); await db.refresh(role)
    await log_event("SYSTEM","role_created",f"New role: {role.title}",role_id=role.id)
    return role

@app.get("/api/roles/{role_id}", response_model=RoleOut)
async def get_role(role_id: int, db: AsyncSession = Depends(get_db)):
    r = await db.get(Role, role_id)
    if not r: raise HTTPException(404)
    return r

@app.delete("/api/roles/{role_id}")
async def delete_role(role_id: int, db: AsyncSession = Depends(get_db)):
    r = await db.get(Role, role_id)
    if not r: raise HTTPException(404)
    await db.delete(r); await db.commit()
    return {"deleted":True}

# ── Candidates ─────────────────────────────────────────────────────────────────
@app.get("/api/roles/{role_id}/candidates", response_model=List[CandidateOut])
async def list_candidates(role_id: int, stage: Optional[str]=None, db: AsyncSession=Depends(get_db)):
    q = select(Candidate).where(Candidate.role_id==role_id)
    if stage: q = q.where(Candidate.stage==stage)
    r = await db.execute(q.order_by(desc(Candidate.score)))
    return r.scalars().all()

@app.post("/api/candidates", response_model=CandidateOut)
async def add_candidate(payload: CandidateCreate, db: AsyncSession=Depends(get_db)):
    c = Candidate(**payload.model_dump(), stage=CandidateStage.SOURCED, last_activity_at=datetime.utcnow())
    db.add(c); await db.commit(); await db.refresh(c)
    return c

@app.get("/api/candidates/{candidate_id}", response_model=CandidateOut)
async def get_candidate(candidate_id: int, db: AsyncSession=Depends(get_db)):
    c = await db.get(Candidate, candidate_id)
    if not c: raise HTTPException(404)
    return c

@app.patch("/api/candidates/{candidate_id}/stage")
async def update_stage(candidate_id: int, stage: str, db: AsyncSession=Depends(get_db)):
    c = await db.get(Candidate, candidate_id)
    if not c: raise HTTPException(404)
    try: c.stage = CandidateStage(stage)
    except ValueError: raise HTTPException(400, f"Invalid stage: {stage}")
    c.last_activity_at = datetime.utcnow(); await db.commit()
    return {"updated":True,"stage":stage}

@app.patch("/api/candidates/{candidate_id}/notes")
async def update_notes(candidate_id: int, notes: str, db: AsyncSession=Depends(get_db)):
    c = await db.get(Candidate, candidate_id)
    if not c: raise HTTPException(404)
    c.notes = notes; await db.commit()
    return {"updated":True}

# ── EMAIL DISCOVERY ────────────────────────────────────────────────────────────
@app.post("/api/candidates/{candidate_id}/discover-email")
async def discover_candidate_email(candidate_id: int, db: AsyncSession=Depends(get_db)):
    """Run full multi-source email discovery on a specific candidate."""
    c = await db.get(Candidate, candidate_id)
    if not c: raise HTTPException(404)
    await log_event("SCOUT","email_discovery_started",f"Discovering email for {c.name}",candidate_id=candidate_id)
    result = await discover_email(name=c.name, github_url=c.github_url, linkedin_url=c.linkedin_url, github_token=settings.GITHUB_TOKEN)
    if result.get("email"):
        c.email = result["email"]
        c.last_activity_at = datetime.utcnow()
        brief = c.screen_brief or {}
        brief["email_discovery"] = {"confidence":result.get("confidence"),"source":result.get("source"),"verified":result.get("verified",False),"alternatives":result.get("alternatives",[]),"discovered_at":datetime.utcnow().isoformat()}
        c.screen_brief = brief
        await db.commit()
        await log_event("SCOUT","email_discovered",f"Found email for {c.name}: {result['email']} [{result.get('confidence')}]",candidate_id=candidate_id)
    return {"candidate_id":candidate_id,"name":c.name,"email":result.get("email"),"confidence":result.get("confidence","not_found"),"source":result.get("source"),"verified":result.get("verified",False),"alternatives":result.get("alternatives",[])}

@app.post("/api/roles/{role_id}/discover-emails")
async def discover_all_emails(role_id: int, background_tasks: BackgroundTasks, db: AsyncSession=Depends(get_db)):
    """Bulk email discovery for all candidates in a role without an email. Runs in background."""
    result = await db.execute(select(Candidate).where(Candidate.role_id==role_id, Candidate.email==None))
    candidates = result.scalars().all()
    async def _run():
        await log_event("SCOUT","bulk_email_start",f"Bulk email discovery: {len(candidates)} candidates",role_id=role_id)
        found = 0
        for cand in candidates:
            disc = await discover_email(name=cand.name, github_url=cand.github_url, linkedin_url=cand.linkedin_url, github_token=settings.GITHUB_TOKEN)
            if disc.get("email"):
                async with AsyncSessionLocal() as s:
                    cc = await s.get(Candidate, cand.id)
                    cc.email = disc["email"]
                    brief = cc.screen_brief or {}
                    brief["email_discovery"] = {"confidence":disc.get("confidence"),"source":disc.get("source"),"verified":disc.get("verified",False)}
                    cc.screen_brief = brief
                    await s.commit()
                found += 1
                await broadcast({"agent":"SCOUT","event":"email_found","message":f"Email found for {cand.name}: {disc['email']} [{disc.get('confidence')}]","candidate_id":cand.id})
            await asyncio.sleep(0.5)
        await log_event("SCOUT","bulk_email_done",f"Bulk discovery: {found}/{len(candidates)} emails found",role_id=role_id)
        await broadcast({"agent":"SCOUT","event":"bulk_email_complete","message":f"Email discovery done: {found}/{len(candidates)} found"})
    background_tasks.add_task(_run)
    return {"status":"started","candidates_without_email":len(candidates)}

@app.post("/api/email/domain-search")
async def domain_email_search(domain: str, max_results: int=10):
    """Search all known emails at a company domain via Hunter.io."""
    results = await hunter_domain_search(domain, max_results)
    return {"domain":domain,"emails":results,"count":len(results)}

@app.get("/api/roles/{role_id}/email-stats")
async def email_stats(role_id: int, db: AsyncSession=Depends(get_db)):
    result = await db.execute(select(Candidate).where(Candidate.role_id==role_id))
    cands = result.scalars().all()
    total = len(cands); with_email = sum(1 for c in cands if c.email)
    conf_breakdown = {}
    for c in cands:
        if c.screen_brief:
            conf = (c.screen_brief.get("email_discovery") or {}).get("confidence","unknown")
            conf_breakdown[conf] = conf_breakdown.get(conf,0)+1
    return {"total_candidates":total,"with_email":with_email,"without_email":total-with_email,"coverage_percent":round(with_email/total*100,1) if total else 0,"confidence_breakdown":conf_breakdown}

# ── SCOUT ─────────────────────────────────────────────────────────────────────
@app.post("/api/scout/stream")
async def scout_stream(payload: ScoutRequest):
    async def gen():
        async for event in run_scout(payload.role_id, payload.keywords, payload.max_candidates):
            yield f"data: {json.dumps(event, default=str)}\n\n"
        yield "data: {\"event\":\"done\"}\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream", headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"})

@app.post("/api/scout")
async def scout_run(payload: ScoutRequest, background_tasks: BackgroundTasks):
    async def _run():
        async for _ in run_scout(payload.role_id, payload.keywords, payload.max_candidates): pass
    background_tasks.add_task(_run)
    return {"status":"started","role_id":payload.role_id}

# ── SCREEN ────────────────────────────────────────────────────────────────────
@app.post("/api/screen/{candidate_id}")
async def screen_one(candidate_id: int):
    brief = await screen_candidate(candidate_id)
    if "error" in brief: raise HTTPException(400, brief["error"])
    return brief

@app.post("/api/screen/role/{role_id}")
async def screen_role(role_id: int, background_tasks: BackgroundTasks):
    background_tasks.add_task(screen_all_sourced, role_id)
    return {"status":"started","role_id":role_id}

# ── ENGAGE ────────────────────────────────────────────────────────────────────
@app.post("/api/engage")
async def engage(payload: EngageRequest):
    results = await engage_bulk(payload.candidate_ids, payload.custom_message)
    return {"results":results,"sent":sum(1 for r in results if r.get("success"))}

@app.post("/api/engage/{candidate_id}")
async def engage_one(candidate_id: int): return await engage_candidate(candidate_id)

@app.post("/api/engage/reply/{candidate_id}")
async def webhook_reply(candidate_id: int): return await mark_replied(candidate_id)

@app.post("/api/engage/followup-sweep")
async def followup_sweep(role_id: Optional[int]=None):
    results = await run_followup_sweep(role_id)
    return {"swept":len(results),"results":results}

# ── COORD ─────────────────────────────────────────────────────────────────────
@app.post("/api/coord/schedule")
async def coord_schedule(payload: CoordRequest):
    result = await schedule_interview(candidate_id=payload.candidate_id, interviewer_email=payload.interviewer_email, duration_minutes=payload.duration_minutes)
    if not result.get("success"): raise HTTPException(400, result.get("error","Scheduling failed"))
    return result

# ── TRACK ─────────────────────────────────────────────────────────────────────
@app.post("/api/track")
async def track(payload: TrackRequest): return await run_track(payload.role_id)

@app.get("/api/track/health/{role_id}")
async def pipeline_health(role_id: int): return await compute_pipeline_health(role_id)

@app.get("/api/track/report")
async def weekly_report():
    html = await generate_weekly_report()
    return {"report_html":html,"generated_at":datetime.utcnow().isoformat()}

# ── Orchestrator ──────────────────────────────────────────────────────────────
@app.post("/api/pipeline/run")
async def run_pipeline(role_id: int, keywords: Optional[str]=None, max_candidates: int=20, background_tasks: BackgroundTasks=BackgroundTasks()):
    kw = keywords.split(",") if keywords else None
    background_tasks.add_task(run_full_pipeline, role_id, kw, max_candidates)
    return {"status":"pipeline_started","role_id":role_id}

# ── Logs ──────────────────────────────────────────────────────────────────────
@app.get("/api/logs", response_model=List[AgentLogOut])
async def get_logs(agent: Optional[str]=None, role_id: Optional[int]=None, limit: int=100, db: AsyncSession=Depends(get_db)):
    q = select(AgentLog).order_by(desc(AgentLog.created_at)).limit(limit)
    if agent: q = q.where(AgentLog.agent==agent)
    if role_id: q = q.where(AgentLog.role_id==role_id)
    r = await db.execute(q)
    return r.scalars().all()

# ── Stats ─────────────────────────────────────────────────────────────────────
@app.get("/api/stats")
async def dashboard_stats(db: AsyncSession=Depends(get_db)):
    roles_r = await db.execute(select(Role))
    roles = roles_r.scalars().all()
    total_c = 0; stage_t = {}; role_stats = []; total_email = 0
    for role in roles:
        cr = await db.execute(select(Candidate).where(Candidate.role_id==role.id))
        cands = cr.scalars().all()
        total_c += len(cands)
        we = sum(1 for c in cands if c.email); total_email += we
        for c in cands: stage_t[c.stage.value] = stage_t.get(c.stage.value,0)+1
        role_stats.append({"id":role.id,"title":role.title,"status":role.status.value,"candidates":len(cands),"with_email":we,"top_score":max((c.score for c in cands if c.score),default=None)})
    return {"total_roles":len(roles),"total_candidates":total_c,"total_with_email":total_email,"email_coverage_pct":round(total_email/total_c*100,1) if total_c else 0,"stage_breakdown":stage_t,"roles":role_stats,"timestamp":datetime.utcnow().isoformat()}

# ── EXPORT ────────────────────────────────────────────────────────────────────
@app.get("/api/roles/{role_id}/export/csv")
async def export_csv(role_id: int, db: AsyncSession=Depends(get_db)):
    """Export candidates as CSV with emails, scores, briefs."""
    role = await db.get(Role, role_id)
    if not role: raise HTTPException(404)
    result = await db.execute(select(Candidate).where(Candidate.role_id==role_id).order_by(desc(Candidate.score)))
    cands = result.scalars().all()
    output = io.StringIO()
    fields = ["id","name","email","email_confidence","email_source","email_verified","github_url","linkedin_url","source","stage","score","hire_recommendation","strengths","concerns","one_line_verdict","outreach_count","last_contacted_at","interview_time","created_at"]
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for c in cands:
        brief = c.screen_brief or {}
        ed = brief.get("email_discovery") or {}
        writer.writerow({
            "id":c.id,"name":c.name,"email":c.email or "","email_confidence":ed.get("confidence","unknown"),"email_source":ed.get("source",""),"email_verified":ed.get("verified",False),
            "github_url":c.github_url or "","linkedin_url":c.linkedin_url or "","source":c.source or "","stage":c.stage.value,"score":c.score or "",
            "hire_recommendation":brief.get("hire_recommendation",""),"strengths":" | ".join(brief.get("strengths",[])),"concerns":" | ".join(brief.get("concerns",[])),
            "one_line_verdict":brief.get("one_line_verdict",""),"outreach_count":c.outreach_count,
            "last_contacted_at":c.last_contacted_at.isoformat() if c.last_contacted_at else "","interview_time":c.interview_time.isoformat() if c.interview_time else "","created_at":c.created_at.isoformat() if c.created_at else ""
        })
    filename = f"hirepath_{role.title.replace(' ','_').lower()}_{datetime.utcnow().strftime('%Y%m%d')}.csv"
    return Response(content=output.getvalue().encode("utf-8"), media_type="text/csv", headers={"Content-Disposition":f"attachment; filename={filename}"})

@app.get("/api/roles/{role_id}/export/json")
async def export_json(role_id: int, db: AsyncSession=Depends(get_db)):
    role = await db.get(Role, role_id)
    if not role: raise HTTPException(404)
    result = await db.execute(select(Candidate).where(Candidate.role_id==role_id).order_by(desc(Candidate.score)))
    cands = result.scalars().all()
    data = [{"id":c.id,"name":c.name,"email":c.email,"email_confidence":(c.screen_brief or {}).get("email_discovery",{}).get("confidence"),"github_url":c.github_url,"source":c.source,"stage":c.stage.value,"score":c.score,"screen_brief":c.screen_brief,"outreach_count":c.outreach_count} for c in cands]
    return JSONResponse({"role":role.title,"exported_at":datetime.utcnow().isoformat(),"candidates":data})

# ── ANALYTICS ────────────────────────────────────────────────────────────────
@app.get("/api/analytics/funnel/{role_id}")
async def funnel_analytics(role_id: int, db: AsyncSession=Depends(get_db)):
    result = await db.execute(select(Candidate).where(Candidate.role_id==role_id))
    cands = result.scalars().all()
    stages = ["sourced","screened","outreach_sent","replied","interview_scheduled","interviewed","offer","hired"]
    counts = {s:0 for s in stages}
    for c in cands:
        if c.stage.value in counts: counts[c.stage.value]+=1
    funnel = []
    for i, s in enumerate(stages):
        prev = counts[stages[i-1]] if i>0 else counts[s]
        funnel.append({"stage":s,"count":counts[s],"conversion_rate":round(counts[s]/prev*100,1) if prev>0 else 0})
    avg_score = sum(c.score for c in cands if c.score)/len([c for c in cands if c.score]) if any(c.score for c in cands) else 0
    sources = {}
    for c in cands: sources[c.source or "unknown"]=sources.get(c.source or "unknown",0)+1
    return {"role_id":role_id,"total":len(cands),"funnel":funnel,"avg_score":round(avg_score,1),"source_breakdown":sources,"email_coverage":round(sum(1 for c in cands if c.email)/len(cands)*100,1) if cands else 0}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=True)
