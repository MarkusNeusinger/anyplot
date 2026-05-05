"""add_impl_tags

Add impl_tags JSONB column to impls table for issue #2434:
Implementation-level tags describing HOW code is implemented.
5 dimensions: dependencies, techniques, patterns, dataprep, styling

Revision ID: a2f4b8c91d23
Revises: 6345896e2e90
Create Date: 2026-01-07

"""

from typing import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "a2f4b8c91d23"
down_revision: str | None = "6345896e2e90"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add impl_tags JSONB column and GIN index to impls table."""
    # Add impl_tags column (JSONB for 5 tag dimensions)
    op.add_column("impls", sa.Column("impl_tags", postgresql.JSONB(), nullable=True))

    # GIN index for fast JSONB containment/existence queries
    # Enables efficient filtering by any impl_tags dimension:
    # - dependencies, techniques, patterns, dataprep, styling
    op.execute("CREATE INDEX ix_impls_impl_tags ON impls USING GIN (impl_tags)")


def downgrade() -> None:
    """Remove impl_tags column and GIN index from impls table."""
    op.execute("DROP INDEX ix_impls_impl_tags")
    op.drop_column("impls", "impl_tags")
