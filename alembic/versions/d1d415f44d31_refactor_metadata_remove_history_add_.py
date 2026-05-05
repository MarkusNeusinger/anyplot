"""refactor_metadata_remove_history_add_review

Revision ID: d1d415f44d31
Revises: 7ccd65103917
Create Date: 2025-12-21 22:59:03.135462

"""

from typing import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "d1d415f44d31"
down_revision: str | None = "7ccd65103917"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add new columns to impls
    op.add_column("impls", sa.Column("updated", sa.DateTime(), nullable=True))
    op.add_column(
        "impls", sa.Column("review_strengths", postgresql.ARRAY(sa.String()), server_default="{}", nullable=False)
    )
    op.add_column(
        "impls", sa.Column("review_weaknesses", postgresql.ARRAY(sa.String()), server_default="{}", nullable=False)
    )
    op.add_column(
        "impls", sa.Column("review_improvements", postgresql.ARRAY(sa.String()), server_default="{}", nullable=False)
    )

    # Remove old columns from impls
    op.drop_column("impls", "quality_feedback")
    op.drop_column("impls", "improvements_suggested")
    op.drop_column("impls", "evaluator_scores")
    op.drop_column("impls", "history")

    # Add updated column to specs, remove history
    op.add_column("specs", sa.Column("updated", sa.DateTime(), nullable=True))
    op.drop_column("specs", "history")
    # NOTE: Keep the GIN index on specs.tags (created in previous migration)


def downgrade() -> None:
    # Restore specs columns
    op.add_column(
        "specs", sa.Column("history", postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True)
    )
    op.drop_column("specs", "updated")

    # Restore impls columns
    op.add_column(
        "impls", sa.Column("history", postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True)
    )
    op.add_column(
        "impls",
        sa.Column("evaluator_scores", postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True),
    )
    op.add_column(
        "impls",
        sa.Column(
            "improvements_suggested", postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True
        ),
    )
    op.add_column("impls", sa.Column("quality_feedback", sa.TEXT(), autoincrement=False, nullable=True))
    op.drop_column("impls", "review_improvements")
    op.drop_column("impls", "review_weaknesses")
    op.drop_column("impls", "review_strengths")
    op.drop_column("impls", "updated")
