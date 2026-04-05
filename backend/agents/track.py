"""
TRACK — Pipeline Intelligence Agent
Monitors pipeline health, detects stale candidates and bottlenecks,
generates weekly reports, fires Slack alerts.
"""
import json
import httpx
from datetime import datetime, timedelta
from collections import Counter
from sqlalchemy import select, func
from database import Candidate, Role, CandidateStage, RoleStatus, AgentLog, AsyncSessionLocal
from utils.llm import groq_chat
from utils.logger import log_event
from config import settings
from schemas import PipelineHealth, PipelineStageCount, CandidateOut


# ── Slack ─────────────────────────────────────────────────────────────────────

async def send_slack_alert(message: str) -> bool:
    if not settings.SLACK_WEBHOOK_URL:
        print(f"[TRACK] Slack not configured. Alert: {message}")
        return True
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(settings.SLACK_WEBHOOK_URL, json={"text": message})
            return resp.status_code == 200
    except Exception as e:
        print(f"[TRACK] Slack error: {e}")
        return False


# ── Stale detection ───────────────────────────────────────────────────────────

async def get_stale_candidates(role_id: int | None = None) -> list[Candidate]:
    """Returns candidates with no activity in STALE_THRESHOLD_DAYS days."""
    cutoff = datetime.utcnow() - timedelta(days=settings.STALE_THRESHOLD_DAYS)
    async with AsyncSessionLocal() as session:
        q = select(Candidate).where(
            Candidate.stage.notin_([CandidateStage.HIRED, CandidateStage.REJECTED, CandidateStage.STALE]),
            Candidate.last_activity_at < cutoff,
        )
        if role_id:
            q = q.where(Candidate.role_id == role_id)
        result = await session.execute(q)
        return result.scalars().all()


async def mark_stale(candidate_ids: list[int]) -> int:
    count = 0
    async with AsyncSessionLocal() as session:
        for cid in candidate_ids:
            c = await session.get(Candidate, cid)
            if c:
                c.stage = CandidateStage.STALE
                count += 1
        await session.commit()
    return count


# ── Pipeline health ───────────────────────────────────────────────────────────

STAGE_ORDER = [
    CandidateStage.SOURCED, CandidateStage.SCREENED,
    CandidateStage.OUTREACH_SENT, CandidateStage.REPLIED,
    CandidateStage.INTERVIEW_SCHEDULED, CandidateStage.INTERVIEWED,
    CandidateStage.OFFER, CandidateStage.HIRED,
]

async def compute_pipeline_health(role_id: int) -> dict:
    async with AsyncSessionLocal() as session:
        role = await session.get(Role, role_id)
        if not role:
            return {}
        result = await session.execute(
            select(Candidate).where(Candidate.role_id == role_id)
        )
        candidates = result.scalars().all()

    if not candidates:
        return {
            "role_id": role_id,
            "role_title": role.title,
            "total_candidates": 0,
            "stage_breakdown": [],
            "stale_candidates": [],
            "bottleneck": None,
            "insights": ["No candidates in pipeline yet. Run SCOUT to source candidates."],
            "health_score": 0.0,
        }

    stage_counts = Counter(c.stage.value for c in candidates)
    breakdown = [{"stage": s, "count": stage_counts.get(s, 0)} for s in [st.value for st in STAGE_ORDER]]

    stale_cutoff = datetime.utcnow() - timedelta(days=settings.STALE_THRESHOLD_DAYS)
    stale = [c for c in candidates if c.last_activity_at and c.last_activity_at < stale_cutoff
             and c.stage not in (CandidateStage.HIRED, CandidateStage.REJECTED)]

    # Detect bottleneck: stage with highest count that isn't terminal
    active_stages = {s: stage_counts.get(s, 0) for s in [st.value for st in STAGE_ORDER[:7]]}
    bottleneck_stage = max(active_stages, key=active_stages.get) if active_stages else None
    bottleneck = bottleneck_stage if active_stages.get(bottleneck_stage, 0) > 2 else None

    # Insights
    insights = []
    total = len(candidates)
    hired = stage_counts.get("hired", 0)
    rejected = stage_counts.get("rejected", 0)
    if stale:
        insights.append(f"⚠️ {len(stale)} candidate(s) have had no activity in {settings.STALE_THRESHOLD_DAYS}+ days.")
    if bottleneck:
        insights.append(f"🚧 Bottleneck at '{bottleneck}' stage — {active_stages[bottleneck]} candidates stuck.")
    offer_declines = stage_counts.get("offer", 0)
    if offer_declines >= 2:
        insights.append(f"📉 {offer_declines} candidates at offer stage — review offer competitiveness.")
    if total > 10 and hired == 0:
        insights.append("🎯 Large pipeline with 0 hires — consider moving top candidates to interview.")
    outreach_sent = stage_counts.get("outreach_sent", 0)
    replied = stage_counts.get("replied", 0)
    if outreach_sent > 5 and replied == 0:
        insights.append(f"📬 {outreach_sent} outreach sent, 0 replies — revisit messaging or targeting.")
    if not insights:
        insights.append("✅ Pipeline looks healthy! Keep momentum going.")

    # Health score: weighted metric
    score = 50.0
    if total > 0:
        score += min(20, total)
    if hired > 0:
        score = min(100, score + 30)
    score -= len(stale) * 5
    score -= (len(candidates) - hired - rejected) * 0.5 if (total - hired - rejected) > 15 else 0
    score = max(0, min(100, score))

    stale_out = []
    for c in stale[:5]:
        stale_out.append({
            "id": c.id, "name": c.name, "stage": c.stage.value,
            "last_activity_at": c.last_activity_at.isoformat() if c.last_activity_at else None,
            "score": c.score,
        })

    return {
        "role_id": role_id,
        "role_title": role.title,
        "total_candidates": total,
        "stage_breakdown": breakdown,
        "stale_candidates": stale_out,
        "bottleneck": bottleneck,
        "insights": insights,
        "health_score": round(score, 1),
    }


# ── Weekly report ─────────────────────────────────────────────────────────────

REPORT_SYSTEM = """You are a senior recruitment operations analyst at a top-tier company.
Given pipeline data, write a concise but actionable weekly hiring health report in HTML.

Structure:
1. Executive summary (2-3 sentences on overall hiring velocity)
2. Per-role breakdown with key metrics and status
3. Red flags and urgent issues
4. 3 specific, actionable recommended next steps with clear owners

Be direct. Use data. Flag problems clearly.
Use <h3>, <p>, <ul>, <strong>. Keep it under 500 words."""

async def generate_weekly_report(role_ids: list[int] | None = None) -> str:
    async with AsyncSessionLocal() as session:
        if role_ids:
            q = select(Role).where(Role.id.in_(role_ids))
        else:
            q = select(Role).where(Role.status == RoleStatus.ACTIVE)
        result = await session.execute(q)
        roles = result.scalars().all()

    all_health = []
    for role in roles:
        health = await compute_pipeline_health(role.id)
        all_health.append(health)

    summary_data = json.dumps(all_health, indent=2, default=str)[:3000]

    if not settings.GROQ_API_KEY:
        lines = ["<h2>Weekly Hiring Health Report</h2>"]
        for h in all_health:
            lines.append(f"<h3>{h['role_title']}</h3>")
            lines.append(f"<p>Total candidates: {h['total_candidates']} | Health score: {h['health_score']}</p>")
            lines.append("<ul>" + "".join(f"<li>{i}</li>" for i in h['insights']) + "</ul>")
        lines.append("<h3>Recommended Actions</h3><ol><li>Run follow-up sweep on stale candidates.</li><li>Move top-scored candidates to interview.</li><li>Review offer-stage dropouts.</li></ol>")
        return "\n".join(lines)

    prompt = f"Pipeline data for weekly report:\n{summary_data}\n\nGenerate the weekly hiring health report HTML."
    return await groq_chat([{"role": "user", "content": prompt}], system=REPORT_SYSTEM, max_tokens=1200)


# ── Main TRACK run ────────────────────────────────────────────────────────────

async def run_track(role_id: int | None = None) -> dict:
    """Full pipeline analysis pass. Fires Slack alerts on issues."""
    await log_event("TRACK", "started", "Running pipeline health analysis", role_id=role_id)

    async with AsyncSessionLocal() as session:
        if role_id:
            roles_result = await session.execute(select(Role).where(Role.id == role_id))
        else:
            roles_result = await session.execute(select(Role).where(Role.status == RoleStatus.ACTIVE))
        roles = roles_result.scalars().all()

    results = {}
    for role in roles:
        health = await compute_pipeline_health(role.id)
        results[role.id] = health

        stale_cands = await get_stale_candidates(role.id)
        if stale_cands:
            msg = f"⚠️ *HIREPATH ALERT* — {len(stale_cands)} stale candidates in '{role.title}' pipeline. Action needed."
            await send_slack_alert(msg)
            await log_event("TRACK", "stale_alert", msg, role_id=role.id)

        if health.get("health_score", 100) < 40:
            msg = f"🔴 *HIREPATH* — '{role.title}' pipeline health is {health['health_score']:.0f}/100. Review urgently."
            await send_slack_alert(msg)

    await log_event("TRACK", "completed", f"Analysis done for {len(roles)} role(s)")
    return {"roles_analyzed": len(roles), "results": results}
