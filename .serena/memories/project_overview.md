# anyplot - Project Overview

## Purpose
**anyplot** is an AI-powered platform for Python data visualization that automatically discovers, generates, tests, and maintains plotting examples across 9 major libraries. Community proposes plot ideas via GitHub Issues → AI generates code → AI quality review → Deployed.

## Supported Libraries (9)
matplotlib, seaborn, plotly, bokeh, altair, plotnine, pygal, highcharts, lets-plot

## Tech Stack
- **Backend**: Python 3.14+, FastAPI, SQLAlchemy async, asyncpg, PostgreSQL
- **Frontend**: React 19, Vite 8, TypeScript 6, MUI 9, Emotion CSS-in-JS
- **Package Managers**: uv (Python), yarn (frontend)
- **Infrastructure**: Google Cloud Run, Cloud SQL, Cloud Storage (GCS)
- **AI**: Claude (code generation, quality review, spec creation)
- **CI/CD**: GitHub Actions (13 workflows, label-driven triggers)

## Directory Structure
```
anyplot/
├── api/                    # FastAPI backend
│   ├── main.py             # App factory, CORS, lifespan
│   ├── routers/            # health, specs, libraries, images, plots, stats,
│   │                       # download, proxy, seo, og_images, debug (11 routers)
│   ├── mcp/               # MCP server (server.py)
│   ├── schemas.py          # Pydantic response models
│   ├── dependencies.py     # DB session injection
│   ├── exceptions.py       # HTTP error handlers
│   ├── cache.py            # Caching layer
│   └── analytics.py        # Analytics tracking
├── core/                   # Shared business logic
│   ├── config.py           # Settings (pydantic-settings)
│   ├── constants.py        # SUPPORTED_LIBRARIES, quality thresholds
│   ├── images.py           # GCS image handling
│   ├── utils.py            # Shared utilities
│   ├── database/
│   │   ├── connection.py   # Async SQLAlchemy engine
│   │   ├── models.py       # ORM models (Spec, Implementation, Tag)
│   │   ├── repositories.py # Data access layer
│   │   └── types.py        # Custom types (PostgreSQL + SQLite compat)
│   └── generators/
│       └── plot_generator.py  # Plot code generation logic
├── app/                    # React frontend
│   └── src/
│       ├── components/     # 16 components (Breadcrumb, ErrorBoundary, FilterBar,
│       │                   # Footer, Header, ImageCard, ImagesGrid, Layout,
│       │                   # LibraryPills, LoaderSpinner, SpecDetailView,
│       │                   # SpecOverview, SpecTabs, ToolbarActions)
│       ├── pages/          # 7 pages (CatalogPage, DebugPage, HomePage,
│       │                   # InteractivePage, LegalPage, McpPage, SpecPage)
│       ├── hooks/          # 10 hooks (useAnalytics, useCodeFetch, useCopyCode,
│       │                   # useFilterFetch, useFilterState, useInfiniteScroll,
│       │                   # useLayoutContext, useLocalStorage, useUrlSync)
│       ├── types/          # TypeScript interfaces
│       ├── utils/          # api.ts (fetch-based API client), filters.ts, fuzzySearch.ts
│       └── theme/          # MUI theme config
├── agentic/                # AI workflow layer
│   ├── workflows/          # Composable phase scripts (Click CLI, uv inline headers)
│   │   ├── plan.py, build.py, test.py, review.py  # Individual phases
│   │   ├── document.py, patch.py, prompt.py, ship.py  # Additional phases
│   │   ├── plan_build.py, plan_build_test.py       # Orchestrators
│   │   ├── plan_build_test_review.py               # Full review pipeline
│   │   ├── plan_build_test_review_document.py      # + documentation
│   │   ├── plan_build_test_review_document_ship.py # + shipping
│   │   └── modules/        # agent.py (execution, types), state.py (persistence),
│   │                        # orchestrator.py, template.py
│   ├── commands/           # 17 .md prompt templates ($1, $2, $ARGUMENTS vars)
│   │                       # agentic, audit, bug, chore, classify, commit, context,
│   │                       # dokument, feature, implement, prime, pull_request,
│   │                       # refactor, review, start, test, update
│   ├── specs/              # Task specification files
│   ├── context/            # Context documentation for specific changes
│   ├── docs/               # project-guide.md
│   └── runs/               # Runtime state (gitignored)
├── automation/             # CI/CD helper scripts
│   └── scripts/            # workflow_cli.py, label_manager.py, sync_to_postgres.py, workflow_utils.py
├── plots/                  # ~259 specifications (plot-centric design)
│   └── {spec-id}/
│       ├── specification.md      # Library-agnostic description
│       ├── specification.yaml    # Tags, metadata
│       ├── implementations/      # {library}.py files
│       └── metadata/             # {library}.yaml files
├── prompts/                # AI prompt files
│   ├── plot-generator.md, quality-*.md, spec-*.md, impl-tags-generator.md
│   ├── default-style-guide.md    # Default visual style rules
│   ├── library/                  # 9 library-specific rule files
│   ├── templates/                # spec/metadata YAML/MD templates
│   └── workflow-prompts/         # ai-quality-review.md, impl-generate-claude.md,
│                                 # impl-repair-claude.md, report-analysis.md
├── tests/                  # pytest suite
│   ├── conftest.py         # Shared fixtures
│   ├── unit/
│   │   ├── api/            # test_routers, test_cache, test_analytics, test_proxy, mcp/
│   │   ├── core/           # test_config, test_constants, test_images, test_types, test_utils
│   │   ├── agentic/        # test_state, test_template, test_agent_*, test_orchestrator*
│   │   ├── automation/     # test_label_manager, test_sync_to_postgres, test_workflow_*
│   │   ├── workflows/      # test_workflows
│   │   └── prompts/        # test_prompts
│   ├── integration/        # test_repositories, api/test_api_endpoints
│   └── e2e/                # test_api_postgres (requires DATABASE_URL)
├── docs/                   # contributing, development, reference/, workflows/, concepts/
├── alembic/                # DB migrations (async engine)
├── .github/workflows/      # 13 GitHub Actions workflows
└── docker-compose.yml      # API + PostgreSQL + frontend
```

## GitHub Actions Workflows (13)
| Workflow | Purpose |
|----------|---------|
| `spec-create.yml` | Creates specs from issues labeled `spec-request` |
| `impl-generate.yml` | Generates implementation for one spec+library |
| `impl-review.yml` | AI quality review of implementations |
| `impl-repair.yml` | Fixes rejected implementations (max 3 attempts) |
| `impl-merge.yml` | Merges approved PRs, creates metadata, promotes GCS |
| `bulk-generate.yml` | Batch generation for multiple specs/libraries |
| `report-validate.yml` | Validates user-submitted issue reports |
| `sync-postgres.yml` | Syncs filesystem specs/impls to PostgreSQL |
| `sync-labels.yml` | Auto-syncs labels after manual PR merges |
| `ci-lint.yml` | Ruff linting on PRs |
| `ci-tests.yml` | Unit tests on PRs |
| `notify-deployment.yml` | Deployment notifications |
| `util-claude.yml` | Claude utility workflow |

## Data Flow
1. GitHub Issue + `spec-request` → `spec-create.yml` generates spec PR
2. `approved` label on Issue → spec merges, gets `spec-ready` label
3. `bulk-generate.yml` → `impl-generate.yml` → `impl-review.yml` → `impl-merge.yml`
4. `sync-postgres.yml` syncs filesystem to PostgreSQL on push to main
5. FastAPI serves data, React frontend displays gallery at anyplot.ai
