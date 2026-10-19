from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from database import CandidateStage, RoleStatus

# ── Role ──────────────────────────────────────────────────────────────────────

class RoleCreate(BaseModel):
    title: str
    description: str
    requirements: Optional[str] = None
    target_locations: Optional[List[Dict[str, Any]]] = None
    department: Optional[str] = None
    location: Optional[str] = None
    hiring_lead: Optional[str] = None
    sourcing_criteria: Optional[Dict[str, Any]] = None

class RoleUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    hiring_lead: Optional[str] = None
    status: Optional[str] = None
    sourcing_criteria: Optional[Dict[str, Any]] = None

class RoleOut(BaseModel):
    id: str
    req_id: Optional[str]
    title: str
    department: Optional[str]
    location: Optional[str]
    status: str
    candidate_count: int
    pipeline_stages: Dict[str, int]
    health_score: int
    health_status: Optional[str]
    last_activity: Optional[Dict[str, str]]
    hiring_lead: Optional[str]
    audit_verified_time: Optional[str]
    total_sourced: Optional[int]
    total_screened: Optional[int]
    total_outreach: Optional[int]
    total_replied: Optional[int]
    total_interview: Optional[int]
    total_offer: Optional[int]
    created_at: Optional[str]
    updated_at: Optional[str]

    model_config = ConfigDict(from_attributes=True)

# ── Candidate ─────────────────────────────────────────────────────────────────

class PublicProfiles(BaseModel):
    github: str
    stackoverflow: Optional[str] = None

class ScoreBreakdownFactor(BaseModel):
    score: int
    max: int
    label: str
    desc: str
    evidence: str

class ScoreBreakdown(BaseModel):
    coreStack: ScoreBreakdownFactor
    distributedSystems: ScoreBreakdownFactor
    experience: ScoreBreakdownFactor
    recency: ScoreBreakdownFactor

class RawLocationSignals(BaseModel):
    locationString: str
    company: str
    timezone: str
    note: str

class ConsentInfo(BaseModel):
    status: str  # recorded, pending, withdrawn
    recordedDate: Optional[str] = None
    expiryDate: Optional[str] = None
    daysRemaining: Optional[int] = None
    channel: Optional[str] = None
    recordedBy: Optional[str] = None
    proofHash: Optional[str] = None
    proofSnippet: Optional[str] = None
    proofMethod: Optional[str] = None

class ActivityTimelineItem(BaseModel):
    action: str
    timestamp: str
    actor: str
    type: str  # system, consent, recruiter, audit

class CandidateOut(BaseModel):
    id: str
    name: str
    roleId: str
    roleTitle: str
    title: str
    avatar: str
    publicProfiles: PublicProfiles
    reposCount: Optional[int]
    followersCount: Optional[str]
    rep: Optional[int]
    email: str
    maskedEmail: str
    isEmailRevealed: bool
    matchScore: int
    scoreBreakdown: ScoreBreakdown
    location: str
    locationConfidence: str
    rawLocationSignals: RawLocationSignals
    source: str
    stage: str
    lastAction: Dict[str, str]
    consent: ConsentInfo
    activityTimeline: List[ActivityTimelineItem]
    created_at: Optional[str]
    updated_at: Optional[str]

    model_config = ConfigDict(from_attributes=True)

class ConsentRequest(BaseModel):
    """A recruiter's explicit record that a candidate agreed to be contacted."""
    confirmed: bool
    source: str = Field(min_length=3, max_length=200)

    @field_validator("source")
    @classmethod
    def normalize_source(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 3:
            raise ValueError("Consent source must contain at least three non-space characters.")
        return value

class PrivacyRequest(BaseModel):
    """A signed, candidate-specific token from an outreach email."""
    token: str = Field(min_length=20, max_length=2000)

# ── Agent Requests ────────────────────────────────────────────────────────────

class ScoutRequest(BaseModel):
    role_id: int
    keywords: Optional[List[str]] = None
    max_candidates: int = 20

class ScreenRequest(BaseModel):
    candidate_id: int

class EngageRequest(BaseModel):
    candidate_ids: List[int]
    custom_message: Optional[str] = None

class CoordRequest(BaseModel):
    candidate_id: int
    interviewer_email: str
    duration_minutes: int = Field(default=45, ge=15, le=480)

class TrackRequest(BaseModel):
    role_id: Optional[int] = None  # None = all roles

# ── Agent Log ─────────────────────────────────────────────────────────────────

class AgentLogOut(BaseModel):
    id: int
    agent: str
    event_type: str
    message: str
    data: Optional[Dict[str, Any]]
    role_id: Optional[int]
    candidate_id: Optional[int]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# ── Pipeline ──────────────────────────────────────────────────────────────────

class PipelineStageCount(BaseModel):
    stage: str
    count: int

class PipelineHealth(BaseModel):
    role_id: int
    role_title: str
    total_candidates: int
    stage_breakdown: List[PipelineStageCount]
    stale_candidates: List[CandidateOut]
    bottleneck: Optional[str]
    insights: List[str]
    health_score: float  # 0–100

# ── Consent Records ───────────────────────────────────────────────────────────

class ConsentRecordOut(BaseModel):
    id: str
    candidate_name: str
    masked_email: str
    role: str
    status: str
    recorded_date: Optional[str]
    expiry_date: Optional[str]
    days_remaining: int
    proof_method: Optional[str]
    proof_snippet: Optional[str]
    proof_hash: Optional[str]
    scope: Optional[str]
    recorded_by: Optional[str]
    created_at: Optional[str]

    model_config = ConfigDict(from_attributes=True)

# ── Outreach & Schedule ──────────────────────────────────────────────────────

class OutreachRequest(BaseModel):
    candidate_ids: List[int]
    template_id: Optional[str] = None

class ScheduleRequest(BaseModel):
    candidate_id: int
    round: str
    duration: str
    slot: str
    note: Optional[str] = None

# ── Reveal Email ──────────────────────────────────────────────────────────────

class RevealEmailRequest(BaseModel):
    candidate_id: int