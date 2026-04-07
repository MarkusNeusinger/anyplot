# 🔌 API Reference

## Overview

The pyplots API is a **FastAPI-based REST API** serving plot data to the frontend.

**Base URL**: `https://api.pyplots.ai`

**Key Principle**: Database is derived from repository via `sync-postgres.yml`. API reads from PostgreSQL.

---

## Core Endpoints

### Specs

#### GET `/specs`

**Purpose**: List all specs with at least one implementation

**Response**:
```json
[
  {
    "id": "scatter-basic",
    "title": "Basic Scatter Plot",
    "description": "A fundamental scatter plot showing...",
    "tags": {
      "plot_type": ["scatter"],
      "domain": ["statistics"],
      "features": ["basic", "2d"],
      "data_type": ["numeric"]
    },
    "library_count": 9
  }
]
```

---

#### GET `/specs/{spec_id}`

**Purpose**: Get detailed spec with all implementations

**Response**:
```json
{
  "id": "scatter-basic",
  "title": "Basic Scatter Plot",
  "description": "A fundamental scatter plot...",
  "applications": ["Show correlation", "Compare distributions"],
  "data": ["x: numeric values", "y: numeric values"],
  "notes": ["Use alpha for overlapping points"],
  "tags": {
    "plot_type": ["scatter"],
    "domain": ["statistics"],
    "features": ["basic"],
    "data_type": ["numeric"]
  },
  "issue": 42,
  "suggested": "CoolContributor",
  "created": "2025-01-10T08:00:00Z",
  "updated": "2025-01-15T10:30:00Z",
  "implementations": [
    {
      "library_id": "matplotlib",
      "library_name": "Matplotlib",
      "preview_url": "https://storage.googleapis.com/pyplots-images/plots/scatter-basic/matplotlib/plot.png",
      "preview_html": null,
      "quality_score": 92.0,
      "code": "import matplotlib.pyplot as plt...",
      "generated_at": "2025-01-15T10:30:00Z",
      "generated_by": "claude-opus-4-5-20251101",
      "python_version": "3.13",
      "library_version": "3.10.0",
      "review_strengths": ["Clean code structure"],
      "review_weaknesses": ["Grid could be more subtle"],
      "review_image_description": "The plot shows...",
      "review_criteria_checklist": {...},
      "review_verdict": "APPROVED"
    }
  ]
}
```

---

#### GET `/specs/{spec_id}/images`

**Purpose**: Get preview images for a spec across all libraries

**Response**:
```json
{
  "spec_id": "scatter-basic",
  "images": [
    {
      "library": "matplotlib",
      "url": "https://storage.googleapis.com/.../plot.png",
      "html": null
    }
  ]
}
```

---

### Libraries

#### GET `/libraries`

**Purpose**: List supported plotting libraries

**Response**:
```json
{
  "libraries": [
    {
      "id": "matplotlib",
      "name": "Matplotlib",
      "version": "3.10.0",
      "documentation_url": "https://matplotlib.org",
      "description": "The classic standard..."
    }
  ]
}
```

---

#### GET `/libraries/{library_id}/images`

**Purpose**: Get all plot images for a library across all specs

**Response**:
```json
{
  "library": "matplotlib",
  "images": [
    {
      "spec_id": "scatter-basic",
      "library": "matplotlib",
      "url": "https://storage.googleapis.com/.../plot.png",
      "html": null,
      "code": "import matplotlib.pyplot as plt..."
    }
  ]
}
```

---

### Plots Filter

#### GET `/plots/filter`

**Purpose**: Filter plots with faceted counts for all filter categories

**Query Parameters** (combinable):

*Spec-level filters (WHAT is visualized):*
- `lib` - Library filter (matplotlib, seaborn, etc.)
- `spec` - Spec ID filter
- `plot` - Plot type tag filter
- `data` - Data type tag filter
- `dom` - Domain tag filter
- `feat` - Features tag filter

*Impl-level filters (HOW it is implemented):*
- `dep` - Dependencies filter (scipy, sklearn, etc.)
- `tech` - Techniques filter (twin-axes, annotations, etc.)
- `pat` - Patterns filter (data-generation, groupby-aggregation, etc.)
- `prep` - Dataprep filter (kde, binning, regression, etc.)
- `style` - Styling filter (minimal-chrome, alpha-blending, etc.)

**Filter Logic**:
- Comma-separated values: OR (`lib=matplotlib,seaborn`)
- Multiple params same name: AND (`lib=matplotlib&lib=seaborn`)
- Different categories: AND (`lib=matplotlib&plot=scatter`)

**Response**:
```json
{
  "total": 42,
  "images": [
    {
      "spec_id": "scatter-basic",
      "library": "matplotlib",
      "quality": 92,
      "url": "https://storage.googleapis.com/.../plot.png",
      "html": null
    }
  ],
  "counts": {
    "lib": {"matplotlib": 5, "seaborn": 3},
    "spec": {"scatter-basic": 2},
    "plot": {"scatter": 10},
    "data": {"numeric": 15},
    "dom": {"statistics": 8},
    "feat": {"basic": 12},
    "dep": {"scipy": 3},
    "tech": {"annotations": 5},
    "pat": {"data-generation": 8},
    "prep": {"kde": 2},
    "style": {"alpha-blending": 4}
  },
  "globalCounts": {...},
  "orCounts": [...]
}
```

---

### Stats

#### GET `/stats`

**Purpose**: Platform statistics

**Response**:
```json
{
  "specs": 42,
  "plots": 378,
  "libraries": 9
}
```

---

### Download

#### GET `/download/{spec_id}/{library}`

**Purpose**: Download plot image (proxy to avoid CORS)

**Response**: PNG image file with `Content-Disposition: attachment`

---

### Health

#### GET `/`

**Purpose**: Root endpoint

**Response**:
```json
{
  "message": "Welcome to pyplots API",
  "version": "0.2.0",
  "docs": "/docs",
  "health": "/health"
}
```

---

#### GET `/health`

**Purpose**: Health check for Cloud Run

**Response**:
```json
{
  "status": "healthy",
  "service": "pyplots-api",
  "version": "0.2.0"
}
```

---

## Insights Endpoints

### GET `/insights/dashboard`

**Purpose**: Rich platform statistics for the public stats page

Returns aggregated data: per-library quality and LOC distributions, coverage matrix, top implementations, tag distribution, implementation timeline.

Cached with stale-while-revalidate (1h refresh, 24h TTL).

### GET `/insights/plot-of-the-day`

**Purpose**: Daily featured high-quality implementation

Deterministically selects an implementation with quality_score >= 90 based on today's date. Returns spec info, preview URL, AI image description, and code.

### GET `/insights/related/{spec_id}`

**Purpose**: Tag-based similarity recommendations

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 6 | Number of results (1-12) |
| `mode` | string | `spec` | `spec` = spec tags only, `full` = spec + impl tags |
| `library` | string | null | In `full` mode, match against this library's impl_tags |

Returns related specs sorted by Jaccard similarity with preview thumbnails and shared tags.

### GET `/specs/{spec_id}/{library}/code`

**Purpose**: Lightweight endpoint for implementation code

Returns only the code field for a single implementation. Used by the frontend to lazy-load code on demand (code is deferred in the main `/specs/{spec_id}` response).

---

## SEO Endpoints

### GET `/sitemap.xml`

**Purpose**: Dynamic XML sitemap for search engines

Includes: root, catalog, all specs with implementations, all implementation pages.

---

### GET `/seo-proxy/`

**Purpose**: Bot-optimized home page with og:tags

Used by nginx to serve correct meta tags to social media bots.

---

### GET `/seo-proxy/catalog`

**Purpose**: Bot-optimized catalog page

---

### GET `/seo-proxy/{spec_id}`

**Purpose**: Bot-optimized spec overview page with collage og:image

---

### GET `/seo-proxy/{spec_id}/{library}`

**Purpose**: Bot-optimized implementation page with branded og:image

---

## OG Image Endpoints

All endpoints are under `/og/` prefix.

### GET `/og/home.png`

**Purpose**: OG image for home page (with tracking)

---

### GET `/og/catalog.png`

**Purpose**: OG image for catalog page

---

### GET `/og/{spec_id}.png`

**Purpose**: Collage OG image for spec overview (2x3 grid of top implementations)

---

### GET `/og/{spec_id}/{library}.png`

**Purpose**: Branded OG image for implementation (1200x630 with pyplots.ai header)

---

## Proxy Endpoints

### GET `/proxy/html`

**Purpose**: Proxy HTML from GCS with size reporting script injection

**Query Parameters**:
- `url` - GCS URL (must be from `pyplots-images` bucket)
- `origin` - Target origin for postMessage (optional)

Used to load interactive plots (plotly, bokeh, altair) in iframes with dynamic sizing.

---

## Error Responses

### Standard Error Format

```json
{
  "detail": "Spec not found"
}
```

### HTTP Status Codes

| Status | Description |
|--------|-------------|
| 200 | Success |
| 400 | Bad request (invalid parameters) |
| 404 | Resource not found |
| 502 | External service error (GCS) |
| 503 | Database not available |

---

## Caching

### In-Memory Cache

API uses in-memory caching with TTL:
- Stats: 5 min
- Specs list: 2 min
- Individual specs: 2 min
- Filter results: 30 sec

### HTTP Cache Headers

```http
Cache-Control: public, max-age=120, stale-while-revalidate=600
```

Applied to:
- `/libraries` - 5 min
- `/stats` - 5 min
- `/specs` - 2 min
- `/specs/{spec_id}` - 2 min
- `/plots/filter` - 30 sec

---

## CORS Configuration

**Allowed Origins**:
- `https://pyplots.ai`
- `http://localhost:*` (development)

**Allowed Methods**: All

---

## GZip Compression

Responses > 500 bytes are compressed with GZip.

Example: `/plots/filter` response: 301KB → ~40KB compressed.

---

## OpenAPI Documentation

Interactive API documentation available at:
- **Swagger UI**: `https://api.pyplots.ai/docs`
- **ReDoc**: `https://api.pyplots.ai/redoc`
- **OpenAPI JSON**: `https://api.pyplots.ai/openapi.json`

---

*For database schema, see [database.md](./database.md)*
