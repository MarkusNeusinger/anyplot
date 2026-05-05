"""add_tags_gin_index

Revision ID: 7ccd65103917
Revises: b26e9f4b532d
Create Date: 2025-12-21 22:24:19.543818

GIN index on specs.tags JSONB column for fast tag filtering.
Supports queries like: WHERE tags->'plot_type' ? 'scatter'
"""

from typing import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "7ccd65103917"
down_revision: str | None = "b26e9f4b532d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # GIN index for fast JSONB containment/existence queries
    # Enables efficient filtering by any tag dimension:
    # - plot_type, data_type, domain, features
    op.execute("CREATE INDEX ix_specs_tags ON specs USING GIN (tags)")


def downgrade() -> None:
    op.execute("DROP INDEX ix_specs_tags")
