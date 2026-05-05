"""add_extended_review_fields

Add extended review data fields to impls table for issue #2845:
- review_image_description: AI's visual description of the plot
- review_criteria_checklist: Detailed per-criterion scoring breakdown
- review_verdict: "APPROVED" or "REJECTED"

Revision ID: 6345896e2e90
Revises: d0c76553a5cc
Create Date: 2026-01-01

"""

from typing import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "6345896e2e90"
down_revision: str | None = "d0c76553a5cc"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add extended review data columns to impls table."""
    # Add review_image_description (text field for AI's visual description)
    op.add_column("impls", sa.Column("review_image_description", sa.Text(), nullable=True))

    # Add review_criteria_checklist (JSONB for detailed scoring breakdown)
    op.add_column("impls", sa.Column("review_criteria_checklist", postgresql.JSONB(), nullable=True))

    # Add review_verdict (short string: "APPROVED" or "REJECTED")
    op.add_column("impls", sa.Column("review_verdict", sa.String(20), nullable=True))


def downgrade() -> None:
    """Remove extended review data columns from impls table."""
    op.drop_column("impls", "review_verdict")
    op.drop_column("impls", "review_criteria_checklist")
    op.drop_column("impls", "review_image_description")
