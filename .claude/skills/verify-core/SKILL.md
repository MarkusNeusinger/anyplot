---
name: verify-core
description: Test and smoke-run the shared Python layer in core/ — run pytest the way CI does, run the ruff + mypy gates, and import-check core modules (palette, constants, repositories) directly without the running app. Use when asked to run, test, lint, or verify core/, the database layer, palette, constants, or shared utilities.
---

# Verify the core layer

`core/` holds the shared Python: database (models, repositories,
custom dual-backend types), `constants.py` (the canonical library
registry), `palette.py` (Imprint), config and utils. Most PRs here
touch one module — the right harness is the unit/integration tests
plus direct invocation, not the running app. All paths relative to
the repo root.

## 1 · Tests (what CI gates)

```bash
uv run pytest tests/unit tests/integration
```

Safe anywhere: unit tests are mocked; integration tests run the API
against SQLite in-memory (the custom types in
`core/database/types.py` translate PostgreSQL ARRAY/JSONB/UUID).
E2E tests (`tests/e2e/`) need `DATABASE_URL`, use a separate `test`
database, and are skipped when unset — CI runs them via a Cloud SQL
proxy. **Add integration tests for repository/model changes** —
that's an explicit acceptance criterion.

Lint + type gates, the same three CI runs (`Run Linting` job):

```bash
uv run ruff check . && uv run ruff format --check .
uv run --extra typecheck mypy api core --pretty
```

Both ruff halves matter — CI checks them separately; fixing lint
does not fix formatting.

## 2 · Direct invocation (single-module changes)

The registry and palette are pure imports — smoke them without any
infrastructure:

```bash
uv run python - <<'EOF'
"""Smoke: canonical registry + palette invariants, no DB/HTTP."""
from core.constants import SUPPORTED_LIBRARIES, SUPPORTED_LANGUAGES, LIBRARIES_METADATA, INTERACTIVE_LIBRARIES
from core.palette import IMPRINT

assert len(SUPPORTED_LIBRARIES) == 15, f"library count changed: {len(SUPPORTED_LIBRARIES)}"
assert SUPPORTED_LANGUAGES == frozenset(["python", "r", "julia", "javascript"])
assert len(IMPRINT) == 8 and all(c.startswith("#") and len(c) == 7 for c in IMPRINT)
assert len(LIBRARIES_METADATA) == len(SUPPORTED_LIBRARIES)
print("libraries:", sorted(SUPPORTED_LIBRARIES))
print("interactive:", sorted(INTERACTIVE_LIBRARIES))
print("imprint:", IMPRINT)
print("OK")
EOF
```

Adapt the asserts to what you changed; the point is checking a value
you can predict by hand ("adding a 16th library must move this count
to 16"), not just "it imports". For repository changes, prefer a
real integration test in `tests/integration/` over an ad-hoc DB
script — the SQLite fixture already exists and CI runs it.

To check against **real** data, don't reach for the DB from a script
— the running API already wires DB + core together; use the
`/verify-api` read sweep.

## Gotchas

- **`core/constants.py` is the single source of truth** for
  libraries/languages/labels. Workflows, prompts, the API and the
  frontend all derive from it — a registry change fans out; grep for
  the library id across `.github/workflows/`, `prompts/`, and
  `app/src/` before assuming a one-file change.
- **Changing `core/` triggers a backend redeploy** on merge to main
  (Cloud Build watches `api/**`, `core/**`, `pyproject.toml`) — a
  latent import error that pytest misses breaks the deploy, not the
  PR checks.
- **The custom SQLAlchemy types are dual-backend by design**
  (PostgreSQL in prod, SQLite in tests). When adding a column type,
  verify it on both: an integration test (SQLite) plus one e2e run
  or a careful review of the PostgreSQL branch.
- **Plain `uv run ruff` can fail on a fresh venv** — dev tools live
  in extras; `uv sync --extra dev` (or `--all-extras`) first, and
  mypy always needs `--extra typecheck`.

## Troubleshooting

- `mypy: command not found` / spawn failure → run it as
  `uv run --extra typecheck mypy api core --pretty`.
- Integration tests fail with PostgreSQL-only SQL → the code bypassed
  the dual-backend types; route through `core/database/types.py`.
