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

## Agent chat (admin only)

> **Status (2026-10-12):** the routes are switched on in production since
> 2026-10-11: the deploy-api trigger sets `AGENT_ENABLED=true` and
> `AGENT_SERVICE_URL`, the `AGENT_USER_ID_KEY` secret is bound, and the
> anyplot-agents service they call runs in Cloud Run. They stay behind the admin
> gate. The chat page that calls these routes, `/debug/agent` in the app, is
> built only with `VITE_ENABLE_AGENT_CHAT=true`, which the deploy-app trigger
> sets since the same day. The feedback triage routes under
> `/debug/agent/cases` and the `agent_feedback` table behind them are built
> since 2026-10-12 (see [Feedback triage](#feedback-triage)), and so is the
> session language, `PUT /sessions/{sid}/language` (see
> [Session language](#session-language)). Design:
> [Agent network design](../concepts/agent-network.md).

The `/debug/agent/*` routes (`api/routers/agent.py`) are a backend for the
frontend (BFF) in front of the private anyplot-agents Cloud Run service. The
browser never calls that service directly: the BFF authenticates the admin,
derives an opaque user id, accepts only allowlisted fields, and re-frames the
chat stream.

### Access, kill switch, and CSRF guard

Every request passes three checks, in this order:

1. **Admin gate.** The same gate as the other `/debug` routes: a Cloudflare
   Access JWT for an allow-listed email, or `X-Admin-Token`. Without either
   you get `401`; a valid JWT for an unlisted email gets `403`, and an
   unconfigured gate gets `503`.
2. **Kill switch.** Every route answers `404 {"detail": "agent chat is not enabled"}`
   unless `AGENT_ENABLED` is true and both `AGENT_SERVICE_URL` and
   `AGENT_USER_ID_KEY` are set. Production has deployed with all three since
   2026-10-11; a deploy that lacks one answers `404` instead of breaking, and
   `_AGENT_ENABLED=false` on the deploy-api trigger switches the chat off again.
3. **CSRF guard** on every method except `GET`, `HEAD`, and `OPTIONS`, so on
   `POST`, `PUT`, `PATCH`, and `DELETE`. The request needs the header
   `X-Anyplot-Client: agent-chat/1`; an `Origin` header, when the browser sends
   one, must be in the CORS allow-list or match `http://localhost:<port>`; and a
   request with a body must send it as `Content-Type: application/json`. A
   failed check answers `403` with `client_header_required`,
   `origin_not_allowed`, or `json_required`.

The deploy smoke test expects `401` on `/debug/agent/status`, whatever the
switch says.

### Identity and request ids

The agents service never sees an email address. The BFF sends
`X-Anyplot-User: adm_<16 hex digits>`, the first 16 hex digits of an
HMAC-SHA256 over the admin's email with `AGENT_USER_ID_KEY`; every caller on
the `X-Admin-Token` path shares the id derived from the string `token`.

A request that gets past the three checks and the body validation is given an
`X-Request-Id`, which the BFF sends upstream and returns on the response, also
as `ref` in an error body or an SSE `error` event. Quote it when you report a
problem. The earlier answers (`401`, `403`, `404` from the kill switch, `422`)
carry no request id, and neither does the `503` of a route that needs the
database (`POST /sessions`, `POST /sessions/{sid}/library`, the feedback route
and the case routes) on an API without a configured database, which comes in
the API-wide shape (see [Standard error format](#standard-error-format)).
Upstream calls carry a Cloud Run ID token whose
audience is `AGENT_SERVICE_URL`; for a `localhost` or `127.0.0.1` URL no token
is fetched.

### Routes

The routes mirror the agents service's `/v1` API. All paths below start with
`/debug/agent`.

| Route | Request | Response |
|---|---|---|
| `GET /status` | None | The service's `{libraries, model, location, version, provider, waiting, in_flight}` plus `"enabled": true`; `waiting` counts the turns in the agents service's run queue and `in_flight` the runs it is running |
| `GET /eligibility?spec=&library=` | Spec id and library id | The agents service's answer, passed through |
| `POST /sessions` | `{spec_id, library, locale}` | `{session_id, eligibility}`; `404 not_found` when the spec has no implementation for the library |
| `POST /sessions/{sid}/library` | `{spec_id, library}` | Switches the library; the dataset and bindings stay |
| `POST /sessions/{sid}/dataset` | `{text, confirmed?}`, at most 1 MB (1,048,576 bytes) of UTF-8 (200 KB before 2026-10-14) | `{preview, profile, bindings, warnings, context_lines, roles, suggestion, version, language}` for a table, stored as version 1 of the data (an earlier paste's undo history is dropped; `suggestion` is the wide-table offer or `null`, see [Data changes](#data-changes); `language` is the session language as `{language, source}` after the paste, see [Session language](#session-language)): CSV, TSV, semicolon or pipe text; JSON as an array of records, an object of column lists, an object of values or an array of `[category, value]` pairs (the last two become the columns `category`, the keys kept as text, and `value`; a repeated key keeps its last value with a warning); a JSON-stat 2.0 dataset, as statistics offices' APIs answer it (or a JSON-stat 1.x bundle of one dataset), flattened into a long table with one column per dimension of more than one category, named by its label and holding the category labels as text, and a typed `value` column, the one-category dimensions and the dataset's label, source and notes coming back in `context_lines` (source format `json_stat`; an inconsistent dataset is `422 unparseable`); the same shapes as a Python literal, also behind an assignment such as `cat_day = {...}`, with single quotes, trailing commas and tuples (text that starts with a bare `(` and is no literal is read as delimited text); a column whose every cell carries the same unit (`65 %`, `15,6 h`, `€ 5`, also with a no-break space) is read as numbers and named `<name> (<unit>)` with a warning, unless the header already names the unit. For text that is no table (prose, a list typed one value per line) of at most 4,000 characters, `{transcribed: true, text, preview, profile, warnings, note}`, the table the judge model read, with its CSV in `text` and nothing stored: the page shows it for confirmation, and confirming posts that CSV through this route again with `confirmed: true`, which skips the free-text fallback (a one-column table would otherwise be read again) and keeps every row (no line is left out as a note or a total), never the parse, the pre-filter, the judge or the store. A pasted table may carry other lines: a title, metadata or notes above it, a source line or notes below it, and up to three summary rows at the end (`Total`, `Summe`…) are left out, each kind with one entry in `warnings`. The lines left out above and below the table (not the summary rows) come back in `context_lines`, one text line each and at most 2,000 characters in all: the notes the assistant reads with the data. They pass the same pre-filter as the cells and then the scope judge; when either refuses them, or the judge does not answer, `context_lines` is empty and `warnings` starts with the reason, while the table is stored all the same and no strike is counted. `413 too_long` above the limit, `422 unparseable` when neither the parser nor the model finds a table, `422 formula` when the text asks for a formula such as `sin(x) von -pi bis pi` or `y = x**2` (no model reads it; ask for the formula in the chat, where the assistant computes the table, see [Data changes](#data-changes)), `422 code` when the text is a program that generates data, such as Python, JavaScript or R (checked before any parse; send it to the chat, where the assistant runs it; only text within the chat's 2,000 characters can move there), `403 data_refused` when a header, a cell or the raw text addresses an AI (personal data such as names, addresses, e-mail addresses, phone numbers and web addresses is allowed), `503 guard_unavailable` when the judge model does not answer |
| `PUT /sessions/{sid}/bindings` | `[{role, column}]`, at most 50 | The agents service's `{bindings, complete, missing_roles, warnings}`; `422 no_dataset` before a parse, `422 invalid` with the check's `errors` lines for a binding the spec roles or the columns refuse, `409 run_active` while a turn or a render is in flight. A change of the bindings drops the data confirmation below |
| `PUT /sessions/{sid}/language` | `{language}`: a short language name or code such as `de`, `Deutsch` or `Swedish`, 1 to 40 characters that match `^[A-Za-z][A-Za-z -]{0,39}$` | The agents service's `{language, source}`, the stored form (`English` comes back as `en`, `Swedish` as typed) with the source now `chosen`: the replies and the plot text of the next version follow it, and the language a typed message implies never replaces it (see [Session language](#session-language)). Versions made before keep their text. `422` for a value outside the pattern, `409 run_active` while a turn or a render is in flight |
| `POST /sessions/{sid}/dataset/confirm` | none | Step 1 of two: you confirm that the stored dataset and its bindings fit; `{confirmed: true, rows, columns}`. The plot pipeline runs only on confirmed data (`create_plot` before it answers `plot{status: "not_ready", reason: "data_unconfirmed"}`); a new paste, a transcription's `.use()`, a binding change, a change of the data by the assistant or an undo drops the confirmation, a library switch keeps it. `422 no_dataset` before a parse, `409 run_active` while a turn or a render is in flight |
| `POST /sessions/{sid}/dataset/undo` | none | Undo the assistant's last change to the data (see [Data changes](#data-changes)): the version before it is the current dataset again, `{preview, profile, bindings, warnings, context_lines, roles, suggestion, version}` like the dataset route (the wide-table offer comes back with a wide version), unconfirmed. The service keeps the last five versions. `422 nothing_to_undo` when the paste was never changed or the first data came from a formula, `409 run_active` while a turn or a render is in flight |
| `POST /sessions/{sid}/dataset/to_long` | none | Make a wide table long for the plot's category and value roles (the page's `.to_long()`, see [Data changes](#data-changes)): the service recomputes its `suggestion` and applies that `pivot_longer` without a model call, as the next version with the default bindings for the new columns, answered like the undo route plus `changes`, unconfirmed. `422 no_suggestion` when the table is not wide for this plot, `409 run_active` while a turn or a render is in flight |
| `POST /sessions/{sid}/messages` | `{text}` (at most 2,000 characters), `{"action": "create_plot"}` or `{"action": "summarize_data"}` | An SSE stream in protocol `anyplot/1`; `413 too_long` above the limit, `409 run_active` while you have a turn or a theme render in flight in any session; a full run queue ends the turn's stream with `error {"code": "capacity"}` (see [SSE protocol](#sse-protocol-anyplot1)). `summarize_data` asks the assistant for the step-1 summary of the data (rows, columns with types and units, missing values, percentages, the proposed bindings, one question when something is ambiguous) without the scope judge, like `create_plot`; when the stored dataset kept notes pasted with the table (`context_lines`, judged when they were pasted), the turn carries them to the assistant fenced as `<user_notes>`, so it can act on a request in them, such as "make it a line chart" |
| `POST /sessions/{sid}/cancel` | None | `204`; a turn that still waits leaves the run queue |
| `POST /sessions/{sid}/versions/{version}/render` | `{"theme": "light"}` or `{"theme": "dark"}`; `version` is 0 to 999, where 0 is the latest version | `{status, reason?, artifacts}` once the render is done (see [Theme toggle](#theme-toggle)) |
| `GET /sessions/{sid}/artifacts/{name}?v=` | `name` is one of `plot-light.png`, `plot-dark.png`, `plot.py`, `data.csv` | The file, with `Cache-Control: private, no-store` and `X-Content-Type-Options: nosniff`; any other name is `404`, and so is the PNG of a theme the version has not rendered. A PNG carries the footer strip (see [Footer strip](#footer-strip)) |
| `GET /sessions/{sid}/bundle?include_data=&version=` | `include_data` is `true` or `false` (the default); `version` is 0 to 999, where 0 or none means every version (the BFF then asks the agents service without one, since there `version=0` is the chat's feedback case) | The session as one JSON file to save (the chat page's `.save()`), with `Content-Disposition: attachment; filename="anyplot-session-<first 8 characters of the session id>.json"`, `Cache-Control: private, no-store` and `X-Content-Type-Options: nosniff`. `404 not_found` for a version the session does not have; a bundle over 32 MiB can't be saved (see [Session bundle](#session-bundle)) |
| `POST /sessions/{sid}/feedback` | `{reaction, message?, include_data, result_version, replaces?}`: `reaction` is `thumbs_up`, `thumbs_down`, `bug` or `idea`; `message` has at most 500 characters after the strip; `include_data` is a JSON boolean and `result_version` a JSON integer from 0 to 999, neither coerced from another type, where 0 is the chat itself (feedback on a session that made no plot, since 2026-10-12); `replaces` is the case id of the earlier submission for the same version, when this one is an edit of it | `201 {case_id, stored}`: the version is stored as a feedback case in the private case bucket and indexed as a row of the `agent_feedback` table, and `stored` lists its file names (see [Feedback case](#feedback-case)); a chat case has no image and no `plot.py`, only `data.csv` when asked for and `manifest.json`. `404 not_found` for a version the session does not have, `422 no_data` for a chat case that asks for `data.csv` before the session has data, `502 storage` when the bucket refused the case, `502 row_missing` with the stored `case_id` when the files are stored but the row insert failed, `503` before the bundle fetch when the API has no database configured, otherwise the errors of the bundle route |
| `GET /cases?reaction=&status=&spec=&library=&model_version=&tag=&include_superseded=&before=&limit=` | Every filter is optional: `reaction` is one of the four reactions; `status` is `new`, `in_progress`, `done`, `wont_solve`, or `open` for the first two; `spec` is a spec id, `library` a library id, `model_version` an exact value and `tag` one tag; `include_superseded=true` lists superseded cases too; `before` is the last case id of the page before; `limit` is 1 to 200, 50 by default | `{items, has_more}`: the cases' `agent_feedback` rows, newest first, each with every column, timestamps in UTC ISO 8601 with `Z`; `has_more` says that a further page exists (see [Feedback triage](#feedback-triage)) |
| `GET /cases/{id}` | A case id such as `20261012T143005Z-1a2b3c4d` | The row plus what the case's `manifest.json` adds: `transcript`, `code` (the case's `plot.py`), `diff` (a unified diff of the catalogue original against that code), `catalogue_library_version`, `snapshot_library_version`, `residual_defects`, `changes`, `result_reason`, `config` and `bindings`, and `siblings`, the ids of the other cases of the same session hash and version. `expired: true` when the lifecycle rule has deleted the manifest: then `transcript`, `code`, `diff`, `snapshot_library_version`, `result_reason` and `config` are `null`, the lists `residual_defects`, `changes` and `bindings` are empty, and the row and `siblings` remain. `404 not_found` for an id without a row, `502 storage` when the bucket could not be read |
| `GET /cases/{id}/files/{name}` | `name` is one of `plot-light.png`, `plot-dark.png`, `plot.py`, `data.csv`, `manifest.json` | The file as stored, with its content type, `Cache-Control: private, no-store`, `Content-Disposition: inline`, `X-Content-Type-Options: nosniff` and `X-Request-Id`. `404 not_found` for an id without a row, a file the case does not hold, or one the lifecycle rule deleted; `502 storage` for any other bucket error |
| `PATCH /cases/{id}` | `{status?, tags?, promoted?, expected?}`, at least one: `status` is `new`, `in_progress`, `done` or `wont_solve`; `tags` replaces the whole list with at most 10 unique tags that match `^[a-z0-9-]{1,40}$`; `promoted` is a JSON boolean; `expected` is `accepted` or `rejected` | The whole row, as the list shows it, with the tags sorted. `promoted: true` sets `promoted_at` once, and when neither the body nor the row names an expected outcome it takes the reaction's (`thumbs_up` accepted, `thumbs_down` rejected); `promoted: false` clears `promoted_at`. `422 no_plot` when you promote a chat case (`result_version` 0, no plot to replay), `422 no_data` when you promote a case stored without `data.csv`, `422 expected_required` when you promote a `bug` or `idea` without an expected outcome, `404 not_found` for an id without a row |
| `DELETE /sessions/{sid}` | None | `204` |

Validation: `spec_id` matches `^[a-z0-9-]{1,100}$`; `library` is one of the 15
supported library ids; `locale` is a language tag of at most 16 characters such
as `de` or `de-CH`, the browser's, recorded with a feedback case and never used
as the session language; `language` matches `^[A-Za-z][A-Za-z -]{0,39}$`; the
session id matches `^[A-Za-z0-9_-]{1,128}$`; a binding
`role` matches `^[A-Za-z_][A-Za-z0-9_]{0,31}$` (the agents contract, so roles
such as `temperature_K` or `X1` pass) and its `column` has at most 64 characters. An
unknown field in a body is a `422`, and so is a body with a lone surrogate
escape such as `"\ud800"`, which UTF-8 cannot carry (`422 invalid_text`).

Personal data is allowed. Your dataset, your messages and the plot may carry
names, postal and e-mail addresses, phone numbers, web addresses and amounts,
for example from your own tax return or contact list, in tick labels, titles
and annotations, and the assistant may name a single value in its reply. The
guardrails refuse misuse of the assistant by intent, such as plot text that
advertises, calls to action, or addresses other people, and never refuse the
data itself. Links are the one limit, and only in what the model writes: a
bare web address such as `jana-novak.de` passes, while a link with a scheme
such as `https://` or with `www.` is stripped from a reply and refused in a
change request, and a `mailto:` link is stripped from a reply. A dataset cell
with a link plots as it is.

The agents service keeps a session's data, code and images in memory for the
session's lifetime and writes no content to its logs. anyplot stores none of
it unless you submit quick feedback (see [Feedback case](#feedback-case)).
That feedback case always holds the conversation, the code, the images and the dataset profile
with its column names and sample rows, so it can show your data even without
the data box; the full data file is in it only when you tick the box. Admins
can read a submitted case on `/debug` through the case routes, the
conversation, the images and the `data.csv` included, until the bucket's
lifecycle rule deletes the files after 180 days. The case's row in the
`agent_feedback` table stays after that: it holds the reaction, your message,
the hashed user and session ids and the run's metadata, but no conversation,
code, images or data. The chat
page's `.save()` downloads something else, the whole session as one bundle with
every version and no case manifest, to your computer (see
[Session bundle](#session-bundle)); anyplot keeps no copy of it.

`POST /sessions` and `POST /sessions/{sid}/library` add the user id and a
catalogue snapshot before they forward the body, because the agents service
has no database access: `{spec_id, title, description, data_roles, notes,
code, library_version}`, with `# noqa` comments stripped from the code.

Version numbers: `{version}` in the theme toggle route and `v` on the artifact
route are the agents service's version numbers. A session's versions are
numbered from 1 in the order the service stores them, and it stores exactly
the turns whose `plot` event has the status `ok` or `needs_attention`. That
`plot` event carries the stored number as `version`, so a client addresses a
version by the server's number instead of counting the events it received; a
`failed` or `not_ready` event has no `version`. `0`, or no `v`, means the
latest version.

Roles and bindings: the dataset response lists the spec's data roles as
`roles`, each `{name, kinds, required, variadic, description, non_negative}`,
where `kinds` names what a role accepts (`numeric`, `categorical`, `text`,
`boolean`, `datetime`; empty means any column), `description` is the spec's own
text, at most 200 characters, and `non_negative` marks a role that needs values
of 0 or more, such as a radius, a size, a standard deviation, or the value of a
pie, treemap or sankey. The default bindings never give such a role a column
with a negative value. A single role binds under its own name. A variadic
family such as `y` binds its members `y1`, `y2`, and so on, never its bare
name. `PUT /sessions/{sid}/bindings` replaces the whole set and answers
`{bindings, complete, missing_roles, warnings}`: the stored bindings, whether
every required role has a column, the required roles that still have none, a
family by its name, and one line per `non_negative` role bound to a column
with a negative value or left open because every fitting column has one (a
warning, never a refusal). A refused set answers
`{"detail": "invalid", "ref": "<request id>", "errors": [...]}` with at most
20 of the binding check's lines, such as
`role 'y' takes numbered members such as 'y1'`.

### Data changes

In step 1 you can ask the assistant in words to change the data: read a column
as numbers or dates, drop a total row, sum or average per month or category,
rename a column, sort, turn columns into rows or rows into columns, add a
category column derived from other columns. The
assistant never writes data rows: it chooses from a fixed set of operations
(`rename`, `drop_columns`, `drop_rows`, `set_type`, `aggregate`, `sort`,
`pivot_longer`, `pivot_wider`, `classify`, at most five per call), the agents service
applies them to the stored data and stores the result as the next version,
numbered from the paste's 1. The turn's `done` event then carries `dataset`,
the new version as the dataset route would answer it plus `changes`, one line
per operation with its counts (for example `dropped 1 row where Tier =
'Gesamt'`), and `data_confirmed: false`: you check the preview and confirm the
new version like a paste. A column the assistant set to text stays text in
every later version. `POST /sessions/{sid}/dataset/undo` restores the
version before the last change; the service keeps the five versions before the
current one, so after more than five changes the history ends above version 1,
and an undo with nothing left answers `422 nothing_to_undo`. A new paste
starts over at version 1 and drops the history.

A table that holds the same quantity side by side, such as
`Sensor_A,Sensor_B,Sensor_C`, on a plot that wants one category column and
one value column (a box, violin or strip plot) carries `suggestion` in every
dataset answer and `done.dataset`: `{kind: "to_long", columns, names_to,
values_to, keys, rows}`, the `pivot_longer` that makes it long, with the
plot's role names as the new columns and date columns kept as keys. It is
`null` for a table with a text column, a plot that takes two numeric roles or
a series family, and long data. `POST /sessions/{sid}/dataset/to_long` (no
body, the page's `.to_long()`) has the service recompute and apply that one
operation without a model call: the next version, with the default bindings
for the new columns, answered like an undo plus `changes`; `422 no_suggestion`
when the table is not wide for this plot.

You can also ask for a mathematical function or curve instead of your data,
such as `sin(x)` from -pi to pi, a parabola or a parametric circle. The
assistant's `generate_data` tool then chooses a spec, never rows: one or two
variables, each a range of evenly spaced points (200 by default, at most
5,000; two variables make a grid of at most 10,000 rows), and one to ten
series, each an expression over the variables with numbers, `pi`, `e`, `tau`,
`+ - * / ** % //`, parentheses and a fixed set of functions (`sin`, `cos`,
`exp`, `log`, `sqrt`, `atan2`, `min`, `max` and others). The agents service
computes the table and stores it like a change: as the next version when the
session has data, which you can undo, or as version 1 when it has none. The
turn's `done` event carries it with a change line such as `generated 200 rows:
x from -3.1416 to 3.1416, y = sin(x)`, plus one line per series with values
the formula does not define (they stay empty). The generated table starts
from the default bindings for its columns. A formula pasted into the data
field answers `422 formula` instead, because the free-text reader is a model
and would write the rows itself; only text within the chat's 2,000-character
cap is refused this way, because the page's offer sends it to the chat as a
turn. Text that holds its own values is data, not
a formula: with three numbers or more besides a range, such as `Umsatz von
2020 bis 2024: 10 12 15 18`, the free-text reader reads it as a table.

You can also paste or type code that generates your data, in Python,
JavaScript, R or as a formula from a textbook. The assistant translates it
into Python and calls its `run_data_code` tool. The agents service validates
the Python (only numpy, pandas, `random`, `math`, `statistics` and the scipy
computing modules; no files, network, plotting or values written out from
memory), runs it in the renderer's sandbox without network access, and stores
the table the code assigns to `df` like a change: the next version, or
version 1 when the session has no data. The turn's `done` event carries it
with the change line `computed from your code: <rows> rows, <columns>
columns` and the Python that ran as `dataset.code`; the data panel shows it
under `# code that made this data`. Code pasted into the data field answers
`422 code` instead.

### Session language

Every session has one language for the assistant's replies and for the text in
the plot: the title, the axis titles, the legend entries and the annotations.
It starts as English (`en`, source `default`), also when your browser is set to
another language. When you paste data before typing anything, the language of
the notes around your table, or else of its column names, sets it (source
`pasted`, shown as `lang: de · from data`); column names such as
`temperature_2m_max` or English notes leave the current language unchanged. Your first typed
message that the assistant answers sets it to the language you write in
(source `detected`), also after a paste: a refused message and the
`create_plot` and `summarize_data` actions set nothing, and later messages do
not change it again; a very short
English message, such as a formula, leaves the current language in place, and
the next message is read for its language again. A paste never changes a
language that a typed message or your choice set. To set it yourself, pick a language
from the `lang:` chip in the chat header, type any language name in Latin
letters into its field, or ask in the chat ("labels in English"). Both make the
same change (source `chosen`), which detection never overrides; when you
already have a plot, a request in the chat also makes the next version in the
new language. The code, its comments, column names and labels from your data
are not translated. A plot you already have keeps its text; the next version
uses the new language. After each turn, the `done` event carries the language
as `{language, source}`, and so does the answer to a paste.

### Theme toggle

A chat turn renders the plot in one theme: light, unless you ask for a dark
plot. `POST /sessions/{sid}/versions/{version}/render` renders another theme
of a finished version from its stored code and data. It calls no model and
does not wait in the run queue, but it shares the one render slot with
running turns, which get a freed slot first, so it can wait for a render in
progress. The response arrives when the render is done:

| `status` | Meaning | `reason` |
|---|---|---|
| `ok` | The theme rendered on the exact canvas | None |
| `needs_attention` | The canvas missed, so the PNG was padded onto it, never cropped | `canvas_padded` |
| `failed` | The render failed the host gates (`render`), or the renderer could not run (`error`); no PNG was stored | `render` or `error` |

`artifacts` lists the version's files after the call, for example
`["plot-light.png", "plot-dark.png", "plot.py", "data.csv"]`. Asking again for
a theme the version already has answers from its record without a new render.
A `render` failure is recorded too: the same code and data fail the same way,
so asking again renders it once more and then answers from the record. An
`error` is not recorded, so you can try again.

The route answers `409 run_active` while the session has a queued or running
turn or another theme render, or while you have one in another session (a
turn in the session also gets `409 run_active` while the theme renders),
`404 not_found` for an unknown version or one whose render was swept, and
`503 capacity` when no render slot came free within 120 seconds or the
agents service's render store is full.

### Footer strip

The PNGs you download through the artifact route carry a strip below the
plot: "made with any.plot()" on the left and "anyplot.ai/<spec-id>" on the
right, in the theme's page colour. The strip adds 64 pixels to a 3200-pixel-wide
plot, so a 3200x1800 render arrives as 3200x1864 and a 2400x2400 render as
2400x2448; size an image box from the PNG itself, not from a fixed 16:9. The
plot above the strip is the render exactly as the gates and the reviewer saw
it, and the exported `plot.py` reproduces the plot without the strip. The
agents service switches the strip off with `AGENT_WATERMARK=false`; the layout
is in [Agent network design](../concepts/agent-network.md#footer-strip).

### Session bundle

`GET /sessions/{sid}/bundle` answers the feedback case that the agents service
assembles for the session: the conversation (your messages and the assistant's
replies, never tool calls or thoughts), the catalogue snapshot's spec id and
library version, every version's working, run and exported code with its adapt
plan, plot result, gate outcome per theme and the PNG of every rendered theme
as base64 (with the footer strip), the dataset profile, the bindings, and a
config stamp (provider, model, judge model, location, ADK and service versions,
prompt hashes); each version's `data.csv` only with `include_data=true`. The
top-level keys are `session`, `snapshot`, `transcript`, `versions`, `profile`,
`bindings` and `config`, plus `refusals` when the agents service runs with
`AGENT_KEEP_REFUSALS`. `session` names the spec, the library, the browser's
locale and the session language (`plot_language`, `plot_language_source`), and
each version carries the `language` its text was written in.

A bundle over 32 MiB can't be saved: that is Cloud Run's limit on an HTTP/1
response that is not streamed, and the agents service answers the bundle in one
piece. On Cloud Run, the agents service's side refuses such a bundle before the
BFF reads a byte, so the route answers `500 upstream`. The BFF reads the whole
bundle before it answers and refuses one over 32 MiB itself with
`502 too_large`, which you see only where nothing sits in front of the agents
service, such as a local run. A typical session stays far below the limit,
because a version's PNGs take about 0.1 to 1 MB of base64.

The BFF compresses the bundle with gzip in a worker thread when the browser
accepts gzip, so the API's compression middleware doesn't hold the event loop
for a large file.

### Feedback case

`POST /sessions/{sid}/feedback` is the result card's quick feedback, and with
`result_version` 0 the chat's own, for a session that made no plot. In phase 1
only admins can send it, like every route here. The BFF fetches the bundle of
the one version you rate (`GET /v1/sessions/{sid}/bundle?version=<result_version>`;
for version 0 the conversation without any version, and the session's current
data as the top-level `data_csv`;
with `data.csv` only when `include_data` is `true`; the same fetch and the same
32 MiB cap as `.save()`), splits it into files in a worker thread, and uploads
them to the private bucket `AGENT_CASES_BUCKET` under `cases/<case_id>/`:

| File | Content type | Contents |
|---|---|---|
| `plot-light.png`, `plot-dark.png` | `image/png` | The version's PNG of each theme it rendered, with the footer strip, as you saw it; a theme it never rendered has none |
| `plot.py` | `text/x-python; charset=utf-8` | The exported code |
| `data.csv` | `text/csv; charset=utf-8` | The version's data, only with `include_data` |
| `manifest.json` | `application/json` | The case record, and the whole bundle without the PNGs and the data, which are the files above |

The case id is the UTC time in ISO 8601 basic format and eight random hex
digits, such as `20261012T143005Z-1a2b3c4d`, so case ids sort by time. The
manifest holds `schema` (1), `id`, `created_at`, `case_uri`, `user_hash` (the HMAC user id the
agents service sees), `session_hash` (the first 16 hex digits of the session
id's SHA-256), `spec_id`, `library_id` (the version's library), `language` (the
session's locale), `reaction`, `message`, `include_data`, `status` (`new`),
`result_version`, `replaces` (as the page sent it, or `null`), `model`,
`model_version`, `judge_model`, `prompt_hash` (one
hash over the config stamp's prompt hashes), `pipeline_status`, `attempts`,
`tokens`, `cost_estimate`, `files` and `bundle`. Every field but `bundle` is a
column of the case's row in the `agent_feedback` table, `language` as `locale`
and `schema` as `manifest_schema`: `core.agent_cases.row_from_manifest` turns
the manifest into that row, for the route and for the backfill of
`agents/evals/sync_cases.py` alike (see [Feedback triage](#feedback-triage)).
A field the bundle does not carry is `null`; today that is `model_version`,
`tokens` and `cost_estimate`. A bundle that lacks the version's data while
`include_data` is set is refused as `502 upstream`, so no manifest claims data
the case lacks.

The manifest is uploaded last, and every upload refuses to replace an existing
object. A case directory without a manifest is an aborted upload, never a case:
when an upload fails, the route answers `502 storage` with a request id and
uploads nothing more. A retried upload that meets an object under its own name
counts as stored only when that object's MD5 matches the bytes it carries (its
own first attempt stored them and lost the response); any other content is a
conflict and `502 storage`.

After the manifest, the route inserts the case's row into `agent_feedback`.
When that insert fails (the database is unreachable, or a constraint refuses
the row), the files are already stored: the route answers `502 row_missing`
with the request id and the stored `case_id`, so the page can name that case
in its next edit, and `sync_cases.py --backfill` can index it later (see
[Sync promoted cases from the bucket](../../agents/README.md#sync-promoted-cases-from-the-bucket)).
An API without a configured database answers `503` before it fetches the
bundle, so it never stores a case it cannot index.

Sending feedback for the same version again stores a new case, and the page
sends the earlier case's id as `replaces`. The new row supersedes the earlier
one only when that row exists with the same session hash and result version
and is not superseded yet; the client sends `replaces`, so the check keeps an
edit from hiding another session's case. A submission without `replaces`
supersedes nothing, and the case detail lists the other cases of the same
version as `siblings`, so duplicates stay visible. The API deletes nothing, so
a replaced case keeps its files, its `data.csv` too, until the bucket's
lifecycle rule deletes them after 180 days; that rule is the retention for
cases and aborted uploads alike. The API's runtime identity needs permission
to create objects in the bucket, to read them (the case routes) and to read
their metadata, which the check of a retried upload uses.

### Feedback triage

The case routes (`GET /cases`, `GET /cases/{id}`, `GET /cases/{id}/files/{name}`
and `PATCH /cases/{id}`) serve the "agent cases" section of `/debug`
(`app/src/sections/debug/`). They never call the agents service. The
`agent_feedback` row is the source of truth for a case's triage state: its
status, tags, expected outcome, promotion and supersession. The bucket holds
the files until its lifecycle rule deletes them, and the row keeps the class
statistics after that. The table's columns are in
[Database schema](database.md#agent_feedback).

- **List.** The section opens on the open queue (`status=open`, which is `new`
  and `in_progress`) with superseded cases hidden, and filters by reaction,
  status, spec, library, model version and tag. `model_version` is `null` on
  every case until the agents service stamps it.
- **Detail.** A case shows the PNG of each theme it holds, the code with a
  unified diff against the catalogue original, the transcript, the defect
  lines, the config stamp and your message. The diff runs against the
  catalogue at triage time, which a regeneration may have changed since the
  session: compare
  `snapshot_library_version`, the version the session adapted, with
  `catalogue_library_version`. The export's attribution header is left out of
  the diff.
- **Status and tags.** The status takes the four values of the site feedback's
  triage; `done` and `wont_solve` retire a case. Tags name failure classes, such
  as `legend-overlap`.
- **Promotion.** Promoting sets `promoted_at` and the outcome the regression
  harness expects (`expected`), and needs the case's `data.csv`, because the
  harness cannot run a case without it. The section shows the rule as
  guidance, and nothing enforces it: promote a case when your reaction
  contradicts the
  pipeline outcome, when it shows a class no fixture covers, or when it is a
  bug or idea with a reproducer; retire it once a fixture or a test covers it.
  On the dev machine, `agents/evals/sync_cases.py` pulls the promoted, active
  cases into `agents/evals/.cases/` and removes the retired ones (see
  [Sync promoted cases from the bucket](../../agents/README.md#sync-promoted-cases-from-the-bucket)).
- **Supersession.** A superseded case keeps its status and tags and can still
  be changed; a new case starts as `new` without tags. When the backfill
  indexes a case after the edit that names it in `replaces`, the case goes in
  already superseded by that edit, in the same commit as its insert, so the
  chain is the same whichever of the two was indexed first.

The feedback route and the case routes need the migration that creates the
table (`alembic/versions/b4e7a9c2d6f1_add_agent_feedback_table.py`).
`sync-postgres.yml` runs it on the merge, in parallel with the API deploy.
Until it has run, the feedback route stores the case and answers
`502 row_missing`, and the case routes answer `500`.

### SSE protocol `anyplot/1`

| Event | Data |
|---|---|
| `ready` | `{v, run_id}` |
| `status` | `{step: "queued", position, waiting}` mid-turn, while the turn's plot run or data snippet waits in the run queue: `position` 1 runs next, and `waiting` counts every queued run, this one included |
| `status` | `{step, attempt}` for a pipeline step: `adapting`, `checking`, `rendering`, `reviewing`, or `repairing`; `repairing` adds `outcome` and `findings`, how the round before it ended (see `rounds` below) |
| `message` | `{text}`: the assistant's reply as plain text, at most 1,200 characters; a longer reply arrives cut to 1,200 characters when the turn ran the plot pipeline, and as the `out_of_scope` refusal otherwise |
| `plot` | `{status, reason, attempts, artifacts, changes, residual_defects, version, rounds}`; `version` only on `ok` and `needs_attention`; `rounds` lists each attempt as `{attempt, outcome, findings, step, shipped}` (`step` is the pipeline step the round ended in, `shipped` marks the round whose render the result shipped), where `outcome` is `ok` (the review passed), `review` (the review named `findings`), `measured` (measured findings went to the repair), `render_failed`, `check_failed`, `answer_unusable`, `unreviewed` or `error` |
| `refusal` | `{code, text}`; `code` is `out_of_scope`, `needs_data` (the request needs data the service would have to fetch), `unsupported_content`, `budget`, `rate_limited` (more than 10 messages in a minute), `daily_limit` (more than 200 messages in a UTC day) or `session_closed` (the session's third `out_of_scope` or `attack` refusal, and every turn after it: reload the page to start a new session), and `text` is the fixed reply for it in the language the scope judge detects in your message, or in the session language for a refusal sent before the judge runs (`budget`, `unsupported_content`, `rate_limited`, `daily_limit`, and `session_closed` after the closing turn), which is English until your pasted data, your first message or your choice sets another (see [Session language](#session-language)): English, German, French, Spanish, Italian, Portuguese, Dutch, Polish, Chinese, Vietnamese or Russian, and English for any other language |
| `error` | `{code, ref}`; `code` is `capacity` (the run queue was full when the turn's plot run or data snippet asked for a place, the run waited the queue's maximum of 600 seconds, or the BFF's turn cap ran out while it waited), `deadline`, `guard_unavailable`, `upstream`, or `internal`; `ref` is the request id |
| `done` | `{llm_calls, tokens, bindings?, data_confirmed?, dataset?, language?}`: after a run, the session's bindings and whether the data is confirmed, so the page syncs its dropdowns and its step after a turn in which the root's `set_bindings` changed them; `dataset` only after a turn in which the assistant changed the data or computed it from a formula (see [Data changes](#data-changes)): `{preview, profile, bindings, warnings, context_lines, roles, changes, version}`, the dataset route's shape (`roles` at most 50; `context_lines`, the pasted notes, carried over to every version made from the paste) plus the turn's change lines, for the page's preview table; `version` is 1 when a formula or the user's code made the session's first data; `code`, only on a version computed from the user's code, holds the Python that ran; `language` after every run: `{language, source}`, the session language and how it was set (`default`, `pasted`, `detected` or `chosen`), so the page syncs its chip |

The BFF re-frames the upstream stream instead of forwarding it. It assembles
each complete event and drops events of any other type, events without a type,
data that is not a JSON object, and every field the table does not list, so
`error_details` and stack traces never reach the browser. An event over 64 KiB
is dropped whole, except `done`, which may carry a dataset version and is
relayed up to 512 KiB (the largest dataset the service accepts fits: the
event carries the 20-row preview and the profile, never the data itself, so
its size does not grow with the 1 MB paste cap or the 2 MB cap of data the
assistant computes). An error
code outside the list becomes `internal`. The BFF stops reading after `done`.

A turn starts at once. Only the work that runs in the sandbox waits in the
agents service's run queue, which runs one such run at a time and starts at
most one a minute: a plot run (the pipeline, after its check that your data is
confirmed) or a snippet that generates data. A question, an answer about your
data or code, a refusal, and a data change that needs no sandbox never wait.
A run that can start at once sends no `queued` status. Otherwise, mid-turn,
the stream sends a `queued` status at once, on every change of the position or
the queue length, and every 15 seconds while nothing changes, and then the
run's own events. A question streams `ready`, `message`, `done`; a plot
streams `ready`, the `queued` statuses if it has to wait, the pipeline steps,
`plot`, `message`, `done`. A turn whose run finds the queue full ends with
`error {"code": "capacity"}` and `done`.

Before the scope check, and without any model call, the stream sends `ready`,
a `refusal` and `done` at once when you are over the daily token budget
(`budget`), past 10 messages in a minute (`rate_limited`) or 200 in a UTC day
(`daily_limit`), counting typed messages and the page's actions alike, or when
the session is closed (`session_closed`). The scope check closes a session at
its third `out_of_scope` refusal; a `needs_data` refusal never counts. A
closed session answers every turn with `session_closed`; reload the page to
start a new session.

While the stream is idle, a `: ping` comment arrives every 15 seconds. Every
stream ends with `done`: when the agents service is unreachable, cuts the
stream, runs past `AGENT_REQUEST_TIMEOUT_S`, or ends without `done`, the BFF
sends `error {"code": "upstream"}` and then `done {}`. Time in the run queue
does not count toward `AGENT_REQUEST_TIMEOUT_S`: every `queued` status starts
the budget again with 15 seconds on top, because the run can start up to one
`queued` status before its first event, and the first event after the wait
starts it again. No turn runs past `AGENT_TURN_MAX_S` (1,190 seconds), which
stays below anyplot-api's own request timeout of 1,200 seconds: a turn that is
still queued when its run could no longer finish inside that cap ends with
`error {"code": "capacity"}` and `done {}`, and leaves the queue before it
spends a token. At the defaults, the agents service's full 600-second queue
maximum plus the 540-second run fit inside the cap, so the BFF never cuts a
wait short. Errors that happen before the stream starts, such as
`413 too_long` or an upstream `409 run_active`, arrive as HTTP statuses
instead.

### Agent error responses

The agent routes answer errors as `{"detail": "<code>", "ref": "<request id>"}`;
the kill switch, the CSRF guard, and the `invalid_text` check leave out `ref`,
and the admin gate and FastAPI's own `422` keep the API-wide shapes. An
upstream `4xx` or `5xx`
keeps its status. Its code is one the agents service documents (`not_eligible`,
`run_active`, `too_long`, `unparseable`, `formula`, `code`, `data_refused`, `session_expired`,
`guard_unavailable` and `capacity` (both `503`, worth a retry), `no_dataset`,
`nothing_to_undo`, `rate_limited`) or
a generic one for the status (`bad_request`, `not_found`, `conflict`,
`too_long`, `invalid`, `rate_limited`, `rejected`, `upstream`); the upstream
body is never echoed, except the binding check's `errors` lines of a refused
binding set (see the routes above), each cut to one line of at most 300
characters. Two cases answer `502` instead:

- `upstream_auth`: an upstream `401`, or a `403` without a documented code.
  Cloud Run IAM refused the BFF's own ID token, which is not the admin's
  session failing.
- `upstream`: the agents service is unreachable, an ID token could not be
  fetched, or a success response is not JSON.

A session bundle over 32 MiB answers `500 upstream` on Cloud Run and
`502 too_large` where the BFF reads it itself (see
[Session bundle](#session-bundle)). The feedback route answers `502 storage`
when the case bucket refused an upload, `502 upstream` when the bundle is
not the shape the agents service documents, and `502 row_missing` when the
case is stored but its table row is not; that body also carries the stored
case id, as
`{"detail": "row_missing", "ref": "<request id>", "case_id": "<case id>"}`
(see [Feedback case](#feedback-case)). The case routes answer
`404 not_found` for a case id without a row and `502 storage` when the bucket
could not be read; `PATCH /cases/{id}` answers `422 no_data` and
`422 expected_required` for a promotion it refuses (see
[Feedback triage](#feedback-triage)).

### Configuration

| Variable | Default | Purpose |
|---|---|---|
| `AGENT_ENABLED` | `false` | The kill switch |
| `AGENT_SERVICE_URL` | Unset | Base URL of anyplot-agents, without `/v1`; also the ID-token audience |
| `AGENT_USER_ID_KEY` | Unset | HMAC key for the user id; from Secret Manager in production |
| `AGENT_REQUEST_TIMEOUT_S` | `550` | Upstream timeout, and the cap on one chat stream outside the run queue; above the agents service's 540-second deadline |
| `AGENT_TURN_MAX_S` | `1190` | Hard cap on one chat turn, queue wait included; keep it below anyplot-api's Cloud Run `--timeout` (1,200 seconds in `api/cloudbuild.yaml`) |
| `AGENT_CASES_BUCKET` | `anyplot-agent-cases` | The private EU bucket the feedback cases go to and the case routes read from (see [Feedback case](#feedback-case)); never the public image bucket. The default is the production bucket, so a local API with Application Default Credentials stores its cases there too; set a bucket of your own for local runs |

In production, `AGENT_ENABLED` and `AGENT_SERVICE_URL` come from the
`_AGENT_ENABLED` and `_AGENT_SERVICE_URL` substitutions in `api/cloudbuild.yaml`.
Change them there: the deploy rewrites both variables on every build.

---

## Error responses

### Standard error format

```json
{
  "status": 404,
  "message": "Spec 'unknown' not found",
  "path": "/specs/unknown"
}
```

Errors that pass through the API's exception handlers (for example 400, 404 and 503) use this shape. Two responses use a `detail` body instead: request validation errors (next section) and the 403 that the origin gate returns to a caller that bypasses `https://api.anyplot.ai`. The agent chat routes use their own `detail` shape; see [Agent error responses](#agent-error-responses).

### Request validation errors

A request whose body or parameters fail schema validation returns status 422 with FastAPI's standard `detail` list instead, one entry per problem:

```json
{
  "detail": [
    {
      "type": "string_type",
      "loc": ["body", "message"],
      "msg": "Input should be a valid string",
      "input": 123
    }
  ]
}
```

The body is always ASCII: any non-ASCII character in the echoed `input` is JSON-escaped, so text that cannot be encoded as UTF-8, such as a lone surrogate (the JSON string `"\ud800"`), still gets a 422 rather than a 500. `POST /feedback` rejects such text in any field this way.

### HTTP status codes

| Status | Description |
|--------|-------------|
| 200 | Success |
| 400 | Bad request (invalid parameters) |
| 404 | Resource not found |
| 422 | Request body or parameters failed schema validation |
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

**Arming and rolling back** are the same procedure with one flag changed. Several
things make it more than two commands, and each of them has bitten a comparable
rollout somewhere. The whole block runs in a fail-fast subshell: half of these
commands feed the next one, so continuing after a failed lookup would mutate the
service from an empty variable and still print a plausible-looking health line
at the end.

```bash
(
set -euo pipefail
SERVICE=anyplot-api
LOC="--project=anyplot --region=europe-west4"

# 0. Do not race the deploy pipeline. A build that ALREADY deployed its
#    candidate promotes it at the end — and that revision was cloned from the
#    pre-arm template, so the promote silently undoes the arm (its own smoke
#    accepts `off`, by design). A build that starts AFTER this block inherits
#    the binding, because the deploy is additive (`--update-secrets`). So the
#    dangerous window is exactly "a build already in flight".
gcloud builds list --project=anyplot --region=europe-west4 --ongoing --format="value(id)" | grep -q . && {
  echo "a Cloud Build is in flight; wait for it to finish (or fail) before arming."
  exit 1
}

# 1. Build the new revision from the image that is SERVING, not from whatever
#    is latest. `services update` clones the service's latest template, and the
#    deploy pipeline deliberately leaves each build's candidate there — smoked
#    and unpromoted on a good build, and still there on a bad one, because a
#    failed smoke skips the promote and nothing cleans it up. Pinning the image
#    means the arm/disarm revision serves what is serving now, whatever state
#    the pipeline is in; naming the revision alone would not have.
read -r SERVING LATEST <<<"$(gcloud run services describe "$SERVICE" $LOC --format=json \
  | python3 -c "import json,sys; d=json.load(sys.stdin); \
      t=[x for x in d['status']['traffic'] if x.get('percent')==100]; \
      print(t[0]['revisionName'], d['status']['latestReadyRevisionName'])")"
IMAGE=$(gcloud run revisions describe "$SERVING" $LOC --format="value(spec.containers[0].image)")
test -n "$SERVING" && test -n "$IMAGE" || { echo "could not resolve the serving revision or its image"; exit 1; }

# A mismatch is a WARNING, never a stop: it is normal right after a deploy, and
# it is permanent after a failed smoke — a hard refusal here would make the
# emergency rollback unavailable exactly when it is needed. With the image
# pinned, the remaining risk is only that the latest template carries a config
# change nobody promoted; check the revision afterwards if this fires.
test "$SERVING" = "$LATEST" || echo "note: latest ($LATEST) is not serving ($SERVING) — image pinned to the serving one"

# 2. Pin the secret to a NUMBER, never `:latest`. Cloud Run resolves a
#    secret-backed variable when each instance starts, so with `:latest` a new
#    secret version reaches new instances while older ones keep the old value —
#    and since the edge stamps exactly one value, the difference shows up as
#    intermittent 403s inside a single revision.
VERSION=$(gcloud secrets versions list ORIGIN_SECRET --project=anyplot \
  --filter="state=ENABLED" --sort-by=~createTime --limit=1 --format="value(name)")
test -n "$VERSION" || { echo "no ENABLED version of ORIGIN_SECRET"; exit 1; }

# 3. Update, then promote BY NAME. The service pins traffic to a named
#    revision, so the update alone serves nothing; and `--to-latest` here would
#    hand traffic to whatever the pipeline last built.
SUFFIX="arm-$(date -u +%Y%m%d%H%M)"
gcloud run services update "$SERVICE" $LOC --image="$IMAGE" \
  --update-secrets="ORIGIN_SECRET=ORIGIN_SECRET:$VERSION" --revision-suffix="$SUFFIX"
gcloud run services update-traffic "$SERVICE" $LOC --to-revisions="$SERVICE-$SUFFIX=100"

# 4. Confirm the result. Not optional: step 0 only narrows the race, and this
#    is what catches a build that promoted over the arm anyway — the verdict
#    would read `off` on a path that carries the header. If it does, that
#    promote reverted the arm; re-run the whole block.
curl -s "https://api.anyplot.ai/health"
gcloud run services describe "$SERVICE" $LOC --format="value(status.traffic)"
)
```

**Rolling back** is its own block, not the one above with a flag swapped. It has
to run in the worst state the service can be in — which includes the secret
having been disabled or deleted during the incident, so it must not look the
secret up at all. Nothing here depends on anything but the currently serving
revision:

```bash
(
set -euo pipefail
SERVICE=anyplot-api
LOC="--project=anyplot --region=europe-west4"

# No in-flight check and no secret lookup: when the gate is the outage, waiting
# for a build is the wrong trade, and step 2 above would abort here on a
# disabled version — leaving the gate armed at the moment it must come off.
SERVING=$(gcloud run services describe "$SERVICE" $LOC --format=json \
  | python3 -c "import json,sys; d=json.load(sys.stdin); \
      print(next(x['revisionName'] for x in d['status']['traffic'] if x.get('percent')==100))")
IMAGE=$(gcloud run revisions describe "$SERVING" $LOC --format="value(spec.containers[0].image)")
test -n "$IMAGE" || { echo "could not resolve the serving image"; exit 1; }

SUFFIX="disarm-$(date -u +%Y%m%d%H%M)"
gcloud run services update "$SERVICE" $LOC --image="$IMAGE" \
  --remove-secrets=ORIGIN_SECRET --revision-suffix="$SUFFIX"
gcloud run services update-traffic "$SERVICE" $LOC --to-revisions="$SERVICE-$SUFFIX=100"

curl -s "https://api.anyplot.ai/health"   # expect "off" or "off-seen"
)
```

Removing the Worker's binding is **not** a rollback — while the service is armed
that takes the apex route down rather than freeing it. Roll back here first.

**Rotating the secret** means changing every side that must agree, and the gate
accepts exactly one value — so there is no overlap window. Roll back first,
rotate the Secret Manager version, the Transform Rule, the Worker binding **and
the `ORIGIN_SECRET` repository secret** in GitHub Actions settings, then arm
again on the new version number. The gate is off in between, which is the
documented safe state; `/health` shows `off-seen` throughout, and `ok` when the
new value is live on both sides.

The repository secret is the copy that is easiest to forget, because nothing
about it lives in the Google Cloud console: `sync-postgres.yml` sends it as
`X-Origin-Secret` on the cache flush, which goes to the direct `run.app` URL and
therefore never passes the edge. Skip it in a rotation and the sync's last step
starts failing with `Cache invalidation was refused by the origin gate (HTTP
403)` — loudly, by design, but a day after the rotation rather than during it.

**Exempt paths** — exact matches, no prefixes, and only this one:

| Path | Why |
|---|---|
| `/health` | the deploy smoke probes the candidate revision on its `run.app` tag URL, which never passes the edge |

`/debug/cache/invalidate` was the second until `sync-postgres.yml` learned to
send `X-Origin-Secret` itself, out of the `ORIGIN_SECRET` repository secret. It
still posts to the direct `run.app` URL — Cloudflare's bot challenge answers an
unauthenticated curl POST against `api.anyplot.ai` with a 403 HTML page — but it
now arrives carrying the header the edge would have stamped, so it needs no hole
in the gate. Its own `CACHE_INVALIDATE_TOKEN` (constant-time compared, 503 when
unconfigured) is the second lock behind the first. If the repository secret goes
missing, that step fails with a message naming it rather than letting the flush
go quietly stale.

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

**The second door, and where it is.** This gate protects the API service. The
app service (`anyplot-app`) also stands with `ingress=all`, and its nginx relays
a crawler user agent through `@seo_proxy` to `https://api.anyplot.ai`, where the
edge stamps the header legitimately — so a caller who sent a crawler user agent
to the app's raw `*.run.app` URL used to reach the prerendered render and its DB
queries, and this gate could not tell: the request it saw really did come
through the edge. That was never a hole in this one. It is a second door on a
second service, and it has a gate of its own now —
`app/origin-gate.conf.template`, the same secret and the same five verdicts,
reported on the app's `/_health` as `X-Origin-Gate`. Its rollout, the hostnames
it covers and the callers that reach that origin without the edge are in
[`infra/cloudflare/README.md`](../../infra/cloudflare/README.md#the-sites-own-origin-anyplot-app).

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

**Exposed headers**: `Mcp-Session-Id` (MCP sessions) and `X-Request-Id` (the
agent chat's reference id).

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
