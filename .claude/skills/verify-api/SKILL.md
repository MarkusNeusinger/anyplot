---
name: verify-api
description: Run and exercise the anyplot FastAPI backend — start the server, sweep the read endpoints with curl, check payload shapes against the live DB, and respect the shared-production-database discipline; also how to check the deployed agent chat through the admin lane after a deploy. Use when asked to run, start, test, or verify the API, a router, an endpoint, or a backend change, or to test the chat on production.
---

# Verify the API against the live server

FastAPI service in `api/` (routers in `api/routers/`), data in Cloud
SQL Postgres (`.env` → `DATABASE_URL`). **Local dev talks to the SAME
Cloud SQL database production reads — there is no separate local
DB.** Treat every write as touching real data. The harness is `curl`
+ `python3` for JSON checks. All paths relative to the repo root.

**Routes have NO `/api` prefix** — `/specs`, not `/api/specs`. This
is the single most-repeated mistake against this backend.

## 1 · Start the server (skip if already up)

```bash
curl -fsS http://localhost:8000/health
```

If not running, start in the background (Bash
`run_in_background: true`):

```bash
uv run python -m api.main
```

Expected: `/health` 200; `/` returns the welcome JSON
(`{"message": "Welcome to anyplot API", …}`). OpenAPI UI:
`http://localhost:8000/docs`. Without `DATABASE_URL`, data endpoints
fail — check `.env` exists at the repo root.

## 2 · Read-endpoint sweep (safe)

All GET, all safe against the shared DB:

```bash
curl -fsS http://localhost:8000/libraries | python3 -c 'import json,sys; d=json.load(sys.stdin); print(len(d), [x.get("id") or x.get("name") for x in d][:5])'
curl -fsS 'http://localhost:8000/specs?limit=3' | python3 -c 'import json,sys; d=json.load(sys.stdin); print(type(d).__name__, str(d)[:150])'
curl -fsS http://localhost:8000/stats | python3 -c 'import json,sys; print(sorted(json.load(sys.stdin).keys())[:10])'
curl -fsS 'http://localhost:8000/plots/filter?limit=3' | python3 -c 'import json,sys; print(sorted(json.load(sys.stdin).keys()))'
```

Expected baseline (2026-07): 15 libraries across 4 languages
(matplotlib … muix); ~327 specs; `/plots/filter` returns the
`FilteredPlotsResponse` shape. Counts grow — check shape and
plausibility, not exact numbers. The full endpoint reference is
`docs/reference/api.md`; when your change adds/renames endpoints,
update that file in the same PR (CLAUDE.md documentation rule).

For a changed endpoint, don't stop at 200: assert the fields your
change added/modified actually appear in the payload, and hit one
edge case (empty filter, unknown spec-id → 404, `?lang=` filter).

## 3 · Writes and state — the shared-DB discipline

- **Preflight before ANY write-shaped or DDL action** — print where
  `.env` points (never print credentials):

  ```bash
  python3 -c "
  import re
  url = next(l.split('=',1)[1].strip() for l in open('.env') if l.startswith('DATABASE_URL='))
  m = re.search(r'@([^:/]+)[:/]([^?\s]*)', url)
  print(f'host={m.group(1)} db={m.group(2)}')"
  ```

  A public IP here IS the production Cloud SQL instance. Alembic
  commands are DDL against it — a dual-heads incident (#7285) once
  stalled the production sync. Never run destructive migrations
  ad hoc; schema changes ride the normal deploy path.
- The feedback widget POST and analytics events write real rows —
  fine to exercise once deliberately, not in a loop.
- Bulk data flows (implementations, metadata, preview URLs) are owned
  by the GitHub Actions pipeline + `sync_to_postgres`, never written
  by hand (CLAUDE.md mandatory-workflow rules).

## 4 · Tests (what CI gates)

```bash
uv run pytest tests/unit tests/integration -n 4 --dist worksteal
```

CI runs the suite on four pytest-xdist workers (`-n 4 --dist worksteal`,
plus `tests/e2e` and the `--cov` flags); `-n auto` uses every local CPU.
A single file or test needs no `-n`.

Safe anywhere: unit tests are mocked, integration tests run on
SQLite in-memory (`core/database/types.py` makes the types
dual-backend). E2E (`uv run pytest tests/e2e`) needs `DATABASE_URL`
and uses a separate `test` database (auto-created/dropped) — skipped
when unset. Lint gate before commit, both halves:

```bash
uv run --extra dev ruff check . && uv run --extra dev ruff format --check .
uv run --extra typecheck --extra agents mypy api core agents --pretty
```

## 5 · Check the deployed agent chat (admin lane)

For a check of a chat change on production after its deploy. Run it only
when the owner asks for it by name: it costs model calls and can store a
feedback case. Use invented tables only.

A script cannot use the page's own path. `https://anyplot.ai/api/debug/*`
sits behind Cloudflare Access and answers a script with a redirect to the
login. Call the API host directly, with the admin token:

1. **Host and prefix:** `https://api.anyplot.ai/debug/agent/...`.
2. **Token:** production's `ADMIN_TOKEN` from Secret Manager. The value in
   `.env` belongs to the local server, and production answers it with
   `401 Invalid admin token`. Reading the secret is Secret Manager access:
   ask the owner first and name the secret. Read it inside the script's own
   process and strip the trailing newline, for example with
   `subprocess.run(["gcloud", "secrets", "versions", "access", "latest", "--secret=ADMIN_TOKEN", "--project=anyplot"], capture_output=True, text=True)`.
   Never print it, write it to a file, or put it on a command line.
3. **Headers on every request:** `X-Admin-Token`, and
   `X-Anyplot-Client: agent-chat/1`. Without the second one every `POST`,
   `PUT`, and `DELETE` answers `403 client_header_required`
   (`docs/reference/api.md`, "Access, kill switch, and CSRF guard"). Send
   bodies as JSON, and set a `User-Agent` of your own, so that you can
   filter the request log for the check afterwards.
4. **The calls, in the order the page makes them:**
   - `POST /sessions` with `{"spec_id", "library", "locale"}` returns
     `session_id`.
   - `POST /sessions/{sid}/dataset` with `{"text": "<the table>"}`.
   - `POST /sessions/{sid}/messages` with `{"text": "..."}` answers as a
     server-sent event stream: `ready`, `status`, `plot`, `message`,
     `done`. The `done` event carries the dataset with its `changes`
     lines.
   - Before the first plot: `POST /sessions/{sid}/dataset/confirm`, then
     `POST /sessions/{sid}/messages` with `{"action": "create_plot"}`.
     Without the confirmation the `plot` event says `not_ready` with the
     reason `data_unconfirmed`.
   - `POST /sessions/{sid}/feedback` takes `result_version`: the `version`
     of a `plot` event, or `0` for the chat itself. The dataset in `done`
     has a `version` of its own, which is a different number; a result
     version that does not exist answers `404`.
5. **Read the evidence, not only the status codes:** the request log by
   your `User-Agent`
   (`gcloud logging read 'httpRequest.userAgent="<yours>"' --project=anyplot`),
   the agents service's lines for the same minutes, and for a feedback case
   its row in a read-only transaction
   (`.claude/skills/triage-agent-cases/casedb.py`, `read_only`).
6. **Report what the check left behind:** the sessions, the number of model
   calls, and every feedback case with its id. Write "post-deploy check,
   invented data" into a case's message, because the case shows in the
   triage queue until a round retires it.

## Gotchas

- **No `/api` prefix** (worth repeating). In production the
  Cloudflare Worker maps `anyplot.ai/api/*` → the API — that prefix
  exists only at the edge, never in FastAPI routes.
- **The DB is shared with production.** The read sweep is always
  safe; anything else needs the §3 preflight and a reason.
- **`api/cache.py` caches spec lookups in-memory** — after changing
  data server-side, a stale read may be the cache, not your bug;
  restart the server before concluding.
- **MCP server** is mounted on the same app (FastMCP) — if your
  change touches `api/mcp*`, verify with an MCP client call, not
  just curl.
- **`uv run python -m api.main` port-conflicts** mean the server is
  already running — just use it (that's why §1 checks first).

## Troubleshooting

- Data endpoints 500/fail while `/health` is fine → `DATABASE_URL`
  missing or unreachable (Cloud SQL allowlists IPs; a new network can
  break connectivity).
- `curl /api/...` returns 404 → drop the `/api` prefix.
