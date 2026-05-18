"""feedback_uuid_and_status

Two cleanups on the feedback table:

1. Fix `feedback.id` column type. PR #5662 created it as varchar(36), but the
   model declares `UniversalUUID` which binds parameters as native UUID on
   Postgres. Result: every read of a freshly-inserted row failed with
   `operator does not exist: character varying = uuid`. We ALTER the column
   to UUID on Postgres (SQLite is unaffected — its UniversalUUID impl maps
   back to String, and these migrations don't run there).

2. Add a `status` column for admin triage from the debug page:
   `new` (default) → `in_progress` → `done` or `wont_solve`. Constrained to
   the allow-list via a CHECK constraint.

Revision ID: e5b1c9d4a7f2
Revises: d4e8a1f2c937
Create Date: 2026-05-18

"""

from typing import Sequence

import sqlalchemy as sa

from alembic import op


revision: str = "e5b1c9d4a7f2"
down_revision: str | None = "d4e8a1f2c937"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        # USING-cast is required because PG can't implicitly coerce varchar -> uuid.
        op.execute("ALTER TABLE feedback ALTER COLUMN id TYPE uuid USING id::uuid")

    with op.batch_alter_table("feedback") as batch_op:
        batch_op.add_column(sa.Column("status", sa.String(20), nullable=False, server_default="new"))
        batch_op.create_check_constraint(
            "ck_feedback_status_valid", "status IN ('new','in_progress','done','wont_solve')"
        )

    # Drop the server default after the existing rows are backfilled — new
    # writes will set status explicitly through the model default.
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TABLE feedback ALTER COLUMN status DROP DEFAULT")


def downgrade() -> None:
    with op.batch_alter_table("feedback") as batch_op:
        batch_op.drop_constraint("ck_feedback_status_valid", type_="check")
        batch_op.drop_column("status")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TABLE feedback ALTER COLUMN id TYPE varchar(36) USING id::varchar")
