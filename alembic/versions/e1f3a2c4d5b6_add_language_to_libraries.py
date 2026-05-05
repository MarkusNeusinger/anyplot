"""add_language_to_libraries

Revision ID: e1f3a2c4d5b6
Revises: b833d85c09ed
Create Date: 2026-04-20 12:00:00.000000

"""

from typing import Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "e1f3a2c4d5b6"
down_revision: str | None = "b833d85c09ed"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("libraries", sa.Column("language", sa.String(length=50), nullable=False, server_default="python"))


def downgrade() -> None:
    op.drop_column("libraries", "language")
