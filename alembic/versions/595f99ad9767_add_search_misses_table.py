"""add_search_misses_table

One counter per UTC day and text for the gallery searches that found nothing
in the whole catalogue (docs/reference/database.md, `search_misses`). The site
sends the finished text, the API normalises it again and adds one to its row
(`api/search_misses.py`), and the owner's section on /debug reads and deletes
them. It replaces the search text that the Plausible events `search` and
`search_no_results` used to carry to the public dashboard.

A row is the text, the day and a count, nothing else: no address, no user
agent, no time of day, no session, no hash. The day and the text are the
primary key, so two equal searches of a day are one row that the API's
`INSERT ... ON CONFLICT DO UPDATE` counts up. The API deletes the rows older
than its retention period itself.

Revision ID: 595f99ad9767
Revises: c9d3f1a7e5b2
Create Date: 2026-11-18

"""

from typing import Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "595f99ad9767"
down_revision: str | None = "c9d3f1a7e5b2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the search_misses table."""
    op.create_table(
        "search_misses",
        sa.Column("day", sa.Date(), primary_key=True, nullable=False),
        sa.Column("query", sa.String(40), primary_key=True, nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
    )


def downgrade() -> None:
    """Drop the search_misses table."""
    op.drop_table("search_misses")
