from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Float, DateTime, Enum, ForeignKey, JSON, Integer, func
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

class CandidateStage(str, enum.Enum):
    SOURCED = "sourced"
    SCREENED = "screened"
    OUTREACH_SENT = "outreach_sent"
    REPLIED = "replied"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    INTERVIEWED = "interviewed"
    OFFER = "offer"
    HIRED = "hired"
    REJECTED = "rejected"
    STALE = "stale"

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
    source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # github/linkedin/wellfound/manual
    stage: Mapped[CandidateStage] = mapped_column(Enum(CandidateStage), default=CandidateStage.SOURCED)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    screen_brief: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    outreach_count: Mapped[int] = mapped_column(Integer, default=0)
    last_contacted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_activity_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    interview_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    calendar_event_id: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
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

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
