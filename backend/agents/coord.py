"""
COORD — Interview Coordination Agent
Finds mutual availability, sends calendar invites,
generates prep docs, sends reminders.
"""
import json
import asyncio
from html import escape
from datetime import datetime, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo
from sqlalchemy import select
from database import Candidate, Role, CandidateStage, AsyncSessionLocal
from utils.llm import groq_chat
from utils.logger import log_event
from utils.evidence import candidate_has_verifiable_evidence, normalize_source_evidence
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
        return None  # Fix #5: No fake event IDs when calendar not connected

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


# Fix #5: Use one named, timezone-aware business timezone across COORD.
IST = ZoneInfo("Asia/Kolkata")
BUSINESS_START_HOUR = 10
BUSINESS_END_HOUR = 17


def _to_ist(value: datetime) -> datetime:
    """Interpret legacy naive values as IST and normalize aware values to IST."""
    if value.tzinfo is None:
        return value.replace(tzinfo=IST)
    return value.astimezone(IST)


def find_next_slot(start_from: datetime | None = None, duration_minutes: int = 45) -> datetime:
    """Return the next weekday slot that fully fits inside IST business hours."""
    if not 15 <= duration_minutes <= 480:
        raise ValueError("Interview duration must be between 15 and 480 minutes.")

    reference = _to_ist(start_from) if start_from else datetime.now(IST) + timedelta(days=1)
    # Schedule on the next whole hour so the slot is not in progress when booked.
    dt = reference.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)

    while True:
        while dt.weekday() >= 5:
            dt = (dt + timedelta(days=1)).replace(hour=BUSINESS_START_HOUR, minute=0)

        if dt.hour < BUSINESS_START_HOUR:
            dt = dt.replace(hour=BUSINESS_START_HOUR, minute=0)

        business_end = dt.replace(hour=BUSINESS_END_HOUR, minute=0)
        if dt.hour >= BUSINESS_END_HOUR or dt + timedelta(minutes=duration_minutes) > business_end:
            dt = (dt + timedelta(days=1)).replace(hour=BUSINESS_START_HOUR, minute=0)
            continue
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
    evidence = normalize_source_evidence(candidate.source_evidence)
    if not settings.GROQ_API_KEY:
        links = "".join(
            f'<li><a href="{escape(entry["url"], quote=True)}">{escape(entry["label"])}</a></li>'
            for entry in evidence
        )
        return f"""<h3>Evidence review required: {escape(candidate.name)}</h3>
<p><strong>Role:</strong> {escape(role.title)}</p>
<p>No model-generated interview claims were created because GROQ_API_KEY is not configured. Review the live public sources before the interview.</p>
<h3>Verified public evidence</h3><ul>{links}</ul>"""

    prompt = f"""
Candidate: {candidate.name}
Role: {role.title}
Screening brief: {json.dumps(brief, indent=2)}
Verified public evidence: {json.dumps(evidence, indent=2)}

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
    if not interviewer_email or not interviewer_email.strip():
        return {"success": False, "error": "An interviewer email is required."}
    if not 15 <= duration_minutes <= 480:
        return {"success": False, "error": "Interview duration must be between 15 and 480 minutes."}

    async with AsyncSessionLocal() as session:
        candidate = await session.get(Candidate, candidate_id)
        if not candidate:
            return {"success": False, "error": "Candidate not found"}
        role = await session.get(Role, candidate.role_id)

    if not role:
        return {"success": False, "error": "Role not found"}
    if not candidate_has_verifiable_evidence(candidate):
        return {"success": False, "error": "Live, recruiter-verifiable public source evidence is required before scheduling an interview."}
    if not candidate.email:
        return {"success": False, "error": "Candidate email is required to schedule an invite."}
    if not candidate.contact_consent_at:
        return {"success": False, "error": "Recruiter-recorded contact consent is required before scheduling an invite."}

    try:
        slot_start = find_next_slot(preferred_slot, duration_minutes=duration_minutes)
    except ValueError as exc:
        return {"success": False, "error": str(exc)}
    slot_end = slot_start + timedelta(minutes=duration_minutes)

    await log_event("COORD", "scheduling_started", f"Finding slot for {candidate.name}", candidate_id=candidate_id, role_id=candidate.role_id)

    # Generate prep doc
    prep_html = await generate_prep_doc(candidate, role)

    # Create calendar event (Fix #9: run sync Google calls in thread)
    service = await asyncio.to_thread(_get_calendar_service)
    attendees = [interviewer_email]
    if candidate.email:
        attendees.append(candidate.email)

    summary = f"Interview: {candidate.name} -- {role.title}"
    event_id = await asyncio.to_thread(
        create_calendar_event,
        service, summary, slot_start, slot_end, attendees,
        f"HIREPATH auto-scheduled interview.\n\nPrep Doc:\n{prep_html[:1000]}",
    )

    # Never mark a candidate scheduled unless Google Calendar actually returned an event id.
    if not event_id:
        reason = (
            "Google Calendar is not configured. Set GOOGLE_CREDENTIALS_JSON in .env to enable interview scheduling."
            if not service
            else "Google Calendar could not create the event. Verify the Calendar credentials and try again."
        )
        await log_event("COORD", "calendar_unavailable",
                        "Google Calendar did not create an event; the interview was not booked.",
                        candidate_id=candidate_id, role_id=candidate.role_id)
        return {
            "success": False,
            "error": reason,
            "candidate": candidate.name,
            "proposed_slot": slot_start.isoformat(),
        }

    # Update candidate record
    async with AsyncSessionLocal() as session:
        c = await session.get(Candidate, candidate_id)
        c.stage = CandidateStage.INTERVIEW
        c.interview_time = slot_start
        c.calendar_event_id = event_id
        c.last_activity_at = datetime.utcnow()
        await session.commit()

    await log_event(
        "COORD", "interview_scheduled",
        f"Interview booked: {slot_start.strftime('%b %d %I:%M %p IST')}",
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
            return {"success": False, "error": "Candidate or interview time not found"}
        if not candidate_has_verifiable_evidence(c):
            return {"success": False, "error": "Live, recruiter-verifiable public source evidence is required before sending a reminder."}
        if not c.contact_consent_at:
            return {"success": False, "error": "Recruiter-recorded contact consent is required before sending a reminder."}
        role = await session.get(Role, c.role_id)

    from agents.engage import send_email_smtp
    # Format the absolute database time in the one business timezone used by COORD.
    interview_time = _to_ist(c.interview_time)
    time_str = interview_time.strftime('%B %d, %Y at %I:%M %p IST')
    subject = f"Reminder: Your interview for {role.title} is coming up"
    body = f"""<p>Hi {c.name.split()[0]},</p>
<p>This is a friendly reminder that your interview for <strong>{role.title}</strong> is scheduled for 
<strong>{time_str}</strong>.</p>
<p>Please check your calendar invite for the meeting link. Feel free to reply if you need to reschedule.</p>
<p>Good luck!</p>
<p style="font-size:11px;color:#999;margin-top:24px;border-top:1px solid #eee;padding-top:8px">If you'd prefer not to receive messages like this, reply with "unsubscribe" and we'll remove you from our list.</p>"""

    # Fix #9: Wrap sync email call in asyncio.to_thread
    sent = await asyncio.to_thread(send_email_smtp, c.email, subject, body)
    if sent:
        async with AsyncSessionLocal() as session:
            candidate = await session.get(Candidate, candidate_id)
            if candidate:
                candidate.reminder_sent_at = datetime.now(timezone.utc)
                await session.commit()
        await log_event("COORD", "reminder_sent", f"Reminder sent to {c.name}", candidate_id=candidate_id)
    return {"success": sent}


async def run_reminder_sweep(hours_before: int = 24, window_hours: int = 1) -> list[dict]:
    """Send each scheduled interview reminder once when it enters the reminder window."""
    now = datetime.now(timezone.utc)
    window_start = now + timedelta(hours=hours_before - window_hours)
    window_end = now + timedelta(hours=hours_before + window_hours)

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Candidate).where(
                Candidate.stage == CandidateStage.INTERVIEW,
                Candidate.interview_time.is_not(None),
                Candidate.reminder_sent_at.is_(None),
                Candidate.source_verified.is_(True),
            )
        )
        candidates = [candidate for candidate in result.scalars().all() if candidate_has_verifiable_evidence(candidate)]

    results = []
    for candidate in candidates:
        interview_utc = _to_ist(candidate.interview_time).astimezone(timezone.utc)
        if window_start <= interview_utc <= window_end:
            results.append(await send_reminder(candidate.id, hours_before=hours_before))
    return results
