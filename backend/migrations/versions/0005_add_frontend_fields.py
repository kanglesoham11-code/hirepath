"""0005 add frontend-compatible fields to roles and candidates

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-18
"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Frontend-compatible fields on roles
    op.add_column("roles", sa.Column("req_id", sa.String(50), nullable=True))
    op.add_column("roles", sa.Column("department", sa.String(100), nullable=True))
    op.add_column("roles", sa.Column("location", sa.String(200), nullable=True))
    op.add_column("roles", sa.Column("candidate_count", sa.Integer(), nullable=True, server_default="0"))
    op.add_column("roles", sa.Column("pipeline_stages", sa.JSON(), nullable=True))
    op.add_column("roles", sa.Column("health_score", sa.Integer(), nullable=True, server_default="70"))
    op.add_column("roles", sa.Column("health_status", sa.String(30), nullable=True))
    op.add_column("roles", sa.Column("hiring_lead", sa.String(100), nullable=True))
    op.add_column("roles", sa.Column("audit_verified_time", sa.String(100), nullable=True))
    op.add_column("roles", sa.Column("total_sourced", sa.Integer(), nullable=True, server_default="0"))
    op.add_column("roles", sa.Column("total_screened", sa.Integer(), nullable=True, server_default="0"))
    op.add_column("roles", sa.Column("total_outreach", sa.Integer(), nullable=True, server_default="0"))
    op.add_column("roles", sa.Column("total_replied", sa.Integer(), nullable=True, server_default="0"))
    op.add_column("roles", sa.Column("total_interview", sa.Integer(), nullable=True, server_default="0"))
    op.add_column("roles", sa.Column("total_offer", sa.Integer(), nullable=True, server_default="0"))

    # Frontend-compatible fields on candidates
    op.add_column("candidates", sa.Column("public_profiles", sa.JSON(), nullable=True))
    op.add_column("candidates", sa.Column("repos_count", sa.Integer(), nullable=True))
    op.add_column("candidates", sa.Column("followers_count", sa.String(50), nullable=True))
    op.add_column("candidates", sa.Column("rep", sa.Integer(), nullable=True))
    op.add_column("candidates", sa.Column("masked_email", sa.String(200), nullable=True))
    op.add_column("candidates", sa.Column("is_email_revealed", sa.Boolean(), nullable=True, server_default="0"))
    op.add_column("candidates", sa.Column("match_score", sa.Integer(), nullable=True))
    op.add_column("candidates", sa.Column("score_breakdown", sa.JSON(), nullable=True))
    op.add_column("candidates", sa.Column("raw_location_signals", sa.JSON(), nullable=True))
    op.add_column("candidates", sa.Column("consent", sa.JSON(), nullable=True))
    op.add_column("candidates", sa.Column("activity_timeline", sa.JSON(), nullable=True))
    op.add_column("candidates", sa.Column("title", sa.String(300), nullable=True))
    op.add_column("candidates", sa.Column("avatar", sa.String(10), nullable=True))


def downgrade() -> None:
    op.drop_column("roles", "req_id")
    op.drop_column("roles", "department")
    op.drop_column("roles", "location")
    op.drop_column("roles", "candidate_count")
    op.drop_column("roles", "pipeline_stages")
    op.drop_column("roles", "health_score")
    op.drop_column("roles", "health_status")
    op.drop_column("roles", "hiring_lead")
    op.drop_column("roles", "audit_verified_time")
    op.drop_column("roles", "total_sourced")
    op.drop_column("roles", "total_screened")
    op.drop_column("roles", "total_outreach")
    op.drop_column("roles", "total_replied")
    op.drop_column("roles", "total_interview")
    op.drop_column("roles", "total_offer")

    op.drop_column("candidates", "public_profiles")
    op.drop_column("candidates", "repos_count")
    op.drop_column("candidates", "followers_count")
    op.drop_column("candidates", "rep")
    op.drop_column("candidates", "masked_email")
    op.drop_column("candidates", "is_email_revealed")
    op.drop_column("candidates", "match_score")
    op.drop_column("candidates", "score_breakdown")
    op.drop_column("candidates", "raw_location_signals")
    op.drop_column("candidates", "consent")
    op.drop_column("candidates", "activity_timeline")
    op.drop_column("candidates", "title")
    op.drop_column("candidates", "avatar")