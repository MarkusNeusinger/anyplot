"""add_impl_check_constraints

Close a model↔migration drift on the impls table: the ORM
(core/database/models.py, Impl.__table_args__) has declared
`ck_quality_score_range` and `ck_review_verdict_valid` since the columns were
introduced, but no migration ever created them — so databases built via the
migration chain (rather than metadata.create_all) silently lack both checks.

Before adding the constraints, normalize any pre-existing rows that would
violate them (out-of-range quality_score, unknown review_verdict) to NULL —
the same treatment sync_to_postgres applies to invalid values — so the
ALTER TABLE cannot fail on legacy data.

Revision ID: f4b8d2c6a9e1
Revises: a1c7e2f9b8d3
Create Date: 2026-07-16

"""

from typing import Sequence

from alembic import op


revision: str = "f4b8d2c6a9e1"
down_revision: str | None = "a1c7e2f9b8d3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Normalize legacy rows that would violate the constraints (mirrors the
    # NULL-on-invalid handling in automation/scripts/sync_to_postgres.py).
    op.execute("UPDATE impls SET quality_score = NULL WHERE quality_score < 0 OR quality_score > 100")
    op.execute(
        "UPDATE impls SET review_verdict = NULL "
        "WHERE review_verdict IS NOT NULL AND review_verdict NOT IN ('APPROVED', 'REJECTED')"
    )

    with op.batch_alter_table("impls") as batch_op:
        batch_op.create_check_constraint(
            "ck_quality_score_range", "quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 100)"
        )
        batch_op.create_check_constraint(
            "ck_review_verdict_valid", "review_verdict IS NULL OR review_verdict IN ('APPROVED', 'REJECTED')"
        )


def downgrade() -> None:
    with op.batch_alter_table("impls") as batch_op:
        batch_op.drop_constraint("ck_review_verdict_valid", type_="check")
        batch_op.drop_constraint("ck_quality_score_range", type_="check")
