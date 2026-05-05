"""add_performance_indexes

Add indexes on frequently queried columns for better query performance:
- impls.library_id (foreign key, heavily queried)
- specs.issue (lookup field)
- impls.quality_score (sorting/filtering)

Note: ix_impls_spec_id is NOT needed because the unique constraint on
(spec_id, library_id) creates an index that covers spec_id queries
via left-prefix optimization.

Revision ID: d0c76553a5cc
Revises: c36d82383e1d
Create Date: 2025-12-28 21:00:41.803150

"""

from typing import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "d0c76553a5cc"
down_revision: str | None = "c36d82383e1d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add performance indexes for frequently queried columns."""
    # Add index on impls.library_id (foreign key lookup)
    # Note: spec_id is covered by the (spec_id, library_id) unique constraint index
    op.create_index("ix_impls_library_id", "impls", ["library_id"], unique=False)

    # Add index on specs.issue (lookup by GitHub issue number)
    op.create_index("ix_specs_issue", "specs", ["issue"], unique=False)

    # Add index on impls.quality_score (sorting and filtering by quality)
    op.create_index("ix_impls_quality_score", "impls", ["quality_score"], unique=False)


def downgrade() -> None:
    """Remove performance indexes."""
    op.drop_index("ix_impls_quality_score", table_name="impls")
    op.drop_index("ix_specs_issue", table_name="specs")
    op.drop_index("ix_impls_library_id", table_name="impls")
