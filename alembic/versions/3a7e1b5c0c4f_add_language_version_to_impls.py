"""add_language_version_to_impls

Adds a `language_version` column to the `impls` table to record the runtime
version of the implementation's own language — Python interpreter for python
libraries, R interpreter for ggplot2. The existing `python_version` column
keeps its original meaning ("Python that ran the impl-generate pipeline",
i.e. 3.13) so multi-language entries no longer abuse it to carry an R
version.

The new column is nullable: old rows stay correct via the fallback chain
(`language_version → python_version`) wired in the API.

Revision ID: 3a7e1b5c0c4f
Revises: f2d9c8a1b4e0
Create Date: 2026-05-16

"""

from typing import Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "3a7e1b5c0c4f"
down_revision: str | None = "f2d9c8a1b4e0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("impls", sa.Column("language_version", sa.String(), nullable=True))

    # Backfill: for existing rows (all python today) the language runtime IS the
    # Python interpreter, so seed language_version from python_version.
    op.execute("UPDATE impls SET language_version = python_version WHERE language_version IS NULL")


def downgrade() -> None:
    op.drop_column("impls", "language_version")
