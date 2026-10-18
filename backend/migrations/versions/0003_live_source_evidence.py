"""Require a captured public source before a candidate enters the workflow.

Revision ID: 0003_live_source_evidence
Revises: 0002_align_enums_and_privacy
Create Date: 2026-10-18 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "0003_live_source_evidence"
down_revision = "0002_align_enums_and_privacy"
branch_labels = None
depends_on = None


def _column_names(bind, table_name: str) -> set[str]:
    return {column["name"] for column in sa.inspect(bind).get_columns(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    columns = _column_names(bind, "candidates")
    missing_columns = {
        "source_verified": sa.Column(
            "source_verified", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        "source_captured_at": sa.Column(
            "source_captured_at", sa.DateTime(timezone=True), nullable=True
        ),
        "source_evidence": sa.Column("source_evidence", sa.JSON(), nullable=True),
    }
    with op.batch_alter_table("candidates") as batch_op:
        for name, column in missing_columns.items():
            if name not in columns:
                batch_op.add_column(column)


def downgrade() -> None:
    bind = op.get_bind()
    columns = _column_names(bind, "candidates")
    with op.batch_alter_table("candidates") as batch_op:
        for name in ("source_evidence", "source_captured_at", "source_verified"):
            if name in columns:
                batch_op.drop_column(name)
