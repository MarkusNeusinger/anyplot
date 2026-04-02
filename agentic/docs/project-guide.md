# Project Guide for AI Agents

This document contains comprehensive project documentation for AI agents working on the pyplots codebase. For critical rules that must always be visible, see [CLAUDE.md](/CLAUDE.md).

## Project Overview

**pyplots** is an AI-powered platform for Python data visualization that automatically discovers, generates, tests, and maintains plotting examples. The platform is specification-driven: every plot starts as a library-agnostic Markdown spec, then AI generates implementations for all supported libraries.

**Supported Libraries** (9 total):
- **matplotlib** - The classic standard, maximum flexibility
- **seaborn** - Statistical visualizations, beautiful defaults
- **plotly** - Interactive web plots, dashboards, 3D
- **bokeh** - Interactive, streaming data, large datasets
- **altair** - Declarative/Vega-Lite, elegant exploration
- **plotnine** - ggplot2 syntax for R users
- **pygal** - Minimalistic SVG charts
- **highcharts** - Interactive web charts, stock charts (requires license for commercial use)
- **lets-plot** - ggplot2 grammar of graphics by JetBrains, interactive

**Core Principle**: Community proposes plot ideas via GitHub Issues -> AI generates code -> AI quality review -> Deployed.

## Essential Commands

### Development Setup

```bash
# Install dependencies (uses uv - fast Python package manager)
uv sync --all-extras

# Start backend API
uv run uvicorn api.main:app --reload --port 8000

# Run database migrations
uv run alembic upgrade head
```

### Testing

```bash
# Run all tests (unit + integration + e2e)
uv run pytest

# Run only unit tests
uv run pytest tests/unit

# Run only integration tests (uses SQLite in-memory)
uv run pytest tests/integration

# Run only E2E tests (requires DATABASE_URL)
uv run pytest tests/e2e

# Run with coverage (sources configured in pyproject.toml)
uv run pytest tests/unit tests/integration --cov --cov-report=html

# Run specific test file
uv run pytest tests/unit/api/test_routers.py

# Run a single test
uv run pytest tests/unit/api/test_routers.py::test_get_specs
```

**Test Infrastructure**:
- **Unit tests** (`tests/unit/`): Fast, mocked dependencies
- **Integration tests** (`tests/integration/`): SQLite in-memory for API tests
- **E2E tests** (`tests/e2e/`): Real PostgreSQL with separate `test` database

**Database for Tests**:
- **Unit/Integration**: SQLite in-memory (via custom types in `core/database/types.py`)
- **E2E**: PostgreSQL with separate `test` database (tables auto-created, auto-dropped)
- E2E tests are skipped if `DATABASE_URL` is not set

### Code Quality

**Both linting and formatting must pass for CI.**

**IMPORTANT: Always run `uv run ruff check <files> && uv run ruff format <files>` on changed files BEFORE every commit!**

```bash
# Linting (required for CI)
uv run ruff check .

# Auto-fix linting issues
uv run ruff check . --fix

# Formatting (required for CI)
uv run ruff format .

# Before committing - always run both on changed files:
uv run ruff check <files> && uv run ruff format <files>
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
plots/{specification-id}/
├── specification.md     # Description, Applications, Data, Notes
├── specification.yaml   # Spec-level metadata (tags, created, issue, suggested, updates)
├── metadata/            # Per-library metadata (one file per library)
│   ├── matplotlib.yaml
│   ├── seaborn.yaml
│   └── ...
└── implementations/     # Library implementations
    ├── matplotlib.py
    ├── seaborn.py
    ├── plotly.py
    ├── bokeh.py
    ├── altair.py
    ├── plotnine.py
    ├── pygal.py
    ├── highcharts.py
    └── letsplot.py
```

Example: `plots/scatter-basic/` contains everything for the basic scatter plot.

**Key benefits of per-library metadata:**
- No merge conflicts (each library updates only its own file)
- Partial implementations OK (6/9 done = fine)
- Each library runs independently

### Spec ID Naming Convention

**Format:** `{plot-type}-{variant}-{modifier}` (all lowercase, hyphens only)

- `plot-type`: Main visualization type (scatter, bar, line, heatmap, histogram, box, violin, pie, etc.)
- `variant`: Main characteristic (basic, grouped, stacked, horizontal, 3d, multi, etc.)
- `modifier`: Optional additional feature (regression, animated, interactive, annotated, etc.)

**Examples:**
- `scatter-basic` - Simple 2D scatter plot
- `scatter-color-mapped` - Scatter with color encoding
- `scatter-regression-linear` - Scatter with trend line
- `bar-grouped-horizontal` - Horizontal grouped bars
- `heatmap-correlation` - Correlation matrix heatmap
- `line-timeseries-multi` - Multiple time series

**Note:** Legacy specs may use numbered format (`scatter-basic-001`). Both formats are supported.

### Directory Structure

- **`plots/{specification-id}/`**: Plot-centric directories (spec, metadata, implementations together)
  - `specification.md`: Library-agnostic specification (Description, Applications, Data, Notes)
  - `specification.yaml`: Spec-level metadata (tags, created, issue, suggested, updates)
  - `metadata/{library}.yaml`: Per-library metadata (preview_url, quality_score, review feedback)
  - `implementations/{library}.py`: Library-specific implementations
- **`prompts/`**: AI agent prompts for code generation, quality evaluation, and tagging
  - `templates/`: Spec and metadata templates
  - `library/`: Library-specific generation rules (9 files)
- **`core/`**: Shared business logic (database, repositories, config, utils, images)
  - **`core/database/types.py`**: Custom SQLAlchemy types (PostgreSQL + SQLite compatibility)
  - **`core/database/repositories.py`**: Data access layer
- **`api/`**: FastAPI backend (routers, schemas, dependencies, cache, analytics, MCP server)
- **`app/`**: React frontend (Vite 8 + TypeScript 6 + MUI 7)
- **`agentic/`**: AI workflow layer (composable phases, prompt templates, runtime state)
  - **`agentic/workflows/`**: Click CLI scripts (plan, build, test, review + orchestrators)
  - **`agentic/commands/`**: Markdown prompt templates
- **`automation/`**: CI/CD helper scripts (workflow_cli, label_manager, sync_to_postgres)
- **`tests/`**: Unit, integration, and e2e tests mirroring source structure
- **`docs/`**: Architecture and workflow documentation

### Key Architecture Patterns

1. **Repository Pattern**: Data access layer in `core/database/repositories.py`
2. **Async Everything**: FastAPI + SQLAlchemy async + asyncpg
3. **Clean Repo**: Only production code in git. Quality reports -> `metadata/{library}.yaml`. Preview images -> GCS.
4. **Issue-Based Workflow**: GitHub Issues as state machine for plot lifecycle

### Metadata System

Plot metadata is split into two types of files to avoid merge conflicts:

**1. Specification-level metadata:** `plots/{specification-id}/specification.yaml`

```yaml
spec_id: scatter-basic
title: Basic Scatter Plot
created: 2025-01-10T08:00:00Z
updated: 2025-01-15T10:30:00Z
issue: 42
suggested: CoolContributor123
tags:
  plot_type: [scatter, point]
  domain: [statistics, general]
  features: [basic, 2d, correlation]
  data_type: [numeric, continuous]
```

**2. Per-library metadata:** `plots/{specification-id}/metadata/{library}.yaml`

```yaml
library: matplotlib
specification_id: scatter-basic

# Timestamps
created: 2025-01-10T08:00:00Z
updated: 2025-01-15T10:30:00Z

# Generation
generated_by: claude-opus-4-5-20251101
workflow_run: 12345678
issue: 42

# Versions
python_version: "3.13"
library_version: "3.10.0"

# Previews
preview_url: https://storage.googleapis.com/pyplots-images/plots/scatter-basic/matplotlib/plot.png
preview_html: null

# Quality
quality_score: 92

# Implementation-level tags (describes HOW the code implements the plot)
impl_tags:
  dependencies: []  # External packages (scipy, sklearn, etc.)
  techniques: [colorbar, annotations]  # Visualization techniques
  patterns: [data-generation]  # Code patterns
  dataprep: []  # Data transformations
  styling: [publication-ready]  # Visual style

# Review feedback (used for regeneration)
review:
  # AI's visual description of the generated plot
  image_description: |
    The plot shows a scatter plot with 100 data points displaying
    a positive correlation. Points are rendered in blue with 70%
    opacity. Axes are clearly labeled and a subtle grid is visible.

  # Detailed scoring breakdown by category
  criteria_checklist:
    visual_quality:
      score: 36
      max: 40
      items:
        - id: VQ-01
          name: Text Legibility
          score: 10
          max: 10
          passed: true
          comment: "All text readable at full size"
    spec_compliance:
      score: 23
      max: 25
      items: [...]
    # ... data_quality, code_quality, library_features

  # Final verdict
  verdict: APPROVED

  # Summary feedback
  strengths:
    - "Clean code structure"
    - "Good use of alpha for overlapping points"
  weaknesses:
    - "Grid could be more subtle"
```

**3. Implementation headers:** `plots/{specification-id}/implementations/{library}.py`

```python
""" pyplots.ai
scatter-basic: Basic Scatter Plot
Library: matplotlib 3.10.0 | Python 3.13
Quality: 92/100 | Created: 2025-01-10
"""
```

**Key points:**
- Spec-level tracking in `specification.yaml`: `created`, `updated`, `issue`, `suggested`, `tags`
- Per-library metadata in separate files (no merge conflicts!)
- **Review feedback** stored in metadata for regeneration (AI reads previous feedback to improve)
- **Extended review data**: `image_description`, `criteria_checklist`, and `verdict` for targeted fixes
- Contributors credited via `suggested` field
- **Two-level tagging**: Spec-level `tags` describe WHAT is visualized (same for all libraries), impl-level `impl_tags` describe HOW code implements it (per-library)
- Per-library metadata updated automatically by `impl-review.yml` (quality score, review feedback, impl_tags)
- `sync-postgres.yml` workflow syncs to database on push to main
- Database stores full spec content (markdown) and implementation code (Python source)

### GCS Storage Structure

Preview images are stored in Google Cloud Storage (`pyplots-images` bucket):

```
gs://pyplots-images/
├── staging/{spec-id}/{library}/         # Temp images (during generation/review)
│   ├── plot.png                         # Generated by plot-generator.yml
│   └── plot.html                        # Optional (interactive libraries)
│
└── plots/{spec-id}/{library}/           # Production images (after merge to main)
    ├── plot.png                         # Promoted by plot-merge.yml
    └── plot.html                        # Optional (interactive libraries)
```

**Flow:**
1. `impl-generate.yml` uploads to `staging/{spec-id}/{library}/`
2. `impl-review.yml` reads from staging for AI evaluation
3. `impl-merge.yml` promotes staging -> production when PR merges to main

**Interactive libraries** (generate `.html`): plotly, bokeh, altair, highcharts, pygal, letsplot
**PNG only**: matplotlib, seaborn, plotnine

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy (async), PostgreSQL, Python 3.14+
- **Frontend**: React 19, Vite 8, TypeScript 6, MUI 7
- **Plotting**: matplotlib, seaborn, plotly, bokeh, altair, plotnine, pygal, highcharts, lets-plot
- **Package Manager**: uv (fast Python installer)
- **Infrastructure**: Google Cloud Run, Cloud SQL, Cloud Storage
- **Automation**: GitHub Actions
- **AI**: Claude (code generation + quality review)

## Code Standards

### Python Style (API, Core, Tests)

- **Linter/Formatter**: Ruff (enforces PEP 8)
- **Line Length**: 120 characters
- **Type Hints**: Required for all functions
- **Docstrings**: Google style for all public functions
- **Import Order**: Standard library -> Third-party -> Local

**Note:** Plot implementations in `plots/` follow a simpler KISS style - see "Implementation Guidelines" below.

Example (for API/core code):
```python
def get_spec_by_id(spec_id: str, db: Session) -> Spec:
    """
    Retrieve a spec by its ID.

    Args:
        spec_id: The unique spec identifier
        db: Database session

    Returns:
        Spec object if found

    Raises:
        NotFoundError: If spec doesn't exist
    """
    pass
```

### Testing Standards

- **Coverage Target**: 90%+ on tested modules (see `codecov.yml` and `pyproject.toml [tool.coverage]`)
- **Test Structure**: Mirror source structure
- **Naming**: `test_{what_it_does}`
- **Fixtures**: Use pytest fixtures in `tests/conftest.py`

### File Naming Conventions

**Spec IDs**: `{type}-{variant}-{modifier}` (e.g., `scatter-basic`, `heatmap-correlation`)
- No numbers needed - descriptive names scale better
- See "Spec ID Naming Convention" section above for details

**Implementation Files** (in `plots/{spec-id}/implementations/`):
- `{library}.py`: One file per library (e.g., `matplotlib.py`, `seaborn.py`)

## Database

**Connection**: PostgreSQL via SQLAlchemy async + asyncpg

**Connection Modes** (priority order):
1. `DATABASE_URL` - Direct connection (local development via public IP)
2. `INSTANCE_CONNECTION_NAME` - Cloud SQL Connector (Cloud Run, uses IAM auth)

**Local Development**:
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your DATABASE_URL
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/pyplots

# Test connection
uv run python -c "from core.database import is_db_configured; print(is_db_configured())"
```

**What's Stored** (synced from `plots/{specification-id}/`):
- Spec content (full markdown from specification.md)
- Spec metadata (title, description, tags, structured_tags from specification.yaml)
- Implementation code (full Python source)
- Implementation metadata (library, variant, quality score, impl_tags, generation info from metadata/*.yaml)
- GCS URLs for preview images

**What's in Repository** (source of truth):
- Everything in `plots/{specification-id}/`:
  - `specification.md` - specification description
  - `specification.yaml` - spec-level metadata (tags, created, issue, etc.)
  - `metadata/{library}.yaml` - per-library metadata (quality score, review feedback)
  - `implementations/*.py` - library implementations

**What's NOT Stored in DB**:
- Preview images (in GCS)

**Migrations**: Managed with Alembic
```bash
# Create migration
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Check current revision
uv run alembic current
```

## Prompts System

The `prompts/` directory contains AI agent prompts for code generation, quality evaluation, and tagging.

### Prompt Files

| File | Purpose |
|------|---------|
| `plot-generator.md` | Base rules for all plot implementations |
| `library/*.md` | Library-specific rules (9 files) |
| `quality-criteria.md` | Definition of code/visual quality |
| `quality-evaluator.md` | AI quality evaluation prompt |
| `spec-validator.md` | Validates plot request issues |
| `spec-id-generator.md` | Assigns unique spec IDs |
| `spec-tags-generator.md` | AI rules for spec-level tag assignment |
| `impl-tags-generator.md` | AI rules for impl-level tag assignment |

### Using Prompts

```bash
# View a prompt
cat prompts/plot-generator.md
cat prompts/library/matplotlib.md

# Edit a prompt
vim prompts/quality-criteria.md
git commit -m "prompts: improve quality criteria"
```

**No folder versioning** - Git history tracks all changes. View old versions with `git log -p prompts/*.md`.

### Workflow Integration

Workflows reference prompts instead of embedding long instructions:

```yaml
# Example usage in workflow
prompt: |
  $(cat prompts/plot-generator.md)
  $(cat prompts/library/matplotlib.md)

  ## Spec
  $(cat plots/scatter-basic/specification.md)
```

## Implementation Guidelines

### Plot Code Style (KISS)

Plot implementations should be **simple, readable scripts** - like matplotlib gallery examples:

```python
"""
scatter-basic: Basic Scatter Plot
Library: matplotlib
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

ax.set_xlabel('X Value')
ax.set_ylabel('Y Value')
ax.set_title('Basic Scatter Plot')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('plot.png', dpi=300, bbox_inches='tight')
```

**Rules:**
- No functions, no classes
- No `if __name__ == '__main__':`
- No type hints or docstrings (in plot code)
- Just: imports -> data -> plot -> save

### Anti-Patterns to Avoid

- No `preview.png` files in repository (use GCS)
- No `quality_report.json` files (use GitHub Issues)
- No hardcoded API keys (use environment variables)
- Avoid version-specific files unless necessary (prefer single `default.py` for Python 3.10-3.13)

## GitHub Actions Workflows

Located in `.github/workflows/`:

### Specification Workflows (`spec-*.yml`)

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| **spec-create.yml** | `spec-request` label | Creates new specification (branch -> PR -> approval -> merge) |

### Implementation Workflows (`impl-*.yml`)

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| **impl-generate.yml** | `generate:{library}` label OR workflow_dispatch | Generates single library implementation |
| **impl-review.yml** | Called by impl-generate | AI quality review, adds `quality:XX` and `ai-approved`/`ai-rejected` |
| **impl-repair.yml** | Called by impl-review (on rejection) | Fixes rejected implementation (max 3 attempts) |
| **impl-merge.yml** | `ai-approved` label OR workflow_dispatch | Merges approved PR, creates metadata/{library}.yaml |
| **bulk-generate.yml** | workflow_dispatch only | Dispatches multiple implementations (max 3 parallel) |

### Report Workflows (`report-*.yml`)

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| **report-validate.yml** | `report-pending` label | Validates and structures user-submitted issue reports |

### Workflow Data Flow

**Flow A: New Specification (with approval gate)**

```
Issue + spec-request label
    |
    v
spec-create.yml
    |-- Creates branch: specification/{specification-id}
    |-- Creates: plots/{specification-id}/specification.md
    |-- Creates: plots/{specification-id}/specification.yaml
    |-- Validates: checks for duplicates (closes issue if duplicate detected)
    |-- Creates PR: specification/{specification-id} -> main
    +-- Posts: spec analysis comment (waits for approval)
    |
    v (maintainer adds `approved` label)
    |
spec-create.yml (merge job)
    |-- Merges PR to main
    |-- sync-postgres.yml triggers (updates database)
    +-- Adds `spec-ready` label
```

**Flow B: Generate Implementation**

```
Issue + generate:matplotlib label  OR  workflow_dispatch
    |
    v
impl-generate.yml
    |-- Creates branch: implementation/{specification-id}/{library}
    |-- Generates implementation code
    |-- Tests with MPLBACKEND=Agg
    |-- Verifies implementation exists before committing metadata
    |-- Uploads preview to GCS staging
    |-- Creates PR: implementation/{specification-id}/{library} -> main
    +-- Triggers impl-review.yml
        |
        v
impl-review.yml
    |-- AI evaluates code + image
    |-- Posts review comment with score
    |-- Adds labels: quality:XX, ai-approved OR ai-rejected
    |
    |-- If APPROVED -> triggers impl-merge.yml
    |       |-- Validates PR completeness (blocks merge if implementation file missing)
    |       |-- Squash-merges PR to main
    |       |-- Creates metadata/{library}.yaml
    |       |-- Promotes GCS: staging -> production
    |       |-- sync-postgres.yml triggers (updates database)
    |       +-- Updates issue: impl:{library}:done
    |
    +-- If REJECTED -> triggers impl-repair.yml (max 3 attempts)
            |-- Reads AI feedback
            |-- Fixes implementation
            +-- Re-triggers impl-review.yml
```

**Flow C: Report Issue**

```
User submits report issue (from pyplots.ai or GitHub)
    |
    v (report-pending label auto-added)
    |
report-validate.yml
    |-- Validates spec/impl exists
    |-- Reads specification and metadata
    |-- AI analyzes the issue
    |-- Posts structured analysis comment
    |-- Updates title: [{spec-id}] {brief description}
    +-- Updates labels: report-validated + category:* + report:spec/impl
    |
    v
Issue ready for maintainer review
    |
    v (maintainer adds `approved` label)
    |
(Fix workflow - future implementation)
```

### Supporting Workflows

| Workflow | Purpose |
|----------|---------|
| **ci-lint.yml** | Ruff linting on PR |
| **ci-tests.yml** | Unit tests on PR |
| **sync-postgres.yml** | Syncs plots/ to database on push to main |
| **sync-labels.yml** | Auto-syncs labels after manual PR merges (spec-ready, impl:*:done) |
| **notify-deployment.yml** | Deployment notifications |
| **util-claude.yml** | Claude utility workflow |

### Decoupled Architecture

The new architecture separates specification and implementation processes:

**Benefits:**
- **No single point of failure** - Each library runs independently
- **Specifications can land in main without implementations**
- **Partial implementations OK** - 6/9 done = fine
- **No merge conflicts** - Per-library metadata files
- **Flexible triggers** - Labels for single, dispatch for bulk
- **PostgreSQL synced on every merge to main**
- **Labels auto-synced** - Manual PR merges automatically update issue labels

**Branch naming:**
- `specification/{specification-id}` - New specification PRs
- `implementation/{specification-id}/{library}` - Library implementation PRs

**Concurrency:**
- Global limit: max 3 implementation workflows simultaneously
- `bulk-generate.yml` uses `max-parallel: 3` in matrix strategy
- Spec merge operations are serialized (one at a time) to prevent race conditions

## GitHub Issue Labels

The project uses a structured labeling system. Setup labels with:
```bash
bash .github/scripts/setup-labels.sh
```

### Specification Labels

- **`spec-request`** - New specification request
- **`spec-ready`** - Specification merged to main, ready for implementations

### Implementation Labels (on specification issue)

- **`generate:{library}`** - Trigger single library generation (e.g., `generate:matplotlib`)
- **`generate:all`** - Trigger all 9 libraries via bulk-generate
- **`impl:{library}:pending`** - Generation in progress
- **`impl:{library}:done`** - Implementation merged to main
- **`impl:{library}:failed`** - Max retries exhausted (3 attempts)

### PR Labels (set by workflows)

- **`ai-attempt-1`**, **`ai-attempt-2`**, **`ai-attempt-3`** - Retry counter
- **`ai-review-failed`** - AI review action failed or timed out
- **`not-feasible`** - Library cannot implement this specification (after 3 failed attempts)

### Approval Labels (Human vs AI distinction)

| Label | Meaning | Set by |
|-------|---------|--------|
| `approved` | Human approved specification for merge | Maintainer manually |
| `ai-approved` | AI quality check passed (score >= 90, or >= 50 after 3 attempts) | Workflow automatically |
| `rejected` | Human rejected | Maintainer manually |
| `ai-rejected` | AI quality check failed (score < 90), triggers repair loop | Workflow automatically |
| `quality-poor` | Score < 50, needs fundamental fixes | Workflow automatically |

**Quality Workflow:**
- **>= 90**: ai-approved, merged immediately
- **< 90**: ai-rejected, repair loop (up to 3 attempts)
- **After 3 attempts**: >= 50 -> ai-approved and merge, < 50 -> close PR and regenerate

### Quality Score Labels

Quality scores are added as labels in format `quality:XX` (e.g., `quality:92`, `quality:85`).

These are set automatically by `impl-review.yml` after AI evaluation and used by `impl-merge.yml` to create metadata/{library}.yaml.

### Development Labels

- **`bug`** - Something isn't working
- **`infrastructure`** - Workflow, backend, or frontend issues
- **`documentation`** - Documentation improvements
- **`enhancement`** - New feature or improvement

### Report Labels

| Label | Purpose |
|-------|---------|
| `report:spec` | Issue with the specification (affects all libraries) |
| `report:impl` | Issue with a specific implementation |
| `report:impl:{library}` | Specific library affected (e.g., `report:impl:matplotlib`) |
| `category:visual` | Design/visual issues |
| `category:data` | Data quality issues |
| `category:functional` | Non-functional elements |
| `category:other` | Other issues |
| `report-pending` | Report submitted, awaiting AI validation |
| `report-validated` | AI validated, ready for maintainer review |

### New Specification Workflow

1. User creates issue with descriptive title (e.g., "3D scatter plot with rotation animation")
2. Add `spec-request` label
3. **`spec-create.yml` automatically runs:**
   - Analyzes the request, assigns spec ID (e.g., `scatter-3d-animated`)
   - Creates branch: `specification/{specification-id}`
   - Generates: `plots/{specification-id}/specification.md` + `specification.yaml`
   - Creates PR: `specification/{specification-id}` -> `main`
   - Posts comment with spec analysis (waits for approval)
4. Maintainer reviews spec and adds `approved` label
5. **`spec-create.yml` merge job triggers:**
   - Merges PR to main
   - Adds `spec-ready` label
   - `sync-postgres.yml` triggers automatically

**Specification is now in main, ready for implementations.**

### Generate Implementations

**Option A: Single library (label trigger)**
1. Add `generate:matplotlib` label to specification issue
2. `impl-generate.yml` triggers for that library

**Option B: Single library (manual dispatch)**
1. Go to Actions -> impl-generate.yml -> Run workflow
2. Enter specification_id and library

**Option C: Bulk (all libraries for one spec)**
1. Go to Actions -> bulk-generate.yml -> Run workflow
2. Enter specification_id, library=all

**Option D: Bulk (one library across all specs)**
1. Go to Actions -> bulk-generate.yml -> Run workflow
2. Enter specification_id=all, library=matplotlib

### Issue Lifecycle

```
[open] spec-request -> approved -> spec-ready [implementations can start]
```

### Implementation PR Lifecycle

```
[open] -> impl-review
       -> ai-approved -> impl-merge -> impl:{library}:done
       -> ai-rejected -> impl-repair (x3) -> ai-attempt-1/2/3
                                          -> not-feasible (after 3 failures)
```

**Test Issues:** When creating issues for testing workflows, add the `test` label to exclude them from production searches.

## Environment Variables

Required in `.env` for local development:
```bash
# Database (Cloud SQL via public IP for local dev)
DATABASE_URL=postgresql+asyncpg://user:password@CLOUD_SQL_IP:5432/pyplots

# Google Cloud Storage
GCS_BUCKET=pyplots-images
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Environment
ENVIRONMENT=development
```

**Production** (Cloud Run): Secrets are injected via Secret Manager and environment variables set in `cloudbuild.yaml`.

See `.env.example` for full list with comments.

## Common Development Tasks

### Adding a New Plot Type

1. Create GitHub Issue with descriptive title (e.g., "Grouped bar chart with error bars")
2. Add label `spec-request`
3. `spec-create.yml` automatically:
   - Assigns spec ID (e.g., `bar-grouped-errorbars`)
   - Creates specification PR
4. Maintainer reviews spec and adds `approved` label
5. Specification merges to main
6. Add `generate:{library}` labels to trigger implementations
   - Or use `bulk-generate.yml` for all libraries at once
7. Each library PR goes through AI quality review
8. Approved implementations merge independently

### Updating an Existing Implementation

1. Use `impl-generate.yml` via workflow_dispatch
2. Enter specification_id and library to regenerate
3. New implementation PR goes through AI quality review
4. Approved changes merge to main

### Testing Plot Generation Locally

```bash
# Run implementation file directly
python plots/scatter-basic/implementations/matplotlib.py
```

## Cloud Deployment

The project runs on **Google Cloud Platform**:

| Service | Component | Purpose |
|---------|-----------|---------|
| **Cloud Run** | `pyplots-backend` | FastAPI API (auto-scaling, serverless) |
| **Cloud Run** | `pyplots-frontend` | React SPA served via nginx |
| **Cloud SQL** | PostgreSQL | Database (connected via Unix socket) |
| **Cloud Storage** | `pyplots-images` | Preview images (GCS bucket) |
| **Secret Manager** | `DATABASE_URL` | Secure credential storage |
| **Cloud Build** | Triggers | Auto-deploy on push to main |

### Automatic Deployment

Push to `main` branch triggers Cloud Build:
- Changes in `api/`, `core/`, `pyproject.toml` -> Backend redeploy
- Changes in `app/` -> Frontend redeploy

### Manual Deployment

```bash
# Backend
gcloud builds submit --config=api/cloudbuild.yaml --project=YOUR_PROJECT_ID

# Frontend
gcloud builds submit --config=app/cloudbuild.yaml --project=YOUR_PROJECT_ID
```

### Configuration Files

- **`api/cloudbuild.yaml`**: Backend build + deploy (includes Cloud SQL connection)
- **`api/Dockerfile`**: Python 3.13 + uv + FastAPI
- **`app/cloudbuild.yaml`**: Frontend build + deploy
- **`app/Dockerfile`**: Multi-stage build (Node -> nginx)

## Debugging Tips

### Database Connection Issues
```bash
psql -U pyplots -d pyplots -h localhost
uv run alembic current
```

### Import Errors
```bash
uv pip list
uv sync --reinstall
```

### Test Failures
```bash
pytest -v          # Verbose
pytest -s          # Show prints
pytest --pdb       # Debug on failure
```

## Key Documentation Files

- **docs/contributing.md**: How to add/improve specs and implementations
- **docs/workflows/overview.md**: Automation flows and label system
- **docs/concepts/vision.md**: Product vision
- **docs/reference/repository.md**: Directory structure
- **docs/reference/api.md**: API endpoints reference
- **docs/reference/database.md**: Database schema
- **prompts/README.md**: AI agent prompt system

## Project Philosophy

- **No manual coding**: AI generates and maintains all plot implementations
- **Spec improvements over code fixes**: If a plot has issues, improve the spec, not the code
- **Your data first**: Examples work with real user data, not fake data
- **Community-driven**: Anyone can propose plots via GitHub Issues
- **AI quality review**: Claude evaluates quality (>=90 instant merge, <90 repair loop, >=50 minimum)
- **Full transparency**: All quality feedback stored in repository (`metadata/{library}.yaml`)
