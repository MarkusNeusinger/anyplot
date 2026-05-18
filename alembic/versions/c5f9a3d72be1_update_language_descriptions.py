"""update language descriptions and backfill metadata

Refreshes the seeded `languages` rows so they carry meaningful descriptions
and complete metadata. The initial seed (LANGUAGES_METADATA) populated
python with a meta-y placeholder ("the default language for anyplot plot
implementations") that didn't actually describe Python, which made the new
language tooltip on plot cards unhelpful. The python row also ended up with
NULL `runtime_version` and `documentation_url` on the live DB, so we
backfill both rows defensively from the current LANGUAGES_METADATA.

We UPDATE explicitly rather than relying on the seeder because
`sync_to_postgres.py` uses `on_conflict_do_nothing`, so once a language row
is seeded it stays frozen on subsequent runs.

Revision ID: c5f9a3d72be1
Revises: 3a7e1b5c0c4f
Create Date: 2026-05-17
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "c5f9a3d72be1"
down_revision: str | None = "3a7e1b5c0c4f"
branch_labels: str | None = None
depends_on: str | None = None


_NEW_ROWS = {
    "python": {
        "runtime_version": "3.13",
        "documentation_url": "https://www.python.org",
        "description": (
            "General-purpose, high-level programming language with a clean, readable syntax. "
            "The lingua franca of data science, scientific computing, and the SciPy / PyData ecosystem."
        ),
    },
    "r": {
        "runtime_version": "4.4",
        "documentation_url": "https://www.r-project.org",
        "description": (
            "Language and environment for statistical computing and graphics. "
            "Widely used in academia, biotech, and finance research, with a rich package ecosystem on CRAN."
        ),
    },
}

# Roll-back values for the description field only — the missing
# runtime_version / documentation_url on python were never explicitly set
# pre-migration, so downgrade leaves those backfills in place rather than
# re-nulling them.
_OLD_DESCRIPTIONS = {
    "python": "The default language for anyplot plot implementations.",
    "r": ("R is a statistical computing environment widely used in academia, biotech, and finance research."),
}


def _languages_table() -> sa.Table:
    return sa.table(
        "languages",
        sa.column("id", sa.String),
        sa.column("runtime_version", sa.String),
        sa.column("documentation_url", sa.String),
        sa.column("description", sa.Text),
    )


def upgrade() -> None:
    languages = _languages_table()
    bind = op.get_bind()
    for lang_id, values in _NEW_ROWS.items():
        bind.execute(languages.update().where(languages.c.id == lang_id).values(**values))


def downgrade() -> None:
    languages = _languages_table()
    bind = op.get_bind()
    for lang_id, desc in _OLD_DESCRIPTIONS.items():
        bind.execute(languages.update().where(languages.c.id == lang_id).values(description=desc))
