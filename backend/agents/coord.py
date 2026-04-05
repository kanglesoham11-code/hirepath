"""
COORD — Interview Coordination Agent
Finds mutual availability, sends calendar invites,
generates prep docs, sends reminders.
"""
import json
import asyncio
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select
from database import Candidate, Role, CandidateStage, AsyncSessionLocal
from utils.llm import groq_chat
from utils.logger import log_event
from config import settings

# Optional Google Calendar SDK
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    HAS_GCAL = True
except ImportError:
    HAS_GCAL = False

SCOPES = ["https://www.googleapis.com/auth/calendar"]


# ── Calendar helpers ──────────────────────────────────────────────────────────

def _get_calendar_service():
    """Returns an authenticated Google Calendar service, or None if unavailable."""
    if not HAS_GCAL or not settings.GOOGLE_CREDENTIALS_JSON:
        return None
    try:
        import os
        from google.auth.transport.requests import Request
        import pickle

        creds = None
        token_path = "token.pickle"
        if os.path.exists(token_path):
            with open(token_path, "rb") as f:
                creds = pickle.load(f)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(settings.GOOGLE_CREDENTIALS_JSON, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(token_path, "wb") as f:
                pickle.dump(creds, f)
        return build("calendar", "v3", credentials=creds)
    except Exception as e:
        print(f"[COORD] Google Calendar auth error: {e}")
        return None


def create_calendar_event(
    service,
    summary: str,
    start: datetime,
    end: datetime,
    attendees: list[str],
    description: str = "",
) -> Optional[str]:
    """Creates a Google Calendar event. Returns event ID or None."""
    if not service:
        return f"mock_event_{start.strftime('%Y%m%d_%H%M')}"

    event = {
        "summary": summary,
        "description": description,
        "start": {"dateTime": start.isoformat(), "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": end.isoformat(), "timeZone": "Asia/Kolkata"},
        "attendees": [{"email": e} for e in attendees],
        "conferenceData": {
            "createRequest": {
                "requestId": f"hirepath_{start.strftime('%Y%m%d%H%M%S')}",
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        },
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "email", "minutes": 24 * 60},
                {"method": "popup", "minutes": 60},
            ],
        },
    }
    try:
        created = service.events().insert(
            calendarId="primary", body=event, conferenceDataVersion=1, sendUpdates="all"
        ).execute()
        return created.get("id")
    except Exception as e:
        print(f"[COORD] Calendar event creation error: {e}")
        return None


def find_next_slot(start_from: datetime = None, duration_minutes: int = 45) -> datetime:
    """Returns the next available weekday slot (simple round-to-next-hour logic)."""
    if not start_from:
        start_from = datetime.utcnow() + timedelta(days=1)
    # Push to business hours (9 AM – 5 PM IST = 3:30 AM – 11:30 AM UTC)
    dt = start_from.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    # Skip weekends
    while dt.weekday() >= 5:
        dt += timedelta(days=1)
    # Business hours check (UTC 4-10 ≈ IST 9:30-15:30)
    if dt.hour < 4:
        dt = dt.replace(hour=10)
    if dt.hour >= 12:
        dt = (dt + timedelta(days=1)).replace(hour=10)
    while dt.weekday() >= 5:
        dt += timedelta(days=1)
    return dt


# ── Interview prep doc generation ────────────────────────────────────────────

PREP_DOC_SYSTEM = """You are a senior engineering hiring manager at a top-tier tech company preparing an interviewer for a candidate assessment.

Generate a structured interview prep document in clean HTML that includes:

1) **Candidate Snapshot** — 3-4 bullets summarizing their background, key strengths, and notable work (reference specific repos, contributions, or experience)
2) **Areas to Probe** — 4 specific technical and behavioral areas to evaluate, directly tied to the role requirements and candidate's profile gaps
3) **Tailored Questions** — 5 numbered questions that are SPECIFIC to this candidate (e.g., "Your work on X repo uses Y pattern — how would you adapt that for Z?"). No generic questions.
4) **What Good Looks Like** — For each question, a 1-sentence description of what a strong answer demonstrates
5) **Red Flags to Watch** — 2-3 specific warning signs to look for based on this candidate's profile

Keep it to 400 words max. Use clean HTML with <h3>, <ul>, <ol>, <p>, <strong>.
Do NOT include generic boilerplate — every line should be specific to this candidate and role."""

async def generate_prep_doc(candidate: "Candidate", role: "Role") -> str:
    brief = candidate.screen_brief or {}
    if not settings.GROQ_API_KEY:
        return f"""<h3>Interview Prep: {candidate.name}</h3>
<p><strong>Role:</strong> {role.title}</p>
<h3>Key areas to probe</h3>
<ul><li>Technical depth in role requirements</li><li>System design experience</li><li>Team collaboration</li></ul>
<h3>Suggested questions</h3>
<ol>
  <li>Walk me through your most complex backend project.</li>
  <li>How have you approached scaling challenges?</li>
  <li>Describe a time you disagreed with a technical decision.</li>
  <li>What does good code review look like to you?</li>
</ol>"""

    prompt = f"""
Candidate: {candidate.name}
Role: {role.title}
Screening brief: {json.dumps(brief, indent=2)}

Generate the interview prep doc HTML.
"""
    return await groq_chat([{"role": "user", "content": prompt}], system=PREP_DOC_SYSTEM, max_tokens=600)


# ── Core coord logic ──────────────────────────────────────────────────────────

async def schedule_interview(
    candidate_id: int,
    interviewer_email: str,
    duration_minutes: int = 45,
    preferred_slot: Optional[datetime] = None,
) -> dict:
    """Full scheduling flow for one candidate."""
    async with AsyncSessionLocal() as session:
        candidate = await session.get(Candidate, candidate_id)
        if not candidate:
            return {"success": False, "error": "Candidate not found"}
        role = await session.get(Role, candidate.role_id)

    slot_start = preferred_slot or find_next_slot(duration_minutes=duration_minutes)
    slot_end = slot_start + timedelta(minutes=duration_minutes)

    await log_event("COORD", "scheduling_started", f"Finding slot for {candidate.name}", candidate_id=candidate_id, role_id=candidate.role_id)

    # Generate prep doc
    prep_html = await generate_prep_doc(candidate, role)

    # Create calendar event
    service = _get_calendar_service()
    attendees = [interviewer_email]
    if candidate.email:
        attendees.append(candidate.email)

    summary = f"Interview: {candidate.name} — {role.title}"
    event_id = create_calendar_event(
        service=service,
        summary=summary,
        start=slot_start,
        end=slot_end,
        attendees=attendees,
        description=f"HIREPATH auto-scheduled interview.\n\nPrep Doc:\n{prep_html[:1000]}",
    )

    # Update candidate record
    async with AsyncSessionLocal() as session:
        c = await session.get(Candidate, candidate_id)
        c.stage = CandidateStage.INTERVIEW_SCHEDULED
        c.interview_time = slot_start
        c.calendar_event_id = event_id
        c.last_activity_at = datetime.utcnow()
        await session.commit()

    await log_event(
        "COORD", "interview_scheduled",
        f"Interview booked: {slot_start.strftime('%b %d %H:%M UTC')} with {interviewer_email}",
        data={"event_id": event_id, "slot": slot_start.isoformat()},
        candidate_id=candidate_id,
        role_id=candidate.role_id,
    )

    return {
        "success": True,
        "candidate": candidate.name,
        "slot_start": slot_start.isoformat(),
        "slot_end": slot_end.isoformat(),
        "duration_minutes": duration_minutes,
        "calendar_event_id": event_id,
        "attendees": attendees,
        "prep_doc_html": prep_html,
    }


async def send_reminder(candidate_id: int, hours_before: int = 24) -> dict:
    """Send reminder email to candidate."""
    async with AsyncSessionLocal() as session:
        c = await session.get(Candidate, candidate_id)
        if not c or not c.email or not c.interview_time:
            return {"success": False}
        role = await session.get(Role, c.role_id)

    from agents.engage import send_email_smtp
    subject = f"Reminder: Your interview for {role.title} is coming up"
    body = f"""<p>Hi {c.name.split()[0]},</p>
<p>This is a friendly reminder that your interview for <strong>{role.title}</strong> is scheduled for 
<strong>{c.interview_time.strftime('%B %d, %Y at %H:%M UTC')}</strong>.</p>
<p>Please check your calendar invite for the meeting link. Feel free to reply if you need to reschedule.</p>
<p>Good luck!</p>"""

    sent = send_email_smtp(c.email, subject, body)
    await log_event("COORD", "reminder_sent", f"Reminder sent to {c.name}", candidate_id=candidate_id)
    return {"success": sent}
