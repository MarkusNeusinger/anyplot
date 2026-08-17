---
name: verify-migrations
description: Verify Alembic schema migrations locally against a throwaway PostgreSQL — single-head check, full upgrade chain, model↔migration drift via alembic check, and a downgrade/upgrade roundtrip — without ever touching the shared production Cloud SQL DB. Use when asked to verify, test, or check a migration, a schema change, or alembic revisions before pushing.
---

# Verify migrations against a throwaway Postgres

The shared Cloud SQL DB must never see an untested revision. **No CI
job runs migrations at PR time** — only `sync-postgres.yml` runs
`alembic upgrade head` against production after a merge — so this
skill is the ONLY pre-merge loop for `alembic/` diffs. A dual-heads
state once stalled the production sync (#7285); the checks below
catch that class before the push. First full run 2026-08-17: all four
checks green — after `alembic check` caught seven migration-created
indexes missing from the ORM models (fixed in the same PR).

## 0 · The `.env` trap (read first)

`alembic/env.py` calls `load_dotenv()`: any alembic command run
WITHOUT `DATABASE_URL` exported silently uses the `.env` URL — the
shared production DB. Exported env vars win over `.env`, so ALWAYS
run the checks with the throwaway URL exported **in the same Bash
invocation** (env does not persist between calls).

## 1 · Start a throwaway Postgres

**With Docker (local machine; prod is PostgreSQL 18):**

```bash
docker run --rm -d --name pg-migrate-check -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=anyplot -p 55432:5432 postgres:18
```

(WSL: if the daemon isn't running, `sudo service docker start` first —
needs the user's password in a real terminal.)

**Without Docker or root (verified 2026-08-17): the `pgserver` wheel
bundles a rootless Postgres (~16.x — fine for the checks; use the
Docker path when prod-version parity matters):**

```bash
uv run --no-project --with pgserver --python 3.12 python - <<'EOF'
import pgserver
db = pgserver.get_server('/var/tmp/pg-anyplot-check', cleanup_mode=None)
db.psql('CREATE DATABASE anyplot;')
print("URI:", db.get_uri())
EOF
```

(`--no-project --python 3.12`: pgserver ships no wheels for the
project's Python 3.13, and `--no-project` sidesteps the
`requires-python >=3.13` constraint — the server is a separate
process; alembic still runs in the project env.)

## 2 · The four checks (one Bash invocation)

```bash
# Docker variant:
export DATABASE_URL='postgresql+asyncpg://postgres:postgres@localhost:55432/anyplot'
# pgserver variant (Unix socket) instead:
# export DATABASE_URL='postgresql+asyncpg://postgres@/anyplot?host=/var/tmp/pg-anyplot-check'
uv run alembic heads                                         # exactly ONE head (dual heads = the #7285 incident class)
uv run alembic upgrade head                                  # the full revision chain
uv run alembic check                                         # model ↔ migration drift (autogenerate diff)
uv run alembic downgrade -1 && uv run alembic upgrade head   # newest revision reversible
```

Expected: `heads` prints a single revision; the upgrade ends at head;
`check` prints "No new upgrade operations detected."; the roundtrip
runs both directions without error.

## 3 · Tear down

```bash
docker rm -f pg-migrate-check        # docker variant
```

```bash
# pgserver variant:
uv run --no-project --with pgserver --python 3.12 python - <<'EOF'
import pgserver, shutil
pgserver.get_server('/var/tmp/pg-anyplot-check').cleanup()
shutil.rmtree('/var/tmp/pg-anyplot-check', ignore_errors=True)
EOF
```

## Gotchas

- **`alembic check` needs the DB already migrated to head** — run it
  after `upgrade head`, never against an empty DB (everything would
  look like drift).
- **The URL must keep the `+asyncpg` driver**
  (`postgresql+asyncpg://…`) — `env.py` runs migrations through the
  async engine when `DATABASE_URL` is set.
- **The downgrade roundtrip only exercises the NEWEST revision** —
  when a PR adds several revisions, widen it
  (`downgrade -<n>` then `upgrade head`).
- **Never point this flow at the shared DB.** The `/verify-api` §3
  preflight applies to every alembic command (a public-IP host with
  db=anyplot IS production). Prod schema changes ride
  `sync-postgres.yml` after the merge — never ad-hoc DDL.
