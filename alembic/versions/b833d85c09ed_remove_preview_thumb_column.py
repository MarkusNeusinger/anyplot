"""remove_preview_thumb_column

Revision ID: b833d85c09ed
Revises: a2f4b8c91d23
Create Date: 2026-03-31 23:07:22.910889

"""

from typing import Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "b833d85c09ed"
down_revision: str | None = "a2f4b8c91d23"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column("impls", "preview_thumb")


def downgrade() -> None:
    op.add_column("impls", sa.Column("preview_thumb", sa.String(), nullable=True))
