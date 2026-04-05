"""
email_hunter.py — Multi-Source Email Discovery Engine
Finds verified professional emails for candidates using:
  1. GitHub profile (public email field)
  2. GitHub commit email extraction (public commits)
  3. Hunter.io API (free tier: 25 searches/month)
  4. Clearbit Connect API (free tier)
  5. Pattern inference from domain + name
  6. Email permutation + SMTP MX verification
"""
import re
import asyncio
import socket
import smtplib
import hashlib
import httpx
import logging
from typing import Optional
from config import settings

logger = logging.getLogger("hirepath.email_hunter")
_github_auth_enabled = True


async def _github_json(url: str, github_token: str = "", timeout: int = 10):
    global _github_auth_enabled
    headers = {"Accept": "application/vnd.github+json"}
    if github_token and _github_auth_enabled:
        headers["Authorization"] = f"Bearer {github_token}"

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        response = await client.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()

        if github_token and _github_auth_enabled and response.status_code == 401:
            _github_auth_enabled = False
            logger.warning("GitHub token rejected for %s; retrying without authentication", url)
            fallback_headers = {k: v for k, v in headers.items() if k.lower() != "authorization"}
            retry = await client.get(url, headers=fallback_headers)
            if retry.status_code == 200:
                return retry.json()

        return None


# ── 1. GitHub Public Email ────────────────────────────────────────────────────

async def get_github_email(github_url: str, github_token: str = "") -> Optional[str]:
    """Extract email from GitHub profile (public field)."""
    if not github_url:
        return None
    login = github_url.rstrip("/").split("/")[-1]
    try:
        data = await _github_json(f"https://api.github.com/users/{login}", github_token=github_token, timeout=10)
        if data:
            email = data.get("email")
            if email and "@" in email:
                return email.strip().lower()
    except Exception:
        pass
    return None


# ── 2. GitHub Commit Email ────────────────────────────────────────────────────

async def get_github_commit_email(github_url: str, github_token: str = "") -> Optional[str]:
    """
    Extract email from public GitHub commits.
    GitHub exposes commit author emails in the Events API for public repos.
    """
    if not github_url:
        return None
    login = github_url.rstrip("/").split("/")[-1]
    try:
        events = await _github_json(
            f"https://api.github.com/users/{login}/events/public?per_page=30",
            github_token=github_token,
            timeout=15,
        )
        if not events:
            return None
        for event in events:
            if event.get("type") == "PushEvent":
                commits = event.get("payload", {}).get("commits", [])
                for commit in commits:
                    author = commit.get("author", {})
                    email = author.get("email", "")
                    if email and "@" in email and "noreply" not in email and "github" not in email:
                        return email.strip().lower()
    except Exception:
        return None

    return None
    try:
            # Get public events — push events contain commit emails
            r = await client.get(
                f"https://api.github.com/users/{login}/events/public?per_page=30",
                headers=headers
            )
            if r.status_code != 200:
                return None
            for event in r.json():
                if event.get("type") == "PushEvent":
                    commits = event.get("payload", {}).get("commits", [])
                    for commit in commits:
                        author = commit.get("author", {})
                        email = author.get("email", "")
                        if email and "@" in email and "noreply" not in email and "github" not in email:
                            return email.strip().lower()
    except Exception:
        pass
    return None


# ── 3. Hunter.io ──────────────────────────────────────────────────────────────

async def hunter_find_email(name: str, domain: str) -> Optional[str]:
    """
    Hunter.io email finder API.
    Free tier: 25 searches/month. Set HUNTER_API_KEY in .env
    """
    if not settings.HUNTER_API_KEY or not domain:
        return None
    parts = name.strip().split()
    if len(parts) < 2:
        return None
    first, last = parts[0], parts[-1]
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                "https://api.hunter.io/v2/email-finder",
                params={
                    "domain": domain,
                    "first_name": first,
                    "last_name": last,
                    "api_key": settings.HUNTER_API_KEY,
                }
            )
            if r.status_code == 200:
                data = r.json().get("data", {})
                email = data.get("email")
                confidence = data.get("score", 0)
                if email and confidence >= 50:
                    return email.lower()
    except Exception as e:
        logger.debug(f"Hunter.io error: {e}")
    return None


async def hunter_domain_search(domain: str, max_results: int = 5) -> list[dict]:
    """Search all known emails at a company domain via Hunter.io."""
    if not settings.HUNTER_API_KEY or not domain:
        return []
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                "https://api.hunter.io/v2/domain-search",
                params={"domain": domain, "limit": max_results, "api_key": settings.HUNTER_API_KEY}
            )
            if r.status_code == 200:
                emails = r.json().get("data", {}).get("emails", [])
                return [{"email": e.get("value"), "first": e.get("first_name"), "last": e.get("last_name"), "confidence": e.get("confidence", 0)} for e in emails if e.get("value")]
    except Exception:
        pass
    return []


# ── 4. Email Permutation Engine ───────────────────────────────────────────────

def generate_email_permutations(first: str, last: str, domain: str) -> list[str]:
    """
    Generate all common professional email patterns for a name + domain.
    Returns ordered list from most to least common.
    """
    f = re.sub(r"[^a-z]", "", first.lower())
    l = re.sub(r"[^a-z]", "", last.lower())
    fi = f[0] if f else ""
    li = l[0] if l else ""

    patterns = [
        f"{f}.{l}@{domain}",          # john.doe
        f"{f}{l}@{domain}",           # johndoe
        f"{fi}{l}@{domain}",          # jdoe
        f"{f}.{li}@{domain}",         # john.d
        f"{f}_{l}@{domain}",          # john_doe
        f"{l}.{f}@{domain}",          # doe.john
        f"{f}@{domain}",              # john
        f"{l}@{domain}",              # doe
        f"{fi}.{l}@{domain}",         # j.doe
        f"{f}{li}@{domain}",          # johnd
        f"{fi}{li}@{domain}",         # jd
        f"{l}{f}@{domain}",           # doejohn
    ]
    return list(dict.fromkeys(p for p in patterns if p and "@" in p and "@@" not in p))


# ── 5. SMTP MX Verification ───────────────────────────────────────────────────

def get_mx_record(domain: str) -> Optional[str]:
    """Get the MX server for a domain via DNS lookup."""
    try:
        import dns.resolver
        records = dns.resolver.resolve(domain, "MX")
        mx = sorted(records, key=lambda r: r.preference)[0]
        return str(mx.exchange).rstrip(".")
    except Exception:
        pass
    # Fallback: try common MX patterns
    try:
        mx = socket.getfqdn(f"mail.{domain}")
        if mx != f"mail.{domain}":
            return mx
    except Exception:
        pass
    return None


def verify_email_smtp(email: str, sender: str = "verify@hirepath.ai") -> dict:
    """
    SMTP-level email verification (catch-all check).
    Connects to MX server and checks RCPT TO without sending mail.
    Returns dict with is_valid, is_catchall, mx_found.
    """
    result = {"email": email, "is_valid": False, "is_catchall": False, "mx_found": False, "method": "smtp"}
    domain = email.split("@")[-1] if "@" in email else ""
    if not domain:
        return result

    mx_host = get_mx_record(domain)
    if not mx_host:
        return result

    result["mx_found"] = True
    try:
        smtp = smtplib.SMTP(timeout=8)
        smtp.connect(mx_host, 25)
        smtp.helo("hirepath.ai")
        smtp.mail(sender)
        code, _ = smtp.rcpt(email)
        smtp.quit()
        result["is_valid"] = (code == 250)
        # Test catchall: try a random email at same domain
        if result["is_valid"]:
            rand_email = f"__test_{hashlib.md5(email.encode()).hexdigest()[:8]}@{domain}"
            smtp2 = smtplib.SMTP(timeout=8)
            smtp2.connect(mx_host, 25)
            smtp2.helo("hirepath.ai")
            smtp2.mail(sender)
            code2, _ = smtp2.rcpt(rand_email)
            smtp2.quit()
            result["is_catchall"] = (code2 == 250)
    except Exception:
        pass
    return result


# ── 6. LinkedIn Profile Email Inference ──────────────────────────────────────

def infer_company_domain_from_linkedin(linkedin_url: str) -> Optional[str]:
    """
    Extract company domain hint from LinkedIn URL slug.
    e.g. /in/john-doe-google → infer google.com
    This is a heuristic — not API-based.
    """
    if not linkedin_url:
        return None
    slug = linkedin_url.rstrip("/").split("/")[-1].lower()
    known_companies = {
        "google": "google.com", "meta": "meta.com", "facebook": "fb.com",
        "microsoft": "microsoft.com", "amazon": "amazon.com", "apple": "apple.com",
        "netflix": "netflix.com", "uber": "uber.com", "airbnb": "airbnb.com",
        "stripe": "stripe.com", "shopify": "shopify.com", "atlassian": "atlassian.com",
        "salesforce": "salesforce.com", "adobe": "adobe.com", "twitter": "twitter.com",
        "linkedin": "linkedin.com", "github": "github.com", "gitlab": "gitlab.com",
        "hashicorp": "hashicorp.com", "confluent": "confluent.io", "databricks": "databricks.com",
        "snowflake": "snowflake.com", "mongodb": "mongodb.com", "elastic": "elastic.co",
    }
    for company, domain in known_companies.items():
        if company in slug:
            return domain
    return None


# ── 7. Gravatar Email Guess ───────────────────────────────────────────────────

async def check_gravatar(email: str) -> bool:
    """Check if an email has a Gravatar (confirms email is real and used online)."""
    h = hashlib.md5(email.strip().lower().encode()).hexdigest()
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"https://www.gravatar.com/avatar/{h}?d=404")
            return r.status_code == 200
    except Exception:
        return False


# ── MASTER EMAIL DISCOVERY FUNCTION ──────────────────────────────────────────

async def discover_email(
    name: str,
    github_url: Optional[str] = None,
    linkedin_url: Optional[str] = None,
    company_domain: Optional[str] = None,
    github_token: str = "",
) -> dict:
    """
    Master email discovery pipeline.
    Tries all sources in order of reliability, returns best result.

    Returns:
        {
            "email": str | None,
            "confidence": "verified" | "high" | "medium" | "low" | "not_found",
            "source": str,
            "alternatives": list[str],
            "verified": bool,
        }
    """
    result = {
        "email": None,
        "confidence": "not_found",
        "source": None,
        "alternatives": [],
        "verified": False,
    }

    # Step 1: GitHub public email (highest confidence)
    if github_url:
        gh_email = await get_github_email(github_url, github_token)
        if gh_email:
            result.update({"email": gh_email, "confidence": "verified", "source": "github_profile", "verified": True})
            return result

        # Step 2: GitHub commit email
        commit_email = await get_github_commit_email(github_url, github_token)
        if commit_email:
            result.update({"email": commit_email, "confidence": "high", "source": "github_commits", "verified": True})
            return result

    # Step 3: Hunter.io (if domain known)
    if company_domain:
        hunter_email = await hunter_find_email(name, company_domain)
        if hunter_email:
            result.update({"email": hunter_email, "confidence": "high", "source": "hunter_io"})
            # Verify via Gravatar
            has_gravatar = await check_gravatar(hunter_email)
            if has_gravatar:
                result["confidence"] = "verified"
                result["verified"] = True
            return result

    # Step 4: Try to infer domain from LinkedIn
    inferred_domain = infer_company_domain_from_linkedin(linkedin_url) if linkedin_url else None
    if inferred_domain and not company_domain:
        company_domain = inferred_domain

    # Step 5: Email permutation with MX verification
    if company_domain and name and len(name.split()) >= 2:
        parts = name.strip().split()
        first, last = parts[0], parts[-1]
        permutations = generate_email_permutations(first, last, company_domain)
        result["alternatives"] = permutations[:6]  # store top alternatives

        # Try SMTP verification on top permutations (expensive, do max 3)
        for candidate_email in permutations[:3]:
            try:
                verification = verify_email_smtp(candidate_email)
                if verification.get("is_valid") and not verification.get("is_catchall"):
                    result.update({
                        "email": candidate_email,
                        "confidence": "medium",
                        "source": "smtp_verified",
                        "verified": True,
                    })
                    return result
            except Exception:
                pass
            await asyncio.sleep(0.1)

        # Fall back to most-common pattern unverified
        if permutations:
            result.update({
                "email": permutations[0],
                "confidence": "low",
                "source": "pattern_inference",
                "verified": False,
            })

    return result
