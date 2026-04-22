"""add_languages_table_and_preview_variants

Phase B of the big plot migration:
- Create a `languages` table (analog to `libraries`) so future R, JavaScript,
  Julia etc. can be added without another schema change.
- Convert `libraries.language` (String) into `libraries.language_id` (FK → languages.id).
- Add `impls.language_id` FK with backfill to "python".
- Broaden the impls unique constraint from (spec_id, library_id) to
  (spec_id, language_id, library_id).
- Rename `preview_url` → `preview_url_light`, `preview_html` → `preview_html_light`;
  add `preview_url_dark` and `preview_html_dark` columns (filled later by Phase C).

Revision ID: f2d9c8a1b4e0
Revises: e1f3a2c4d5b6
Create Date: 2026-04-22 15:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op


revision: str = "f2d9c8a1b4e0"
down_revision: Union[str, None] = "e1f3a2c4d5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create languages table
    op.create_table(
        "languages",
        sa.Column("id", sa.String(length=50), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("file_extension", sa.String(length=10), nullable=False),
        sa.Column("runtime_version", sa.String(length=50), nullable=True),
        sa.Column("documentation_url", sa.String(length=500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created", sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )

    # 2. Seed: Python is the only language that exists today.
    op.execute(
        """
        INSERT INTO languages (id, name, file_extension, description, created)
        VALUES ('python', 'Python', '.py',
                'The default language for anyplot plot implementations.',
                NOW())
        """
    )

    # 3. libraries.language (String) → libraries.language_id (FK → languages.id)
    op.alter_column("libraries", "language", new_column_name="language_id")
    op.alter_column("libraries", "language_id", server_default=None)
    op.create_foreign_key(
        "fk_libraries_language_id", "libraries", "languages", ["language_id"], ["id"], ondelete="RESTRICT"
    )

    # 4. Add impls.language_id FK with backfill default "python"
    op.add_column("impls", sa.Column("language_id", sa.String(length=50), nullable=False, server_default="python"))
    op.create_foreign_key("fk_impls_language_id", "impls", "languages", ["language_id"], ["id"], ondelete="RESTRICT")
    # Drop the server_default after the backfill is in place — future inserts must provide language_id explicitly.
    op.alter_column("impls", "language_id", server_default=None)

    # 5. Broaden the unique constraint
    op.drop_constraint("uq_impl", "impls", type_="unique")
    op.create_unique_constraint("uq_impl", "impls", ["spec_id", "language_id", "library_id"])

    # 6. Preview columns: rename light, add dark variants
    op.alter_column("impls", "preview_url", new_column_name="preview_url_light")
    op.alter_column("impls", "preview_html", new_column_name="preview_html_light")
    op.add_column("impls", sa.Column("preview_url_dark", sa.String(), nullable=True))
    op.add_column("impls", sa.Column("preview_html_dark", sa.String(), nullable=True))


def downgrade() -> None:
    # 6. Restore preview column names
    op.drop_column("impls", "preview_html_dark")
    op.drop_column("impls", "preview_url_dark")
    op.alter_column("impls", "preview_html_light", new_column_name="preview_html")
    op.alter_column("impls", "preview_url_light", new_column_name="preview_url")

    # 5. Restore old unique constraint
    op.drop_constraint("uq_impl", "impls", type_="unique")
    op.create_unique_constraint("uq_impl", "impls", ["spec_id", "library_id"])

    # 4. Drop impls.language_id FK + column
    op.drop_constraint("fk_impls_language_id", "impls", type_="foreignkey")
    op.drop_column("impls", "language_id")

    # 3. Restore libraries.language (String, no FK)
    op.drop_constraint("fk_libraries_language_id", "libraries", type_="foreignkey")
    op.alter_column("libraries", "language_id", new_column_name="language", server_default=sa.text("'python'"))

    # 1-2. Drop languages table
    op.drop_table("languages")
