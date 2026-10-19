"""
Location resolver — pure functions, no network.

Input:  raw location text
Output: LocationResult frozen dataclass with city, district, state,
        country_iso2, confidence, matched_text, reason, accepted.
"""
from __future__ import annotations

import csv
import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal

ConfidenceLevel = Literal["high", "medium", "low", "none"]
RejectReason = Literal[
    "past_location",
    "foreign_country",
    "other_state",
    "ambiguous_name",
    "origin_not_residence",
    "no_match",
]

GAZETTEER_PATH = Path(__file__).resolve().parent.parent / "data" / "location_gazetteer.csv"

# ── Past / negation markers ──────────────────────────────────────────────────
PAST_MARKERS = {
    "ex", "former", "formerly", "previously", "alumni", "was",
    "earlier", "moved", "relocated", "left", "before", "used", "prior", "past",
}

# ── Foreign countries / regions ──────────────────────────────────────────────
FOREIGN_COUNTRIES = {
    "sri lanka", "usa", "us", "united states", "united states of america",
    "uk", "united kingdom", "great britain", "england", "scotland", "wales",
    "canada", "uae", "united arab emirates", "dubai", "abu dhabi", "qatar",
    "singapore", "pakistan", "bangladesh", "nepal", "china", "japan",
    "germany", "france", "australia", "new zealand", "south africa",
    "netherlands", "sweden", "switzerland", "ireland", "italy", "spain",
    "portugal", "brazil", "saudi arabia", "oman", "bahrain", "kuwait",
    "indonesia", "malaysia", "thailand", "vietnam", "south korea", "russia",
    "nigeria", "kenya", "egypt", "turkey", "poland", "norway", "denmark",
    "finland", "belgium", "austria", "czech republic", "czechia",
    "philippines", "mexico", "argentina", "colombia", "chile",
    "israel", "jordan", "lebanon", "iran", "iraq",
}

# ── Indian states other than Maharashtra ─────────────────────────────────────
OTHER_INDIAN_STATES = {
    "andhra pradesh", "arunachal pradesh", "assam", "bihar",
    "chhattisgarh", "goa", "gujarat", "haryana", "himachal pradesh",
    "jharkhand", "karnataka", "kerala", "madhya pradesh",
    "manipur", "meghalaya", "mizoram", "nagaland", "odisha",
    "punjab", "rajasthan", "sikkim", "tamil nadu", "telangana",
    "tripura", "uttar pradesh", "uttarakhand", "west bengal",
    "delhi", "new delhi", "ncr", "chandigarh", "puducherry",
    "jammu and kashmir", "ladakh", "andaman and nicobar",
    "lakshadweep", "dadra and nagar haveli",
}

# Cities that exist in multiple Indian states — need qualifier
AMBIGUOUS_NAMES = {"aurangabad"}


@dataclass(frozen=True)
class LocationResult:
    """Immutable result from the location resolver."""
    raw: str
    city: str | None
    district: str | None
    state: str | None
    country_iso2: str | None
    confidence: ConfidenceLevel
    matched_text: str | None
    reason: str | None
    accepted: bool


@dataclass(frozen=True)
class GazetteerEntry:
    canonical: str
    kind: str          # district|city|town|state
    district: str
    state: str
    country_iso2: str
    aliases: list[str]


@lru_cache(maxsize=1)
def _load_gazetteer(path: str | None = None) -> tuple[list[GazetteerEntry], dict[str, GazetteerEntry]]:
    """Load the gazetteer CSV.  Returns (entries, alias_map).

    The alias_map keys are normalised lowercase strings.
    """
    csv_path = Path(path) if path else GAZETTEER_PATH
    entries: list[GazetteerEntry] = []
    alias_map: dict[str, GazetteerEntry] = {}

    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            aliases_raw = row.get("aliases", "") or ""
            aliases = [a.strip() for a in aliases_raw.split("|") if a.strip()]
            entry = GazetteerEntry(
                canonical=row["canonical"].strip(),
                kind=row["kind"].strip(),
                district=row.get("district", "").strip(),
                state=row.get("state", "").strip(),
                country_iso2=row.get("country_iso2", "").strip(),
                aliases=aliases,
            )
            entries.append(entry)
            # Index by canonical (lowered) and each alias
            key = entry.canonical.lower()
            if key not in alias_map or _entry_priority(entry) > _entry_priority(alias_map[key]):
                alias_map[key] = entry
            for alias in aliases:
                akey = alias.lower()
                if akey not in alias_map or _entry_priority(entry) > _entry_priority(alias_map[akey]):
                    alias_map[akey] = entry

    return entries, alias_map


def _entry_priority(entry: GazetteerEntry) -> int:
    """Towns rank higher than cities, which rank higher than districts."""
    return {"town": 4, "city": 3, "district": 1, "state": 0}.get(entry.kind, 0)


# ── Text normalisation ───────────────────────────────────────────────────────

_SEGMENT_RE = re.compile(r"[,;|/·()\n\r\t]+")
_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001FAD6"
    "\U0001FA70-\U0001FAFF"
    "\U00002702-\U000027B0"
    "\U0000FE00-\U0000FE0F"
    "\U0001F900-\U0001F9FF"
    "\U00002600-\U000026FF"
    "\U0000200D"
    "\U0000231A\U0000231B"
    "\U000023E9-\U000023F3"
    "\U000025AA\U000025AB"
    "\U000025B6\U000025C0"
    "\U000025FB-\U000025FE"
    "\U0001F1E0-\U0001F1FF"  # flags
    "]+",
    flags=re.UNICODE,
)
_SYMBOL_RE = re.compile(r"[#•★☆♦♣♠♥◆●○■□▲△▼▽→←↑↓⇒⇐@~`=+\[\]{}\"']+")


def _normalise(text: str) -> str:
    """NFKD, drop accents, lowercase, remove emoji/symbols, hyphens→spaces."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = _EMOJI_RE.sub(" ", text)
    text = _SYMBOL_RE.sub(" ", text)
    text = text.replace("-", " ")
    return text


def _segment(text: str) -> list[str]:
    """Split normalised text on separators, return non-empty segments."""
    return [s.strip() for s in _SEGMENT_RE.split(text) if s.strip()]


# ── Core resolver ────────────────────────────────────────────────────────────

def _has_past_marker(segment: str) -> bool:
    """Check if segment contains past/negation markers."""
    words = segment.split()
    return bool(set(words) & PAST_MARKERS)


def _has_from_prefix(segment: str) -> bool:
    """Check 'from <city>' pattern indicating origin, not residence."""
    return segment.strip().startswith("from ")


def _contains_foreign_country(segment: str) -> str | None:
    """Return the matched foreign country name or None."""
    seg_lower = segment.lower()
    for country in FOREIGN_COUNTRIES:
        if re.search(r"\b" + re.escape(country) + r"\b", seg_lower):
            return country
    return None


def _contains_other_state(segment: str) -> str | None:
    """Return the matched other Indian state name or None."""
    seg_lower = segment.lower()
    for state in OTHER_INDIAN_STATES:
        if re.search(r"\b" + re.escape(state) + r"\b", seg_lower):
            return state
    return None


def _find_best_match(segment: str, alias_map: dict[str, GazetteerEntry]) -> tuple[GazetteerEntry | None, str | None]:
    """Longest whole-token alias match in the segment. Returns (entry, matched_text).
    
    Whole-token matching means: the alias must be surrounded by word boundaries.
    """
    best_entry: GazetteerEntry | None = None
    best_text: str | None = None
    best_len = 0

    for alias_key, entry in alias_map.items():
        if len(alias_key) < 2:
            continue
        # Whole-token matching using word boundaries
        pattern = r"\b" + re.escape(alias_key) + r"\b"
        m = re.search(pattern, segment)
        if m and len(alias_key) > best_len:
            best_entry = entry
            best_text = m.group(0)
            best_len = len(alias_key)

    return best_entry, best_text


def resolve_location(
    raw: str,
    target_state: str = "Maharashtra",
    target_country: str = "IN",
    gazetteer_path: str | None = None,
) -> LocationResult:
    """Resolve a raw location string to a structured LocationResult.
    
    Rules applied in order per segment:
    a. Past/negation markers → reject past_location
    b. Foreign country named → reject foreign_country
    c. Other Indian state → reject other_state
    d. Longest alias wins, whole tokens only
    e. Maharashtra/MH or India named → high confidence
    f. Maharashtra city with no country/state → medium confidence
    g. Ambiguous name without qualifier → low, rejected (ambiguous_name)
    h. "from <city>" → low, rejected (origin_not_residence)
    i. No match → none, no_match
    """
    if not raw or not raw.strip():
        return LocationResult(
            raw=raw or "", city=None, district=None, state=None,
            country_iso2=None, confidence="none", matched_text=None,
            reason="no_match", accepted=False,
        )

    _, alias_map = _load_gazetteer(gazetteer_path)
    normalised = _normalise(raw)
    segments = _segment(normalised)
    if not segments:
        segments = [normalised]

    # Collect information across all segments
    best_match: GazetteerEntry | None = None
    best_matched_text: str | None = None
    has_maharashtra_qualifier = False
    has_india_qualifier = False
    has_foreign_country = False
    foreign_country_name: str | None = None
    has_other_state = False
    other_state_name: str | None = None
    has_past_marker_found = False
    has_from_prefix_match = False

    # We look at ALL segments to collect qualifiers, then decide
    segment_matches: list[tuple[int, GazetteerEntry | None, str | None, bool, bool]] = []

    for i, seg in enumerate(segments):
        past = _has_past_marker(seg)
        from_prefix = _has_from_prefix(seg)
        fc = _contains_foreign_country(seg)
        os_match = _contains_other_state(seg)
        entry, matched = _find_best_match(seg, alias_map)

        if past:
            has_past_marker_found = True
        if from_prefix:
            has_from_prefix_match = True
        if fc:
            has_foreign_country = True
            foreign_country_name = fc
        if os_match:
            has_other_state = True
            other_state_name = os_match

        # Check if segment mentions maharashtra, mh, or india
        if re.search(r"\bmaharashtra\b", seg) or re.search(r"\bmh\b", seg):
            has_maharashtra_qualifier = True
        if re.search(r"\bindia\b", seg) or re.search(r"\bin\b", seg) and len(seg.split()) <= 2:
            has_india_qualifier = True

        segment_matches.append((i, entry, matched, past, from_prefix))

        # Track the best match across segments
        if entry and entry.state == target_state:
            if best_match is None or _entry_priority(entry) > _entry_priority(best_match):
                best_match = entry
                best_matched_text = matched

    # ── Decision logic ───────────────────────────────────────────────────

    # If a past marker appears in the same segment as the match, reject
    if best_match:
        for i, entry, matched, past, from_prefix in segment_matches:
            if entry == best_match and past:
                return LocationResult(
                    raw=raw, city=best_match.canonical if best_match.kind in ("city", "town") else None,
                    district=best_match.district, state=best_match.state,
                    country_iso2=best_match.country_iso2, confidence="low",
                    matched_text=best_matched_text, reason="past_location", accepted=False,
                )

    # If there is a past marker anywhere and no direct match without it, reject
    if has_past_marker_found and best_match:
        # Check if the best match is in a segment without a past marker
        match_has_past = False
        for i, entry, matched, past, from_prefix in segment_matches:
            if entry == best_match and past:
                match_has_past = True
        if match_has_past:
            return LocationResult(
                raw=raw, city=best_match.canonical if best_match.kind in ("city", "town") else None,
                district=best_match.district, state=best_match.state,
                country_iso2=best_match.country_iso2, confidence="low",
                matched_text=best_matched_text, reason="past_location", accepted=False,
            )

    # Foreign country present → reject
    if has_foreign_country and best_match:
        return LocationResult(
            raw=raw, city=best_match.canonical if best_match.kind in ("city", "town") else None,
            district=best_match.district, state=best_match.state,
            country_iso2=best_match.country_iso2, confidence="low",
            matched_text=best_matched_text, reason="foreign_country", accepted=False,
        )
    if has_foreign_country and not best_match:
        return LocationResult(
            raw=raw, city=None, district=None, state=None,
            country_iso2=None, confidence="none",
            matched_text=None, reason="foreign_country", accepted=False,
        )

    # Other Indian state present without Maharashtra match → reject
    if has_other_state and not best_match:
        return LocationResult(
            raw=raw, city=None, district=None, state=other_state_name,
            country_iso2="IN", confidence="none",
            matched_text=None, reason="other_state", accepted=False,
        )
    if has_other_state and best_match and not has_maharashtra_qualifier:
        # The match could be ambiguous (Aurangabad in Bihar vs Maharashtra)
        if best_matched_text and best_matched_text.lower() in AMBIGUOUS_NAMES:
            return LocationResult(
                raw=raw, city=best_match.canonical if best_match.kind in ("city", "town") else None,
                district=best_match.district, state=best_match.state,
                country_iso2=best_match.country_iso2, confidence="low",
                matched_text=best_matched_text, reason="ambiguous_name", accepted=False,
            )

    # No match at all
    if not best_match:
        return LocationResult(
            raw=raw, city=None, district=None, state=None,
            country_iso2=None, confidence="none",
            matched_text=None, reason="no_match", accepted=False,
        )

    # "from <city>" pattern — likely origin, not current residence
    for i, entry, matched, past, from_prefix in segment_matches:
        if entry == best_match and from_prefix:
            return LocationResult(
                raw=raw, city=best_match.canonical if best_match.kind in ("city", "town") else None,
                district=best_match.district, state=best_match.state,
                country_iso2=best_match.country_iso2, confidence="low",
                matched_text=best_matched_text, reason="origin_not_residence", accepted=False,
            )

    # Ambiguous name without qualifier
    if best_matched_text and best_matched_text.lower() in AMBIGUOUS_NAMES and not has_maharashtra_qualifier:
        return LocationResult(
            raw=raw, city=best_match.canonical if best_match.kind in ("city", "town") else None,
            district=best_match.district, state=best_match.state,
            country_iso2=best_match.country_iso2, confidence="low",
            matched_text=best_matched_text, reason="ambiguous_name", accepted=False,
        )

    # ── Confidence determination ─────────────────────────────────────────
    city = best_match.canonical if best_match.kind in ("city", "town") else None
    district = best_match.district
    state = best_match.state

    if has_maharashtra_qualifier or has_india_qualifier:
        confidence: ConfidenceLevel = "high"
    elif best_match.kind == "state":
        confidence = "high"  # "Maharashtra" itself
    else:
        confidence = "medium"

    return LocationResult(
        raw=raw,
        city=city,
        district=district,
        state=state,
        country_iso2=best_match.country_iso2,
        confidence=confidence,
        matched_text=best_matched_text,
        reason=None,
        accepted=True,
    )


def resolve_for_target(
    raw: str,
    target_locations: list[dict] | None = None,
) -> LocationResult:
    """Resolve location against a role's target_locations list.
    
    target_locations is a list of dicts:
        [{"state": "Maharashtra", "cities": ["Pune"], "country_iso2": "IN", "remote_ok": false}]
    
    Default target: Maharashtra, IN.
    """
    if not target_locations:
        target_locations = [{"state": "Maharashtra", "country_iso2": "IN", "remote_ok": False}]

    # For now we resolve against the first target (Maharashtra)
    target = target_locations[0]
    result = resolve_location(
        raw,
        target_state=target.get("state", "Maharashtra"),
        target_country=target.get("country_iso2", "IN"),
    )

    # If target specifies specific cities, check the result matches
    cities = target.get("cities", [])
    if cities and result.accepted and result.city:
        if result.city not in cities:
            return LocationResult(
                raw=result.raw, city=result.city, district=result.district,
                state=result.state, country_iso2=result.country_iso2,
                confidence="low", matched_text=result.matched_text,
                reason="outside_target_cities", accepted=False,
            )

    return result
