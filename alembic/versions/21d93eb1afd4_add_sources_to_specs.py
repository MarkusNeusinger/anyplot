"""add_sources_to_specs

The `sources` block of a spec's `specification.yaml` (core/spec_sources.py): the
works that gave the idea for the plot (`inspired_by`), the literature its values
follow (`references`), and where its example data comes from (`data`). The
database sync stores the block as normalised JSON, and NULL when the spec names
no source, which is every spec when this revision lands.

Revision ID: 21d93eb1afd4
Revises: 595f99ad9767
Create Date: 2026-11-21

"""

from typing import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "21d93eb1afd4"
down_revision: str | None = "595f99ad9767"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the nullable sources column to specs."""
    op.add_column("specs", sa.Column("sources", postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    """Drop the sources column from specs."""
    op.drop_column("specs", "sources")
