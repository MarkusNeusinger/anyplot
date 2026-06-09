"""migrate_highcharts_to_javascript

Phase 2 of the JavaScript rollout (docs/concepts/library-expansion.md §6, the
"most-used variant" rule): native highcharts.js (~1 M npm downloads/wk) vastly
outweighs the highcharts-core Python wrapper (~5 k/wk), so the canonical
`highcharts` registry entry moves from Python to JavaScript.

The libraries seed in automation/scripts/sync_to_postgres.py upserts with
ON CONFLICT DO NOTHING, so it inserts *new* libraries but never rewrites an
existing row. `highcharts` predates the language column (it was backfilled to
'python'), so flipping its language requires an explicit data migration here.

This is a data-only migration (no schema change): it points the existing
`highcharts` row at the 'javascript' language and refreshes its version to the
vendored highcharts.js (package.json / package-lock.json). The 'javascript'
language row already exists (seeded in Phase 1). On a fresh database the
libraries table is empty when migrations run, so the UPDATE simply matches zero
rows and the seed later inserts `highcharts` straight as JavaScript — making the
migration a safe no-op in that case.

Revision ID: a1c7e2f9b8d3
Revises: f7a2c9d4e8b1
Create Date: 2026-06-09 16:45:00.000000

"""

from typing import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "a1c7e2f9b8d3"
down_revision: str | None = "f7a2c9d4e8b1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE libraries
        SET language_id = 'javascript',
            framework   = 'none',
            version     = '12.6.0'
        WHERE id = 'highcharts'
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE libraries
        SET language_id = 'python',
            framework   = 'none',
            version     = '1.10.0'
        WHERE id = 'highcharts'
        """
    )
