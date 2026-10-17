"""
SCOUT — Sourcing Agent (Live Scraping — Maharashtra Focus)
Sources candidates LIVE from GitHub, StackOverflow, and web search.
All candidates are scraped in real-time — NO hardcoded data.
Location filter: Maharashtra, India.
"""
import httpx
import asyncio
import logging
import re
from typing import AsyncGenerator
from sqlalchemy import select
from database import Candidate, Role, CandidateStage, AsyncSessionLocal
from utils.llm import groq_json
from utils.logger import log_event
from config import settings

logger = logging.getLogger("hirepath.scout")

GITHUB_API = "https://api.github.com"

SCORE_REQUIRED_KEYS = ["score", "summary", "strengths", "concerns"]

# Maharashtra cities for location matching
MAHARASHTRA_LOCATIONS = [
    "maharashtra", "mumbai", "pune", "nagpur", "thane", "nashik",
    "aurangabad", "solapur", "kolhapur", "sangli", "navi mumbai",
    "amravati", "nanded", "bhiwandi", "jalgaon", "akola", "latur",
    "dhule", "ahmednagar", "chandrapur", "parbhani", "ichalkaranji",
    "jalna", "ambernath", "malegaon", "mira-bhayandar", "panvel",
    "india",  # Include broad India matches — we'll prioritize Maharashtra
]


# ── GitHub helpers ────────────────────────────────────────────────────────────

async def _github_headers() -> dict:
    h = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if settings.GITHUB_TOKEN:
        h["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"
    return h


def _is_maharashtra_location(location: str | None) -> bool:
    """Check if a location string matches Maharashtra or its cities."""
    if not location:
        return False
    loc_lower = location.lower().strip()
    for mh_loc in MAHARASHTRA_LOCATIONS:
        if mh_loc in loc_lower:
            return True
    return False


async def search_github_users_maharashtra(keywords: list[str], max_results: int = 20) -> list[dict]:
    """
    Search GitHub for users matching job keywords LOCATED IN MAHARASHTRA.
    Uses GitHub's location qualifier for targeted results.
    All data is fetched LIVE from the GitHub API.
    """
    all_candidates = []
    headers = await _github_headers()

    # Strategy 1: Search with location:Maharashtra + keywords
    maharashtra_locations = ["Maharashtra", "Mumbai", "Pune", "Nagpur", "Thane", "Nashik"]
    
    for mh_city in maharashtra_locations[:4]:  # Top 4 cities
        keyword_query = "+".join(keywords[:3])
        query = f"{keyword_query}+location:{mh_city}+type:user"
        url = f"{GITHUB_API}/search/users?q={query}&per_page={min(max_results, 30)}&sort=repositories"
        
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    items = resp.json().get("items", [])
                    for item in items:
                        all_candidates.append({
                            "login": item.get("login"),
                            "url": item.get("url", ""),
                            "html_url": item.get("html_url", ""),
                            "city_hint": mh_city,
                        })
                elif resp.status_code == 403:
                    logger.warning("GitHub rate limit hit. Waiting...")
                    await asyncio.sleep(5)
                else:
                    logger.warning(f"GitHub search returned {resp.status_code} for {mh_city}")
        except Exception as e:
            logger.error(f"GitHub search error for {mh_city}: {e}")
        
        await asyncio.sleep(0.8)  # Respect rate limits

    # Strategy 2: Broader keyword search, then filter by location
    keyword_query = "+".join(keywords[:4])
    url = f"{GITHUB_API}/search/users?q={keyword_query}+type:user&per_page=30&sort=repositories"
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                items = resp.json().get("items", [])
                for item in items:
                    all_candidates.append({
                        "login": item.get("login"),
                        "url": item.get("url", ""),
                        "html_url": item.get("html_url", ""),
                        "city_hint": "global_search",
                    })
    except Exception as e:
        logger.error(f"GitHub global search error: {e}")

    # Deduplicate by login
    seen_logins = set()
    unique_candidates = []
    for c in all_candidates:
        login = c.get("login", "").lower()
        if login and login not in seen_logins:
            seen_logins.add(login)
            unique_candidates.append(c)

    # Fetch full profiles and filter by Maharashtra location
    enriched = []
    for item in unique_candidates[:max_results * 2]:  # Fetch more to filter
        if len(enriched) >= max_results:
            break

        profile = {}
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                pr = await client.get(item["url"], headers=headers)
                if pr.status_code == 200:
                    profile = pr.json()
                elif pr.status_code == 403:
                    logger.warning("Rate limited on profile fetch, sleeping...")
                    await asyncio.sleep(10)
                    continue
        except Exception:
            continue

        location = profile.get("location", "")
        
        # For location-targeted searches (from Maharashtra cities), include even without location
        is_from_mh_search = item.get("city_hint") not in ("global_search",)
        is_mh_location = _is_maharashtra_location(location)
        
        # Include if: from Maharashtra-specific search OR has Maharashtra location
        if not is_from_mh_search and not is_mh_location:
            continue

        # Fetch top repos for richer profile data
        repos_data = []
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                repos_url = f"{GITHUB_API}/users/{item.get('login')}/repos?sort=stars&per_page=5"
                repos_resp = await client.get(repos_url, headers=headers)
                if repos_resp.status_code == 200:
                    for repo in repos_resp.json()[:5]:
                        repos_data.append({
                            "name": repo.get("name"),
                            "stars": repo.get("stargazers_count", 0),
                            "language": repo.get("language"),
                            "description": (repo.get("description") or "")[:100],
                        })
        except Exception:
            pass

        enriched.append({
            "name": profile.get("name") or item.get("login", ""),
            "github_url": item.get("html_url", ""),
            "email": profile.get("email"),
            "location": location,
            "bio": profile.get("bio"),
            "company": profile.get("company"),
            "public_repos": profile.get("public_repos", 0),
            "followers": profile.get("followers", 0),
            "hireable": profile.get("hireable"),
            "top_repos": repos_data,
            "source": "github_maharashtra",
            "raw": profile,
        })
        
        await asyncio.sleep(0.5)  # Rate limit between profile fetches

    return enriched


async def search_github_repo_contributors(repo: str, max_results: int = 10) -> list[dict]:
    """
    Get contributors from a specific repo, filter for Maharashtra-based devs.
    ALL data is fetched LIVE from GitHub API.
    """
    url = f"{GITHUB_API}/repos/{repo}/contributors?per_page={max_results * 3}"
    headers = await _github_headers()
    
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                return []
            items = resp.json()
    except Exception:
        return []

    candidates = []
    for item in items:
        if len(candidates) >= max_results:
            break
            
        # Fetch full profile to check location
        profile = {}
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                pr = await client.get(item.get("url", ""), headers=headers)
                profile = pr.json() if pr.status_code == 200 else {}
        except Exception:
            continue

        location = profile.get("location", "")
        # Only include Maharashtra-based contributors
        if not _is_maharashtra_location(location):
            continue

        candidates.append({
            "name": profile.get("name") or item.get("login", ""),
            "github_url": item.get("html_url", ""),
            "email": profile.get("email"),
            "location": location,
            "bio": profile.get("bio"),
            "company": profile.get("company"),
            "public_repos": profile.get("public_repos", 0),
            "followers": profile.get("followers", 0),
            "source": "github_contributor_maharashtra",
            "contributed_to": repo,
            "contributions": item.get("contributions", 0),
            "raw": item,
        })
        
        await asyncio.sleep(0.3)

    return candidates


# ── StackOverflow (Live Scraping) ─────────────────────────────────────────────

async def search_stackoverflow_users(keywords: list[str], max_results: int = 10) -> list[dict]:
    """
    Search StackOverflow for users with relevant tags located in Maharashtra.
    Uses the public StackExchange API — ALL data is fetched LIVE.
    """
    candidates = []
    tag_query = ";".join(keywords[:3])
    
    # StackExchange API — search users by tag expertise in India/Maharashtra
    for location_filter in ["Mumbai", "Pune", "Maharashtra", "India"]:
        url = (
            f"https://api.stackexchange.com/2.3/users"
            f"?order=desc&sort=reputation"
            f"&inname={location_filter}"
            f"&site=stackoverflow"
            f"&pagesize=15"
            f"&filter=!nNPvSNdWme"
        )
        
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    for user in data.get("items", []):
                        user_location = user.get("location", "")
                        if _is_maharashtra_location(user_location):
                            # Check if user has relevant tag scores
                            profile_url = user.get("website_url", "")
                            github_url = ""
                            if profile_url and "github.com" in profile_url:
                                github_url = profile_url
                            
                            candidates.append({
                                "name": user.get("display_name", "Unknown"),
                                "github_url": github_url,
                                "email": None,
                                "location": user_location,
                                "bio": f"StackOverflow reputation: {user.get('reputation', 0):,}",
                                "company": None,
                                "public_repos": 0,
                                "followers": user.get("reputation", 0),
                                "source": "stackoverflow_maharashtra",
                                "stackoverflow_url": user.get("link", ""),
                                "reputation": user.get("reputation", 0),
                                "raw": user,
                            })
        except Exception as e:
            logger.error(f"StackOverflow search error: {e}")
        
        await asyncio.sleep(0.5)
        
        if len(candidates) >= max_results:
            break

    return candidates[:max_results]


# ── Scoring ───────────────────────────────────────────────────────────────────

SCORING_SYSTEM = """You are a senior technical recruiter with 15+ years of experience evaluating engineering talent.

You MUST evaluate candidates with precision based ONLY on verifiable evidence from their profile.
Do NOT assume skills — only credit what is demonstrably shown in their repos, bio, contributions, or stated experience.

Scoring rubric:
- 85-100: Exceptional match. Evidence of deep expertise in multiple required skills. Active contributor, senior-level.
- 70-84: Strong match. Clear evidence of core required skills. Solid engineering background.
- 55-69: Moderate match. Some relevant skills shown, but gaps in key requirements.
- 40-54: Weak match. Limited evidence of required skills. Might need significant ramp-up.
- 0-39: Poor match. Little to no relevant evidence found.

Be HONEST. Do not inflate scores. A GitHub profile with 2 repos and no relevant language experience is NOT a 70+ score.

Always return a valid JSON object with exactly these keys:
  "score" (integer 0-100 — be precise and evidence-based),
  "summary" (1-2 sentences explaining the score with specific evidence cited),
  "strengths" (list of 2-4 specific, evidence-backed strengths — reference actual repos, contributions, or bio details),
  "concerns" (list of 1-3 specific concerns or gaps relative to the role requirements)"""


async def score_candidate(candidate: dict, role_description: str, role_requirements: str) -> dict:
    """Uses Groq to score a candidate 0-100 and return a brief."""
    if not settings.GROQ_API_KEY:
        return {"score": 50.0, "summary": "LLM scoring unavailable — set GROQ_API_KEY", "strengths": [], "concerns": []}

    # Build a rich candidate profile for the LLM
    profile_parts = []
    profile_parts.append(f"Name: {candidate.get('name', 'Unknown')}")
    profile_parts.append(f"Source: {candidate.get('source', 'unknown')}")
    profile_parts.append(f"Location: {candidate.get('location', 'Maharashtra, India')}")
    
    if candidate.get('github_url'):
        profile_parts.append(f"GitHub: {candidate['github_url']}")
    if candidate.get('stackoverflow_url'):
        profile_parts.append(f"StackOverflow: {candidate['stackoverflow_url']}")
    if candidate.get('bio'):
        profile_parts.append(f"Bio: {candidate['bio']}")
    if candidate.get('company'):
        profile_parts.append(f"Company: {candidate['company']}")
    if candidate.get('public_repos') is not None:
        profile_parts.append(f"Public Repos: {candidate['public_repos']}")
    if candidate.get('followers') is not None:
        profile_parts.append(f"Followers: {candidate['followers']}")
    if candidate.get('hireable') is not None:
        profile_parts.append(f"Open to hire: {'Yes' if candidate['hireable'] else 'Not specified'}")
    if candidate.get('contributed_to'):
        profile_parts.append(f"Contributed to: {candidate['contributed_to']} ({candidate.get('contributions', 0)} contributions)")
    if candidate.get('reputation'):
        profile_parts.append(f"StackOverflow Reputation: {candidate['reputation']:,}")
    if candidate.get('top_repos'):
        repos_text = "\n".join([
            f"  - {r['name']} (★{r['stars']}, {r['language'] or 'N/A'}): {r['description']}"
            for r in candidate['top_repos']
        ])
        profile_parts.append(f"Top Repositories:\n{repos_text}")
    if candidate.get('skills'):
        profile_parts.append(f"Listed Skills: {', '.join(candidate['skills'])}")

    candidate_profile = "\n".join(profile_parts)

    prompt = f"""## Role Requirements
{role_requirements or role_description}

## Candidate Profile
{candidate_profile}

Evaluate this candidate against the role requirements. Score based ONLY on demonstrable evidence.
Return a JSON object with keys: score, summary, strengths, concerns."""

    try:
        result = await groq_json(
            [{"role": "user", "content": prompt}],
            system=SCORING_SYSTEM,
            required_keys=SCORE_REQUIRED_KEYS,
            max_tokens=1024,
        )
        # Validate and clamp score
        score = result.get("score", 40)
        if isinstance(score, str):
            try:
                score = int(score)
            except (ValueError, TypeError):
                score = 40
        result["score"] = max(0, min(100, int(score)))
        
        # Ensure list types
        result["strengths"] = result.get("strengths") or []
        result["concerns"] = result.get("concerns") or []
        if isinstance(result["strengths"], str):
            result["strengths"] = [result["strengths"]]
        if isinstance(result["concerns"], str):
            result["concerns"] = [result["concerns"]]
            
        return result
    except Exception as e:
        logger.error(f"Scoring error for {candidate.get('name')}: {e}")
        return {"score": 40, "summary": f"Scoring error — will retry on next run", "strengths": [], "concerns": ["Automated scoring failed — manual review needed"]}


# ── Deduplication ─────────────────────────────────────────────────────────────

async def is_duplicate(role_id: int, github_url: str | None, email: str | None) -> bool:
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


# ── Main SCOUT entrypoint ─────────────────────────────────────────────────────

async def run_scout(role_id: int, keywords: list[str] | None = None, max_candidates: int = 20) -> AsyncGenerator[dict, None]:
    """
    Async generator — yields progress events as candidates are found.
    ALL candidates are sourced LIVE from APIs — no hardcoded data.
    Location filter: Maharashtra, India.
    Saves each qualified candidate to DB.
    """
    async with AsyncSessionLocal() as session:
        role = await session.get(Role, role_id)
        if not role:
            yield {"event": "error", "message": f"Role {role_id} not found"}
            return

    role_keywords = keywords or _extract_keywords(role.title + " " + (role.requirements or ""))
    
    await log_event("SCOUT", "started", f"Scouting for role: {role.title} | Location: Maharashtra", {"keywords": role_keywords, "location": "Maharashtra, India"}, role_id=role_id)
    yield {"event": "started", "agent": "SCOUT", "message": f"Starting LIVE candidate search for '{role.title}' in Maharashtra", "keywords": role_keywords, "location": "Maharashtra, India"}

    all_raw: list[dict] = []

    # 1. GitHub users in Maharashtra
    yield {"event": "progress", "agent": "SCOUT", "message": "🔍 Searching GitHub users in Maharashtra..."}
    github_users = await search_github_users_maharashtra(role_keywords, max_results=12)
    all_raw.extend(github_users)
    yield {"event": "progress", "agent": "SCOUT", "message": f"Found {len(github_users)} GitHub users in Maharashtra"}

    # 2. GitHub contributors from relevant repos (filtered by Maharashtra)
    repo_map = _keywords_to_repos(role_keywords)
    for repo in repo_map[:2]:
        yield {"event": "progress", "agent": "SCOUT", "message": f"Checking Maharashtra-based contributors in {repo}..."}
        contribs = await search_github_repo_contributors(repo, max_results=5)
        all_raw.extend(contribs)
        await asyncio.sleep(0.5)

    # 3. StackOverflow users in Maharashtra
    yield {"event": "progress", "agent": "SCOUT", "message": "🔍 Searching StackOverflow for Maharashtra developers..."}
    so_users = await search_stackoverflow_users(role_keywords, max_results=8)
    all_raw.extend(so_users)
    yield {"event": "progress", "agent": "SCOUT", "message": f"Found {len(so_users)} StackOverflow users in Maharashtra"}

    yield {"event": "progress", "agent": "SCOUT", "message": f"Total raw candidates found: {len(all_raw)}. Scoring and deduplicating..."}

    added = 0
    for raw in all_raw[:max_candidates]:
        gh = raw.get("github_url")
        em = raw.get("email")

        if await is_duplicate(role_id, gh, em):
            continue

        # Score candidate with rate limit protection
        try:
            scoring = await score_candidate(raw, role.description, role.requirements or "")
        except Exception as e:
            logger.error(f"Score failed for {raw.get('name')}: {e}")
            await asyncio.sleep(2)
            continue
            
        score_val = float(scoring.get("score", 0))

        if score_val < 20:  # skip very low scores
            continue

        async with AsyncSessionLocal() as session:
            c = Candidate(
                role_id=role_id,
                name=raw.get("name") or "Unknown",
                email=em,
                github_url=gh,
                source=raw.get("source", "unknown"),
                stage=CandidateStage.SOURCED,
                score=score_val,
                screen_brief={"scout_summary": scoring.get("summary"), "strengths": scoring.get("strengths", []), "concerns": scoring.get("concerns", []), "location": raw.get("location", "Maharashtra, India")},
                last_activity_at=__import__("datetime").datetime.utcnow(),
                raw_data=raw.get("raw", {}),
            )
            session.add(c)
            await session.commit()
            await session.refresh(c)
            cid = c.id

        added += 1
        await log_event("SCOUT", "candidate_added", f"Added {raw.get('name')} from {raw.get('location', 'Maharashtra')} (score={score_val:.0f})", candidate_id=cid, role_id=role_id)
        yield {
            "event": "candidate_found",
            "agent": "SCOUT",
            "candidate": {
                "id": cid,
                "name": raw.get("name"),
                "github_url": gh,
                "source": raw.get("source"),
                "score": score_val,
                "location": raw.get("location", "Maharashtra"),
                "summary": scoring.get("summary"),
                "strengths": scoring.get("strengths", []),
            }
        }
        
        # Small delay between LLM calls to respect rate limits
        await asyncio.sleep(1)

    await log_event("SCOUT", "completed", f"Scout complete: {added} Maharashtra-based candidates added", role_id=role_id)
    yield {"event": "completed", "agent": "SCOUT", "message": f"Scout complete. {added} Maharashtra-based candidates added to pipeline.", "count": added}


# ── Utilities ─────────────────────────────────────────────────────────────────

def _extract_keywords(text: str) -> list[str]:
    """Extract relevant tech keywords from a role description."""
    common_tech = ["python", "fastapi", "django", "react", "node", "typescript", "golang",
                   "rust", "java", "scala", "kubernetes", "aws", "ml", "llm", "langchain",
                   "postgres", "redis", "docker", "backend", "frontend", "fullstack", "devops",
                   "pytorch", "tensorflow", "huggingface", "rag", "celery", "graphql",
                   "tailwind", "nextjs", "vue", "angular", "mongodb", "elasticsearch",
                   "flutter", "dart", "swift", "kotlin", "android", "ios", "spring",
                   "microservices", "kafka", "rabbitmq", "terraform", "jenkins", "cicd"]
    words = text.lower().split()
    # Also check multi-word combos
    text_lower = text.lower()
    found = [kw for kw in common_tech if kw in text_lower]
    return found[:6] if found else text.split()[:3]


def _keywords_to_repos(keywords: list[str]) -> list[str]:
    mapping = {
        "fastapi": ["tiangolo/fastapi"],
        "python": ["psf/requests", "pallets/flask"],
        "langchain": ["langchain-ai/langchain"],
        "react": ["facebook/react"],
        "django": ["django/django"],
        "golang": ["golang/go"],
        "rust": ["rust-lang/rust"],
        "kubernetes": ["kubernetes/kubernetes"],
        "llm": ["huggingface/transformers"],
        "pytorch": ["pytorch/pytorch"],
        "rag": ["langchain-ai/langchain"],
        "redis": ["redis/redis"],
        "docker": ["moby/moby"],
        "typescript": ["microsoft/TypeScript"],
        "nextjs": ["vercel/next.js"],
        "vue": ["vuejs/vue"],
        "graphql": ["graphql/graphql-js"],
        "flutter": ["flutter/flutter"],
        "spring": ["spring-projects/spring-boot"],
        "terraform": ["hashicorp/terraform"],
    }
    repos = []
    for kw in keywords:
        repos.extend(mapping.get(kw.lower(), []))
    return list(dict.fromkeys(repos))  # dedupe while preserving order
