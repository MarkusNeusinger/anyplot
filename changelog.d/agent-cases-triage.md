### Added

- **Agent cases: the triage half of quick feedback.** A new table
  `agent_feedback` (Alembic revision `b4e7a9c2d6f1`) holds one row per feedback
  case of the agent chat. `POST /debug/agent/sessions/{sid}/feedback` inserts it
  right after the case's files are in the private bucket, and answers
  `502 row_missing` with the stored case id when the files are stored but the
  row is not, so the page names that case in its next edit. The debug page's
  new "agent cases" section lists the cases with filters (reaction, status,
  spec, library, model version, tag; superseded cases hidden by default), opens
  one (its PNGs, the code with a unified diff against the catalogue original,
  the transcript, the defect lines, the config stamp, the message), sets its
  status and tags, and promotes it to an eval case, through
  `GET /debug/agent/cases`, `GET /debug/agent/cases/{id}`,
  `GET /debug/agent/cases/{id}/files/{name}` and `PATCH /debug/agent/cases/{id}`.
  An edit's `replaces` supersedes the earlier row only for the same session
  hash and result version. The row is the source of truth for status, tags and
  promotion; the bucket holds the files until its lifecycle rule deletes them,
  and the row keeps the failure-class statistics after that.
- **`agents.evals.sync_cases` pulls promoted cases into the harness.** On the
  dev machine it reads the table, downloads each promoted, active case from the
  bucket and imports it through `import_case` into the git-ignored
  `agents/evals/.cases/`, removes the directories of retired, superseded or
  unpromoted cases, and with `--backfill` indexes the cases that reached the
  bucket without a row (a dry run unless `--apply`).
- **CI verifies every migration before merge.** The new workflow
  `ci-migrations.yml` (check `Verify Migrations`) runs the checks of
  `/verify-migrations` on a PostgreSQL 18 service container for every PR that
  touches `alembic/`, `alembic.ini`, `core/database/`, `pyproject.toml` or
  `uv.lock`: one head, `upgrade head`, `alembic check`, and a downgrade to the
  base commit's head and back, plus a CHECK-constraint parity query that
  `alembic check` cannot do. Until now the first database to see a new revision
  was production, after the merge.
