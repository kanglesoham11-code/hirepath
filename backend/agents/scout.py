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
from datetime import datetime, timezone
from typing import AsyncGenerator
from sqlalchemy import func, or_, select
from database import Candidate, Role, CandidateStage, AsyncSessionLocal
from utils.logger import log_event
from utils.evidence import normalize_public_evidence_url, normalize_source_evidence
from config import settings

logger = logging.getLogger("hirepath.scout")

GITHUB_API = "https://api.github.com"

SCORE_REQUIRED_KEYS = ["score", "summary", "strengths", "concerns"]

# Maharashtra cities for location matching (Fix #11: removed 'india' — too loose)
MAHARASHTRA_LOCATIONS = [
    "maharashtra", "mumbai", "pune", "nagpur", "thane", "nashik",
    "aurangabad", "solapur", "kolhapur", "sangli", "navi mumbai",
    "amravati", "nanded", "bhiwandi", "jalgaon", "akola", "latur",
    "dhule", "ahmednagar", "chandrapur", "parbhani", "ichalkaranji",
    "jalna", "ambernath", "malegaon", "mira-bhayandar", "panvel",
]


# ── GitHub helpers ────────────────────────────────────────────────────────────

_github_token_invalid = False

async def _github_headers() -> dict:
    global _github_token_invalid
    h = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "HirePath/2.0 (Recruitment Intelligence; https://github.com/kanglesoham11-code/hirepath)",
    }
    if settings.GITHUB_TOKEN and not _github_token_invalid:
        h["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"
    return h


async def _github_get(client: httpx.AsyncClient, url: str, headers: dict) -> httpx.Response:
    """Wrapper that retries without Authorization if GitHub returns 401 Bad credentials."""
    global _github_token_invalid
    resp = await client.get(url, headers=headers)
    if resp.status_code == 401 and "Authorization" in headers:
        _github_token_invalid = True
        logger.warning(f"GitHub returned 401 for {url}. Configured GITHUB_TOKEN is invalid/expired. Switching to unauthenticated mode.")
        fallback = {k: v for k, v in headers.items() if k != "Authorization"}
        resp = await client.get(url, headers=fallback)
    return resp


def _is_maharashtra_location(location: str | None) -> bool:
    """Check if a location string matches Maharashtra or its cities.
    Fix #11: Uses word-boundary matching to avoid false positives like 'Indianapolis'."""
    if not location:
        return False
    loc_lower = location.lower().strip()
    for mh_loc in MAHARASHTRA_LOCATIONS:
        # Use word boundary matching: check the location word is surrounded
        # by non-alpha chars (or string boundaries)
        if re.search(r'\b' + re.escape(mh_loc) + r'\b', loc_lower):
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
        keyword_query = "+".join(keywords[:3]) if keywords else "developer"
        query = f"{keyword_query}+location:{mh_city}+type:user"
        url = f"{GITHUB_API}/search/users?q={query}&per_page={min(max_results, 30)}&sort=repositories"
        
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await _github_get(client, url, headers)
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
    keyword_query = "+".join(keywords[:4]) if keywords else "developer"
    url = f"{GITHUB_API}/search/users?q={keyword_query}+type:user&per_page=30&sort=repositories"
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await _github_get(client, url, headers)
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
                pr = await _github_get(client, item["url"], headers)
                if pr.status_code == 200:
                    profile = pr.json()
                elif pr.status_code == 403:
                    logger.warning("Rate limited on profile fetch, sleeping...")
                    await asyncio.sleep(10)
                    continue
        except Exception:
            continue

        location = profile.get("location", "")
        
        # A location search is only a GitHub search hint. Validate every enriched
        # profile itself so a missing or mismatched profile location cannot pass.
        if not _is_maharashtra_location(location):
            continue

        # Fetch top repos for richer profile data
        repos_data = []
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                repos_url = f"{GITHUB_API}/users/{item.get('login')}/repos?sort=stars&per_page=5"
                repos_resp = await _github_get(client, repos_url, headers)
                if repos_resp.status_code == 200:
                    for repo in repos_resp.json()[:5]:
                        repos_data.append({
                            "name": repo.get("name"),
                            "url": repo.get("html_url"),
                            "stars": repo.get("stargazers_count", 0),
                            "language": repo.get("language"),
                            "description": (repo.get("description") or "")[:100],
                        })
        except Exception:
            pass

        enriched.append({
            "name": profile.get("name") or item.get("login", ""),
            "github_url": profile.get("html_url") or item.get("html_url", ""),
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
            resp = await _github_get(client, url, headers)
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
                pr = await _github_get(client, item.get("url", ""), headers)
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
    # StackExchange does not provide a location query. We fetch a bounded set
    # of public profiles, then retain only accounts with a declared Maharashtra
    # location and relevant public answer tags.
    role_keywords = {keyword.lower() for keyword in keywords if keyword.strip()}
    for page in range(1, 4):
        url = (
            f"https://api.stackexchange.com/2.3/users"
            f"?order=desc&sort=reputation"
            f"&site=stackoverflow"
            f"&pagesize=15"
            f"&page={page}"
            f"&filter=!nNPvSNdWme"
        )
        
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    for user in data.get("items", []):
                        if len(candidates) >= max_results:
                            break
                        user_location = user.get("location", "")
                        if not _is_maharashtra_location(user_location):
                            continue

                        user_id = user.get("user_id")
                        tag_names: list[str] = []
                        if user_id:
                            tags_url = (
                                f"https://api.stackexchange.com/2.3/users/{user_id}/top-answer-tags"
                                f"?site=stackoverflow&pagesize=20"
                            )
                            tags_response = await client.get(tags_url)
                            if tags_response.status_code == 200:
                                tag_names = [
                                    str(tag.get("name")).lower()
                                    for tag in tags_response.json().get("items", [])
                                    if tag.get("name")
                                ]

                        # A high reputation alone does not establish relevance
                        # for a role. Require at least one public answer tag that
                        # matches the role query when the role supplied keywords.
                        if role_keywords and not (role_keywords & set(tag_names)):
                            continue

                        profile_url = user.get("website_url", "")
                        github_url = normalize_public_evidence_url(profile_url) or ""
                        if github_url and "github.com" not in github_url:
                            github_url = ""

                        candidates.append({
                            "name": user.get("display_name") or "",
                            "github_url": github_url,
                            "email": None,
                            "location": user_location,
                            "bio": (
                                f"Stack Overflow reputation: {user.get('reputation', 0):,}. "
                                f"Public answer tags: {', '.join(tag_names[:8])}."
                            ),
                            "skills": tag_names,
                            "company": None,
                            "public_repos": 0,
                            "followers": user.get("reputation", 0),
                            "source": "stackoverflow_maharashtra",
                            "stackoverflow_url": user.get("link", ""),
                            "reputation": user.get("reputation", 0),
                            "raw": {"profile": user, "top_answer_tags": tag_names},
                        })
        except Exception as e:
            logger.error(f"StackOverflow search error: {e}")
        
        await asyncio.sleep(0.5)
        
        if len(candidates) >= max_results:
            break

    return candidates[:max_results]


# ── Public-source evidence ───────────────────────────────────────────────────

def build_source_evidence(candidate: dict) -> list[dict[str, str]]:
    """Build recruiter-facing evidence from URLs returned by the live APIs.

    This deliberately never fabricates a link.  Each entry is normalized to a
    supported public host and is shown unchanged to the recruiter for review.
    """
    evidence: list[dict[str, str]] = []

    github_url = normalize_public_evidence_url(candidate.get("github_url"))
    if github_url:
        evidence.append({
            "type": "github_profile",
            "label": "GitHub profile",
            "url": github_url,
        })

    stackoverflow_url = normalize_public_evidence_url(candidate.get("stackoverflow_url"))
    if stackoverflow_url:
        evidence.append({
            "type": "stackoverflow_profile",
            "label": "Stack Overflow profile",
            "url": stackoverflow_url,
        })

    for repo in candidate.get("top_repos", [])[:5]:
        if not isinstance(repo, dict):
            continue
        repo_url = normalize_public_evidence_url(repo.get("url"))
        repo_name = str(repo.get("name") or "repository").strip()
        if not repo_url or not repo_name:
            continue
        detail_parts = []
        if repo.get("language"):
            detail_parts.append(str(repo["language"]))
        if isinstance(repo.get("stars"), int):
            detail_parts.append(f"{repo['stars']} stars")
        evidence.append({
            "type": "github_repository",
            "label": f"GitHub repository: {repo_name}",
            "url": repo_url,
            "detail": " · ".join(detail_parts),
        })

    # Contributor results identify the repository directly even when we did
    # not fetch its top-repository list.
    contributed_to = str(candidate.get("contributed_to") or "").strip()
    if re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", contributed_to):
        contribution_url = normalize_public_evidence_url(f"https://github.com/{contributed_to}")
        if contribution_url:
            evidence.append({
                "type": "github_repository",
                "label": f"GitHub repository: {contributed_to}",
                "url": contribution_url,
                "detail": "Repository with recorded contributor activity",
            })

    return normalize_source_evidence(evidence)


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


def compute_quick_heuristic_score(candidate: dict, role_description: str, role_requirements: str) -> dict:
    """Fix #19: Lightweight heuristic scoring for SCOUT pre-filtering.
    Keeps a single AI scoring step in SCREEN, avoiding double AI calls and saving Groq rate limits."""
    combined_reqs = (role_requirements + " " + role_description).lower()
    req_keywords = _extract_keywords(combined_reqs)

    score = 25  # Base score for qualifying Maharashtra profile
    matched_skills = []

    # Check top repos languages and descriptions
    repo_langs = set()
    total_stars = 0
    for r in candidate.get("top_repos", []):
        lang = (r.get("language") or "").lower()
        if lang:
            repo_langs.add(lang)
        desc = (r.get("description") or "").lower()
        for kw in req_keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', desc) or kw == lang:
                if kw not in matched_skills:
                    matched_skills.append(kw)
        total_stars += r.get("stars", 0)

    # Check candidate bio and listed skills
    bio = (candidate.get("bio") or "").lower()
    for kw in req_keywords:
        if re.search(r'\b' + re.escape(kw) + r'\b', bio):
            if kw not in matched_skills:
                matched_skills.append(kw)

    for sk in candidate.get("skills", []):
        sk_lower = str(sk).lower()
        for kw in req_keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', sk_lower) and kw not in matched_skills:
                matched_skills.append(kw)

    # Add points for matched skills (up to 45 pts)
    score += min(len(matched_skills) * 15, 45)

    # Add points for repos and contributions (up to 20 pts)
    public_repos = candidate.get("public_repos") or 0
    if public_repos > 5:
        score += 10
    if candidate.get("contributions", 0) > 0 or candidate.get("contributed_to"):
        score += 10

    # Add points for stars (up to 15 pts)
    if total_stars >= 50:
        score += 15
    elif total_stars >= 10:
        score += 10
    elif total_stars > 0:
        score += 5

    score = max(0, min(100, score))

    strengths = [f"Matches skills: {', '.join(matched_skills)}"] if matched_skills else ["Active technical profile in Maharashtra"]
    if total_stars > 0:
        strengths.append(f"{total_stars} stars across top repositories")
    if candidate.get("contributed_to"):
        strengths.append(f"Contributed to {candidate['contributed_to']}")

    concerns = []
    missing_skills = [kw for kw in req_keywords if kw not in matched_skills]
    if missing_skills:
        concerns.append(f"No direct evidence in bio/top repos for: {', '.join(missing_skills[:3])}")

    return {
        "score": score,
        "summary": f"SCOUT initial screen: {score}/100. Matched skills: {', '.join(matched_skills) if matched_skills else 'general background'}. Detailed AI evaluation handled by SCREEN.",
        "strengths": strengths,
        "concerns": concerns,
    }


async def score_candidate(candidate: dict, role_description: str, role_requirements: str) -> dict:
    """Fix #19: Single AI scoring pass. SCOUT uses fast heuristic scoring, leaving full AI evaluation to SCREEN."""
    return compute_quick_heuristic_score(candidate, role_description, role_requirements)


# ── Deduplication ─────────────────────────────────────────────────────────────

async def is_duplicate(role_id: int, github_url: str | None, email: str | None, name: str | None = None, source: str | None = None) -> bool:
    """Fix #8: Check duplicates by github_url, email, OR name+source."""
    async with AsyncSessionLocal() as session:
        q = select(Candidate).where(Candidate.role_id == role_id)
        if github_url:
            normalized_url = github_url.strip().rstrip("/").lower()
            result = await session.execute(q.where(func.lower(func.rtrim(Candidate.github_url, "/")) == normalized_url))
            if result.scalars().first():
                return True
        if email:
            result = await session.execute(q.where(func.lower(Candidate.email) == email.strip().lower()))
            if result.scalars().first():
                return True
        # Fix #8: Also check by name+source for candidates with no github/email
        if name and source:
            result = await session.execute(
                q.where(func.lower(Candidate.name) == name.strip().lower(), func.lower(Candidate.source) == source.strip().lower())
            )
            if result.scalars().first():
                return True
        return False


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

    if not settings.GITHUB_TOKEN:
        message = "GITHUB_TOKEN is required before SCOUT can run. Add it to backend/.env and restart the service."
        await log_event("SCOUT", "configuration_error", message, role_id=role_id)
        yield {"event": "error", "agent": "SCOUT", "message": message}
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

    # Fix #8: Deduplicate FIRST, then apply limit. A source record must also
    # include a public evidence URL before it can become a candidate.
    added = 0
    for raw in all_raw:
        if added >= max_candidates:
            break

        gh = normalize_public_evidence_url(raw.get("github_url"))
        if gh and "github.com" not in gh:
            gh = None
        em = raw.get("email")
        name = str(raw.get("name") or "").strip()
        source = raw.get("source")

        evidence = build_source_evidence(raw)
        if not name or not source or not evidence:
            await log_event(
                "SCOUT", "source_record_rejected",
                "Skipped a source record without a verifiable public profile or repository link.",
                role_id=role_id,
            )
            continue

        if await is_duplicate(role_id, gh, em, name, source):
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
                name=name,
                email=em,
                github_url=gh,
                source=source,
                source_verified=True,
                source_captured_at=datetime.now(timezone.utc),
                source_evidence=evidence,
                stage=CandidateStage.SOURCED,
                score=score_val,
                screen_brief={
                    "scout_summary": scoring.get("summary"),
                    "strengths": scoring.get("strengths", []),
                    "concerns": scoring.get("concerns", []),
                    "location": raw.get("location", "Maharashtra, India"),
                    "evidence": evidence,
                },
                last_activity_at=datetime.utcnow(),
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
                "source_evidence": evidence,
                "score": score_val,
                "location": raw.get("location", "Maharashtra"),
                "summary": scoring.get("summary"),
                "strengths": scoring.get("strengths", []),
            }
        }
        
        # Smooth UI streaming
        await asyncio.sleep(0.05)

    await log_event("SCOUT", "completed", f"Scout complete: {added} Maharashtra-based candidates added", role_id=role_id)
    yield {"event": "completed", "agent": "SCOUT", "message": f"Scout complete. {added} Maharashtra-based candidates added to pipeline.", "count": added}


# ── Utilities ─────────────────────────────────────────────────────────────────

def _extract_keywords(text: str) -> list[str]:
    """Extract relevant tech keywords from a role description.
    Fix #12: Uses whole-word matching to avoid false positives."""
    common_tech = ["python", "fastapi", "django", "react", "node", "typescript", "golang",
                   "rust", "java", "scala", "kubernetes", "aws", "ml", "llm", "langchain",
                   "postgres", "postgresql", "redis", "docker", "backend", "frontend", "fullstack", "devops",
                   "pytorch", "tensorflow", "huggingface", "rag", "celery", "graphql",
                   "tailwind", "nextjs", "vue", "angular", "mongodb", "elasticsearch",
                   "flutter", "dart", "swift", "kotlin", "android", "ios", "spring",
                   "microservices", "kafka", "rabbitmq", "terraform", "jenkins", "cicd",
                   "ai", "data", "engineer", "software", "cloud", "api", "sql", "c++", "nlp"]
    text_lower = text.lower()
    # Fix #12: Match whole words only using word boundaries
    found = [kw for kw in common_tech if re.search(r'\b' + re.escape(kw) + r'\b', text_lower)]
    if found:
        return found[:6]
    # Fallback: clean words, ignore pure numbers or short tokens
    words = [re.sub(r'[^a-z0-9]', '', w) for w in text_lower.split()]
    words = [w for w in words if len(w) >= 2 and not w.isdigit() and w not in ("years", "year", "plus", "exp", "experience")]
    return words[:4] if words else ["developer"]


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
