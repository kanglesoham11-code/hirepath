"""
ENGAGE — Outreach & Nurture Agent
Sends personalized outreach emails, tracks replies,
sends follow-ups, escalates unresponsive high-priority candidates.

Fix #17 Note on Contact Data & Consent:
HirePath currently utilizes only public GitHub emails disclosed on developer profiles.
Most developers do not publish emails publicly, so ENGAGE skips profiles lacking contact info.
Before real-world outreach, implement recruiter-in-the-loop verification, explicit candidate
opt-in consent, or an enterprise email lookup service complying with data privacy laws.
"""
import smtplib
import asyncio
from html import escape
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select
from database import Candidate, Role, CandidateStage, AsyncSessionLocal
from utils.llm import groq_chat
from utils.logger import log_event
from utils.privacy import PrivacyTokenError, privacy_links
from utils.evidence import candidate_has_verifiable_evidence
from config import settings


# ── Email sending ─────────────────────────────────────────────────────────────

def send_email_smtp(to_email: str, subject: str, body_html: str) -> bool:
    """Sends via Gmail SMTP. Returns True on success."""
    if not settings.GMAIL_USER or not settings.GMAIL_APP_PASSWORD:
        print("[ENGAGE] SMTP is not configured; outreach was not sent.")
        return False  # Fix #4: Do NOT treat unconfigured as success

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
        print(f"[ENGAGE] SMTP error: {type(e).__name__}")
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
        first_name = escape(candidate.name.split()[0])
        body = f"""<p>Hi {first_name},</p>
<p>I came across your profile and think you could be a great fit for our <strong>{escape(role.title)}</strong> role.</p>
<p>{escape(role.description[:200])}...</p>
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
        body = f"""<p>Hi {escape(candidate.name.split()[0])},</p>
<p>Just following up on my previous note about the {escape(role.title)} role. I know inboxes get busy!</p>
<p>If you're open to a quick conversation, just reply 'yes'. No worries if the timing isn't right.</p>
<p>Best,<br>The Hiring Team</p>"""
        return subject, body

    prompt = f"Candidate: {candidate.name}\nRole: {role.title}\nFollow-up attempt #{attempt}. Write the follow-up email."
    body = await groq_chat([{"role": "user", "content": prompt}], system=FOLLOWUP_SYSTEM, max_tokens=250)
    return subject, body


# ── Core engage logic ─────────────────────────────────────────────────────────

def _privacy_footer(candidate_id: int) -> str:
    """Build action-specific, signed privacy links without putting PII in URLs."""
    links = privacy_links(candidate_id)
    opt_out_url = escape(links["opt_out"], quote=True)
    delete_url = escape(links["delete"], quote=True)
    return (
        '<p style="font-size:11px;color:#999;margin-top:24px;border-top:1px solid #eee;padding-top:8px">'
        f'Prefer not to receive HirePath messages? <a href="{opt_out_url}">Opt out of outreach</a> '
        f'or <a href="{delete_url}">delete your candidate data</a>.</p>'
    )

async def engage_candidate(candidate_id: int, custom_message: Optional[str] = None) -> dict:
    """Send outreach to a single candidate. Returns status dict."""
    async with AsyncSessionLocal() as session:
        candidate = await session.get(Candidate, candidate_id)
        if not candidate:
            return {"success": False, "error": "Candidate not found"}
        role = await session.get(Role, candidate.role_id)

    if not role:
        return {"success": False, "error": "Role not found"}

    if not candidate_has_verifiable_evidence(candidate):
        await log_event(
            "ENGAGE", "source_evidence_required",
            "Outreach skipped because the candidate has no live, recruiter-verifiable public source evidence.",
            candidate_id=candidate_id, role_id=candidate.role_id,
        )
        return {
            "success": False,
            "error": "Live, recruiter-verifiable public source evidence is required before outreach.",
            "candidate_id": candidate_id,
        }

    if not candidate.email:
        await log_event("ENGAGE", "skipped", "Candidate has no contact email", candidate_id=candidate_id)
        return {"success": False, "error": "No email address", "candidate_id": candidate_id}

    if not candidate.contact_consent_at:
        await log_event(
            "ENGAGE", "consent_required", "Outreach skipped until recruiter-recorded contact consent is available.",
            candidate_id=candidate_id, role_id=candidate.role_id,
        )
        return {"success": False, "error": "Recruiter-recorded contact consent is required before outreach.", "candidate_id": candidate_id}

    if candidate.stage in (CandidateStage.REJECTED, CandidateStage.HIRED):
        return {"success": False, "error": "Candidate is in a terminal stage.", "candidate_id": candidate_id}

    is_followup = candidate.outreach_count > 0
    attempt = candidate.outreach_count + 1

    if is_followup:
        subject, body = await generate_followup_email(candidate, role, attempt)
    else:
        subject, body = await generate_outreach_email(candidate, role)

    if custom_message:
        body += f"<p><em>{escape(custom_message)}</em></p>"

    try:
        body += _privacy_footer(candidate.id)
    except PrivacyTokenError as exc:
        await log_event("ENGAGE", "privacy_link_error", str(exc), candidate_id=candidate_id, role_id=candidate.role_id)
        return {"success": False, "error": "Cannot create required privacy links for outreach.", "candidate_id": candidate_id}

    # Fix #9: Run sync SMTP in thread to avoid blocking the event loop
    sent = await asyncio.to_thread(send_email_smtp, candidate.email, subject, body)

    async with AsyncSessionLocal() as session:
        c = await session.get(Candidate, candidate_id)
        # Fix #4: No state or activity changes when SMTP is unavailable or rejects the email.
        if sent and c:
            c.outreach_count = attempt
            c.last_activity_at = datetime.utcnow()
            c.last_contacted_at = datetime.utcnow()
            if c.stage in (CandidateStage.SOURCED, CandidateStage.SCREENED):
                c.stage = CandidateStage.OUTREACH
            await session.commit()

    action = ("followup_sent" if is_followup else "outreach_sent") if sent else "outreach_failed"
    await log_event(
        "ENGAGE", action,
        f"Outreach {'sent' if sent else 'failed'} (attempt #{attempt})",
        candidate_id=candidate_id, role_id=candidate.role_id,
    )

    return {
        "success": sent,
        "candidate_id": candidate_id,
        "subject": subject,
        "attempt": attempt,
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
            Candidate.stage == CandidateStage.OUTREACH,
            Candidate.last_contacted_at < cutoff,
            Candidate.outreach_count < 3,  # max 3 follow-ups
            Candidate.source_verified.is_(True),
        )
        if role_id:
            q = q.where(Candidate.role_id == role_id)
        result = await session.execute(q)
        stale = [candidate for candidate in result.scalars().all() if candidate_has_verifiable_evidence(candidate)]

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
        if not candidate_has_verifiable_evidence(c):
            return {"error": "Live, recruiter-verifiable public source evidence is required before recording a reply."}
        c.stage = CandidateStage.REPLIED
        c.last_activity_at = datetime.utcnow()
        await session.commit()
    await log_event("ENGAGE", "reply_received", f"{c.name} replied to outreach", candidate_id=candidate_id, role_id=c.role_id)
    return {"success": True, "stage": "replied"}
