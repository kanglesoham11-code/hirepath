"""
SCOUT — Sourcing Agent (Live Scraping — Location Engine v2)
Sources candidates LIVE from GitHub, StackOverflow, and web search.
All candidates are scraped in real-time — NO hardcoded data.
Location filter: Production-grade resolver with configurable target regions.
"""
import httpx
import asyncio
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import AsyncGenerator
from sqlalchemy import func, or_, select
from database import Candidate, Role, CandidateStage, AsyncSessionLocal
from utils.logger import log_event
from utils.evidence import normalize_public_evidence_url, normalize_source_evidence
from utils.location_resolver import resolve_location, resolve_for_target, LocationResult
from utils.rate_limiter import get_github_search_limiter
from config import settings

logger = logging.getLogger("hirepath.scout")


def mask_email(email: str) -> str:
    """Mask email for display."""
    if not email or "@" not in email:
        return email
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked_local = local[0] + "*" * (len(local) - 1)
    else:
        masked_local = local[:2] + "*" * (len(local) - 2)
    return f"{masked_local}@{domain}"


def _sanitize_for_json(obj: any) -> any:
    """Recursively convert LocationResult dataclass instances to dict for JSON serialization."""
    if isinstance(obj, LocationResult):
        return {
            "raw": obj.raw,
            "city": obj.city,
            "district": obj.district,
            "state": obj.state,
            "country_iso2": obj.country_iso2,
            "confidence": obj.confidence,
            "matched_text": obj.matched_text,
            "reason": obj.reason,
            "accepted": obj.accepted,
        }
    if isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_for_json(v) for v in obj]
    if isinstance(obj, tuple):
        return tuple(_sanitize_for_json(v) for v in obj)
    return obj

GITHUB_API = "https://api.github.com"
GITHUB_GRAPHQL = "https://api.github.com/graphql"

SCORE_REQUIRED_KEYS = ["score", "summary", "strengths", "concerns"]


# ── Per-run state (Phase 0.3: remove module-level global) ─────────────────────

@dataclass
class ScoutRunState:
    """Per-run mutable state for a single SCOUT execution."""
    github_token_invalid: bool = False
    searched: int = 0
    returned: int = 0
    accepted: int = 0
    rejected_by_reason: dict = None

    def __post_init__(self):
        if self.rejected_by_reason is None:
            self.rejected_by_reason = {}

    def record_rejection(self, reason: str) -> None:
        self.rejected_by_reason[reason] = self.rejected_by_reason.get(reason, 0) + 1


# ── GitHub helpers ────────────────────────────────────────────────────────────

def _github_headers(state: ScoutRunState) -> dict:
    h = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "HirePath/2.0 (Recruitment Intelligence; https://github.com/kanglesoham11-code/hirepath)",
    }
    if settings.GITHUB_TOKEN and not state.github_token_invalid:
        h["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"
    return h


async def _github_get(client: httpx.AsyncClient, url: str, headers: dict, state: ScoutRunState) -> httpx.Response:
    """Wrapper that retries without Authorization if GitHub returns 401 Bad credentials."""
    limiter = get_github_search_limiter()
    async with limiter:
        resp = await client.get(url, headers=headers)
    if resp.status_code == 401 and "Authorization" in headers:
        state.github_token_invalid = True
        logger.warning(f"GitHub returned 401 for {url}. Configured GITHUB_TOKEN is invalid/expired. Switching to unauthenticated mode.")
        fallback = {k: v for k, v in headers.items() if k != "Authorization"}
        async with limiter:
            resp = await client.get(url, headers=fallback)
    elif resp.status_code in (403, 429):
        await limiter.handle_rate_limit_response(resp.status_code, dict(resp.headers))
    return resp


async def _github_graphql_search(
    client: httpx.AsyncClient,
    query: str,
    headers: dict,
    state: ScoutRunState,
    max_results: int = 100,
) -> list[dict]:
    """Search GitHub users via GraphQL search(type: USER) with pagination.
    Returns empty list and sets state.github_token_invalid on 401.
    """
    limiter = get_github_search_limiter()
    results = []
    cursor = None

    graphql_query = """
    query($q: String!, $first: Int!, $after: String) {
      search(query: $q, type: USER, first: $first, after: $after) {
        userCount
        pageInfo { hasNextPage endCursor }
        nodes {
          ... on User {
            login
            name
            location
            bio
            url
            email
            company
            followers { totalCount }
            repositories(first: 5, orderBy: {field: STARGAZERS, direction: DESC}) {
              totalCount
              nodes {
                name
                url
                stargazerCount
                primaryLanguage { name }
                description
              }
            }
            isHireable
          }
        }
      }
      rateLimit { remaining resetAt }
    }
    """

    while len(results) < max_results:
        batch_size = min(100, max_results - len(results))
        variables = {"q": query, "first": batch_size}
        if cursor:
            variables["after"] = cursor

        async with limiter:
            resp = await client.post(
                GITHUB_GRAPHQL,
                headers=headers,
                json={"query": graphql_query, "variables": variables},
                timeout=20,
            )

        if resp.status_code == 401:
            state.github_token_invalid = True
            logger.warning("GitHub GraphQL returned 401 — token is invalid/expired. Will fall back to REST search.")
            return results  # Caller will use REST fallback

        if resp.status_code in (403, 429):
            await limiter.handle_rate_limit_response(resp.status_code, dict(resp.headers))
            break

        if resp.status_code != 200:
            logger.warning(f"GitHub GraphQL returned {resp.status_code}")
            break

        data = resp.json()
        if "errors" in data:
            logger.warning(f"GitHub GraphQL errors: {data['errors']}")
            break

        search_data = data.get("data", {}).get("search", {})
        nodes = search_data.get("nodes", [])

        # Log rate limit info
        rate_limit = data.get("data", {}).get("rateLimit", {})
        if rate_limit:
            logger.debug(f"GitHub GraphQL rate limit remaining: {rate_limit.get('remaining')}")

        for node in nodes:
            if node and node.get("login"):
                raw_repos = node.get("repositories", {}).get("nodes", []) or []
                top_repos = []
                for r in raw_repos:
                    if r and r.get("name"):
                        lang = r.get("primaryLanguage", {})
                        top_repos.append({
                            "name": r["name"],
                            "url": r.get("url"),
                            "stars": r.get("stargazerCount", 0),
                            "language": lang.get("name") if lang else None,
                            "description": (r.get("description") or "")[:100],
                        })
                results.append({
                    "login": node["login"],
                    "name": node.get("name"),
                    "location": node.get("location"),
                    "bio": node.get("bio"),
                    "url": node.get("url"),
                    "email": node.get("email"),
                    "company": node.get("company"),
                    "followers": node.get("followers", {}).get("totalCount", 0),
                    "public_repos": node.get("repositories", {}).get("totalCount", 0),
                    "hireable": node.get("isHireable"),
                    "top_repos": top_repos,
                })

        page_info = search_data.get("pageInfo", {})
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")

    return results


async def _github_rest_search_users(
    client: httpx.AsyncClient,
    query: str,
    state: ScoutRunState,
    max_results: int = 30,
) -> list[dict]:
    """Search GitHub users via REST /search/users API.
    Works both authenticated and unauthenticated (10 req/min unauth).
    This is the fallback when GraphQL fails due to invalid token.
    """
    limiter = get_github_search_limiter()
    results = []
    page = 1
    per_page = min(max_results, 30)
    # REST search never sends the invalid token
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "HirePath/2.0 (Recruitment Intelligence; https://github.com/kanglesoham11-code/hirepath)",
    }
    if settings.GITHUB_TOKEN and not state.github_token_invalid:
        headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"

    while len(results) < max_results:
        url = f"{GITHUB_API}/search/users?q={query}&per_page={per_page}&page={page}"
        try:
            async with limiter:
                resp = await client.get(url, headers=headers, timeout=20)

            if resp.status_code == 401:
                # Drop auth and retry once
                state.github_token_invalid = True
                headers = {k: v for k, v in headers.items() if k != "Authorization"}
                async with limiter:
                    resp = await client.get(url, headers=headers, timeout=20)

            if resp.status_code in (403, 429):
                await limiter.handle_rate_limit_response(resp.status_code, dict(resp.headers))
                break
            if resp.status_code == 422:
                logger.warning(f"GitHub REST search validation error: {resp.text[:200]}")
                break
            if resp.status_code != 200:
                logger.warning(f"GitHub REST search returned {resp.status_code}")
                break

            data = resp.json()
            items = data.get("items", [])
            if not items:
                break

            for item in items:
                if len(results) >= max_results:
                    break
                # REST /search/users returns minimal info, fetch full profile
                profile_url = item.get("url", "")
                profile = {}
                if profile_url:
                    try:
                        async with limiter:
                            pr = await client.get(profile_url, headers=headers, timeout=10)
                        if pr.status_code == 200:
                            profile = pr.json()
                    except Exception:
                        pass

                results.append({
                    "login": item.get("login", ""),
                    "name": profile.get("name") or item.get("login", ""),
                    "location": profile.get("location"),
                    "bio": profile.get("bio"),
                    "url": item.get("html_url", ""),
                    "email": profile.get("email"),
                    "company": profile.get("company"),
                    "followers": profile.get("followers", 0),
                    "public_repos": profile.get("public_repos", 0),
                    "hireable": profile.get("hireable"),
                })

            page += 1
            # REST search only returns max ~1000 results
            if len(items) < per_page:
                break
        except Exception as e:
            logger.error(f"GitHub REST search error: {e}")
            break

        await asyncio.sleep(0.5)  # Be gentle with unauthenticated rate limits

    return results


async def search_github_users_graphql(
    keywords: list[str],
    target_locations: list[dict] | None,
    max_results: int = 20,
    state: ScoutRunState | None = None,
) -> list[dict]:
    """Search GitHub users via GraphQL, run location resolver on each result.

    Uses all gazetteer entries for search queries, not just 4 cities.
    """
    if state is None:
        state = ScoutRunState()

    from utils.location_resolver import _load_gazetteer
    _, alias_map = _load_gazetteer()

    # Build unique search location terms from the gazetteer
    search_locations = set()
    for entry_key in alias_map:
        entry = alias_map[entry_key]
        if entry.state == "Maharashtra" and entry.kind in ("city", "state"):
            search_locations.add(entry.canonical)

    # If token is invalid/unauthenticated, only search major cities to avoid rate limits
    if state.github_token_invalid or not settings.GITHUB_TOKEN:
        major_cities = {"Mumbai", "Pune", "Nagpur", "Nashik", "Thane", "Navi Mumbai", "Pimpri-Chinchwad"}
        search_locations = {loc for loc in search_locations if loc in major_cities}
    # Prioritize major tech hubs first so candidates are found rapidly in seconds
    priority_order = ["Pune", "Mumbai", "Nagpur", "Nashik", "Thane", "Navi Mumbai", "Pimpri-Chinchwad", "Aurangabad", "Maharashtra"]
    sorted_locs = [loc for loc in priority_order if loc in search_locations]
    sorted_locs.extend([loc for loc in sorted(search_locations) if loc not in priority_order])

    all_candidates = []
    headers = _github_headers(state)

    # Clean and isolate keywords - remove commas and punctuation
    cleaned_keywords = []
    for kw in keywords:
        cleaned = re.sub(r'[,;]+', ' ', kw).strip()
        for sub in cleaned.split():
            sub_clean = sub.strip()
            if sub_clean and len(sub_clean) >= 2 and sub_clean.lower() not in [k.lower() for k in cleaned_keywords]:
                cleaned_keywords.append(sub_clean)
    
    if not cleaned_keywords:
        cleaned_keywords = ["developer"]

    async with httpx.AsyncClient(timeout=25) as client:
        # Loop through keywords and locations
        for kw in cleaned_keywords[:3]:
            if len(all_candidates) >= max_results:
                break
            for location_name in sorted_locs:
                if len(all_candidates) >= max_results:
                    break

                # Quote multi-word places
                loc_q = f'"{location_name}"' if " " in location_name else location_name
                query = f"{kw} location:{loc_q} type:user"
                state.searched += 1

                try:
                    if state.github_token_invalid or not settings.GITHUB_TOKEN:
                        users = await _github_rest_search_users(
                            client, query, state,
                            max_results=min(max_results - len(all_candidates), 30),
                        )
                    else:
                        users = await _github_graphql_search(
                            client, query, headers, state,
                            max_results=min(max_results - len(all_candidates), 30),
                        )
                        if not users and state.github_token_invalid:
                            users = await _github_rest_search_users(
                                client, query, state,
                                max_results=min(max_results - len(all_candidates), 30),
                            )
                    state.returned += len(users)

                    for user in users:
                        location_text = user.get("location", "")
                        loc_result = resolve_for_target(location_text or "", target_locations)

                        if loc_result.accepted:
                            state.accepted += 1
                            user["_location_result"] = loc_result
                            all_candidates.append(user)
                        else:
                            state.record_rejection(loc_result.reason or "no_match")

                except Exception as e:
                    logger.error(f"GitHub search error for {kw} in {location_name}: {e}")

                if len(all_candidates) >= max_results:
                    break

    # Deduplicate by login
    seen_logins = set()
    unique = []
    for c in all_candidates:
        login = (c.get("login") or "").lower()
        if login and login not in seen_logins:
            seen_logins.add(login)
            unique.append(c)

    # Enrich with top repos if not already populated by GraphQL
    enriched = []
    async with httpx.AsyncClient(timeout=15) as client:
        for user in unique[:max_results]:
            repos_data = user.get("top_repos") or []
            if not repos_data and (state.github_token_invalid or not settings.GITHUB_TOKEN):
                try:
                    repos_url = f"{GITHUB_API}/users/{user['login']}/repos?sort=stars&per_page=5"
                    repos_resp = await _github_get(client, repos_url, _github_headers(state), state)
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

            loc_result: LocationResult = user.get("_location_result")
            enriched.append({
                "name": user.get("name") or user.get("login", ""),
                "github_url": user.get("url", "").replace("https://api.github.com/users/", "https://github.com/") if "api.github.com" in user.get("url", "") else user.get("url", ""),
                "email": user.get("email"),
                "location": user.get("location"),
                "bio": user.get("bio"),
                "company": user.get("company"),
                "public_repos": user.get("public_repos", 0),
                "followers": user.get("followers", 0),
                "hireable": user.get("hireable"),
                "top_repos": repos_data,
                "source": "github_maharashtra",
                "raw": user,
                "_location_result": loc_result,
            })

    return enriched


async def search_github_repo_contributors(
    repo: str,
    target_locations: list[dict] | None,
    max_results: int = 10,
    state: ScoutRunState | None = None,
) -> list[dict]:
    """Get contributors from a specific repo, filter for target location devs."""
    if state is None:
        state = ScoutRunState()

    url = f"{GITHUB_API}/repos/{repo}/contributors?per_page={max_results * 3}"
    headers = _github_headers(state)

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await _github_get(client, url, headers, state)
            if resp.status_code != 200:
                return []
            items = resp.json()
    except Exception:
        return []

    candidates = []
    async with httpx.AsyncClient(timeout=10) as client:
        for item in items:
            if len(candidates) >= max_results:
                break

            profile = {}
            try:
                pr = await _github_get(client, item.get("url", ""), headers, state)
                profile = pr.json() if pr.status_code == 200 else {}
            except Exception:
                continue

            location_text = profile.get("location", "")
            loc_result = resolve_for_target(location_text or "", target_locations)

            if not loc_result.accepted:
                state.record_rejection(loc_result.reason or "no_match")
                continue

            state.accepted += 1
            candidates.append({
                "name": profile.get("name") or item.get("login", ""),
                "github_url": item.get("html_url", ""),
                "email": profile.get("email"),
                "location": location_text,
                "bio": profile.get("bio"),
                "company": profile.get("company"),
                "public_repos": profile.get("public_repos", 0),
                "followers": profile.get("followers", 0),
                "source": "github_contributor_maharashtra",
                "contributed_to": repo,
                "contributions": item.get("contributions", 0),
                "raw": item,
                "_location_result": loc_result,
            })

    return candidates


# ── StackOverflow (Live Scraping) ─────────────────────────────────────────────

async def search_stackoverflow_users(
    keywords: list[str],
    target_locations: list[dict] | None,
    max_results: int = 10,
    state: ScoutRunState | None = None,
) -> list[dict]:
    """Search StackOverflow for users with relevant tags located in target region."""
    if state is None:
        state = ScoutRunState()

    candidates = []
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
                        loc_result = resolve_for_target(user_location or "", target_locations)
                        if not loc_result.accepted:
                            state.record_rejection(loc_result.reason or "no_match")
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

                        if role_keywords and not (role_keywords & set(tag_names)):
                            continue

                        profile_url = user.get("website_url", "")
                        github_url = normalize_public_evidence_url(profile_url) or ""
                        if github_url and "github.com" not in github_url:
                            github_url = ""

                        state.accepted += 1
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
                            "_location_result": loc_result,
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

    score = 25  # Base score for qualifying profile
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

    strengths = [f"Matches skills: {', '.join(matched_skills)}"] if matched_skills else ["Active technical profile"]
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
    Location filter: configurable per-role target (defaults to Maharashtra).
    Saves each qualified candidate to DB.
    """
    run_state = ScoutRunState()

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

    # Per-role target locations (Phase 2.6)
    target_locations = role.target_locations or [{"state": "Maharashtra", "country_iso2": "IN", "remote_ok": False}]
    target_label = target_locations[0].get("state", "Maharashtra") if target_locations else "Maharashtra"

    role_keywords = keywords or _extract_keywords(role.title + " " + (role.requirements or ""))

    await log_event("SCOUT", "started", f"Scouting for role: {role.title} | Location: {target_label}", {"keywords": role_keywords, "location": target_label}, role_id=role_id)
    yield {"event": "started", "agent": "SCOUT", "message": f"Starting LIVE candidate search for '{role.title}' in {target_label}", "keywords": role_keywords, "location": target_label}

    all_raw: list[dict] = []

    # 1. GitHub users via GraphQL search - target sufficient candidates to satisfy max_candidates
    gh_target = max(max_candidates * 2, 25)
    yield {"event": "progress", "agent": "SCOUT", "message": f"🔍 Searching GitHub users in {target_label} via GraphQL..."}
    github_users = await search_github_users_graphql(role_keywords, target_locations, max_results=gh_target, state=run_state)
    all_raw.extend(github_users)
    yield {"event": "progress", "agent": "SCOUT", "message": f"Found {len(github_users)} GitHub users in {target_label}"}

    # 2. GitHub contributors from relevant repos if more needed
    if len(all_raw) < max_candidates:
        repo_map = _keywords_to_repos(role_keywords)
        for repo in repo_map[:2]:
            yield {"event": "progress", "agent": "SCOUT", "message": f"Checking {target_label}-based contributors in {repo}..."}
            contribs = await search_github_repo_contributors(repo, target_locations, max_results=5, state=run_state)
            all_raw.extend(contribs)

    # 3. StackOverflow users if more needed
    if len(all_raw) < max_candidates:
        yield {"event": "progress", "agent": "SCOUT", "message": f"🔍 Searching StackOverflow for {target_label} developers..."}
        so_users = await search_stackoverflow_users(role_keywords, target_locations, max_results=8, state=run_state)
        all_raw.extend(so_users)
        yield {"event": "progress", "agent": "SCOUT", "message": f"Found {len(so_users)} StackOverflow users in {target_label}"}

    yield {"event": "progress", "agent": "SCOUT", "message": f"Total raw candidates found: {len(all_raw)}. Scoring and deduplicating..."}

    # Deduplicate FIRST, then apply limit
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

        # Score candidate
        try:
            scoring = await score_candidate(raw, role.description, role.requirements or "")
        except Exception as e:
            logger.error(f"Score failed for {raw.get('name')}: {e}")
            continue

        score_val = float(scoring.get("score", 0))

        # Phase 0.4: Dead threshold — base is 25, so use 25 as actual threshold
        if score_val < 25:
            continue

        # Get location result from the raw candidate
        loc_result: LocationResult | None = raw.get("_location_result")
        location_text = raw.get("location", "")

        # Build location display string
        loc_display = ""
        if loc_result and loc_result.accepted:
            parts = [p for p in [loc_result.city, loc_result.state] if p]
            loc_display = ", ".join(parts) if parts else location_text

        # Convert LocationResult to dict for JSON serialization in raw_data
        raw_copy = _sanitize_for_json(dict(raw))

        # Build screen_brief with primitive values only (no dataclass refs)
        screen_brief = {
            "scout_summary": scoring.get("summary"),
            "strengths": scoring.get("strengths", []),
            "concerns": scoring.get("concerns", []),
            "location": loc_display or location_text or target_label,
            "evidence": evidence,
            "location_confidence": loc_result.confidence if loc_result else None,
            "location_matched": loc_result.matched_text if loc_result else None,
        }

        async with AsyncSessionLocal() as session:
            # Build public profiles
            public_profiles = {}
            if gh:
                public_profiles["github"] = gh.replace("https://github.com/", "")
            
            # Generate avatar from name
            avatar = "".join([n[0] for n in name.split()[:2]]).upper()
            
            # Build score breakdown from heuristic scoring
            strengths = scoring.get("strengths", [])
            concerns = scoring.get("concerns", [])
            score_breakdown = {
                "coreStack": {"score": min(30, int(score_val * 0.4)), "max": 30, "label": "Core Stack", "desc": "; ".join(strengths[:2]), "evidence": raw.get("github_url", "")},
                "distributedSystems": {"score": min(25, int(score_val * 0.3)), "max": 25, "label": "Distributed Systems", "desc": "; ".join(strengths[2:4]), "evidence": ""},
                "experience": {"score": min(25, int(score_val * 0.2)), "max": 25, "label": "Experience", "desc": "", "evidence": ""},
                "recency": {"score": min(20, int(score_val * 0.1)), "max": 20, "label": "Recency", "desc": "", "evidence": ""},
            }
            
            # Build raw location signals
            raw_location_signals = {
                "locationString": location_text or "",
                "company": raw.get("company", "") or "",
                "timezone": "UTC+05:30",
                "note": f"Matched {loc_result.matched_text} in {source}" if loc_result and loc_result.matched_text else "",
            }
            
            # Build consent info (default pending)
            consent = {
                "status": "pending",
                "recordedDate": None,
                "expiryDate": None,
                "daysRemaining": None,
                "channel": None,
                "recordedBy": None,
                "proofHash": None,
                "proofSnippet": None,
                "proofMethod": None,
            }
            
            # Build activity timeline
            activity_timeline = [{
                "action": f"Sourced via {source} search",
                "timestamp": datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M IST"),
                "actor": "HirePath System",
                "type": "system",
            }]
            
            # Generate avatar from name
            avatar = "".join([n[0] for n in name.split()[:2]]).upper()
            
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
                screen_brief=screen_brief,
                last_activity_at=datetime.now(timezone.utc),
                raw_data=raw_copy,
                # Resolved location fields (Phase 2.1)
                location_raw=location_text or None,
                location_city=loc_result.city if loc_result else None,
                location_district=loc_result.district if loc_result else None,
                location_state=loc_result.state if loc_result else None,
                location_country_iso2=loc_result.country_iso2 if loc_result else None,
                location_confidence=loc_result.confidence if loc_result else None,
                location_reason=loc_result.reason if loc_result else None,
                location_source=source,
                location_resolved_at=datetime.now(timezone.utc),
                # Frontend-compatible fields
                public_profiles=public_profiles,
                repos_count=raw.get("public_repos"),
                followers_count=str(raw.get("followers", 0)) if raw.get("followers") else None,
                rep=raw.get("followers"),
                masked_email=mask_email(em) if em else None,
                is_email_revealed=False,
                match_score=int(score_val),
                score_breakdown=score_breakdown,
                raw_location_signals=raw_location_signals,
                consent=consent,
                activity_timeline=activity_timeline,
                title=raw.get("title") or raw.get("bio", "")[:100] if raw.get("bio") else None,
                avatar="".join([n[0] for n in name.split()[:2]]).upper(),
            )
            session.add(c)
            # Update role stage counter dynamically in DB
            role_obj = await session.get(Role, role_id)
            if role_obj:
                role_obj.candidate_count = (role_obj.candidate_count or 0) + 1
                curr_stages = dict(role_obj.pipeline_stages or {})
                curr_stages["sourced"] = curr_stages.get("sourced", 0) + 1
                role_obj.pipeline_stages = curr_stages
            await session.commit()
            await session.refresh(c)
            cid = c.id

        added += 1
        await log_event("SCOUT", "candidate_added", f"Added {raw.get('name')} from {loc_display or location_text} (score={score_val:.0f})", candidate_id=cid, role_id=role_id)
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
                "location": loc_display or location_text or target_label,
                "location_confidence": loc_result.confidence if loc_result else None,
                "summary": scoring.get("summary"),
                "strengths": scoring.get("strengths", []),
            }
        }

        # Smooth UI streaming
        await asyncio.sleep(0.05)

    # Phase 4.3: Log counts by stage
    logger.info(
        f"SCOUT complete: searched={run_state.searched} returned={run_state.returned} "
        f"accepted={run_state.accepted} added={added} "
        f"rejections={run_state.rejected_by_reason}"
    )
    await log_event(
        "SCOUT", "completed",
        f"Scout complete: {added} candidates added from {target_label}",
        data={
            "searched": run_state.searched,
            "returned": run_state.returned,
            "accepted": run_state.accepted,
            "added": added,
            "rejected_by_reason": run_state.rejected_by_reason,
        },
        role_id=role_id,
    )
    yield {"event": "completed", "agent": "SCOUT", "message": f"Scout complete. {added} candidates added to pipeline from {target_label}.", "count": added}


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
                   "ai", "data", "engineer", "software", "cloud", "api", "sql", "c++", "nlp",
                   "product", "manager", "management", "agile", "scrum", "qa", "security", "designer", "architect"]
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
    """Phase 0.5: Map keywords to repos by most specific match first."""
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
    # Phase 0.5: Most specific match first — sort by longest keyword match
    repos = []
    sorted_keywords = sorted(keywords, key=len, reverse=True)
    for kw in sorted_keywords:
        repos.extend(mapping.get(kw.lower(), []))
    return list(dict.fromkeys(repos))  # dedupe while preserving order
