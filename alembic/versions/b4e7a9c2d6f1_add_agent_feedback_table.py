"""add_agent_feedback_table

One row per quick-feedback case of the agent chat (docs/concepts/agent-network.md,
"Feedback capture"). The BFF's feedback route inserts it after the case's files are
in the private case bucket, and the "Agent cases" section of /debug reads and
updates it. The row is the source of truth for the triage state (status, tags,
expected, promoted_at, superseded_by); every other column copies the case manifest,
so the class statistics outlive the files, which the bucket's lifecycle rule deletes
after 180 days.

The types are the PostgreSQL types the model's TypeDecorators resolve to
(`StringArray` -> ARRAY(VARCHAR)), the lesson of e5b1c9d4a7f2. The CHECKs are
portable IN lists: the integration tests build the same model on SQLite.

Revision ID: b4e7a9c2d6f1
Revises: a7c3e9d1f5b8
Create Date: 2026-10-12

"""

from typing import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "b4e7a9c2d6f1"
down_revision: str | None = "a7c3e9d1f5b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the agent_feedback table with its CHECK constraints and indexes."""
    op.create_table(
        "agent_feedback",
        sa.Column("id", sa.String(25), primary_key=True, nullable=False),
        sa.Column("manifest_schema", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("case_uri", sa.String(255), nullable=False),
        sa.Column("user_hash", sa.String(20), nullable=False),
        sa.Column("session_hash", sa.String(16), nullable=False),
        sa.Column("spec_id", sa.String(100), nullable=True),
        sa.Column("library_id", sa.String(50), nullable=True),
        sa.Column("locale", sa.String(16), nullable=True),
        sa.Column("reaction", sa.String(20), nullable=False),
        sa.Column("message", sa.String(500), nullable=True),
        sa.Column("include_data", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("result_version", sa.Integer(), nullable=False),
        sa.Column("replaces", sa.String(25), nullable=True),
        sa.Column("model", sa.String(100), nullable=True),
        sa.Column("model_version", sa.String(100), nullable=True),
        sa.Column("judge_model", sa.String(100), nullable=True),
        sa.Column("prompt_hash", sa.String(16), nullable=True),
        sa.Column("pipeline_status", sa.String(20), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=True),
        sa.Column("tokens", sa.Integer(), nullable=True),
        sa.Column("cost_estimate", sa.Float(), nullable=True),
        sa.Column("files", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("tags", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("expected", sa.String(10), nullable=True),
        sa.Column("promoted_at", sa.DateTime(), nullable=True),
        sa.Column("superseded_by", sa.String(25), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "reaction IN ('thumbs_up','thumbs_down','bug','idea')", name="ck_agent_feedback_reaction_valid"
        ),
        sa.CheckConstraint(
            "status IN ('new','in_progress','done','wont_solve')", name="ck_agent_feedback_status_valid"
        ),
        sa.CheckConstraint(
            "expected IS NULL OR expected IN ('accepted','rejected')", name="ck_agent_feedback_expected_valid"
        ),
    )
    op.create_index("ix_agent_feedback_session_version", "agent_feedback", ["session_hash", "result_version"])
    op.create_index("ix_agent_feedback_spec_library", "agent_feedback", ["spec_id", "library_id"])
    op.create_index("ix_agent_feedback_tags", "agent_feedback", ["tags"], postgresql_using="gin")


def downgrade() -> None:
    """Drop the agent_feedback table and its indexes."""
    op.drop_index("ix_agent_feedback_tags", table_name="agent_feedback")
    op.drop_index("ix_agent_feedback_spec_library", table_name="agent_feedback")
    op.drop_index("ix_agent_feedback_session_version", table_name="agent_feedback")
    op.drop_table("agent_feedback")
