"""Validation helpers for public, recruiter-verifiable source evidence.

HirePath only presents a candidate when SCOUT captured at least one public
profile or repository link from an allowed source.  The helpers in this module
are deliberately shared by every workflow stage so an old or manually inserted
record cannot bypass that rule.
"""
from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
import re
from typing import Any
from urllib.parse import urlsplit, urlunsplit


ALLOWED_EVIDENCE_HOSTS = frozenset(
    {
        "github.com",
        "www.github.com",
        "stackoverflow.com",
        "www.stackoverflow.com",
    }
)
ALLOWED_EVIDENCE_TYPES = frozenset(
    {"github_profile", "github_repository", "stackoverflow_profile"}
)
_GITHUB_PATH_PART = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")


def normalize_public_evidence_url(value: object) -> str | None:
    """Return a safe canonical public-profile URL, or ``None`` when invalid.

    Evidence is intentionally limited to the public sources SCOUT retrieves.
    Removing query strings and fragments keeps recruiter links stable and avoids
    presenting tracking or injected URL content in the dashboard.
    """
    if not isinstance(value, str) or not value.strip():
        return None

    try:
        parsed = urlsplit(value.strip())
    except ValueError:
        return None

    if parsed.scheme.lower() != "https" or not parsed.hostname:
        return None
    try:
        port = parsed.port
    except ValueError:
        return None
    if parsed.username or parsed.password or port not in {None, 443}:
        return None

    host = parsed.hostname.lower()
    if host not in ALLOWED_EVIDENCE_HOSTS:
        return None

    path_parts = [part for part in parsed.path.split("/") if part]
    if host.endswith("github.com"):
        # SCOUT captures only canonical profile (one segment) and repository
        # (two segments) pages. Reject settings, issue, and crafted paths.
        if not 1 <= len(path_parts) <= 2 or not all(
            _GITHUB_PATH_PART.fullmatch(part) for part in path_parts
        ):
            return None
    elif (
        not 2 <= len(path_parts) <= 3
        or path_parts[0].lower() != "users"
        or not path_parts[1].isdigit()
    ):
        # Stack Overflow profile URLs are public and recruiter-reviewable.
        return None

    canonical_host = host.removeprefix("www.")
    canonical_path = "/" + "/".join(path_parts)
    return urlunsplit((parsed.scheme.lower(), canonical_host, canonical_path, "", ""))


def normalize_source_evidence(items: object) -> list[dict[str, str]]:
    """Normalize a JSON-compatible evidence list and discard unsafe entries."""
    if not isinstance(items, Iterable) or isinstance(items, (str, bytes, dict)):
        return []

    normalized: list[dict[str, str]] = []
    seen_urls: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        url = normalize_public_evidence_url(item.get("url"))
        if not url or url in seen_urls:
            continue

        label = str(item.get("label") or "Public source").strip()
        evidence_type = str(item.get("type") or "public_profile").strip().lower()
        if not label or evidence_type not in ALLOWED_EVIDENCE_TYPES:
            continue

        host = urlsplit(url).hostname or ""
        parts = [part for part in urlsplit(url).path.split("/") if part]
        is_compatible = (
            (evidence_type == "github_profile" and host == "github.com" and len(parts) == 1)
            or (evidence_type == "github_repository" and host == "github.com" and len(parts) == 2)
            or (evidence_type == "stackoverflow_profile" and host == "stackoverflow.com" and parts[:1] == ["users"])
        )
        if not is_compatible:
            continue

        entry = {
            "id": f"E{len(normalized) + 1}",
            "type": evidence_type[:50],
            "label": label[:180],
            "url": url,
        }
        detail = item.get("detail")
        if isinstance(detail, str) and detail.strip():
            entry["detail"] = detail.strip()[:240]
        normalized.append(entry)
        seen_urls.add(url)

    return normalized


def candidate_has_verifiable_evidence(candidate: Any) -> bool:
    """True only for records captured by SCOUT with safe public evidence."""
    return bool(
        getattr(candidate, "source_verified", False)
        and isinstance(getattr(candidate, "source_captured_at", None), datetime)
        and normalize_source_evidence(getattr(candidate, "source_evidence", None))
    )
