# 💾 Database Schema

## Overview

anyplot uses **PostgreSQL** (Cloud SQL) as the primary data store for the website. The database contains **all data needed to serve the frontend** - specs, implementations (including full code), and metadata.

**Key Principle**: Repository is source of truth, database is derived via `sync-postgres.yml`.

---

## Database Stack Decision

| Database | Status | Use Case | When to Consider |
|----------|--------|----------|------------------|
| **PostgreSQL** | ✅ **Current** | All data: specs, implementations, tags, quality scores | Start here - handles everything |
| **Google Cloud Storage** | ✅ **Current** | Preview images, user-generated plots | Already implemented |
| **GitHub** | ✅ **Current** | Code, specs, workflow state (via labels) | Already implemented |

**Current Approach**: All data in PostgreSQL + GCS + GitHub.

---

## What's Stored Where

### ✅ Stored in Database (PostgreSQL)

**Specs:**
- Full spec content (title, description, applications, data, notes)
- Tags (JSONB with plot_type, domain, features, data_type)
- Metadata (created, updated, issue, suggested)

**Implementations:**
- Full Python source code (`impls.code`)
- GCS URLs for preview images
- Quality scores and review feedback
- Generation metadata (model, workflow run, versions)

**Other:**
- Library information (name, version, docs URL)

### ✅ Stored in GCS (Google Cloud Storage)

- Preview images (PNG, thumbnails)
- Interactive HTML plots (plotly, bokeh, altair, etc.)

### ✅ Stored in GitHub

- Source of truth for all code and specs (`plots/` directory)
- Quality reports (as Issue comments)
- Workflow state (via labels on Issues/PRs)

### ❌ NOT Stored Anywhere Permanently

- User uploaded data (processed in-memory only)

---

## Database Schema

### Type Compatibility (PostgreSQL & SQLite)

The database models use **custom SQLAlchemy types** (`core/database/types.py`) that work with both PostgreSQL (production) and SQLite (tests):

| Field Type | PostgreSQL (Prod) | SQLite (Tests) | Custom Type |
|------------|-------------------|----------------|-------------|
| String arrays | `ARRAY(String)` | JSON text | `StringArray` |
| JSON fields | `JSONB` | `JSON` | `UniversalJSON` |
| UUIDs | `UUID` | `String(36)` | `UniversalUUID` |

**Benefits**:
- ✅ Production uses optimized PostgreSQL native types
- ✅ Integration tests run with SQLite in-memory (no PostgreSQL needed in CI)
- ✅ Same code/tests work in both environments

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
    generated_by    VARCHAR,                    -- Model ID: "claude-opus-4-5-20251101"
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
```

**Note**: Tags are stored as JSONB in the `specs` table (not a separate table).

---

## Table Details

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
  "generated_by": "claude-opus-4-5-20251101",
  "issue": 42,
  "workflow_run": 12345678
}
```

**Unique Constraint**: `(spec_id, library_id)` - one implementation per spec per library

---

## Data Access Patterns

### 1. Browse All Plots (with implementation count)

```sql
SELECT s.id, s.title, s.description, s.tags,
       COUNT(DISTINCT i.library_id) as library_count,
       MAX(i.quality_score) as best_quality_score
FROM specs s
LEFT JOIN impls i ON s.id = i.spec_id
GROUP BY s.id, s.title, s.description, s.tags
ORDER BY best_quality_score DESC, s.updated_at DESC;
```

### 2. Get Implementations for a Spec

```sql
SELECT i.*, l.name as library_name
FROM impls i
JOIN libraries l ON i.library_id = l.id
WHERE i.spec_id = 'scatter-basic'
ORDER BY i.quality_score DESC;
```

### 3. Search by Tags (JSONB)

```sql
SELECT s.*
FROM specs s
WHERE s.tags->'plot_type' ? 'scatter'
  AND s.tags->'domain' ? 'statistics'
ORDER BY s.updated_at DESC;
```

---

## Database Migrations

### Migration Strategy

Use **Alembic** for schema migrations:

```bash
# Create new migration
alembic revision -m "add new column"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Migration Files

```python
# migrations/versions/001_initial_schema.py
def upgrade():
    op.create_table('specs', ...)
    op.create_table('libraries', ...)
    op.create_table('impls', ...)

def downgrade():
    op.drop_table('impls')
    op.drop_table('libraries')
    op.drop_table('specs')
```

---

## Connection Management

### Connection Modes

anyplot supports two connection modes (priority order):

| Mode | Environment | Variable | Description |
|------|-------------|----------|-------------|
| Direct URL | Local development | `DATABASE_URL` | Connects via public IP |
| Cloud SQL Connector | Cloud Run | `INSTANCE_CONNECTION_NAME` | Uses IAM auth, no public IP needed |

### Local Development (Direct Connection)

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

### Connection Pooling

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

## Backup Strategy

### Automated Backups

Cloud SQL automatic backups:
- Daily backups at 3:00 AM UTC
- Retained for 7 days
- Point-in-time recovery enabled

### Manual Backups

Before major changes:
```bash
gcloud sql backups create \
  --instance=anyplot-db \
  --description="Before migration 005"
```

---

## Performance Considerations

### Indexes

Strategic indexes for common queries:
- Spec lookups by ID (primary key)
- Implementation searches by spec_id and library_id
- JSONB GIN index for tag searches

### Query Optimization

Use `EXPLAIN ANALYZE` for slow queries:
```sql
EXPLAIN ANALYZE
SELECT s.*, COUNT(i.id) as impl_count
FROM specs s
LEFT JOIN impls i ON s.id = i.spec_id
GROUP BY s.id;
```

---

## Data Lifecycle

### New Plot Flow

```
1. Spec created (via spec-create.yml)
   → INSERT INTO specs (from specification.md + specification.yaml)

2. Implementation generated (via impl-generate.yml)
   → INSERT INTO impls (code, preview URLs, quality_score)

3. Sync on merge (via sync-postgres.yml)
   → Database updated from plots/ directory
```

### Update Flow

```
1. New version of implementation
   → UPDATE impls SET preview_url=..., quality_score=..., updated_at=NOW()
   → GCS images overwritten with latest version
```

### Deletion Flow

```
1. Complete removal (rare)
   → DELETE FROM specs WHERE id=...
   → Cascade deletes impls
```

---

## Security

### Access Control

- API has full read/write access (service account)
- Frontend has read-only access via API
- No direct database access from frontend or n8n
- Secrets stored in Google Secret Manager

### SQL Injection Prevention

Use parameterized queries (SQLAlchemy ORM):
```python
# ✅ Good
await session.execute(
    select(Spec).where(Spec.id == spec_id)
)

# ❌ Bad (never do this)
await session.execute(f"SELECT * FROM specs WHERE id = '{spec_id}'")
```

### Data Privacy

- No user data stored permanently
- Anonymous session IDs only
- Usage data auto-deleted after 90 days
- GDPR-compliant (no personal data)

---

## Monitoring

### Key Metrics

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
