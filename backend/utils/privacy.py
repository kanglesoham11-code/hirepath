"""Signed candidate privacy links used in outreach email.

The token carries only a candidate id, an action, and an expiry.  It is signed
with the API secret, so a recipient cannot opt out or delete another profile by
editing a URL.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Literal
from urllib.parse import urlencode

from config import settings


PrivacyAction = Literal["opt_out", "delete"]


class PrivacyTokenError(ValueError):
    """Raised when a privacy token is unavailable, invalid, or expired."""


def _secret() -> bytes:
    if not settings.API_SECRET_KEY:
        raise PrivacyTokenError("API_SECRET_KEY is required to create privacy links.")
    return settings.API_SECRET_KEY.encode("utf-8")


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    decoded = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    # Phase 0.2: Strict round-trip — reject if re-encoding differs
    re_encoded = base64.urlsafe_b64encode(decoded).decode("ascii").rstrip("=")
    if re_encoded != value:
        raise PrivacyTokenError("The privacy link is invalid.")
    return decoded


def create_privacy_token(candidate_id: int, action: PrivacyAction) -> str:
    if action not in ("opt_out", "delete"):
        raise ValueError(f"Unsupported privacy action: {action}")

    ttl_seconds = max(1, settings.PRIVACY_TOKEN_TTL_DAYS) * 24 * 60 * 60
    payload = {
        "candidate_id": candidate_id,
        "action": action,
        "exp": int(time.time()) + ttl_seconds,
    }
    raw_payload = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    signature = hmac.new(_secret(), raw_payload, hashlib.sha256).digest()
    return f"{_b64encode(raw_payload)}.{_b64encode(signature)}"


def verify_privacy_token(token: str, expected_action: PrivacyAction) -> int:
    try:
        encoded_payload, encoded_signature = token.split(".", 1)
        raw_payload = _b64decode(encoded_payload)
        signature = _b64decode(encoded_signature)
        expected_signature = hmac.new(_secret(), raw_payload, hashlib.sha256).digest()
        if not hmac.compare_digest(signature, expected_signature):
            raise PrivacyTokenError("The privacy link is invalid.")
        payload = json.loads(raw_payload)
        if payload.get("action") != expected_action:
            raise PrivacyTokenError("The privacy link is for a different action.")
        if not isinstance(payload.get("candidate_id"), int):
            raise PrivacyTokenError("The privacy link is invalid.")
        if int(payload.get("exp", 0)) < int(time.time()):
            raise PrivacyTokenError("This privacy link has expired.")
        return payload["candidate_id"]
    except PrivacyTokenError:
        raise
    except Exception as exc:
        raise PrivacyTokenError("The privacy link is invalid.") from exc


def privacy_links(candidate_id: int) -> dict[str, str]:
    """Return confirmation-page URLs for opting out and deleting data."""
    base_url = settings.FRONTEND_URL.rstrip("/")
    return {
        action: f"{base_url}/?{urlencode({'privacy_action': action, 'token': create_privacy_token(candidate_id, action)})}"
        for action in ("opt_out", "delete")
    }
