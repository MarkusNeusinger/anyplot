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

## Agent chat (admin only, switched off by default)

> **Status (2026-10-10):** the routes exist and ship switched off. The
> anyplot-agents service they call runs locally but is not deployed yet, so
> with the switch on in production every route that calls it answers
> `502 upstream` until that service is deployed. The chat page that calls
> these routes, `/debug/agent` in the app, is built only with
> `VITE_ENABLE_AGENT_CHAT=true`. Design:
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
   `AGENT_USER_ID_KEY` are set. Production deploys with `AGENT_ENABLED=false`,
   so a deploy never breaks while the configuration is incomplete.
3. **CSRF guard** on `POST`, `PUT`, and `DELETE`. The request needs the header
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
carry no request id. Upstream calls carry a Cloud Run ID token whose
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
| `POST /sessions/{sid}/dataset` | `{text}`, at most 200 KB (204,800 bytes) of UTF-8 | `{preview, profile, bindings, warnings}`; `413 too_long` above the limit |
| `PUT /sessions/{sid}/bindings` | `[{role, column}]`, at most 50 | The agents service's `{bindings, complete, missing_roles}`; `422 no_dataset` before a parse, `422 invalid` for a binding the spec roles or the columns refuse |
| `POST /sessions/{sid}/messages` | `{text}` (at most 2,000 characters) or `{"action": "create_plot"}` | An SSE stream in protocol `anyplot/1`; `413 too_long` above the limit, `409 run_active` while you have a queued or running turn or a theme render in any session, `503 capacity` when the run queue is full |
| `POST /sessions/{sid}/cancel` | None | `204`; a turn that still waits leaves the run queue |
| `POST /sessions/{sid}/versions/{version}/render` | `{"theme": "light"}` or `{"theme": "dark"}`; `version` is 0 to 999, where 0 is the latest version | `{status, reason?, artifacts}` once the render is done (see [Theme toggle](#theme-toggle)) |
| `GET /sessions/{sid}/artifacts/{name}?v=` | `name` is one of `plot-light.png`, `plot-dark.png`, `plot.py`, `data.csv` | The file, with `Cache-Control: private, no-store` and `X-Content-Type-Options: nosniff`; any other name is `404`, and so is the PNG of a theme the version has not rendered |
| `DELETE /sessions/{sid}` | None | `204` |

Validation: `spec_id` matches `^[a-z0-9-]{1,100}$`; `library` is one of the 15
supported library ids; `locale` is a language tag of at most 16 characters such
as `de` or `de-CH`; the session id matches `^[A-Za-z0-9_-]{1,128}$`; a binding
`role` matches `^[A-Za-z_][A-Za-z0-9_]{0,31}$` (the agents contract, so roles
such as `temperature_K` or `X1` pass) and its `column` has at most 64 characters. An
unknown field in a body is a `422`, and so is a body with a lone surrogate
escape such as `"\ud800"`, which UTF-8 cannot carry (`422 invalid_text`).

`POST /sessions` and `POST /sessions/{sid}/library` add the user id and a
catalogue snapshot before they forward the body, because the agents service
has no database access: `{spec_id, title, description, data_roles, notes,
code, library_version}`, with `# noqa` comments stripped from the code.

Version numbers: `{version}` in the theme toggle route and `v` on the artifact
route are the agents service's version numbers. A session's versions are
numbered from 1 in the order the service stores them, and it stores exactly
the turns whose `plot` event has the status `ok` or `needs_attention`. The
`plot` event carries no number, so a client counts those events, as the chat
page does (`app/src/hooks/useAgentSession.ts`); `0`, or no `v`, means the
latest version.

`PUT /sessions/{sid}/bindings` answers `{bindings, complete, missing_roles}`:
the stored bindings, whether every required role has a column, and the
required roles that still have none. The dataset response names only the roles
the server could bind by default, so the chat page sends those defaults back
once after a parse to learn the missing roles and show a dropdown for them.

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

### SSE protocol `anyplot/1`

| Event | Data |
|---|---|
| `ready` | `{v, run_id}` |
| `status` | `{step: "queued", position, waiting}` while the turn waits in the run queue: `position` 1 runs next, and `waiting` counts every queued turn, this one included |
| `status` | `{step, attempt}` for a pipeline step: `adapting`, `checking`, `rendering`, `reviewing`, or `repairing` |
| `message` | `{text}` |
| `plot` | `{status, reason, attempts, artifacts, changes, residual_defects}` |
| `refusal` | `{code, text}` |
| `error` | `{code, ref}`; `code` is `capacity` (also when the turn waited the run queue's maximum of 600 seconds, or the BFF's turn cap ran out while it waited), `deadline`, `guard_unavailable`, `upstream`, or `internal`; `ref` is the request id |
| `done` | `{llm_calls, tokens}` |

The BFF re-frames the upstream stream instead of forwarding it. It assembles
each complete event and drops events of any other type, events without a type,
data that is not a JSON object, and every field the table does not list, so
`error_details` and stack traces never reach the browser. An error code outside
the list becomes `internal`. The BFF stops reading after `done`.

Every turn waits in the agents service's run queue, which runs one turn at a
time and starts at most one a minute. A turn that can start at once sends no
`queued` status. Otherwise the stream sends `ready`, then a `queued` status at
once, on every change of the position or the queue length, and every 15
seconds while nothing changes, and then the turn's own events. If you are
already over the daily token budget, the stream sends `ready`,
`refusal {"code": "budget"}` and `done` at once, and the turn never enters the
queue.

While the stream is idle, a `: ping` comment arrives every 15 seconds. Every
stream ends with `done`: when the agents service is unreachable, cuts the
stream, runs past `AGENT_REQUEST_TIMEOUT_S`, or ends without `done`, the BFF
sends `error {"code": "upstream"}` and then `done {}`. Time in the run queue
does not count toward `AGENT_REQUEST_TIMEOUT_S`: every `queued` status starts
the budget again with 15 seconds on top, because the run can start up to one
`queued` status before its first event, and the first event after the wait
starts it again. No turn runs past `AGENT_TURN_MAX_S` (590 seconds), which
stays below anyplot-api's own request timeout of 600 seconds: a turn that is
still queued when its run could no longer finish inside that cap ends with
`error {"code": "capacity"}` and `done {}`, and leaves the queue before it
spends a token. At the defaults, a turn waits at most about 385 seconds
through the BFF. Errors that happen before the stream starts, such as
`413 too_long`, an upstream `409 run_active`, or `503 capacity` from a full
run queue, arrive as HTTP statuses instead.

### Agent error responses

The agent routes answer errors as `{"detail": "<code>", "ref": "<request id>"}`;
the kill switch, the CSRF guard, and the `invalid_text` check leave out `ref`,
and the admin gate and FastAPI's own `422` keep the API-wide shapes. An
upstream `4xx` or `5xx`
keeps its status. Its code is one the agents service documents (`not_eligible`,
`run_active`, `too_long`, `unparseable`, `data_refused`, `session_expired`,
`guard_unavailable` and `capacity` (both `503`, worth a retry), `no_dataset`,
`rate_limited`) or
a generic one for the status (`bad_request`, `not_found`, `conflict`,
`too_long`, `invalid`, `rate_limited`, `rejected`, `upstream`); the upstream
body is never echoed. Two cases answer `502` instead:

- `upstream_auth`: an upstream `401`, or a `403` without a documented code.
  Cloud Run IAM refused the BFF's own ID token, which is not the admin's
  session failing.
- `upstream`: the agents service is unreachable, an ID token could not be
  fetched, or a success response is not JSON.

### Configuration

| Variable | Default | Purpose |
|---|---|---|
| `AGENT_ENABLED` | `false` | The kill switch |
| `AGENT_SERVICE_URL` | Unset | Base URL of anyplot-agents, without `/v1`; also the ID-token audience |
| `AGENT_USER_ID_KEY` | Unset | HMAC key for the user id; from Secret Manager in production |
| `AGENT_REQUEST_TIMEOUT_S` | `190` | Upstream timeout, and the cap on one chat stream outside the run queue; above the agents service's 180-second deadline |
| `AGENT_TURN_MAX_S` | `590` | Hard cap on one chat turn, queue wait included; keep it below anyplot-api's Cloud Run `--timeout` (600 seconds in `api/cloudbuild.yaml`) |

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
