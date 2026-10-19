from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Boolean, String, Text, Float, DateTime, Enum, ForeignKey, JSON, Integer, false, func
from datetime import datetime
from typing import Optional, List
import enum
from config import settings

db_url = settings.DATABASE_URL
engine_kwargs = {"echo": False}

if db_url.startswith("sqlite+aiosqlite://"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_async_engine(db_url, **engine_kwargs)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

# Frontend-compatible stages
class CandidateStage(str, enum.Enum):
    SOURCED = "sourced"
    SCREENED = "screened"
    OUTREACH = "outreach"
    REPLIED = "replied"
    INTERVIEW = "interview"
    OFFER = "offer"
    HIRED = "hired"
    REJECTED = "rejected"
    CLOSED = "closed"  # Replaces STALE

class RoleStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    FILLED = "filled"

class Role(Base):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    requirements: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[RoleStatus] = mapped_column(Enum(RoleStatus), default=RoleStatus.ACTIVE)
    # Per-role target locations (Phase 2.6).  Default: Maharashtra.
    target_locations: Mapped[Optional[list[dict]]] = mapped_column(JSON, nullable=True)
    # Frontend-compatible fields
    req_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    candidate_count: Mapped[int] = mapped_column(Integer, default=0)
    pipeline_stages: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    health_score: Mapped[int] = mapped_column(Integer, default=70)
    health_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    hiring_lead: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    audit_verified_time: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    total_sourced: Mapped[int] = mapped_column(Integer, default=0)
    total_screened: Mapped[int] = mapped_column(Integer, default=0)
    total_outreach: Mapped[int] = mapped_column(Integer, default=0)
    total_replied: Mapped[int] = mapped_column(Integer, default=0)
    total_interview: Mapped[int] = mapped_column(Integer, default=0)
    total_offer: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    candidates: Mapped[List["Candidate"]] = relationship("Candidate", back_populates="role")

class Candidate(Base):
    __tablename__ = "candidates"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    github_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    resume_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    # Candidate records are visible to recruiters only after SCOUT captures at
    # least one public, human-reviewable source URL.
    source_verified: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false(), nullable=False)
    source_captured_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    source_evidence: Mapped[Optional[list[dict]]] = mapped_column(JSON, nullable=True)
    stage: Mapped[CandidateStage] = mapped_column(Enum(CandidateStage), default=CandidateStage.SOURCED)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    screen_brief: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    outreach_count: Mapped[int] = mapped_column(Integer, default=0)
    last_contacted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_activity_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    interview_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    calendar_event_id: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    contact_consent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    contact_consent_source: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    reminder_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # Resolved location fields
    location_raw: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    location_city: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    location_district: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    location_state: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    location_country_iso2: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    location_confidence: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    location_reason: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    location_source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    location_resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    # Frontend-compatible fields
    public_profiles: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # github, stackoverflow
    repos_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    followers_count: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    rep: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    masked_email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    is_email_revealed: Mapped[bool] = mapped_column(Boolean, default=False)
    match_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    score_breakdown: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    raw_location_signals: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    consent: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    activity_timeline: Mapped[Optional[list[dict]]] = mapped_column(JSON, nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    avatar: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    role: Mapped["Role"] = relationship("Role", back_populates="candidates")

class AgentLog(Base):
    __tablename__ = "agent_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent: Mapped[str] = mapped_column(String(50))
    event_type: Mapped[str] = mapped_column(String(100))
    message: Mapped[str] = mapped_column(Text)
    data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    role_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    candidate_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

# Consent records for frontend compliance view
class ConsentRecord(Base):
    __tablename__ = "consent_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"))
    candidate_name: Mapped[str] = mapped_column(String(200))
    masked_email: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(30))  # recorded, pending, withdrawn
    recorded_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    expiry_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    days_remaining: Mapped[int] = mapped_column(Integer, default=0)
    proof_method: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    proof_snippet: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    proof_hash: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    scope: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    recorded_by: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)





