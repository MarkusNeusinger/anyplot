"""feedback_rename_email_to_contact

Rename `feedback.email` to `feedback.contact`, drop the `heart` reaction from
the CHECK constraint, and make `message` nullable so a reaction-only entry is
accepted. The contact column is now free-form (name, email, handle, …)
instead of strictly an email address.

Revision ID: d4e8a1f2c937
Revises: c5d7e9f1a3b2
Create Date: 2026-05-18

"""

from typing import Sequence

import sqlalchemy as sa

from alembic import op


revision: str = "d4e8a1f2c937"
down_revision: str | None = "c5d7e9f1a3b2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("feedback") as batch_op:
        batch_op.alter_column("email", new_column_name="contact", existing_type=sa.String(255))
        batch_op.alter_column("message", existing_type=sa.String(500), nullable=True)
        batch_op.drop_constraint("ck_feedback_reaction_valid", type_="check")
        batch_op.create_check_constraint(
            "ck_feedback_reaction_valid", "reaction IS NULL OR reaction IN ('thumbs_up','thumbs_down','bug','idea')"
        )


def downgrade() -> None:
    with op.batch_alter_table("feedback") as batch_op:
        batch_op.drop_constraint("ck_feedback_reaction_valid", type_="check")
        batch_op.create_check_constraint(
            "ck_feedback_reaction_valid",
            "reaction IS NULL OR reaction IN ('thumbs_up','thumbs_down','bug','idea','heart')",
        )
        batch_op.alter_column("message", existing_type=sa.String(500), nullable=False)
        batch_op.alter_column("contact", new_column_name="email", existing_type=sa.String(255))
