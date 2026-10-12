# Development guide

Guide for setting up a local development environment.

---

## Prerequisites

- **Python 3.13+**
- **Node.js 22.12+** and yarn — `app/.nvmrc` names the version to use (`nvm use` in `app/`),
  and `app/package.json` refuses anything older. Take the latest 22.x: the build toolchain
  needs 22.12, and the dev-only test stack (jsdom) currently wants 22.22.
- **PostgreSQL** (or access to Cloud SQL)
- **uv** - Fast Python package manager

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## Backend setup

```bash
# Clone and install
git clone https://github.com/MarkusNeusinger/anyplot.git
cd anyplot
uv sync --all-extras

# Database configuration
cp .env.example .env
# Edit .env with your DATABASE_URL:
# DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/anyplot

# Run migrations
uv run alembic upgrade head

# Start API server
uv run uvicorn api.main:app --reload
# → http://localhost:8000/docs
```

---

## Frontend setup

```bash
cd app
yarn install
yarn dev
# → http://localhost:3000
```

For production build:
```bash
yarn build
```

---

## Running tests

```bash
# All tests
uv run pytest

# Only unit tests (fast, no DB needed)
uv run pytest tests/unit

# Only integration tests (SQLite in-memory)
uv run pytest tests/integration

# Only E2E tests (requires DATABASE_URL)
uv run pytest tests/e2e

# With coverage report (sources configured in pyproject.toml)
uv run pytest tests/unit tests/integration --cov --cov-report=html

# Unit and integration suites on one worker per CPU (pytest-xdist)
uv run pytest tests/unit tests/integration -n auto
```

The CI job "Run Tests" (`.github/workflows/ci-tests.yml`) runs the suite on the
four CPUs of the hosted runner:

```bash
uv run pytest tests/unit tests/integration tests/e2e -n 4 --dist worksteal --durations=25 \
  --cov=core --cov=api --cov=automation --cov=agentic/workflows/modules --cov=agents
```

`-n` is not in the pytest defaults, so a single file or test still runs in one
process. For a full run, add `-n auto` (one worker per CPU): on four CPUs the
CI-equivalent run takes about 80 s instead of about 3.5 minutes in one
process. Tests must not depend on the order they run in or share a fixed file
path, because each worker runs a different slice of the suite in its own
process.

**Coverage target**: 90%+ on tested modules (`core/`, `api/`, `automation/`, `agentic/workflows/modules/`, `agents/`).
Coverage config is in `pyproject.toml` (`[tool.coverage]`) and `codecov.yml`. Coverage
measures through `sys.monitoring` (`core = "sysmon"`): on Python 3.13 the C tracer
made a serial run about 45 % slower. On 3.13 sysmon measures lines only, so leave
`branch` off; with it on, coverage falls back to the C tracer.

---

## Code quality

Both linting and formatting must pass for CI.

```bash
# Check linting
uv run ruff check .

# Auto-fix linting issues
uv run ruff check . --fix

# Check formatting
uv run ruff format --check .

# Auto-format
uv run ruff format .
```

**Always run before committing:**
```bash
uv run ruff check . && uv run ruff format .
```

---

## Database

### Local PostgreSQL

Set `DATABASE_URL` in `.env`:
```
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/anyplot
```

### Cloud SQL (development)

For Cloud SQL access, your IP must be in the authorized networks. Set:
```
DATABASE_URL=postgresql+asyncpg://user:pass@CLOUD_SQL_PUBLIC_IP:5432/anyplot
```

### Migrations

```bash
# Apply all migrations
uv run alembic upgrade head

# Create new migration
uv run alembic revision --autogenerate -m "description"

# Check current version
uv run alembic current
```

Run these only against a database of your own, such as a local PostgreSQL.
The Cloud SQL database is the shared production database, and it receives a
new revision only through `sync-postgres.yml` after the merge.

To verify a new revision:

1. Push the branch and open the PR. The CI job `Verify Migrations`
   (`.github/workflows/ci-migrations.yml`) runs on every PR that touches
   `alembic/`, `alembic.ini`, `core/database/`, `pyproject.toml` or `uv.lock`.
   On a throwaway PostgreSQL 18 container it checks for a single head, runs
   `alembic upgrade head` and `alembic check`, compares the CHECK constraints
   with the models, and downgrades every revision the PR adds and upgrades
   again. It needs nothing on your machine.
2. Optional: to check before you push, run the same checks locally against a
   throwaway PostgreSQL with the `/verify-migrations` skill
   (`.claude/skills/verify-migrations/SKILL.md`). It starts the database with
   Docker, or with the `pgserver` wheel where Docker doesn't run, and exports
   the throwaway `DATABASE_URL` in the same command as every alembic call, so
   no check can reach production.

How a merged revision reaches production, and how to revert one, is in
[Database migrations](reference/database.md#database-migrations).

---

## Environment variables

Copy `.env.example` and configure:

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `GCS_BUCKET` | No | GCS bucket for images (default: anyplot-images) |
| `GOOGLE_APPLICATION_CREDENTIALS` | No | Path to service account JSON |
| `ENVIRONMENT` | No | `development` or `production` |
| `ORIGIN_SECRET` | No | Production only — leave unset locally and in tests. Arms the [origin gate](reference/api.md#origin-gate), which refuses every request that did not come through Cloudflare |

---

## Project structure

```
anyplot/
├── api/                # FastAPI backend
├── app/                # React frontend
├── core/               # Shared business logic
├── plots/              # Plot specifications and implementations
├── prompts/            # AI agent prompts
├── tests/              # Test suite
│   ├── unit/           # Fast, mocked tests
│   ├── integration/    # SQLite in-memory
│   └── e2e/            # Real PostgreSQL
└── docs/               # Documentation
```

See [Repository Structure](reference/repository.md) for details.

---

## Useful commands

```bash
# Run single test file
uv run pytest tests/unit/api/test_routers.py

# Run single test
uv run pytest tests/unit/api/test_routers.py::test_get_specs -v

# Debug test failures
uv run pytest --pdb

# Check database connection
uv run python -c "from core.database import is_db_configured; print(is_db_configured())"
```

---

## Troubleshooting

### Import errors
```bash
uv sync --reinstall
```

### Database connection issues
```bash
# Test connection
psql -U anyplot -d anyplot -h localhost

# Check migrations
uv run alembic current
```

### Test failures
- Unit/integration tests should work without DATABASE_URL
- E2E tests are skipped if DATABASE_URL is not set
- Run `uv run pytest tests/unit -v` to isolate issues
