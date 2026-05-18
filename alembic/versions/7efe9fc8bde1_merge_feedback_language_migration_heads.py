"""merge feedback + language migration heads

The feedback-widget branch (#7143) and the language-descriptions branch
(#7142) both descended from `3a7e1b5c0c4f` and merged to main
independently, leaving two alembic heads (`e5b1c9d4a7f2`,
`c5f9a3d72be1`). That broke `Sync: PostgreSQL` on every push to main
with "Multiple head revisions are present for given argument 'head'".

This is a no-op merge revision that joins both heads into a single
head (`7efe9fc8bde1`) so `alembic upgrade head` resolves again.

Revision ID: 7efe9fc8bde1
Revises: c5f9a3d72be1, e5b1c9d4a7f2
Create Date: 2026-05-18
"""

from __future__ import annotations

from collections.abc import Sequence


# revision identifiers, used by Alembic.
revision: str = "7efe9fc8bde1"
down_revision: tuple[str, str] = ("c5f9a3d72be1", "e5b1c9d4a7f2")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
