"""feedback_library_and_language

The 👍/👎 buttons moved from the floating feedback widget onto the plot
itself, so a reaction is now about one implementation rather than a page.
Store that implementation explicitly — `library_id` + `language` next to the
existing `spec_id` — instead of parsing it back out of `path`, and index the
(spec_id, library_id) pair so votes can be counted per image later.

Both columns are nullable: page-level feedback from the floating widget
(messages, bug/idea reactions) still leaves them empty.

Revision ID: a7c3e9d1f5b8
Revises: f4b8d2c6a9e1
Create Date: 2026-09-10

"""

from typing import Sequence

import sqlalchemy as sa

from alembic import op


revision: str = "a7c3e9d1f5b8"
down_revision: str | None = "f4b8d2c6a9e1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("feedback") as batch_op:
        batch_op.add_column(sa.Column("library_id", sa.String(50), nullable=True))
        batch_op.add_column(sa.Column("language", sa.String(50), nullable=True))
        batch_op.create_index("ix_feedback_spec_library", ["spec_id", "library_id"])


def downgrade() -> None:
    with op.batch_alter_table("feedback") as batch_op:
        batch_op.drop_index("ix_feedback_spec_library")
        batch_op.drop_column("language")
        batch_op.drop_column("library_id")
