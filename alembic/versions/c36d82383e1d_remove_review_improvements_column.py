"""remove_review_improvements_column

Revision ID: c36d82383e1d
Revises: d1d415f44d31
Create Date: 2025-12-22 23:35:11.604405

"""

from typing import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "c36d82383e1d"
down_revision: str | None = "d1d415f44d31"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Remove review_improvements column - AI now decides how to fix weaknesses
    op.drop_column("impls", "review_improvements")


def downgrade() -> None:
    op.add_column(
        "impls",
        sa.Column(
            "review_improvements",
            postgresql.ARRAY(sa.VARCHAR()),
            server_default=sa.text("'{}'::character varying[]"),
            autoincrement=False,
            nullable=False,
        ),
    )
