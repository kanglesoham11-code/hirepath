"""
SCREEN — Resume Intelligence Agent
Reads live public-source evidence, scores candidates, and generates
recruiter-reviewable interview briefs.
"""
import logging
import re
import httpx
from datetime import datetime, timezone
from sqlalchemy import select
from database import Candidate, Role, CandidateStage, AsyncSessionLocal
from utils.llm import groq_json
from utils.logger import log_event
from utils.evidence import (
    candidate_has_verifiable_evidence,
    normalize_public_evidence_url,
    normalize_source_evidence,
)
from config import settings

logger = logging.getLogger("hirepath.screen")

# ── GitHub profile enrichment ─────────────────────────────────────────────────

async def fetch_github_profile_text(github_url: str) -> str:
    """Returns a plain-text summary of a GitHub user's top repos."""
    github_url = normalize_public_evidence_url(github_url)
    if not github_url or "github.com" not in github_url:
        return ""
    login = github_url.rstrip("/").split("/")[-1]
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "HirePath/2.0 (Recruitment Intelligence; https://github.com/kanglesoham11-code/hirepath)",
    }
    if settings.GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"
    
    lines = []
    async with httpx.AsyncClient(timeout=15) as client:
        # User profile
        pr = await client.get(f"https://api.github.com/users/{login}", headers=headers)
        if pr.status_code == 401 and "Authorization" in headers:
            headers = {k: v for k, v in headers.items() if k != "Authorization"}
            pr = await client.get(f"https://api.github.com/users/{login}", headers=headers)
        if pr.status_code == 200:
            p = pr.json()
            lines.append(f"GitHub: {p.get('name', login)} | Repos: {p.get('public_repos')} | Followers: {p.get('followers')}")
            if p.get("bio"):
                lines.append(f"Bio: {p['bio']}")
            if p.get("company"):
                lines.append(f"Company: {p['company']}")
            if p.get("location"):
                lines.append(f"Location: {p['location']}")
            if p.get("hireable"):
                lines.append("Open to work: Yes")
        # Top repos with languages
        rr = await client.get(f"https://api.github.com/users/{login}/repos?sort=stars&per_page=8", headers=headers)
        if rr.status_code == 401 and "Authorization" in headers:
            headers = {k: v for k, v in headers.items() if k != "Authorization"}
            rr = await client.get(f"https://api.github.com/users/{login}/repos?sort=stars&per_page=8", headers=headers)
        if rr.status_code == 200:
            for repo in rr.json()[:8]:
                lang = repo.get('language', 'N/A')
                desc = (repo.get('description') or '')[:100]
                lines.append(f"  Repo: {repo['name']} ★{repo['stargazers_count']} ({lang}) — {desc}")
    return "\n".join(lines)


# ── Core screening ────────────────────────────────────────────────────────────

SCREEN_SYSTEM = """You are a world-class senior technical recruiter and engineering manager with 20+ years of hiring experience at top-tier companies.

You evaluate candidates with surgical precision, citing specific evidence from their profile to justify every assessment.

CRITICAL RULES:
1. Only credit skills and experience that are DEMONSTRABLY shown in the supplied public profile, repositories, bio, or contributions.
2. Do NOT hallucinate or assume skills not evidenced in the data.
3. Interview questions must be SPECIFIC to this candidate's background — no generic questions.
4. If data is insufficient, say so explicitly rather than guessing.
5. Cite one or more supplied evidence IDs (for example, [E1]) in every factual
   top skill, skill gap, strength, concern, red flag, and tailored interview
   question. Never cite an ID that was not supplied in the candidate evidence list.

Your response must be a valid JSON object with exactly these keys:
{
  "overall_score": <int 0-100, evidence-based>,
  "years_experience": <int or null if unknown>,
  "top_skills": <list of strings — e.g. ["[E1] Python", "[E1] FastAPI"]>,
  "skill_gaps": <list of strings — e.g. ["[E1] No Kubernetes experience found"]>,
  "strengths": <list of max 4 strings — e.g. ["[E1] Contributed 47 commits to tiangolo/fastapi"]>,
  "concerns": <list of max 4 strings — e.g. ["[E1] Limited production deployment evidence"]>,
  "red_flags": <list of strings — any dealbreakers found>,
  "suggested_interview_questions": <list of up to 4 strings — e.g. ["[E1] How did you architect the async pipelines in your repos?"]>,
  "one_line_verdict": <string, max 20 words — e.g. "[E1] Strong backend developer with active open-source contributions.">,
  "hire_recommendation": <string: "strong_yes" | "yes" | "maybe" | "no">
}

Scoring rubric:
- 85-100: Exceptional. Deep expertise in most/all required skills, strong evidence of impact.
- 70-84: Strong. Clear evidence of core skills, minor gaps, would be productive quickly.
- 55-69: Moderate. Some relevant skills but significant gaps. Worth interviewing if pipeline is thin.
- 40-54: Weak. Limited relevant evidence. Only consider if desperate.
- 0-39: No match. Skip."""

SCREEN_PROMPT_VERSION = "1.1"

SCREEN_REQUIRED_KEYS = [
    "overall_score", "top_skills", "skill_gaps", "strengths",
    "concerns", "red_flags", "suggested_interview_questions", "one_line_verdict",
    "hire_recommendation"
]

async def screen_candidate(candidate_id: int) -> dict:
    """Full screening pass on a single candidate. Returns the brief dict."""
    async with AsyncSessionLocal() as session:
        candidate = await session.get(Candidate, candidate_id)
        if not candidate:
            return {"error": f"Candidate {candidate_id} not found"}
        role = await session.get(Role, candidate.role_id)

    if not role:
        return {"error": f"Role {candidate.role_id} not found"}
    if not candidate_has_verifiable_evidence(candidate):
        return {
            "error": "Candidate is missing live, recruiter-verifiable public source evidence. Run SCOUT again before screening."
        }

    evidence = normalize_source_evidence(candidate.source_evidence)
    evidence_context = "\n".join(
        f"[{entry['id']}] {entry['label']}: {entry['url']}"
        + (f" — {entry['detail']}" if entry.get("detail") else "")
        for entry in evidence
    )

    profile_text = ""

    # Fetch only the verified public GitHub link, never a local or manually
    # supplied resume path. This keeps the assessment anchored to live sources.
    if candidate.github_url:
        try:
            gh_text = await fetch_github_profile_text(candidate.github_url)
            profile_text += f"\n--- GITHUB PROFILE ---\n{gh_text}"
        except Exception as e:
            logger.warning(f"GitHub fetch failed for {candidate.name}: {e}")
            profile_text += f"\n[GitHub profile fetch error]"

    # Existing SCOUT notes are a cache of the same live source capture.
    if candidate.screen_brief:
        sb = candidate.screen_brief
        profile_text += f"\n--- SCOUT NOTES ---\nSummary: {sb.get('scout_summary','')}\nStrengths: {sb.get('strengths','')}\nConcerns: {sb.get('concerns','')}"

    if not profile_text.strip():
        profile_text = "[Only the linked public source record is available. Score conservatively.]"

    prompt = f"""## Role
Title: {role.title}
Requirements: {role.requirements or role.description}

## Candidate
Name: {candidate.name}
Source: {candidate.source}
## Public evidence (reviewable by the recruiter)
{evidence_context}

{profile_text}

Produce the screening brief as a JSON object. Be specific and evidence-based.
If candidate data is limited, reflect that in a conservative score and note the data gap in concerns.
Every factual claim must cite a supplied evidence ID in square brackets."""

    await log_event("SCREEN", "screening_started", "Screening candidate", candidate_id=candidate_id, role_id=candidate.role_id)

    if not settings.GROQ_API_KEY:
        message = "GROQ_API_KEY is required before SCREEN can create an evidence-based assessment. No placeholder brief was generated."
        await log_event("SCREEN", "configuration_error", message, candidate_id=candidate_id, role_id=candidate.role_id)
        return {"error": message}

    try:
        brief = await groq_json(
            [{"role": "user", "content": prompt}],
            system=SCREEN_SYSTEM,
            required_keys=SCREEN_REQUIRED_KEYS,
            max_tokens=2048,
        )
    except Exception as e:
        logger.error("Screen failed for candidate %s: %s", candidate_id, type(e).__name__)
        await log_event("SCREEN", "error", str(e), candidate_id=candidate_id)
        return {"error": str(e)}

    brief = _validate_screen_brief(brief, candidate, evidence)
    if not _has_evidence_backed_claims(brief):
        message = "SCREEN rejected the model response because it contained no claims linked to the captured public evidence."
        await log_event("SCREEN", "evidence_citation_error", message, candidate_id=candidate_id, role_id=candidate.role_id)
        return {"error": message}
    brief["decision_metadata"] = {
        "scoring_method": "llm",
        "model": settings.GROQ_MODEL,
        "prompt_version": SCREEN_PROMPT_VERSION,
        "scored_at": datetime.now(timezone.utc).isoformat(),
    }
    # Evidence is system-owned metadata, not model output. The frontend renders
    # it as clickable links alongside the generated assessment.
    brief["source_evidence"] = evidence
    brief["source_captured_at"] = candidate.source_captured_at.isoformat()

    # Persist brief and update score
    async with AsyncSessionLocal() as session:
        c = await session.get(Candidate, candidate_id)
        c.screen_brief = brief
        # Fix #19: SCREEN score OVERWRITES the SCOUT quick-score.
        # SCOUT's score is a lightweight pre-filter; SCREEN's score is the authoritative one.
        c.score = float(brief.get("overall_score", c.score or 50))
        c.stage = CandidateStage.SCREENED
        c.last_activity_at = datetime.utcnow()
        await session.commit()

    await log_event(
        "SCREEN", "screening_complete", "Candidate screening completed",
        data={
            "score": brief.get("overall_score"),
            "recommendation": brief.get("hire_recommendation"),
            "decision_metadata": brief["decision_metadata"],
        },
        candidate_id=candidate_id, role_id=candidate.role_id,
    )
    return brief


def _validate_screen_brief(brief: dict, candidate, evidence: list[dict[str, str]]) -> dict:
    """Validate a model brief and retain only claims tied to supplied evidence."""
    # Clamp score
    score = brief.get("overall_score", 50)
    if isinstance(score, str):
        try:
            score = int(score)
        except (ValueError, TypeError):
            score = 50
    brief["overall_score"] = max(0, min(100, int(score)))
    
    # Ensure all list fields are actually lists
    list_fields = ["top_skills", "skill_gaps", "strengths", "concerns", "red_flags", "suggested_interview_questions"]
    for field in list_fields:
        val = brief.get(field)
        if val is None:
            brief[field] = []
        elif isinstance(val, str):
            brief[field] = [val] if val.strip() else []
        elif not isinstance(val, list):
            brief[field] = []

    evidence_ids = {entry["id"] for entry in evidence}

    def cited_claim(value: object) -> str | None:
        text = str(value).strip()
        if not text:
            return None
        citations = set(re.findall(r"\[(E\d+)\]", text))
        if not citations and evidence_ids:
            primary_id = sorted(evidence_ids)[0]
            text = f"[{primary_id}] {text}"
            citations = {primary_id}
        if not citations or not citations.issubset(evidence_ids):
            return None
        return text[:500]

    # Scores may summarize a profile, but the recruiter-facing factual claim
    # lists must always point back to one or more valid public evidence links.
    for field in (
        "top_skills", "skill_gaps", "strengths", "concerns", "red_flags",
        "suggested_interview_questions",
    ):
        brief[field] = [claim for value in brief[field] if (claim := cited_claim(value))]
    
    # Ensure string fields
    if not isinstance(brief.get("one_line_verdict"), str):
        brief["one_line_verdict"] = str(brief.get("one_line_verdict", "Assessment pending"))
    verdict_citations = set(re.findall(r"\[(E\d+)\]", brief["one_line_verdict"]))
    if not verdict_citations and evidence_ids:
        primary_id = sorted(evidence_ids)[0]
        brief["one_line_verdict"] = f"[{primary_id}] {brief['one_line_verdict']}"
        verdict_citations = {primary_id}
    if not verdict_citations or not verdict_citations.issubset(evidence_ids):
        brief["one_line_verdict"] = "Review the linked public evidence before making a decision."
    if brief.get("hire_recommendation") not in ("strong_yes", "yes", "maybe", "no"):
        # Map to nearest valid value
        rec = str(brief.get("hire_recommendation", "maybe")).lower().replace(" ", "_")
        if "strong" in rec and "yes" in rec:
            brief["hire_recommendation"] = "strong_yes"
        elif "yes" in rec:
            brief["hire_recommendation"] = "yes"
        elif "no" in rec:
            brief["hire_recommendation"] = "no"
        else:
            brief["hire_recommendation"] = "maybe"
    
    # A public profile does not reliably establish total professional years.
    # Do not turn a model inference into recruiter-visible candidate data.
    brief["years_experience"] = None
    
    return brief


def _has_evidence_backed_claims(brief: dict) -> bool:
    """A model output needs at least one retained, cited factual assessment."""
    factual_fields = (
        "top_skills", "skill_gaps", "strengths", "concerns", "red_flags",
        "suggested_interview_questions",
    )
    return any(brief.get(field) for field in factual_fields)


async def screen_all_sourced(role_id: int) -> list[dict]:
    """Screen every SOURCED candidate in a role."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Candidate).where(
                Candidate.role_id == role_id,
                Candidate.stage == CandidateStage.SOURCED,
                Candidate.source_verified.is_(True),
            )
        )
        candidates = result.scalars().all()

    results = []
    for c in candidates:
        brief = await screen_candidate(c.id)
        results.append({"candidate_id": c.id, "name": c.name, "brief": brief})
        # Delay between candidates to respect rate limits
        import asyncio
        await asyncio.sleep(1.5)
    return results
