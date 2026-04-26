# 📁 Repository Structure

## Overview

anyplot follows a **plot-centric repository pattern** where everything for one plot type lives in a single directory:

```
plots/{specification-id}/
├── specification.md     # Description, Applications, Data, Notes
├── specification.yaml   # Spec-level metadata (tags, created, issue, suggested)
├── metadata/            # Per-library metadata (one file per library)
│   ├── matplotlib.yaml
│   ├── seaborn.yaml
│   └── ...
└── implementations/     # Library implementations
    ├── matplotlib.py
    ├── seaborn.py
    └── ...
```

**Key Principle**: The repository is the **source of truth** for all code, specs, and quality data. Preview images are stored in GCS. Database is derived via sync.

**Key Benefit**: Per-library metadata files eliminate merge conflicts when multiple implementations are generated in parallel.

---

## Directory Layout

```
anyplot/
├── plots/                             # Plot-centric directories
│   ├── scatter-basic/                 # Everything for basic scatter plot
│   │   ├── specification.md           # Library-agnostic specification
│   │   ├── specification.yaml         # Spec-level metadata (tags, created, issue)
│   │   ├── metadata/                  # Per-library metadata
│   │   │   ├── matplotlib.yaml
│   │   │   ├── seaborn.yaml
│   │   │   └── ...
│   │   └── implementations/           # Library-specific code
│   │       ├── matplotlib.py
│   │       ├── seaborn.py
│   │       ├── plotly.py
│   │       ├── bokeh.py
│   │       ├── altair.py
│   │       ├── plotnine.py
│   │       ├── pygal.py
│   │       ├── highcharts.py
│   │       └── letsplot.py
│   │
│   ├── bar-basic/
│   │   ├── specification.md
│   │   ├── specification.yaml
│   │   ├── metadata/
│   │   └── implementations/
│   │       └── ...
│   │
│   └── heatmap-correlation/
│       ├── specification.md
│       ├── specification.yaml
│       ├── metadata/
│       └── implementations/
│           └── ...
│
├── prompts/                           # AI agent prompts
│   ├── plot-generator.md              # Base rules for code generation
│   ├── quality-criteria.md            # Quality evaluation criteria
│   ├── quality-evaluator.md           # AI quality evaluation prompt
│   ├── spec-validator.md              # Validates plot requests
│   ├── spec-id-generator.md           # Assigns spec IDs
│   ├── default-style-guide.md         # Default visual style rules
│   ├── library/                       # Library-specific rules (9 files)
│   │   ├── matplotlib.md
│   │   ├── seaborn.md
│   │   └── ...
│   ├── templates/                     # Templates for new specs
│   │   ├── specification.md
│   │   └── specification.yaml
│   └── workflow-prompts/              # Workflow-specific prompts
│       └── ...
│
├── core/                              # Shared business logic
│   ├── __init__.py
│   ├── config.py                      # Configuration (.env-based)
│   ├── constants.py                   # Library metadata, constants
│   ├── images.py                      # Image processing utilities
│   ├── utils.py                       # General utilities
│   ├── database/                      # Database layer
│   │   ├── __init__.py
│   │   ├── connection.py              # Async connection management
│   │   ├── models.py                  # SQLAlchemy ORM models
│   │   ├── repositories.py            # Repository pattern
│   │   └── types.py                   # Custom SQLAlchemy types
│
├── api/                               # FastAPI backend
│   ├── __init__.py
│   ├── main.py                        # Application entry point
│   └── Dockerfile                     # Cloud Run deployment
│
├── app/                               # React frontend
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── lib/
│   ├── package.json
│   └── Dockerfile
│
├── automation/                        # Workflow automation
│   └── scripts/                       # Workflow-specific utilities
│       ├── sync_to_postgres.py        # Sync plots/ to database
│       ├── workflow_utils.py          # Utilities for GitHub Actions
│       ├── label_manager.py           # Label operations
│       └── workflow_cli.py            # CLI for workflows
│
├── tests/                             # Test suite
│   ├── conftest.py                    # Shared fixtures
│   ├── unit/                          # Fast, mocked tests
│   │   ├── api/
│   │   ├── core/
│   │   └── ...
│   ├── integration/                   # SQLite in-memory tests
│   └── e2e/                           # Real PostgreSQL tests
│
├── .github/
│   └── workflows/                     # GitHub Actions CI/CD
│       ├── spec-create.yml            # Creates specification (branch → PR → approval)
│       ├── impl-generate.yml          # Generates single library implementation
│       ├── impl-review.yml            # AI quality evaluation
│       ├── impl-repair.yml            # Repairs rejected implementation
│       ├── impl-merge.yml             # Merges approved implementation
│       ├── bulk-generate.yml          # Batch operations (multiple specs/libraries)
│       ├── sync-postgres.yml          # Sync to database on push to main
│       └── ...
│
├── alembic/                           # Database migrations
│   └── versions/
│
├── scripts/                           # One-time and manual scripts
│   ├── evaluate-plot.py               # Manual plot evaluation
│   ├── regenerate-thumbnails.py       # Image processing
│   ├── backfill_review_metadata.py    # One-time migration
│   ├── fix_library_versions.py        # One-time fix
│   ├── migrate_metadata_format.py     # One-time migration
│   ├── migrate_to_new_structure.py    # One-time migration
│   └── upgrade_specs*.py              # Spec upgrade utilities
│
├── docs/                              # Documentation
│   ├── concepts/
│   ├── reference/
│   ├── workflows/
│   ├── contributing.md
│   └── index.md
│
├── pyproject.toml                     # Python project config (uv)
├── uv.lock                            # Dependency lock file
├── .env.example                       # Environment variables template
├── CLAUDE.md                          # AI assistant instructions
└── README.md
```

---

## Key Directories Explained

### `plots/{specification-id}/`

**Purpose**: Plot-centric directories containing everything for one plot type

**Structure**:
```
plots/{specification-id}/
├── specification.md     # Library-agnostic specification
├── specification.yaml   # Spec-level metadata (tags, created, issue, suggested)
├── metadata/            # Per-library metadata
│   ├── matplotlib.yaml  # Quality score, preview URL, generation history
│   └── ...
└── implementations/     # Library-specific implementations
    ├── matplotlib.py
    ├── seaborn.py
    └── ...
```

**Characteristics**:
- ✅ Self-contained (spec + metadata + code + quality reports together)
- ✅ Easy to navigate (one folder = one plot type)
- ✅ Synced to PostgreSQL via `sync-postgres.yml`
- ✅ No merge conflicts (per-library metadata files)
- ✅ Quality reports in `metadata/python/{library}.yaml` (review section)
- ❌ NO preview images (stored in GCS)

**Example**: `plots/scatter-basic/` contains everything for the basic scatter plot.

---

### `plots/{specification-id}/specification.md`

**Purpose**: Library-agnostic plot specification

**Contents**:
- Title and description
- Data requirements (columns, types)
- Use cases with domain context
- Visual requirements

**Naming**: Always `specification.md` (consistent across all plots)

---

### `plots/{specification-id}/specification.yaml`

**Purpose**: Spec-level metadata synced to PostgreSQL

**Contents**:
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
  features: [basic, 2d]
  data_type: [numeric]
```

**Key Points**:
- Tags are at spec level (same for all libraries)
- `suggested` credits the contributor who proposed the spec
- `updated` timestamp set on any change (git history for details)

---

### `plots/{specification-id}/metadata/python/{library}.yaml`

**Purpose**: Per-library metadata (one file per library)

**Contents**:
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
preview_url: https://storage.googleapis.com/anyplot-images/plots/scatter-basic/matplotlib/plot.png
preview_html: null

# Quality
quality_score: 92

# Review feedback (used by AI for regeneration)
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
        - id: VQ-02
          name: No Overlap
          score: 8
          max: 8
          passed: true
          comment: "No element overlap detected"
    spec_compliance:
      score: 23
      max: 25
      items: [...]
    data_quality:
      score: 18
      max: 20
      items: [...]
    code_quality:
      score: 10
      max: 10
      items: [...]
    library_features:
      score: 5
      max: 5
      items: [...]

  # Final verdict
  verdict: APPROVED

  # Summary feedback
  strengths:
    - "Clean code structure"
    - "Good use of alpha for overlapping points"
  weaknesses:
    - "Grid could be more subtle"
```

**Key Points**:
- Each library has its own file (no merge conflicts!)
- Created by `impl-generate.yml`, updated by `impl-review.yml`
- Review feedback persisted for AI to improve on regeneration
- Extended review data includes `image_description`, `criteria_checklist`, and `verdict` for targeted fixes

### GCS Storage

Preview images are stored in Google Cloud Storage (not in repo):

```
gs://anyplot-images/
├── plots/{spec-id}/{library}/           # Production (after merge)
│   ├── plot.png                         # Full-size optimized image
│   └── plot.html                        # Optional (interactive libraries)
│
└── staging/{spec-id}/{library}/         # Temp (during review)
    └── plot.png, plot.html
```

**Interactive libraries** (`.html`): plotly, bokeh, altair, highcharts, pygal, letsplot

**Image Processing**: Images are optimized with pngquant. Branding is included in the plot title itself (e.g., `scatter-basic · matplotlib · anyplot.ai`).

---

### `plots/{spec-id}/implementations/`

**Purpose**: Library-specific Python implementations

**File Naming**: `{library}.py`
- `matplotlib.py`
- `seaborn.py`
- `plotly.py`
- `bokeh.py`
- `altair.py`
- `plotnine.py`
- `pygal.py`
- `highcharts.py`
- `letsplot.py`

**Code Style** (KISS):
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
ax.scatter(x, y, alpha=0.7, s=50)
ax.set_title('Basic Scatter Plot')

plt.tight_layout()
plt.savefig('plot.png', dpi=300)
```

**Header Format** (4 lines):
1. `""" anyplot.ai` - Branding
2. `{spec-id}: {Title}` - Identification
3. `Library: {lib} {version} | Python {version}` - Versions
4. `Quality: {score}/100 | Created: {date}` - Quality + date

**Rules**:
- No functions, no classes
- No `if __name__ == '__main__':`
- Just: imports → data → plot → save

---

### `prompts/`

**Purpose**: AI agent prompts for code generation and quality evaluation

**Subdirectories**:
- `library/` - Library-specific rules (9 files: matplotlib, seaborn, plotly, etc.)
- `templates/` - Templates for new specs (`specification.md`, `specification.yaml`)
- `workflow-prompts/` - Workflow-specific prompt templates

**Files**:
- `plot-generator.md` - Base rules for all implementations
- `quality-criteria.md` - Definition of quality
- `quality-evaluator.md` - AI quality evaluation
- `spec-validator.md` - Validates plot requests
- `spec-id-generator.md` - Assigns spec IDs
- `default-style-guide.md` - Default visual style rules

---

### `core/`

**Purpose**: Shared business logic and reusable components

**Key Components**:
- `database/connection.py` - Async database connection
- `database/models.py` - SQLAlchemy ORM models
- `database/repositories.py` - Repository pattern for data access

---

### `automation/`

**Purpose**: Workflow-specific automation used by GitHub Actions

**Key Components**:
- `scripts/sync_to_postgres.py` - Database sync (used by sync-postgres.yml)
- `scripts/workflow_utils.py` - Parsing and utilities for workflows
- `scripts/label_manager.py` - Label operations and transitions
- `scripts/workflow_cli.py` - CLI interface for workflow steps

**Principle**: Only contains components actively used by workflows. One-time or manual scripts belong in `scripts/`.

---

### `scripts/`

**Purpose**: One-time migrations and manually-run utilities

**Key Components**:
- `evaluate-plot.py` - Manual plot quality evaluation
- `regenerate-thumbnails.py` - Image processing utilities
- `backfill_review_metadata.py` - One-time backfill migration
- `migrate_*.py` - One-time structure migrations
- `upgrade_specs*.py` - Spec upgrade utilities

**Principle**: Scripts that are not part of automated workflows. Used for maintenance, migrations, and manual operations.

---

### `api/`

**Purpose**: FastAPI REST API

**Key Files**:
- `main.py` - FastAPI app with all endpoints

---

### `app/`

**Purpose**: React frontend (Vite + TypeScript + MUI)

---

### `.github/workflows/`

**Purpose**: CI/CD automation via GitHub Actions

**Specification Workflows**:
- `spec-create.yml` - Creates specification (branch → PR → approval → merge)

**Implementation Workflows**:
- `impl-generate.yml` - Generates single library (`generate:{lib}` label OR dispatch)
- `impl-review.yml` - AI quality evaluation
- `impl-repair.yml` - Repairs rejected implementation (max 3 attempts)
- `impl-merge.yml` - Merges approved PR, creates per-library metadata
- `bulk-generate.yml` - Batch operations (max 3 parallel)

**Supporting Workflows**:
- `sync-postgres.yml` - Syncs plots/ to database on push to main

---

## Naming Conventions

### Spec IDs

Format: `{type}-{variant}` or `{type}-{variant}-{modifier}`

**Examples**:
- `scatter-basic` - Basic scatter plot
- `scatter-color-groups` - Scatter with color-coded groups
- `bar-grouped-horizontal` - Horizontal grouped bars
- `heatmap-correlation` - Correlation matrix heatmap

**Rules**:
- All lowercase
- Hyphens as separators
- Descriptive names (no numbers needed)

### Implementation Files

Always named by library: `{library}.py`
- `matplotlib.py`, `seaborn.py`, `plotly.py`, etc.

---

## What's NOT in the Repository

### ❌ Preview Images
- **Where**: Google Cloud Storage (`gs://anyplot-images/plots/...`)
- **Why**: Binary files bloat git history

### ❌ Secrets
- **Where**: Environment variables, Cloud Secret Manager
- **Why**: Security
- **Note**: `.env.example` shows required variables without values

**Note**: Quality reports ARE stored in the repository in `metadata/python/{library}.yaml` (the `review:` section with strengths, weaknesses, criteria_checklist, verdict).

---

## Database Sync

The `sync-postgres.yml` workflow syncs `plots/` to PostgreSQL on push to main:

**What's Synced**:
- Spec content (full markdown from specification.md)
- Spec metadata (title, description, tags from specification.yaml)
- Implementation code (full Python source)
- Implementation metadata (quality score, generation info from metadata/*.yaml)
- Preview URLs from per-library metadata files
- Quality review data (strengths, weaknesses, criteria_checklist, verdict)

**Source of Truth**: The `plots/` directory is authoritative. Database is derived.

---

*For contribution guidelines, see [contributing.md](../contributing.md)*
