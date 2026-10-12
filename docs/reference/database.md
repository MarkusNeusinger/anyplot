# Database schema

## Overview

anyplot uses **PostgreSQL** (Cloud SQL) as the primary data store for the website. The database contains **all data needed to serve the frontend** - specs, implementations (including full code), and metadata.

**Key Principle**: Repository is source of truth, database is derived via `sync-postgres.yml`. The exceptions are the two feedback tables, `feedback` and `agent_feedback`: their rows are written by the API and are the source of truth themselves.

---

## Database stack decision

| Database | Status | Use Case | When to Consider |
|----------|--------|----------|------------------|
| **PostgreSQL** | ✅ **Current** | All data: specs, implementations, tags, quality scores | Start here - handles everything |
| **Google Cloud Storage** | ✅ **Current** | Preview images, user-generated plots | Already implemented |
| **GitHub** | ✅ **Current** | Code, specs, workflow state (via labels) | Already implemented |

**Current Approach**: All data in PostgreSQL + GCS + GitHub.

---

## What's stored where

### Stored in the database (PostgreSQL)

**Specs:**
- Full spec content (title, description, applications, data, notes)
- Tags (JSONB with plot_type, domain, features, data_type)
- Metadata (created, updated, issue, suggested)

**Implementations:**
- Full Python source code (`impls.code`)
- GCS URLs for preview images
- Quality scores and review feedback
- Generation metadata (model, workflow run, versions)

**Feedback:**
- Site feedback from the feedback widget and the plot votes (`feedback`), with its triage status
- One row per quick-feedback case of the admin-only agent chat (`agent_feedback`): the reaction, the message, hashed user and session ids, the run's metadata, and the triage state (status, tags, expected outcome, promotion, supersession); never the conversation, code, images or data

**Other:**
- Library information (name, version, docs URL)

### Stored in GCS (Google Cloud Storage)

- Preview images (PNG, thumbnails)
- Interactive HTML plots (plotly, bokeh, altair, etc.)
- The files of each agent chat feedback case, in the private EU bucket `gs://anyplot-agent-cases` under `cases/<case_id>/` (the PNGs, `plot.py`, `data.csv` only when the admin ticked the box, and `manifest.json`); a lifecycle rule deletes them after 180 days

### Stored in GitHub

- Source of truth for all code and specs (`plots/` directory)
- Quality reports (as Issue comments)
- Workflow state (via labels on Issues/PRs)

### Not stored anywhere permanently

- User uploaded data (processed in-memory only). The one exception is a quick-feedback case of the agent chat: when an admin submits one with the data box ticked, the case's `data.csv` stays in `gs://anyplot-agent-cases` until the lifecycle rule deletes it after 180 days

---

## Database schema

### Type compatibility (PostgreSQL & SQLite)

The database models use **custom SQLAlchemy types** (`core/database/types.py`) that work with both PostgreSQL (production) and SQLite (tests):

| Field Type | PostgreSQL (Prod) | SQLite (Tests) | Custom Type |
|------------|-------------------|----------------|-------------|
| String arrays | `ARRAY(String)` | JSON text | `StringArray` |
| JSON fields | `JSONB` | `JSON` | `UniversalJSON` |
| UUIDs | `UUID` | `String(36)` | `UniversalUUID` |

**Benefits**:
- Production uses optimized PostgreSQL native types
- Integration tests run with SQLite in-memory; PostgreSQL in CI is limited to the E2E tests (the Cloud SQL `test` database) and the migration check's throwaway container (see [Database migrations](#database-migrations))
- Same code/tests work in both environments

When a query branches on the dialect, the SQLite suite runs only the SQLite arm. Compile the PostgreSQL arm in a unit test and assert its operator and bind values; `tests/unit/core/database/test_repositories.py` does this for the spec tag filter and the agent case tag filter.

**See**: `core/database/types.py` for implementation details.

---

### Tables

```sql
-- Plot specifications (library-agnostic)
CREATE TABLE specs
(
    id          VARCHAR PRIMARY KEY,      -- "scatter-basic"
    title       VARCHAR NOT NULL,         -- "Basic Scatter Plot"
    description TEXT,                     -- From specification.md
    applications VARCHAR[],               -- Use cases
    data        VARCHAR[],                -- Data requirements
    notes       VARCHAR[],                -- Optional hints
    created     TIMESTAMP,                -- When spec was created
    issue       INTEGER,                  -- GitHub issue number
    suggested   VARCHAR,                  -- GitHub username who suggested
    tags        JSONB,                    -- {plot_type, domain, features, audience, data_type}
    history     JSONB,                    -- Spec update history
    updated_at  TIMESTAMP DEFAULT NOW()
);

-- Supported plotting libraries
CREATE TABLE libraries
(
    id                VARCHAR PRIMARY KEY,      -- "matplotlib", "seaborn", "plotly"
    name              VARCHAR NOT NULL,         -- "Matplotlib"
    version           VARCHAR,                  -- "3.9.0"
    documentation_url VARCHAR,                  -- "https://matplotlib.org"
    description       TEXT                      -- Short library description
);

-- Library-specific implementations
CREATE TABLE impls
(
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    spec_id         VARCHAR NOT NULL REFERENCES specs (id) ON DELETE CASCADE,
    library_id      VARCHAR NOT NULL REFERENCES libraries (id) ON DELETE CASCADE,

    -- Code
    code            TEXT,                       -- Python source code

    -- Preview URLs (GCS)
    preview_url     VARCHAR,                    -- Full PNG: gs://anyplot-images/plots/.../plot.png
    preview_html    VARCHAR,                    -- Interactive: gs://anyplot-images/plots/.../plot.html

    -- Version info
    python_version  VARCHAR,                    -- e.g., "3.13"
    library_version VARCHAR,                    -- e.g., "3.9.0"

    -- Test results: [{"py": "3.11", "lib": "3.8.5", "ok": true}, ...]
    tested          JSONB,

    -- Quality & Generation
    quality_score   FLOAT,                      -- 0-100
    generated_at    TIMESTAMP,
    updated         TIMESTAMP,                  -- Last update
    generated_by    VARCHAR,                    -- Model ID: "claude-opus-4-7"
    issue           INTEGER,                    -- GitHub Issue number
    workflow_run    BIGINT,                     -- GitHub Actions run ID

    -- Review feedback (for regeneration)
    review_strengths  VARCHAR[],                -- What's good about this implementation
    review_weaknesses VARCHAR[],                -- What needs improvement

    -- Extended review data (issue #2845)
    review_image_description TEXT,              -- AI's visual description of the plot
    review_criteria_checklist JSONB,            -- Detailed scoring breakdown
    review_verdict  VARCHAR(20),                -- "APPROVED" or "REJECTED"

    updated_at      TIMESTAMP DEFAULT NOW(),

    UNIQUE (spec_id, library_id)
);

-- Indexes for performance
CREATE INDEX idx_impls_spec ON impls (spec_id);
CREATE INDEX idx_impls_library ON impls (library_id);

-- Site feedback: the floating widget and the plot votes (written by the API)
CREATE TABLE feedback
(
    id          UUID PRIMARY KEY,
    message     VARCHAR(500),
    reaction    VARCHAR(20),                -- thumbs_up, thumbs_down, bug, idea
    contact     VARCHAR(255),
    path        VARCHAR(500),
    spec_id     VARCHAR(100),
    library_id  VARCHAR(50),                -- set only by a plot vote
    language    VARCHAR(50),                -- the programming language of a plot vote
    user_agent  VARCHAR(500),
    viewport    VARCHAR(20),
    session_id  VARCHAR(64),
    ip_hash     VARCHAR(64),                -- SHA-256 of the client IP, for the rate limit
    status      VARCHAR(20) NOT NULL,       -- new, in_progress, done, wont_solve
    created_at  TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_feedback_reaction_valid
        CHECK (reaction IS NULL OR reaction IN ('thumbs_up','thumbs_down','bug','idea')),
    CONSTRAINT ck_feedback_status_valid
        CHECK (status IN ('new','in_progress','done','wont_solve'))
);

CREATE INDEX ix_feedback_created_at ON feedback (created_at DESC);
CREATE INDEX ix_feedback_ip_hash_created_at ON feedback (ip_hash, created_at DESC);
CREATE INDEX ix_feedback_spec_library ON feedback (spec_id, library_id);

-- Quick-feedback cases of the admin-only agent chat (written by the API)
CREATE TABLE agent_feedback
(
    id              VARCHAR(25) PRIMARY KEY,    -- the case id: "20261012T143005Z-1a2b3c4d"
    manifest_schema INTEGER NOT NULL,           -- the manifest's schema (1)
    created_at      TIMESTAMP NOT NULL,         -- UTC, from the manifest
    case_uri        VARCHAR(255) NOT NULL,      -- gs://anyplot-agent-cases/cases/<id>/
    user_hash       VARCHAR(20) NOT NULL,       -- the HMAC user id the agents service sees
    session_hash    VARCHAR(16) NOT NULL,       -- first 16 hex digits of the session id's SHA-256
    spec_id         VARCHAR(100),
    library_id      VARCHAR(50),
    locale          VARCHAR(16),                -- the session's UI locale ("de-CH")
    reaction        VARCHAR(20) NOT NULL,       -- thumbs_up, thumbs_down, bug, idea
    message         VARCHAR(500),
    include_data    BOOLEAN NOT NULL,           -- the case holds data.csv
    status          VARCHAR(20) NOT NULL,       -- new, in_progress, done, wont_solve
    result_version  INTEGER NOT NULL,           -- the rated version, 1 to 999; 0 is the chat itself
    replaces        VARCHAR(25),                -- the case id an edit names
    model           VARCHAR(100),
    model_version   VARCHAR(100),
    judge_model     VARCHAR(100),
    prompt_hash     VARCHAR(16),                -- one hash over the prompt hashes
    pipeline_status VARCHAR(20),                -- ok, needs_attention, failed, ...
    attempts        INTEGER,
    tokens          INTEGER,
    cost_estimate   FLOAT,
    files           VARCHAR[] NOT NULL,         -- the case's file names

    -- Triage state, never in a manifest
    tags            VARCHAR[] NOT NULL,         -- lowercase slugs, at most 10
    expected        VARCHAR(10),                -- accepted, rejected
    promoted_at     TIMESTAMP,
    superseded_by   VARCHAR(25),                -- the case id that replaced this one
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_agent_feedback_reaction_valid
        CHECK (reaction IN ('thumbs_up','thumbs_down','bug','idea')),
    CONSTRAINT ck_agent_feedback_status_valid
        CHECK (status IN ('new','in_progress','done','wont_solve')),
    CONSTRAINT ck_agent_feedback_expected_valid
        CHECK (expected IS NULL OR expected IN ('accepted','rejected'))
);

CREATE INDEX ix_agent_feedback_session_version ON agent_feedback (session_hash, result_version);
CREATE INDEX ix_agent_feedback_spec_library ON agent_feedback (spec_id, library_id);
CREATE INDEX ix_agent_feedback_tags ON agent_feedback USING GIN (tags);
```

**Note**: Tags are stored as JSONB in the `specs` table (not a separate table).

---

## Table details

### `specs`

**Purpose**: Store library-agnostic plot specifications

**Key Fields**:
- `id` - Spec identifier (e.g., "scatter-basic")
- `title` - Display title
- `description` - Full description from specification.md
- `applications` - Use cases array
- `data` - Data requirements array
- `tags` - JSONB with structured tags (plot_type, domain, features, audience, data_type)

**Example Row**:
```json
{
  "id": "scatter-basic",
  "title": "Basic Scatter Plot",
  "description": "A fundamental scatter plot showing relationship between two variables...",
  "applications": ["Show correlation", "Compare distributions"],
  "data": ["x: numeric values", "y: numeric values"],
  "notes": ["Use alpha for overlapping points"],
  "created": "2025-01-10T08:00:00Z",
  "issue": 42,
  "suggested": "CoolContributor",
  "tags": {
    "plot_type": ["scatter", "point"],
    "domain": ["statistics"],
    "features": ["basic", "2d"]
  }
}
```

---

### `libraries`

**Purpose**: Track supported plotting libraries

**Example Rows**:
```sql
INSERT INTO libraries (id, name, version, documentation_url) VALUES
('matplotlib', 'Matplotlib', '3.9.0', 'https://matplotlib.org'),
('seaborn', 'Seaborn', '0.13.0', 'https://seaborn.pydata.org'),
('plotly', 'Plotly', '5.18.0', 'https://plotly.com/python'),
('altair', 'Altair', '5.2.0', 'https://altair-viz.github.io');
```

---

### `impls`

**Purpose**: Track library-specific implementations of specs

**Key Fields**:
- `spec_id` - References spec
- `library_id` - Which library
- `code` - Full Python source code
- `preview_url` - GCS URL to full-size image
- `preview_html` - GCS URL to interactive HTML (optional)
- `quality_score` - AI quality score (0-100)
- `python_version` - Python version used for generation
- `library_version` - Library version used

**Example Row**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "spec_id": "scatter-basic",
  "library_id": "matplotlib",
  "code": "import matplotlib.pyplot as plt\n...",
  "preview_url": "https://storage.googleapis.com/anyplot-images/plots/scatter-basic/matplotlib/plot.png",
  "preview_html": null,
  "python_version": "3.13",
  "library_version": "3.9.0",
  "quality_score": 92.0,
  "generated_at": "2025-01-15T10:30:00Z",
  "generated_by": "claude-opus-4-7",
  "issue": 42,
  "workflow_run": 12345678
}
```

**Unique Constraint**: `(spec_id, library_id)` - one implementation per spec per library

---

### `agent_feedback`

**Purpose**: Index the quick-feedback cases of the admin-only agent chat and hold their triage state. The feedback route `POST /debug/agent/sessions/{sid}/feedback` inserts one row per case right after the case's files are in `gs://anyplot-agent-cases`, and the "agent cases" section of `/debug` reads and updates it through the case routes ([Feedback triage](api.md#feedback-triage)). The row is the source of truth for the triage; the bucket holds the files until its lifecycle rule deletes them after 180 days, and the row stays, so the class statistics outlive the files. Created by migration `b4e7a9c2d6f1`.

**Key Fields**:
- `id` - The bucket's case id: the UTC time in ISO 8601 basic format and eight random hex digits, so ids sort by time and link a row to its files under `cases/<id>/`
- `reaction`, `message`, `include_data`, `result_version`, `replaces` - What the admin sent; `include_data` says whether the case holds `data.csv`. `result_version` 0 (since 2026-10-12) is feedback on the chat itself, from a session that made no plot: such a case has no image and no `plot.py`, no pipeline status, and cannot be promoted
- `user_hash`, `session_hash` - Hashed ids; the table holds no email address and no session id
- `locale` - The session's UI locale, the manifest's `language`; unlike `feedback.language`, which holds a programming language
- `model`, `model_version`, `judge_model`, `prompt_hash`, `pipeline_status`, `attempts`, `tokens`, `cost_estimate` - The run's metadata from the case manifest; `model_version`, `tokens` and `cost_estimate` are `null` until the agents service stamps them
- `status` - The triage state, the same four values as `feedback.status`; `done` and `wont_solve` retire a case
- `tags` - Failure classes, lowercase slugs that match `^[a-z0-9-]{1,40}$`, at most 10
- `promoted_at`, `expected` - When the case was promoted to the regression harness, and the outcome the harness expects (`accepted` or `rejected`); `agents/evals/sync_cases.py` reads both
- `superseded_by` - The case that replaced this one: an edit whose `replaces` names this case with the same `session_hash` and `result_version`. Superseded rows are hidden in the triage list by default and never deleted

Every column but the triage state copies the field of the same name in the case's `manifest.json` (`core.agent_cases.row_from_manifest`); the conversation, the code, the images and the data stay in the bucket.

**Example Row**:
```json
{
  "id": "20261012T143005Z-1a2b3c4d",
  "manifest_schema": 1,
  "created_at": "2026-10-12T14:30:05",
  "case_uri": "gs://anyplot-agent-cases/cases/20261012T143005Z-1a2b3c4d/",
  "user_hash": "adm_0123456789abcdef",
  "session_hash": "9f8e7d6c5b4a3f2e",
  "spec_id": "scatter-basic",
  "library_id": "matplotlib",
  "locale": "de-CH",
  "reaction": "thumbs_down",
  "message": "The legend covers the largest points.",
  "include_data": true,
  "status": "new",
  "result_version": 2,
  "replaces": null,
  "model": "claude-haiku-5-5",
  "model_version": null,
  "judge_model": "claude-haiku-5-5",
  "prompt_hash": "3c1f9a0b7d2e4f68",
  "pipeline_status": "ok",
  "attempts": 1,
  "tokens": null,
  "cost_estimate": null,
  "files": ["plot-light.png", "plot.py", "data.csv", "manifest.json"],
  "tags": [],
  "expected": null,
  "promoted_at": null,
  "superseded_by": null,
  "updated_at": "2026-10-12T14:30:06"
}
```

---

## Data access patterns

### 1. Browse all plots (with implementation count)

```sql
SELECT s.id, s.title, s.description, s.tags,
       COUNT(DISTINCT i.library_id) as library_count,
       MAX(i.quality_score) as best_quality_score
FROM specs s
LEFT JOIN impls i ON s.id = i.spec_id
GROUP BY s.id, s.title, s.description, s.tags
ORDER BY best_quality_score DESC, s.updated_at DESC;
```

### 2. Get implementations for a spec

```sql
SELECT i.*, l.name as library_name
FROM impls i
JOIN libraries l ON i.library_id = l.id
WHERE i.spec_id = 'scatter-basic'
ORDER BY i.quality_score DESC;
```

### 3. Search by tags (JSONB)

```sql
SELECT s.*
FROM specs s
WHERE s.tags->'plot_type' ? 'scatter'
  AND s.tags->'domain' ? 'statistics'
ORDER BY s.updated_at DESC;
```

---

## Database migrations

### Migration strategy

Use **Alembic** for schema migrations:

```bash
# Create new migration
uv run alembic revision -m "add new column"

# Apply migrations
uv run alembic upgrade head

# Rollback
uv run alembic downgrade -1
```

Never run these against the shared production database by hand: production
schema changes reach Cloud SQL only through `sync-postgres.yml` after the merge
(see [How a migration reaches production](#how-a-migration-reaches-production)).

### Migration files

Revisions live in `alembic/versions/<revision>_<slug>.py`, for example:

```python
# alembic/versions/b4e7a9c2d6f1_add_agent_feedback_table.py
revision = "b4e7a9c2d6f1"
down_revision = "a7c3e9d1f5b8"

def upgrade() -> None:
    op.create_table("agent_feedback", ...)
    op.create_index("ix_agent_feedback_tags", "agent_feedback", ["tags"], postgresql_using="gin")

def downgrade() -> None:
    op.drop_index("ix_agent_feedback_tags", table_name="agent_feedback")
    op.drop_table("agent_feedback")
```

Declare every index and CHECK constraint that a migration creates in
`core/database/models.py` as well. `alembic check` compares the indexes and
proposes to drop an undeclared one; the CHECK constraints are compared by the
CI job below, because `alembic check` does not see them.

### How a migration reaches production

1. **Before the merge**, the workflow `ci-migrations.yml` (check
   `Verify Migrations`) runs on every PR that touches `alembic/`,
   `alembic.ini`, `core/database/`, `pyproject.toml` or `uv.lock`. On a
   throwaway PostgreSQL 18 service container, the major version production
   runs, it checks that the revision graph has exactly one head, runs
   `alembic upgrade head` and `alembic check`, compares the CHECK constraints
   of the migrated schema with the models' by name and quoted values, and
   downgrades to the base commit's head and upgrades again, so every revision
   the PR adds is reversed. The job tests the PR at its last push: when two
   migration PRs fork from the same head and merge one after the other, the
   second head shows up only after the merge, in the push run on `main` and in
   `sync-postgres.yml`, because ruleset `main` does not require branches to be
   up to date. For the local loop before you push, see
   [Migrations](../development.md#migrations).
2. **After the merge**, `sync-postgres.yml` runs on every push to `main` that
   touches `plots/**` or `alembic/versions/**`. Its step "Run database
   migrations" runs `alembic upgrade head` against Cloud SQL before the step
   that syncs the plots. Nothing orders it before the API deploy, which runs in
   parallel: code that needs the new schema meets the old one for the minutes
   in between.

### Revert a migration PR

Every later `sync-postgres.yml` run, plots pushes included, starts with
`alembic upgrade head`. If production's `alembic_version` names a revision
whose file is gone, that step fails with
`Can't locate revision identified by '<revision>'`, and the plots stop syncing
until someone downgrades production by hand. So never revert a migration PR
whole:

- Keep the revision file in the revert. The revision stays resolvable, and an
  unused table or column is harmless.
- Or downgrade production first, then revert. No workflow runs a downgrade,
  so this is a one-off `alembic downgrade <previous revision>` against Cloud
  SQL, after a backup (see [Manual backups](#manual-backups)); it drops what the
  revision created, rows included.

---

## Connection management

### Connection modes

anyplot supports two connection modes (priority order):

| Mode | Environment | Variable | Description |
|------|-------------|----------|-------------|
| Direct URL | Local development | `DATABASE_URL` | Connects via public IP |
| Cloud SQL Connector | Cloud Run | `INSTANCE_CONNECTION_NAME` | Uses IAM auth, no public IP needed |

### Local development (direct connection)

```bash
# .env
DATABASE_URL=postgresql+asyncpg://user:pass@34.x.x.x:5432/anyplot
```

Requires IP to be authorized in Cloud SQL Authorized Networks.

### Cloud Run (Cloud SQL Connector)

```bash
# Set via Secret Manager / cloudbuild.yaml
INSTANCE_CONNECTION_NAME=project:region:instance
DB_USER=anyplot
DB_PASS=xxx
DB_NAME=anyplot
```

Uses `cloud-sql-python-connector[asyncpg]` for secure connection without exposing public IP.

### Connection pooling

```python
# core/database/connection.py
engine = create_async_engine(
    "postgresql+asyncpg://",
    async_creator=get_conn,  # Cloud SQL Connector
    pool_size=5,             # Connections in pool
    max_overflow=10,         # Additional connections if needed
    pool_pre_ping=True       # Verify connection before use
)
```

---

## Backup strategy

### Automated backups

Cloud SQL automatic backups:
- Daily backups at 3:00 AM UTC
- Retained for 7 days
- Point-in-time recovery enabled

### Manual backups

Before major changes:
```bash
gcloud sql backups create \
  --instance=anyplot-db \
  --description="Before migration 005"
```

---

## Performance considerations

### Indexes

Strategic indexes for common queries:
- Spec lookups by ID (primary key)
- Implementation searches by spec_id and library_id
- JSONB GIN index for tag searches

### Query optimization

Use `EXPLAIN ANALYZE` for slow queries:
```sql
EXPLAIN ANALYZE
SELECT s.*, COUNT(i.id) as impl_count
FROM specs s
LEFT JOIN impls i ON s.id = i.spec_id
GROUP BY s.id;
```

---

## Data lifecycle

### New plot flow

```
1. Spec created (via spec-create.yml)
   → INSERT INTO specs (from specification.md + specification.yaml)

2. Implementation generated (via impl-generate.yml)
   → INSERT INTO impls (code, preview URLs, quality_score)

3. Sync on merge (via sync-postgres.yml)
   → Database updated from plots/ directory
```

### Update flow

```
1. New version of implementation
   → UPDATE impls SET preview_url=..., quality_score=..., updated_at=NOW()
   → GCS images overwritten with latest version
```

### Deletion flow

```
1. Complete removal (rare)
   → DELETE FROM specs WHERE id=...
   → Cascade deletes impls
```

---

## Security

### Access control

- API has full read/write access (service account)
- Frontend has read-only access via API
- No direct database access from frontend or n8n
- Secrets stored in Google Secret Manager

### SQL injection prevention

Use parameterized queries (SQLAlchemy ORM):
```python
# ✅ Good
await session.execute(
    select(Spec).where(Spec.id == spec_id)
)

# ❌ Bad (never do this)
await session.execute(f"SELECT * FROM specs WHERE id = '{spec_id}'")
```

### Data privacy

- No user data stored permanently, with one exception: the quick-feedback cases of the admin-only agent chat. When an admin submits one, the case (the conversation, the code, the images, the message, a hashed user id, and `data.csv` when the box is ticked) is stored in the private bucket `gs://anyplot-agent-cases` until the lifecycle rule deletes it after 180 days. Its row in `agent_feedback` holds the message and the hashed ids, but no conversation, code, images or data, and stays
- Anonymous session IDs only
- Usage data auto-deleted after 90 days
- GDPR-compliant (no personal data)

---

## Monitoring

### Key metrics

Track in Cloud SQL:
- Query performance (slow query log)
- Connection pool usage
- Storage usage
- Backup success/failure

### Alerting

Set up alerts for:
- Storage > 80% full
- Connection pool exhausted
- Failed backups
- Slow queries > 1 second

---

*For API endpoints using this database, see [api.md](./api.md)*
