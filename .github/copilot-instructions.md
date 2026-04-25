# Copilot Instructions

This file provides guidance to GitHub Copilot when working with code in this repository.

## Important Rules

- **No Co-authored-by in commit messages** - Never add `Co-authored-by:` lines to commit messages. Keep commit messages clean without AI attribution footers.
- **Always write in English** - All output text (code comments, commit messages, PR descriptions, issue comments, documentation) must be in English, even if the user writes in another language.

## Task Suitability

**Good tasks for Copilot:**
- Bug fixes in existing plot implementations
- Adding new plot types following existing patterns
- Updating documentation
- Writing or improving unit tests
- Code refactoring within established patterns
- Fixing linting/formatting issues
- Updating dependencies (after checking security advisories)

**Tasks requiring human review:**
- Changes to core architecture or database schema
- Security-sensitive code (authentication, API keys, credentials)
- Complex algorithmic changes requiring domain expertise
- Breaking changes to public APIs
- Infrastructure or deployment configuration changes

**How to iterate with Copilot:**
- Use `@copilot` in PR comments to request changes or corrections
- Provide specific, actionable feedback referencing line numbers
- Link to relevant documentation or examples in the codebase
- Request explanations if the approach is unclear

## Project Overview

**anyplot** is an AI-powered platform for Python data visualization that automatically discovers, generates, tests, and maintains plotting examples. The platform is specification-driven: every plot starts as a library-agnostic Markdown spec, then AI generates implementations for all supported libraries.

**Supported Libraries** (9 total):
- matplotlib, seaborn, plotly, bokeh, altair, plotnine, pygal, highcharts, lets-plot

**Core Principle**: Community proposes plot ideas via GitHub Issues → AI generates code → AI quality review → Deployed.

## Development Setup

```bash
# Install dependencies (uses uv - fast Python package manager)
uv sync --all-extras

# Run all tests (unit + integration + e2e)
uv run pytest

# Run only unit tests
uv run pytest tests/unit

# Run only integration tests (uses SQLite in-memory)
uv run pytest tests/integration

# Run only E2E tests (requires DATABASE_URL)
uv run pytest tests/e2e

# Linting (required for CI)
uv run ruff check .

# Auto-fix linting issues
uv run ruff check . --fix

# Formatting (required for CI)
uv run ruff format .
```

### Frontend Development

```bash
cd app
yarn install
yarn dev          # Development server
yarn build        # Production build
```

## Architecture

### Plot-Centric Design

Everything for one plot type lives in a single directory:

```
plots/{spec-id}/
├── specification.md     # Library-agnostic description
├── specification.yaml   # Tags, created, issue, suggested
├── metadata/            # Per-library metadata
│   ├── matplotlib.yaml
│   └── ...
└── implementations/     # Library implementations
    ├── matplotlib.py
    ├── seaborn.py
    └── ...
```

Example: `plots/scatter-basic/` contains everything for the basic scatter plot.

### Spec ID Naming Convention

**Format:** `{plot-type}-{variant}-{modifier}` (all lowercase, hyphens only)

Examples: `scatter-basic`, `scatter-color-mapped`, `bar-grouped-horizontal`, `heatmap-correlation`

### Directory Structure

- **`plots/{spec-id}/`**: Plot-centric directories (spec + metadata + implementations)
- **`prompts/`**: AI agent prompts for code generation and quality evaluation
- **`core/`**: Shared business logic (database, repositories, config, utils, images)
  - **`core/database/types.py`**: Custom SQLAlchemy types (PostgreSQL + SQLite compatibility)
  - **`core/database/repositories.py`**: Data access layer
- **`api/`**: FastAPI backend (routers, schemas, dependencies, cache, analytics, MCP server)
- **`app/`**: React frontend (React 19 + TypeScript 6 + Vite 8 + MUI 9)
- **`agentic/`**: AI workflow layer (composable phases, prompt templates, runtime state)
- **`automation/`**: CI/CD helper scripts (workflow_cli, label_manager, sync_to_postgres)
- **`tests/unit/`**: Unit tests with mocked dependencies
- **`tests/integration/`**: Integration tests with SQLite in-memory database
- **`tests/e2e/`**: End-to-end tests with full FastAPI stack
- **`docs/`**: Architecture and workflow documentation

## GitHub Issue Labels

### Specification Labels

- **`spec-request`** - New specification request
- **`spec-ready`** - Specification merged to main, ready for implementations

### Implementation Labels

- **`generate:{library}`** - Trigger single library generation (e.g., `generate:matplotlib`)
- **`generate:all`** - Trigger all 9 libraries via bulk-generate
- **`impl:{library}:done`** - Implementation merged to main
- **`impl:{library}:failed`** - Max retries exhausted (3 attempts)

### PR Labels (set by workflows)

- **`approved`** - Human approved specification for merge
- **`ai-approved`** - AI quality check passed (score >= 90, or >= 50 after 3 attempts)
- **`ai-rejected`** - AI quality check failed (score < 90), triggers repair loop
- **`quality:XX`** - Quality score (e.g., `quality:92`)

**Specification Lifecycle:**
```
[open] spec-request → approved → spec-ready [implementations can start]
```

**Implementation PR Lifecycle:**
```
[open] → impl-review → ai-approved (≥90) → impl-merge → impl:{library}:done
                     → ai-rejected (<90) → impl-repair (×3) → ai-approved (≥50) or failed (<50)
```

## Code Standards

### Python Style

- **Linter/Formatter**: Ruff (enforces PEP 8)
- **Line Length**: 120 characters
- **Type Hints**: Required for all functions
- **Docstrings**: Google style for all public functions
- **Import Order**: Standard library → Third-party → Local

### Testing Standards

- **Coverage Target**: 90%+
- **Test Structure**: Mirror source structure in `tests/unit/` and `tests/integration/`
- **Naming**: `test_{what_it_does}`
- **Fixtures**: Use pytest fixtures in `tests/conftest.py`
- **Test Types**:
  - **Unit tests** (`tests/unit/`): Fast, isolated, mocked dependencies
  - **Integration tests** (`tests/integration/`): SQLite in-memory for API tests
  - **E2E tests** (`tests/e2e/`): Real PostgreSQL with separate `test` database (skipped if DATABASE_URL not set)
- **Markers**: Use `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.e2e`

### Plot Implementation Style (KISS)

Plot implementations are **simple, readable scripts** - like matplotlib gallery examples:

```python
""" anyplot.ai
scatter-basic: Basic Scatter Plot
Library: matplotlib 3.10.0 | Python 3.13
Quality: 92/100 | Created: 2025-01-10
"""

import matplotlib.pyplot as plt
import numpy as np

# Data
np.random.seed(42)
x = np.random.randn(100)
y = x * 0.8 + np.random.randn(100) * 0.5

# Plot
fig, ax = plt.subplots(figsize=(16, 9))
ax.scatter(x, y, alpha=0.7, s=50, color='#306998')
ax.set_title('Basic Scatter Plot')

plt.tight_layout()
plt.savefig('plot.png', dpi=300, bbox_inches='tight')
```

**Header format:** 4-line docstring with anyplot.ai branding, spec-id, library version, quality score.
**Rules:** No functions, no classes, no `if __name__ == '__main__'`. Just: imports → data → plot → save.

### Anti-Patterns to Avoid

- No `preview.png` files in repository (stored in GCS)
- No hardcoded API keys (use environment variables)

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy (async), PostgreSQL, Python 3.14+
- **Frontend**: React 19, TypeScript 6, Vite 8, MUI 9
- **Package Manager**: uv (Python), yarn (Node.js)
- **Linting**: Ruff (Python), ESLint (TypeScript)

## Deployment

The project runs on **Google Cloud Platform** (europe-west4 region):

| Service | Component          | Purpose |
|---------|--------------------|---------|
| **Cloud Run** | `anyplot-backend`  | FastAPI API (auto-scaling, serverless) |
| **Cloud Run** | `anyplot-frontend` | React SPA served via nginx |
| **Cloud SQL** | PostgreSQL 18      | Database (Unix socket in production) |
| **Cloud Storage** | `anyplot-images`   | Preview images (GCS bucket) |
| **Secret Manager** | `DATABASE_URL`     | Secure credential storage |
| **Cloud Build** | Triggers           | Auto-deploy on push to main |

Automatic deployment on push to `main`:
- `api/**`, `core/**`, `pyproject.toml` changes → Backend redeploy
- `app/**` changes → Frontend redeploy

## Acceptance Criteria

Before completing any task:
1. All tests pass: `uv run pytest tests/unit tests/integration`
2. Code passes linting: `uv run ruff check .`
3. Code is properly formatted: `uv run ruff format --check .`
4. Type hints are included for all new functions
5. Docstrings follow Google style for public functions
6. Add integration tests for database-related changes (repositories, models)

## Database

**Connection**: PostgreSQL via SQLAlchemy async + asyncpg

**Connection Modes** (priority order):
1. `DATABASE_URL` - Direct connection (local development)
2. `INSTANCE_CONNECTION_NAME` - Cloud SQL Connector (Cloud Run)

**Database Types** (`core/database/types.py`):
- Custom SQLAlchemy types support both PostgreSQL (production) and SQLite (tests)
- **Production**: Uses optimized PostgreSQL native types (ARRAY, JSONB, UUID)
- **Tests**: Uses compatible SQLite types (JSON, String) for in-memory testing
- **StringArray**: ARRAY(String) in PostgreSQL, JSON text in SQLite
- **UniversalJSON**: JSONB in PostgreSQL, JSON in SQLite
- **UniversalUUID**: UUID in PostgreSQL, String(36) in SQLite

**Benefits**:
- Integration tests run with SQLite in CI (no PostgreSQL needed)
- Production still uses optimized PostgreSQL types
- Same models/code work in both environments

**Local Setup**:
```bash
cp .env.example .env
# Edit .env with DATABASE_URL
uv run alembic upgrade head
```

**Note**: The API works without database in limited mode (filesystem fallback for specs).

## Environment and Troubleshooting

### Known Limitations

- **Package Manager**: `uv` may not be available in all environments. Fallback to `pip` if needed.
- **External Dependencies**: Some domains may be blocked. If encountering network issues, document them in the PR.
- **Database**: Cloud SQL requires proper credentials. Use `.env.example` as template for local development.

### Getting Help

- **Documentation**: Check `docs/` directory for architecture, workflow, and development guides
- **Examples**: Look at existing plot implementations in `plots/` for patterns
- **CLAUDE.md**: Additional guidance specific to Claude AI agent workflows
- **Issue Templates**: Use GitHub issue templates for consistent problem reporting

### Common Issues

- **Import errors**: Run `uv sync --all-extras` or `pip install -e ".[dev]"` to install dependencies
- **Test failures**: Ensure you're testing only changes related to your task, not pre-existing issues
- **Linting failures**: Run `uv run ruff check . --fix` to auto-fix common issues
- **Type checking**: Add type hints using standard Python typing (e.g., `list[str]`, `dict[str, int]`)
