"""add_link_shares_table

One counter per day, platform and page for the link previews a messenger or a
social network fetches when a person shares a link to the site
(docs/reference/plausible.md, "Shared links"). The API adds one to the counter
after it served the page's preview image (`api/shared_links.py`), and the
"Shared links" tile on /stats and the section on /debug read the sums.

A row is a count and nothing else: no address, no user agent, no time of day.
The seven key columns are the primary key, and `spec_id`, `language` and
`library_id` are the empty string where the page has none: a NULL in a key
conflicts with nothing, so the counter's `ON CONFLICT` would add a row per
fetch instead of counting. `verified` says whether Cloudflare verified the
fetcher as the bot it claims to be; the platform's name is read from a user
agent anyone can write.

The CHECK is a portable IN list: the integration tests build the same model on
SQLite. `platform` has none, because its set grows with every platform that
learns to preview links.

Revision ID: c9d3f1a7e5b2
Revises: b4e7a9c2d6f1
Create Date: 2026-11-11

"""

from typing import Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "c9d3f1a7e5b2"
down_revision: str | None = "b4e7a9c2d6f1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the link_shares table with its CHECK constraint."""
    op.create_table(
        "link_shares",
        sa.Column("day", sa.Date(), primary_key=True, nullable=False),
        sa.Column("platform", sa.String(32), primary_key=True, nullable=False),
        sa.Column("verified", sa.Boolean(), primary_key=True, nullable=False),
        sa.Column("page", sa.String(20), primary_key=True, nullable=False),
        sa.Column("spec_id", sa.String(100), primary_key=True, nullable=False),
        sa.Column("language", sa.String(50), primary_key=True, nullable=False),
        sa.Column("library_id", sa.String(50), primary_key=True, nullable=False),
        sa.Column("fetches", sa.Integer(), nullable=False),
        sa.CheckConstraint("page IN ('home','plots','spec_overview','spec_detail')", name="ck_link_shares_page_valid"),
    )


def downgrade() -> None:
    """Drop the link_shares table."""
    op.drop_table("link_shares")
