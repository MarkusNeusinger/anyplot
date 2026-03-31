"""remove_preview_thumb_column

Revision ID: b833d85c09ed
Revises: a2f4b8c91d23
Create Date: 2026-03-31 23:07:22.910889

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b833d85c09ed'
down_revision: Union[str, None] = 'a2f4b8c91d23'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("impls", "preview_thumb")


def downgrade() -> None:
    op.add_column(
        "impls",
        sa.Column("preview_thumb", sa.String(), nullable=True),
    )
