"""Init HIREPATH tables

Revision ID: 0001
Revises: 
Create Date: 2025-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('requirements', sa.Text(), nullable=True),
        # SQLAlchemy persists Python Enum member names by default. Keep PostgreSQL
        # labels aligned with RoleStatus.ACTIVE / CandidateStage.SOURCED.
        sa.Column('status', sa.Enum('ACTIVE','PAUSED','FILLED', name='rolestatus'), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'candidates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), sa.ForeignKey('roles.id'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('email', sa.String(200), nullable=True),
        sa.Column('linkedin_url', sa.String(500), nullable=True),
        sa.Column('github_url', sa.String(500), nullable=True),
        sa.Column('resume_path', sa.String(500), nullable=True),
        sa.Column('source', sa.String(100), nullable=True),
        sa.Column('stage', sa.Enum('SOURCED','SCREENED','OUTREACH_SENT','REPLIED','INTERVIEW_SCHEDULED','INTERVIEWED','OFFER','HIRED','REJECTED','STALE', name='candidatestage'), nullable=False, server_default='SOURCED'),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('screen_brief', sa.JSON(), nullable=True),
        sa.Column('outreach_count', sa.Integer(), server_default='0'),
        sa.Column('last_contacted_at', sa.DateTime(), nullable=True),
        sa.Column('last_activity_at', sa.DateTime(), nullable=True),
        sa.Column('interview_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('calendar_event_id', sa.String(300), nullable=True),
        sa.Column('contact_consent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('contact_consent_source', sa.String(200), nullable=True),
        sa.Column('reminder_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('raw_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'agent_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent', sa.String(50), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('data', sa.JSON(), nullable=True),
        sa.Column('role_id', sa.Integer(), nullable=True),
        sa.Column('candidate_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('agent_logs')
    op.drop_table('candidates')
    op.drop_table('roles')
    op.execute("DROP TYPE IF EXISTS rolestatus")
    op.execute("DROP TYPE IF EXISTS candidatestage")
