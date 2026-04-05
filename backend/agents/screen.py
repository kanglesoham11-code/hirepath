"""
SCREEN — Resume Intelligence Agent
Reads resumes (PDF) and GitHub profiles, extracts structured data,
scores candidates, generates interview briefs.
"""
import io
import logging
import httpx
from sqlalchemy import select
from database import Candidate, Role, CandidateStage, AsyncSessionLocal
from utils.llm import groq_json
from utils.logger import log_event
from config import settings

logger = logging.getLogger("hirepath.screen")

# Optional PDF parsing
try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False


# ── PDF text extraction ───────────────────────────────────────────────────────

def extract_text_from_pdf(path_or_bytes: str | bytes) -> str:
    if not HAS_FITZ:
        return "[PyMuPDF not installed — install with: pip install PyMuPDF]"
    if isinstance(path_or_bytes, bytes):
        doc = fitz.open(stream=path_or_bytes, filetype="pdf")
    else:
        doc = fitz.open(path_or_bytes)
    text = "\n".join(page.get_text() for page in doc)
    doc.close()
    return text[:8000]  # trim to model context limit


# ── GitHub profile enrichment ─────────────────────────────────────────────────

async def fetch_github_profile_text(github_url: str) -> str:
    """Returns a plain-text summary of a GitHub user's top repos."""
    if not github_url:
        return ""
    login = github_url.rstrip("/").split("/")[-1]
    headers = {"Accept": "application/vnd.github+json"}
    if settings.GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"
    
    lines = []
    async with httpx.AsyncClient(timeout=15) as client:
        # User profile
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
1. Only credit skills and experience that are DEMONSTRABLY shown in the candidate's profile (repos, bio, contributions, resume).
2. Do NOT hallucinate or assume skills not evidenced in the data.
3. Interview questions must be SPECIFIC to this candidate's background — no generic questions.
4. If data is insufficient, say so explicitly rather than guessing.

Your response must be a valid JSON object with exactly these keys:
{
  "overall_score": <int 0-100, evidence-based>,
  "years_experience": <int or null if unknown>,
  "top_skills": <list of strings — only skills with evidence>,
  "skill_gaps": <list of strings — specific skills required by the role but missing from profile>,
  "strengths": <list of max 4 strings — specific, evidence-backed, e.g. "Contributed 47 commits to tiangolo/fastapi">,
  "concerns": <list of max 4 strings — specific concerns, e.g. "No evidence of async Python experience">,
  "red_flags": <list of strings — any dealbreakers found>,
  "suggested_interview_questions": <list of exactly 4 strings — tailored to THIS candidate's specific background>,
  "one_line_verdict": <string, max 20 words — crisp assessment>,
  "hire_recommendation": <string: "strong_yes" | "yes" | "maybe" | "no">
}

Scoring rubric:
- 85-100: Exceptional. Deep expertise in most/all required skills, strong evidence of impact.
- 70-84: Strong. Clear evidence of core skills, minor gaps, would be productive quickly.
- 55-69: Moderate. Some relevant skills but significant gaps. Worth interviewing if pipeline is thin.
- 40-54: Weak. Limited relevant evidence. Only consider if desperate.
- 0-39: No match. Skip."""

SCREEN_REQUIRED_KEYS = [
    "overall_score", "top_skills", "skill_gaps", "strengths",
    "concerns", "suggested_interview_questions", "one_line_verdict",
    "hire_recommendation"
]

async def screen_candidate(candidate_id: int) -> dict:
    """Full screening pass on a single candidate. Returns the brief dict."""
    async with AsyncSessionLocal() as session:
        candidate = await session.get(Candidate, candidate_id)
        if not candidate:
            return {"error": f"Candidate {candidate_id} not found"}
        role = await session.get(Role, candidate.role_id)

    profile_text = ""

    # 1. Resume PDF if available
    if candidate.resume_path:
        try:
            resume_text = extract_text_from_pdf(candidate.resume_path)
            profile_text += f"\n--- RESUME ---\n{resume_text}"
        except Exception as e:
            profile_text += f"\n[Resume parse error: {e}]"

    # 2. GitHub profile
    if candidate.github_url:
        try:
            gh_text = await fetch_github_profile_text(candidate.github_url)
            profile_text += f"\n--- GITHUB PROFILE ---\n{gh_text}"
        except Exception as e:
            logger.warning(f"GitHub fetch failed for {candidate.name}: {e}")
            profile_text += f"\n[GitHub profile fetch error]"

    # 3. Existing scout data
    if candidate.screen_brief:
        sb = candidate.screen_brief
        profile_text += f"\n--- SCOUT NOTES ---\nSummary: {sb.get('scout_summary','')}\nStrengths: {sb.get('strengths','')}\nConcerns: {sb.get('concerns','')}"

    if not profile_text.strip():
        profile_text = f"Candidate name: {candidate.name}\nSource: {candidate.source}\n[Limited data available — score conservatively]"

    prompt = f"""## Role
Title: {role.title}
Requirements: {role.requirements or role.description}

## Candidate
Name: {candidate.name}
Source: {candidate.source}
{profile_text}

Produce the screening brief as a JSON object. Be specific and evidence-based.
If candidate data is limited, reflect that in a conservative score and note the data gap in concerns."""

    await log_event("SCREEN", "screening_started", f"Screening {candidate.name}", candidate_id=candidate_id, role_id=candidate.role_id)

    if not settings.GROQ_API_KEY:
        brief = {
            "overall_score": candidate.score or 50,
            "years_experience": None,
            "top_skills": [],
            "skill_gaps": [],
            "strengths": ["GROQ_API_KEY not set"],
            "concerns": [],
            "red_flags": [],
            "suggested_interview_questions": [
                "Tell me about your most complex backend project.",
                "How have you handled scaling challenges?",
                "Describe a technical mistake and what you learned.",
                "Why are you interested in this role?"
            ],
            "one_line_verdict": "LLM unavailable — set GROQ_API_KEY",
            "hire_recommendation": "maybe"
        }
    else:
        try:
            brief = await groq_json(
                [{"role": "user", "content": prompt}],
                system=SCREEN_SYSTEM,
                required_keys=SCREEN_REQUIRED_KEYS,
                max_tokens=2048,
            )
            
            # Post-process and validate the brief
            brief = _validate_screen_brief(brief, candidate)
            
        except Exception as e:
            logger.error(f"Screen failed for {candidate.name}: {e}")
            await log_event("SCREEN", "error", str(e), candidate_id=candidate_id)
            return {"error": str(e)}

    # Persist brief and update score
    async with AsyncSessionLocal() as session:
        c = await session.get(Candidate, candidate_id)
        c.screen_brief = brief
        c.score = float(brief.get("overall_score", c.score or 50))
        c.stage = CandidateStage.SCREENED
        import datetime
        c.last_activity_at = datetime.datetime.utcnow()
        await session.commit()

    await log_event("SCREEN", "screening_complete", f"Score: {brief.get('overall_score')} | {brief.get('one_line_verdict')}", data={"score": brief.get("overall_score"), "recommendation": brief.get("hire_recommendation")}, candidate_id=candidate_id, role_id=candidate.role_id)
    return brief


def _validate_screen_brief(brief: dict, candidate) -> dict:
    """Validate and sanitize the screening brief to ensure data integrity."""
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
    
    # Ensure string fields
    if not isinstance(brief.get("one_line_verdict"), str):
        brief["one_line_verdict"] = str(brief.get("one_line_verdict", "Assessment pending"))
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
    
    # Ensure years_experience is int or null
    ye = brief.get("years_experience")
    if ye is not None:
        try:
            brief["years_experience"] = int(ye)
        except (ValueError, TypeError):
            brief["years_experience"] = None
    
    return brief


async def screen_all_sourced(role_id: int) -> list[dict]:
    """Screen every SOURCED candidate in a role."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Candidate).where(Candidate.role_id == role_id, Candidate.stage == CandidateStage.SOURCED)
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
