from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from database import CandidateStage, RoleStatus

# ── Role ──────────────────────────────────────────────────────────────────────

class RoleCreate(BaseModel):
    title: str
    description: str
    requirements: Optional[str] = None

class RoleOut(BaseModel):
    id: int
    title: str
    description: str
    requirements: Optional[str]
    status: RoleStatus
    created_at: datetime
    class Config:
        from_attributes = True

# ── Candidate ─────────────────────────────────────────────────────────────────

class CandidateOut(BaseModel):
    id: int
    role_id: int
    name: str
    email: Optional[str]
    linkedin_url: Optional[str]
    github_url: Optional[str]
    source: Optional[str]
    stage: CandidateStage
    score: Optional[float]
    screen_brief: Optional[Dict[str, Any]]
    outreach_count: int
    last_contacted_at: Optional[datetime]
    last_activity_at: Optional[datetime]
    interview_time: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class CandidateCreate(BaseModel):
    role_id: int
    name: str
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    source: Optional[str] = "manual"
    notes: Optional[str] = None

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
    duration_minutes: int = 45

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
    class Config:
        from_attributes = True

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
