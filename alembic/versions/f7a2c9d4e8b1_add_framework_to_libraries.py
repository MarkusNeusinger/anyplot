"""add_framework_to_libraries

Adds the `framework` column to the libraries table. It models the UI-framework
runtime constraint a charting library imposes (none | react | vue | svelte |
angular) so a single `javascript` language entry can cover both
framework-agnostic libraries (Chart.js, D3, ECharts) and React-only libraries
without duplicating the registry — see docs/concepts/library-expansion.md §6.
All existing libraries are framework-agnostic, so the column defaults to "none".

Revision ID: f7a2c9d4e8b1
Revises: 7efe9fc8bde1
Create Date: 2026-06-02 20:00:00.000000

"""

from typing import Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f7a2c9d4e8b1"
down_revision: str | None = "7efe9fc8bde1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("libraries", sa.Column("framework", sa.String(length=20), nullable=False, server_default="none"))


def downgrade() -> None:
    op.drop_column("libraries", "framework")
