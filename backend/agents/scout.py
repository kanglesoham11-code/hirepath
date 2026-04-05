"""
SCOUT — Sourcing Agent (Enhanced)
Sources candidates from GitHub, runs multi-source email discovery,
scores against job requirements via Groq LLM, deduplicates, saves to pipeline.
"""
import httpx
import asyncio
import logging
from typing import AsyncGenerator
from sqlalchemy import select
from database import Candidate, Role, CandidateStage, AsyncSessionLocal
from utils.llm import groq_json
from utils.logger import log_event
from utils.email_hunter import discover_email
from config import settings

logger = logging.getLogger("hirepath.scout")
GITHUB_API = "https://api.github.com"
SCORE_REQUIRED_KEYS = ["score", "summary", "strengths", "concerns"]
_github_auth_enabled = True

async def _github_headers() -> dict:
    global _github_auth_enabled
    h = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if settings.GITHUB_TOKEN and _github_auth_enabled:
        h["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"
    return h

async def _github_get_json(client: httpx.AsyncClient, url: str, params: dict | None = None):
    global _github_auth_enabled
    headers = await _github_headers()
    resp = await client.get(url, headers=headers, params=params)
    if resp.status_code == 200:
        return resp.json()

    if settings.GITHUB_TOKEN and _github_auth_enabled and resp.status_code == 401:
        _github_auth_enabled = False
        logger.warning("GitHub token rejected for %s; retrying without authentication", url)
        fallback_headers = {k: v for k, v in headers.items() if k.lower() != "authorization"}
        retry = await client.get(url, headers=fallback_headers, params=params)
        if retry.status_code == 200:
            return retry.json()
        resp = retry

    logger.warning("GitHub request failed for %s with status %s", url, resp.status_code)
    return None

async def search_github_users(keywords: list, max_results: int = 15) -> list:
    query = " ".join(keywords[:4])
    url = f"{GITHUB_API}/search/users"
    candidates = []
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            data = await _github_get_json(
                client,
                url,
                params={
                    "q": f"{query} type:user".strip(),
                    "per_page": min(max_results, 30),
                    "sort": "repositories",
                },
            )
            if not data:
                return []
            items = data.get("items", [])
            for item in items[:max_results]:
                profile = {}
                profile_data = await _github_get_json(client, item.get("url", ""))
                if isinstance(profile_data, dict):
                    profile = profile_data

                repos_data = []
                repos = await _github_get_json(
                    client,
                    f"{GITHUB_API}/users/{item.get('login')}/repos",
                    params={"sort": "stars", "per_page": 5},
                )
                if isinstance(repos, list):
                    for repo in repos[:5]:
                        repos_data.append({"name": repo.get("name"), "stars": repo.get("stargazers_count", 0), "language": repo.get("language"), "description": (repo.get("description") or "")[:100]})
                candidates.append({
                    "name": profile.get("name") or item.get("login", ""),
                    "github_url": item.get("html_url", ""),
                    "email": profile.get("email"),
                    "location": profile.get("location"),
                    "bio": profile.get("bio"),
                    "company": profile.get("company"),
                    "public_repos": profile.get("public_repos", 0),
                    "followers": profile.get("followers", 0),
                    "hireable": profile.get("hireable"),
                    "top_repos": repos_data,
                    "source": "github",
                    "raw": profile,
                })
    except Exception as e:
        logger.error(f"GitHub search error: {e}")
        return []
    return candidates

async def search_github_repo_contributors(repo: str, max_results: int = 10) -> list:
    url = f"{GITHUB_API}/repos/{repo}/contributors?per_page={max_results}"
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            items = await _github_get_json(client, url)
            if not items:
                return []
            candidates = []
            for item in items:
                profile = {}
                profile_data = await _github_get_json(client, item.get("url", ""))
                if isinstance(profile_data, dict):
                    profile = profile_data
                candidates.append({
                    "name": profile.get("name") or item.get("login", ""),
                    "github_url": item.get("html_url", ""),
                    "email": profile.get("email"),
                    "bio": profile.get("bio"),
                    "company": profile.get("company"),
                    "public_repos": profile.get("public_repos", 0),
                    "followers": profile.get("followers", 0),
                    "source": "github_contributor",
                    "contributed_to": repo,
                    "contributions": item.get("contributions", 0),
                    "raw": item,
                })
    except Exception:
        return []
    return candidates

SCORING_SYSTEM = """You are a senior technical recruiter with 15+ years experience.
Evaluate candidates with precision based ONLY on verifiable evidence.
Scoring rubric: 85-100 exceptional, 70-84 strong, 55-69 moderate, 40-54 weak, 0-39 poor.
Return valid JSON with exactly these keys: score (int 0-100), summary (1-2 sentences), strengths (list 2-4), concerns (list 1-3)."""

async def score_candidate(candidate: dict, role_description: str, role_requirements: str) -> dict:
    if not settings.GROQ_API_KEY:
        return {"score": 50, "summary": "LLM scoring unavailable — set GROQ_API_KEY", "strengths": [], "concerns": []}
    profile_parts = [f"Name: {candidate.get('name', 'Unknown')}", f"Source: {candidate.get('source', 'unknown')}"]
    for k, label in [("github_url","GitHub"),("bio","Bio"),("company","Company"),("location","Location")]:
        if candidate.get(k):
            profile_parts.append(f"{label}: {candidate[k]}")
    if candidate.get('public_repos') is not None:
        profile_parts.append(f"Public Repos: {candidate['public_repos']}")
    if candidate.get('contributed_to'):
        profile_parts.append(f"Contributed to: {candidate['contributed_to']} ({candidate.get('contributions',0)} contributions)")
    if candidate.get('top_repos'):
        profile_parts.append("Top Repositories:\n" + "\n".join([f"  - {r['name']} (★{r['stars']}, {r['language'] or 'N/A'}): {r['description']}" for r in candidate['top_repos']]))
    prompt = f"## Role Requirements\n{role_requirements or role_description}\n\n## Candidate Profile\n{chr(10).join(profile_parts)}\n\nEvaluate. Return JSON: score, summary, strengths, concerns."
    try:
        result = await groq_json([{"role": "user", "content": prompt}], system=SCORING_SYSTEM, required_keys=SCORE_REQUIRED_KEYS, max_tokens=1024)
        score = result.get("score", 40)
        if isinstance(score, str):
            try: score = int(score)
            except: score = 40
        result["score"] = max(0, min(100, int(score)))
        result["strengths"] = result.get("strengths") or []
        result["concerns"] = result.get("concerns") or []
        if isinstance(result["strengths"], str): result["strengths"] = [result["strengths"]]
        if isinstance(result["concerns"], str): result["concerns"] = [result["concerns"]]
        return result
    except Exception as e:
        logger.error(f"Scoring error for {candidate.get('name')}: {e}")
        return {"score": 40, "summary": "Scoring error", "strengths": [], "concerns": ["Automated scoring failed"]}

async def is_duplicate(role_id: int, github_url, email) -> bool:
    async with AsyncSessionLocal() as session:
        q = select(Candidate).where(Candidate.role_id == role_id)
        if github_url:
            q = q.where(Candidate.github_url == github_url)
        elif email:
            q = q.where(Candidate.email == email)
        else:
            return False
        result = await session.execute(q)
        return result.scalar_one_or_none() is not None

async def enrich_candidate_email(raw: dict) -> dict:
    """Run email discovery pipeline on a candidate dict. Returns enriched dict."""
    existing_email = raw.get("email")
    if existing_email and "@" in existing_email and "noreply" not in existing_email and "github" not in existing_email.lower():
        raw["email_source"] = "github_profile"
        raw["email_confidence"] = "verified"
        raw["email_verified"] = True
        return raw
    discovery = await discover_email(
        name=raw.get("name", ""),
        github_url=raw.get("github_url"),
        linkedin_url=raw.get("linkedin_url"),
        company_domain=raw.get("company_domain"),
        github_token=settings.GITHUB_TOKEN,
    )
    if discovery.get("email"):
        raw["email"] = discovery["email"]
        raw["email_source"] = discovery.get("source", "unknown")
        raw["email_confidence"] = discovery.get("confidence", "low")
        raw["email_alternatives"] = discovery.get("alternatives", [])
        raw["email_verified"] = discovery.get("verified", False)
    else:
        raw["email_source"] = "not_found"
        raw["email_confidence"] = "not_found"
        raw["email_verified"] = False
        raw["email_alternatives"] = []
    return raw

async def run_scout(role_id: int, keywords=None, max_candidates: int = 20) -> AsyncGenerator:
    async with AsyncSessionLocal() as session:
        role = await session.get(Role, role_id)
        if not role:
            yield {"event": "error", "message": f"Role {role_id} not found"}
            return

    role_keywords = keywords or _extract_keywords(role.title + " " + (role.requirements or ""))
    await log_event("SCOUT", "started", f"Scouting for role: {role.title}", {"keywords": role_keywords}, role_id=role_id)
    yield {"event": "started", "agent": "SCOUT", "message": f"Starting candidate search for '{role.title}'", "keywords": role_keywords}

    all_raw = []
    yield {"event": "progress", "agent": "SCOUT", "message": "Searching GitHub users..."}
    all_raw.extend(await search_github_users(role_keywords, max_results=10))

    for repo in _keywords_to_repos(role_keywords)[:2]:
        yield {"event": "progress", "agent": "SCOUT", "message": f"Fetching contributors from {repo}..."}
        all_raw.extend(await search_github_repo_contributors(repo, max_results=8))
        await asyncio.sleep(0.5)

    added = 0
    for raw in all_raw[:max_candidates]:
        gh = raw.get("github_url")
        if await is_duplicate(role_id, gh, raw.get("email")):
            continue

        yield {"event": "progress", "agent": "SCOUT", "message": f"Discovering email for {raw.get('name', '?')}..."}
        raw = await enrich_candidate_email(raw)
        em = raw.get("email")
        email_confidence = raw.get("email_confidence", "not_found")
        email_source = raw.get("email_source", "")

        try:
            scoring = await score_candidate(raw, role.description, role.requirements or "")
        except Exception as e:
            logger.error(f"Score failed for {raw.get('name')}: {e}")
            await asyncio.sleep(2)
            continue

        score_val = float(scoring.get("score", 0))
        if score_val < settings.MIN_SCORE_THRESHOLD:
            continue

        import datetime
        async with AsyncSessionLocal() as session:
            c = Candidate(
                role_id=role_id,
                name=raw.get("name") or "Unknown",
                email=em,
                github_url=gh,
                source=raw.get("source", "unknown"),
                stage=CandidateStage.SOURCED,
                score=score_val,
                screen_brief={
                    "scout_summary": scoring.get("summary"),
                    "strengths": scoring.get("strengths", []),
                    "concerns": scoring.get("concerns", []),
                    "email_discovery": {
                        "confidence": email_confidence,
                        "source": email_source,
                        "verified": raw.get("email_verified", False),
                        "alternatives": raw.get("email_alternatives", []),
                    },
                },
                last_activity_at=datetime.datetime.utcnow(),
                raw_data=raw.get("raw", {}),
            )
            session.add(c)
            await session.commit()
            await session.refresh(c)
            cid = c.id

        added += 1
        await log_event("SCOUT", "candidate_added", f"Added {raw.get('name')} (score={score_val:.0f}, email={'found' if em else 'not found'} [{email_confidence}])", candidate_id=cid, role_id=role_id)
        yield {
            "event": "candidate_found", "agent": "SCOUT",
            "candidate": {"id": cid, "name": raw.get("name"), "github_url": gh, "email": em, "email_confidence": email_confidence, "email_source": email_source, "source": raw.get("source"), "score": score_val, "summary": scoring.get("summary"), "strengths": scoring.get("strengths", [])}
        }
        await asyncio.sleep(1)

    await log_event("SCOUT", "completed", f"Scout complete: {added} candidates added", role_id=role_id)
    yield {"event": "completed", "agent": "SCOUT", "message": f"Scout complete. {added} candidates added to pipeline.", "count": added}

def _extract_keywords(text: str) -> list:
    common_tech = ["python","fastapi","django","react","node","typescript","golang","rust","java","scala","kubernetes","aws","ml","llm","langchain","postgres","redis","docker","backend","frontend","fullstack","devops","pytorch","tensorflow","huggingface","rag","celery","graphql","tailwind","nextjs","vue","angular","mongodb","elasticsearch"]
    text_lower = text.lower()
    found = [kw for kw in common_tech if kw in text_lower]
    return found[:6] if found else text.split()[:3]

def _keywords_to_repos(keywords: list) -> list:
    mapping = {"fastapi":["tiangolo/fastapi"],"python":["psf/requests","pallets/flask"],"langchain":["langchain-ai/langchain"],"react":["facebook/react"],"django":["django/django"],"golang":["golang/go"],"rust":["rust-lang/rust"],"kubernetes":["kubernetes/kubernetes"],"llm":["huggingface/transformers"],"pytorch":["pytorch/pytorch"],"rag":["langchain-ai/langchain"],"redis":["redis/redis"],"docker":["moby/moby"],"typescript":["microsoft/TypeScript"],"nextjs":["vercel/next.js"],"vue":["vuejs/vue"],"graphql":["graphql/graphql-js"]}
    repos = []
    for kw in keywords:
        repos.extend(mapping.get(kw.lower(), []))
    return list(dict.fromkeys(repos))
