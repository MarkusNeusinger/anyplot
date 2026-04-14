# Development Guide

Guide for setting up a local development environment.

---

## Prerequisites

- **Python 3.14+**
- **Node.js 18+** and yarn
- **PostgreSQL** (or access to Cloud SQL)
- **uv** - Fast Python package manager

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## Backend Setup

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

## Frontend Setup

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

## Running Tests

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
```

**Coverage target**: 90%+ on tested modules (`core/`, `api/`, `automation/`, `agentic/workflows/modules/`).
Coverage config is in `pyproject.toml` (`[tool.coverage]`) and `codecov.yml`.

---

## Code Quality

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

---

## Environment Variables

Copy `.env.example` and configure:

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `GCS_BUCKET` | No | GCS bucket for images (default: anyplot-images) |
| `GOOGLE_APPLICATION_CREDENTIALS` | No | Path to service account JSON |
| `ENVIRONMENT` | No | `development` or `production` |

---

## Project Structure

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

## Useful Commands

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
