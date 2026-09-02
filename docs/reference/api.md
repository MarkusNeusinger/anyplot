# API reference

## Overview

The anyplot API is a **FastAPI-based REST API** serving plot data to the frontend.

**Base URL**: `https://api.anyplot.ai`

**Key Principle**: Database is derived from repository via `sync-postgres.yml`. API reads from PostgreSQL.

---

## Core endpoints

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
      "preview_url": "https://storage.googleapis.com/anyplot-images/plots/scatter-basic/matplotlib/plot.png",
      "preview_html": null,
      "quality_score": 92.0,
      "code": "import matplotlib.pyplot as plt...",
      "generated_at": "2025-01-15T10:30:00Z",
      "generated_by": "claude-opus-4-7",
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
      "language": "python",
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
      "language": "python",
      "url": "https://storage.googleapis.com/.../plot.png",
      "html": null,
      "code": "import matplotlib.pyplot as plt..."
    }
  ]
}
```

---

### Plots filter

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
  "message": "Welcome to anyplot API",
  "version": "3.2.0",
  "docs": "/docs",
  "health": "/health"
}
```

---

#### GET `/health`

**Purpose**: Health check for Cloud Run, and the one place the
[origin gate](#origin-gate) can be observed

**Response**:
```json
{
  "status": "healthy",
  "service": "anyplot-api",
  "version": "3.2.0",
  "origin_gate": "off"
}
```

`version` is the installed package's version (`api/version.py`), so it moves
with each release rather than staying at the value written here.

`origin_gate` reports what the gate makes of *this* request — never the secret
itself. `/health` is exempt from the gate, so every route into the service can
be asked. See [Origin gate](#origin-gate) for the five values.

---

## Insights endpoints

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

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `language` | string | resolved from the library | Optional override. Library ids are globally unique, so the language is looked up in `core/constants.py` when the parameter is absent — `/specs/{id}/ggplot2/code` works without `?language=r`. |

---

## SEO endpoints

### GET `/llms-full.txt`

**Purpose**: Whole-catalogue index for AI agents ([llms.txt convention](https://llmstxt.org/))

One line per spec (`spec_id | title | hub URL | libraries`) plus a header that
documents the user-agent-independent retrieval recipes (code endpoint, GCS
image URL pattern, OpenAPI, MCP). nginx serves `anyplot.ai/llms-full.txt` from
this endpoint.

---

### GET `/sitemap.xml`

**Purpose**: Dynamic XML sitemap for search engines

Includes: root, plots, specs, all specs with implementations, all implementation pages.

---

### GET `/seo-proxy/`

**Purpose**: Bot-optimized home page with og:tags

Used by nginx to serve correct meta tags to social media bots.

---

### GET `/seo-proxy/plots`

**Purpose**: Bot-optimized plots page

---

### GET `/seo-proxy/{spec_id}`

**Purpose**: Bot-optimized spec overview page with collage og:image

---

### GET `/seo-proxy/{spec_id}/{library}`

**Purpose**: Bot-optimized implementation page with branded og:image

---

## OG image endpoints

All endpoints are under `/og/` prefix.

### GET `/og/home.png`

**Purpose**: OG image for home page (with tracking)

---

### GET `/og/plots.png`

**Purpose**: OG image for plots page

---

### GET `/og/{spec_id}.png`

**Purpose**: Collage OG image for spec overview (2x3 grid of top implementations)

---

### GET `/og/{spec_id}/{library}.png`

**Purpose**: Branded OG image for implementation (1200x630 with anyplot.ai header)

---

## Proxy endpoints

### GET `/proxy/html`

**Purpose**: Proxy HTML from GCS with size reporting script injection

**Query Parameters**:
- `url` - GCS URL (must be from `anyplot-images` bucket)
- `origin` - Target origin for postMessage (optional)

Used to load interactive plots (plotly, bokeh, altair) in iframes with dynamic sizing.

---

## Error responses

### Standard error format

```json
{
  "detail": "Spec not found"
}
```

### HTTP status codes

| Status | Description |
|--------|-------------|
| 200 | Success |
| 400 | Bad request (invalid parameters) |
| 404 | Resource not found |
| 502 | External service error (GCS) |
| 503 | Database not available |

---

## Caching

### In-memory cache

API uses in-memory caching with TTL:
- Stats: 5 min
- Specs list: 2 min
- Individual specs: 2 min
- Filter results: 30 sec

### HTTP cache headers

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

## Origin gate

The API runs on Cloud Run with `ingress=all`, so it answers on two addresses:
`https://api.anyplot.ai`, which Cloudflare proxies, and the raw `*.run.app`
URL, which it does not. Everything the edge enforces — the bot challenge, the
WAF, the cache that makes the `max-age=300` reads free — is one URL away from
being bypassed.

A Cloudflare Transform Rule stamps `X-Origin-Secret` onto every request it
proxies for `api.anyplot.ai`, and `api/origin_gate.py` refuses anything without
it with `403`. It is not authentication: it says "you came through the front
door", nothing about who you are — `require_admin` still decides what a caller
may do on `/debug/*`.

**Unset means off.** The gate is dormant unless `ORIGIN_SECRET` is set on the
service, which is what makes local development, the test suite and the rollback
work: remove the variable from the service, promote the resulting revision, and
the gate is gone.

**Exempt paths** — exact matches, no prefixes, and only these two:

| Path | Why |
|---|---|
| `/health` | the deploy smoke probes the candidate revision on its `run.app` tag URL, which never passes the edge |
| `/debug/cache/invalidate` | `sync-postgres.yml` posts here from a GitHub runner over the direct URL, because Cloudflare's bot challenge answers an unauthenticated curl POST with a 403 HTML page. The endpoint has its own token (`CACHE_INVALIDATE_TOKEN`, constant-time compared, 503 when unconfigured) |

`OPTIONS` is exempt too — a browser cannot attach a custom header to a CORS
preflight, so a gate that refused one would break every cross-origin call
instead of protecting anything.

`/seo-proxy/…` is **not** exempt. The site's nginx fetches the prerendered pages
over `https://api.anyplot.ai`, so that path carries the header — while an
exemption would leave the API's most expensive reads open on the direct URL: a
cache miss or an unknown id queries the repositories, and a crawler user agent
schedules an outbound Plausible event per request. Validate the crawler path end
to end while the gate is still off (below), not with an exemption:

```bash
curl -s -A 'Mozilla/5.0 (compatible; Googlebot/2.1)' https://anyplot.ai/scatter-basic | head -5
```

**Observing it.** `GET /health` reports `origin_gate` for the request it was
asked with, never the value:

| Value | Meaning |
|---|---|
| `off` | not armed, no header arrived |
| `off-seen` | not armed, the header arrived — the state to be in before arming |
| `ok` | armed, header matches |
| `missing` | armed, no header — this path would now be dead |
| `mismatch` | armed, wrong value (a half-applied rotation) |

That is what makes the rollout measurable: put the Transform Rule live while
the gate is still off, ask every route into the service (`api.anyplot.ai`, the
apex `anyplot.ai/api/*` Worker, the site's nginx, the raw `run.app`), and only
arm it once every path that must keep working answers `off-seen`.

The apex Worker stamps the header itself rather than getting it from the rule,
because a Worker subrequest to a host in the same zone bypasses that zone's
Transform Rules. Its source and the measuring procedure live in
[`infra/cloudflare/`](../../infra/cloudflare/README.md).

---

## CORS configuration

**Allowed Origins**:
- `https://anyplot.ai`
- `http://localhost:*` (development)

**Allowed Methods**: All

The origin gate sits directly inside `CORSMiddleware`, so a `403` from it still
carries the CORS headers a browser needs to read it as a 403 rather than as an
opaque network error.

---

## GZip compression

Responses > 500 bytes are compressed with GZip.

Example: `/plots/filter` response: 301KB → ~40KB compressed.

---

## OpenAPI documentation

Interactive API documentation available at:
- **Swagger UI**: `https://api.anyplot.ai/docs`
- **ReDoc**: `https://api.anyplot.ai/redoc`
- **OpenAPI JSON**: `https://api.anyplot.ai/openapi.json`

---

*For database schema, see [database.md](./database.md)*
