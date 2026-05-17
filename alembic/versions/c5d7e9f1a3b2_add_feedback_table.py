"""add_feedback_table

Add `feedback` table for the in-app quick feedback widget (issue #5662).
Stores lightweight user remarks submitted via the floating widget on
anyplot.ai. Entries are immutable once written; triage is manual.

Revision ID: c5d7e9f1a3b2
Revises: 3a7e1b5c0c4f
Create Date: 2026-05-17

"""

from typing import Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "c5d7e9f1a3b2"
down_revision: str | None = "3a7e1b5c0c4f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the feedback table plus indexes for recent-first browsing and rate-limit lookups."""
    op.create_table(
        "feedback",
        sa.Column("id", sa.String(36), primary_key=True, nullable=False),
        sa.Column("message", sa.String(500), nullable=False),
        sa.Column("reaction", sa.String(20), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("path", sa.String(500), nullable=True),
        sa.Column("spec_id", sa.String(100), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("viewport", sa.String(20), nullable=True),
        sa.Column("session_id", sa.String(64), nullable=True),
        sa.Column("ip_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "reaction IS NULL OR reaction IN ('thumbs_up','thumbs_down','bug','idea','heart')",
            name="ck_feedback_reaction_valid",
        ),
    )
    op.create_index("ix_feedback_created_at", "feedback", [sa.text("created_at DESC")])
    op.create_index("ix_feedback_ip_hash_created_at", "feedback", ["ip_hash", sa.text("created_at DESC")])


def downgrade() -> None:
    """Drop the feedback table and its indexes."""
    op.drop_index("ix_feedback_ip_hash_created_at", table_name="feedback")
    op.drop_index("ix_feedback_created_at", table_name="feedback")
    op.drop_table("feedback")
