"""Align enum storage and add privacy and reminder fields.

Revision ID: 0002_align_enums_and_privacy
Revises: 0001
Create Date: 2026-10-18 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "0002_align_enums_and_privacy"
down_revision = "0001"
branch_labels = None
depends_on = None


def _column_names(bind, table_name: str) -> set[str]:
    return {column["name"] for column in sa.inspect(bind).get_columns(table_name)}


def _postgres_enum_labels(bind, enum_name: str) -> list[str]:
    rows = bind.execute(
        sa.text(
            "SELECT e.enumlabel "
            "FROM pg_enum e JOIN pg_type t ON t.oid = e.enumtypid "
            "WHERE t.typname = :enum_name ORDER BY e.enumsortorder"
        ),
        {"enum_name": enum_name},
    )
    return [row[0] for row in rows]


def _replace_postgres_enum(
    bind,
    *,
    enum_name: str,
    table_name: str,
    column_name: str,
    labels: tuple[str, ...],
    default_label: str,
) -> None:
    """Rebuild a PostgreSQL enum only when a legacy migration used wrong labels."""
    if _postgres_enum_labels(bind, enum_name) == list(labels):
        return

    legacy_name = f"{enum_name}_legacy_0002"
    # Names are internal constants, not user input.
    op.execute(f"DROP TYPE IF EXISTS {legacy_name}")
    op.execute(f"ALTER TYPE {enum_name} RENAME TO {legacy_name}")
    sa.Enum(*labels, name=enum_name).create(bind, checkfirst=False)
    op.execute(f"ALTER TABLE {table_name} ALTER COLUMN {column_name} DROP DEFAULT")
    op.execute(
        f"ALTER TABLE {table_name} ALTER COLUMN {column_name} "
        f"TYPE {enum_name} USING UPPER({column_name}::text)::{enum_name}"
    )
    op.execute(
        f"ALTER TABLE {table_name} ALTER COLUMN {column_name} "
        f"SET DEFAULT '{default_label}'::{enum_name}"
    )
    op.execute(f"DROP TYPE {legacy_name}")


def upgrade() -> None:
    bind = op.get_bind()
    candidate_columns = _column_names(bind, "candidates")
    candidate_column_info = {
        column["name"]: column for column in sa.inspect(bind).get_columns("candidates")
    }

    if bind.dialect.name == "postgresql":
        _replace_postgres_enum(
            bind,
            enum_name="rolestatus",
            table_name="roles",
            column_name="status",
            labels=("ACTIVE", "PAUSED", "FILLED"),
            default_label="ACTIVE",
        )
        _replace_postgres_enum(
            bind,
            enum_name="candidatestage",
            table_name="candidates",
            column_name="stage",
            labels=(
                "SOURCED", "SCREENED", "OUTREACH_SENT", "REPLIED",
                "INTERVIEW_SCHEDULED", "INTERVIEWED", "OFFER", "HIRED",
                "REJECTED", "STALE",
            ),
            default_label="SOURCED",
        )
        # Older values were timezone-naive but represented IST wall-clock times.
        # A fresh 0001 install already has TIMESTAMPTZ, so leave it untouched.
        interview_type = candidate_column_info["interview_time"]["type"]
        if not getattr(interview_type, "timezone", False):
            op.alter_column(
                "candidates",
                "interview_time",
                existing_type=sa.DateTime(),
                type_=sa.DateTime(timezone=True),
                postgresql_using="interview_time AT TIME ZONE 'Asia/Kolkata'",
            )

    missing_columns = {
        "contact_consent_at": sa.Column("contact_consent_at", sa.DateTime(timezone=True), nullable=True),
        "contact_consent_source": sa.Column("contact_consent_source", sa.String(length=200), nullable=True),
        "reminder_sent_at": sa.Column("reminder_sent_at", sa.DateTime(timezone=True), nullable=True),
    }
    with op.batch_alter_table("candidates") as batch_op:
        for name, column in missing_columns.items():
            if name not in candidate_columns:
                batch_op.add_column(column)


def downgrade() -> None:
    bind = op.get_bind()
    candidate_columns = _column_names(bind, "candidates")
    with op.batch_alter_table("candidates") as batch_op:
        for name in ("reminder_sent_at", "contact_consent_source", "contact_consent_at"):
            if name in candidate_columns:
                batch_op.drop_column(name)

    if bind.dialect.name == "postgresql":
        op.alter_column(
            "candidates",
            "interview_time",
            existing_type=sa.DateTime(timezone=True),
            type_=sa.DateTime(),
            postgresql_using="interview_time AT TIME ZONE 'Asia/Kolkata'",
        )
