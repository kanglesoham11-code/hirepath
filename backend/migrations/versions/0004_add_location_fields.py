"""0004 add resolved location fields to candidates

Revision ID: 0004
Revises: 0003_live_source_evidence
Create Date: 2026-10-18
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003_live_source_evidence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Resolved location columns on candidates
    op.add_column("candidates", sa.Column("location_raw", sa.String(500), nullable=True))
    op.add_column("candidates", sa.Column("location_city", sa.String(200), nullable=True))
    op.add_column("candidates", sa.Column("location_district", sa.String(200), nullable=True))
    op.add_column("candidates", sa.Column("location_state", sa.String(200), nullable=True))
    op.add_column("candidates", sa.Column("location_country_iso2", sa.String(5), nullable=True))
    op.add_column("candidates", sa.Column("location_confidence", sa.String(20), nullable=True))
    op.add_column("candidates", sa.Column("location_reason", sa.String(50), nullable=True))
    op.add_column("candidates", sa.Column("location_source", sa.String(100), nullable=True))
    op.add_column("candidates", sa.Column("location_resolved_at", sa.DateTime(timezone=True), nullable=True))

    # Per-role target locations
    op.add_column("roles", sa.Column("target_locations", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("candidates", "location_raw")
    op.drop_column("candidates", "location_city")
    op.drop_column("candidates", "location_district")
    op.drop_column("candidates", "location_state")
    op.drop_column("candidates", "location_country_iso2")
    op.drop_column("candidates", "location_confidence")
    op.drop_column("candidates", "location_reason")
    op.drop_column("candidates", "location_source")
    op.drop_column("candidates", "location_resolved_at")
    op.drop_column("roles", "target_locations")
