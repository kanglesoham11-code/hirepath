"""
ENGAGE — Outreach & Nurture Agent
Sends personalized outreach emails, tracks replies,
sends follow-ups, escalates unresponsive high-priority candidates.
"""
import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select
from database import Candidate, Role, CandidateStage, AsyncSessionLocal
from utils.llm import groq_chat
from utils.logger import log_event
from config import settings


# ── Email sending ─────────────────────────────────────────────────────────────

def send_email_smtp(to_email: str, subject: str, body_html: str) -> bool:
    """Sends via Gmail SMTP. Returns True on success."""
    if not settings.GMAIL_USER or not settings.GMAIL_APP_PASSWORD:
        print(f"[ENGAGE] SMTP not configured. Would send to {to_email}: {subject}")
        return True  # treat as success in dev mode

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.GMAIL_USER
        msg["To"] = to_email
        msg.attach(MIMEText(body_html, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(settings.GMAIL_USER, settings.GMAIL_APP_PASSWORD)
            server.sendmail(settings.GMAIL_USER, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"[ENGAGE] SMTP error: {e}")
        return False


# ── Personalized email generation ─────────────────────────────────────────────

OUTREACH_SYSTEM = """You are a world-class recruiter at a top technology company writing highly personalized outreach.
You have a 40%+ response rate because your emails feel genuinely human and insightful.

Write a concise email (150-200 words) that:
- Opens with a SPECIFIC observation about the candidate's work (name an actual repo, contribution, or bio detail) — NOT generic flattery
- Briefly explains why this specific role matches their demonstrated expertise
- Keeps the tone warm, conversational, and genuinely curious — never corporate or templated
- Ends with a single, low-friction CTA: just reply 'interested' or 'not right now'
- Uses their first name naturally

Do NOT:
- Use phrases like 'I came across your profile' or 'I was impressed by'
- Be generic — every sentence should only apply to THIS candidate
- Use exclamation marks excessively
- Mention salary or benefits

Return only the email body HTML (no subject line). Use <p> tags.
"""

async def generate_outreach_email(candidate: "Candidate", role: "Role") -> tuple[str, str]:
    """Returns (subject, html_body)."""
    profile_hint = ""
    if candidate.github_url:
        profile_hint = f"GitHub: {candidate.github_url}"
    if candidate.screen_brief:
        strengths = candidate.screen_brief.get("strengths", [])
        profile_hint += f"\nTop strengths: {', '.join(strengths[:2])}"

    subject = f"Quick note — {role.title} opportunity"

    if not settings.GROQ_API_KEY:
        body = f"""<p>Hi {candidate.name.split()[0]},</p>
<p>I came across your profile and think you could be a great fit for our <strong>{role.title}</strong> role.</p>
<p>{role.description[:200]}...</p>
<p>Would you be open to a quick chat? Just reply with a simple 'yes' or 'no' — no pressure either way.</p>
<p>Best,<br>The Hiring Team</p>"""
        return subject, body

    prompt = f"""
Candidate: {candidate.name}
{profile_hint}

Role: {role.title}
Company context: {role.description[:300]}

Write the outreach email body HTML.
"""
    body = await groq_chat([{"role": "user", "content": prompt}], system=OUTREACH_SYSTEM, max_tokens=400)
    return subject, body


FOLLOWUP_SYSTEM = """You are a recruiter sending a brief, friendly follow-up email.
Keep it to 3-4 sentences. Reference that this is a follow-up.
Acknowledge they might be busy. Renew the CTA clearly.
Return only the email body HTML using <p> tags.
"""

async def generate_followup_email(candidate: "Candidate", role: "Role", attempt: int) -> tuple[str, str]:
    subject = f"Following up — {role.title}"
    if not settings.GROQ_API_KEY:
        body = f"""<p>Hi {candidate.name.split()[0]},</p>
<p>Just following up on my previous note about the {role.title} role. I know inboxes get busy!</p>
<p>If you're open to a quick conversation, just reply 'yes'. No worries if the timing isn't right.</p>
<p>Best,<br>The Hiring Team</p>"""
        return subject, body

    prompt = f"Candidate: {candidate.name}\nRole: {role.title}\nFollow-up attempt #{attempt}. Write the follow-up email."
    body = await groq_chat([{"role": "user", "content": prompt}], system=FOLLOWUP_SYSTEM, max_tokens=250)
    return subject, body


# ── Core engage logic ─────────────────────────────────────────────────────────

async def engage_candidate(candidate_id: int, custom_message: Optional[str] = None) -> dict:
    """Send outreach to a single candidate. Returns status dict."""
    async with AsyncSessionLocal() as session:
        candidate = await session.get(Candidate, candidate_id)
        if not candidate:
            return {"success": False, "error": "Candidate not found"}
        role = await session.get(Role, candidate.role_id)

    if not candidate.email:
        await log_event("ENGAGE", "skipped", f"No email for {candidate.name}", candidate_id=candidate_id)
        return {"success": False, "error": "No email address", "candidate": candidate.name}

    is_followup = candidate.outreach_count > 0
    attempt = candidate.outreach_count + 1

    if is_followup:
        subject, body = await generate_followup_email(candidate, role, attempt)
    else:
        subject, body = await generate_outreach_email(candidate, role)

    if custom_message:
        body += f"<p><em>{custom_message}</em></p>"

    sent = send_email_smtp(candidate.email, subject, body)

    async with AsyncSessionLocal() as session:
        c = await session.get(Candidate, candidate_id)
        c.outreach_count = attempt
        c.last_contacted_at = datetime.utcnow()
        c.last_activity_at = datetime.utcnow()
        if c.stage == CandidateStage.SOURCED or c.stage == CandidateStage.SCREENED:
            c.stage = CandidateStage.OUTREACH_SENT
        await session.commit()

    action = "followup_sent" if is_followup else "outreach_sent"
    await log_event("ENGAGE", action, f"Email {'sent' if sent else 'failed'} to {candidate.name} <{candidate.email}> (attempt #{attempt})", candidate_id=candidate_id, role_id=candidate.role_id)

    return {
        "success": sent,
        "candidate": candidate.name,
        "email": candidate.email,
        "subject": subject,
        "attempt": attempt,
        "body_preview": body[:200]
    }


async def engage_bulk(candidate_ids: list[int], custom_message: Optional[str] = None) -> list[dict]:
    """Engage multiple candidates concurrently (with rate limiting)."""
    results = []
    for cid in candidate_ids:
        result = await engage_candidate(cid, custom_message)
        results.append(result)
        await asyncio.sleep(1)  # basic rate limit: 1 email/sec
    return results


async def run_followup_sweep(role_id: Optional[int] = None, follow_up_after_hours: int = 48) -> list[dict]:
    """
    Finds candidates who haven't replied after N hours and sends follow-ups.
    Called by scheduler / TRACK agent.
    """
    cutoff = datetime.utcnow() - timedelta(hours=follow_up_after_hours)
    async with AsyncSessionLocal() as session:
        q = select(Candidate).where(
            Candidate.stage == CandidateStage.OUTREACH_SENT,
            Candidate.last_contacted_at < cutoff,
            Candidate.outreach_count < 3,  # max 3 follow-ups
        )
        if role_id:
            q = q.where(Candidate.role_id == role_id)
        result = await session.execute(q)
        stale = result.scalars().all()

    results = []
    for c in stale:
        res = await engage_candidate(c.id)
        results.append(res)
    return results


async def mark_replied(candidate_id: int) -> dict:
    """Called when a reply webhook fires."""
    async with AsyncSessionLocal() as session:
        c = await session.get(Candidate, candidate_id)
        if not c:
            return {"error": "Not found"}
        c.stage = CandidateStage.REPLIED
        c.last_activity_at = datetime.utcnow()
        await session.commit()
    await log_event("ENGAGE", "reply_received", f"{c.name} replied to outreach", candidate_id=candidate_id, role_id=c.role_id)
    return {"success": True, "stage": "replied"}
