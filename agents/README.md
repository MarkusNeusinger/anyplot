# Agent network

This directory holds the anyplot agent network: the service that lets an admin paste their own data on a plot page and get that plot adapted, rendered and reviewed ("Use with my data"). It is built with [Google ADK](https://adk.dev) 2.11. The design, including every contract and guardrail, is in [Agent network design](../docs/concepts/agent-network.md).

## What is built

The runtime core runs locally: the agents, the plot pipeline, the guardrail plugins, the render layer, the private `/v1` service with its run queue, and the theme toggle. The renderer service `anyplot-renderer` (`renderer/`), which runs the adapted code in Cloud Run sandboxes, and the `remote` backend that calls it are built, with the renderer's image and Cloud Build config, but not deployed yet (status of 2026-10-10). Not built yet: the agents image, the deploy of the agents service, the regression harness and the evals.

The model is **Claude Haiku 5.5 on Vertex AI** (`claude-haiku-5-5`) by default. **Gemini 3.8 Flash** is the second arm: set `AGENT_PROVIDER=gemini` together with Gemini model ids, so the two can be compared on price and quality later. Every agent and the scope judge run on the configured provider.

## What lives here

| Path | Contents |
|---|---|
| `main.py` | The `anyplot-agents` FastAPI service: the `/v1` routes the BFF (`api/routers/agent.py`) calls, the caller check, the run registry behind `409 run_active`, in-memory session and artifact services, and the idle sweeper |
| `stream.py` | The `anyplot/1` stream translator: ADK events in, sanitised `ready`, `status` (including `queued`), `message`, `plot`, `refusal`, `error` and `done` events out |
| `anyplot/run_queue.py` | The run queue in front of every `/messages` turn: one run in flight, one start a minute, a 600-second maximum wait, a `premium` lane that nothing sets yet |
| `anyplot/theme_render.py` | The theme toggle: renders another theme of a finished version from its stored run form, behind waiting pipeline renders, with no model call |
| `anyplot/agent.py` | The root agent `anyplot`, the `ALL_AGENTS` registry and `app` (the ADK `App` with its plugins), which `adk web` loads |
| `anyplot/models.py` | The only place that builds a model or a model client: `make_model`, `make_content_config` and `make_judge_client`, for Claude on Vertex AI and for Gemini |
| `anyplot/policy.py` | Composes each agent's static instruction from `anyplot/prompts/` and the catalogue's prompt sources, read verbatim; the fixed refusals; the data fences |
| `anyplot/prompts/` | `root.md`, `adapter.md`, `reviewer.md`, `scope_judge.md`, `data_judge.md` and `refusals.yaml` (English and German) |
| `anyplot/pipeline.py` | The `plot_pipeline` node: adapt, check, render, review once, repair once, always a `PlotResult` |
| `anyplot/sub_agents/` | One single-turn adapter per enabled library and the tool-less reviewer |
| `anyplot/tools/session.py` | The root's tools: `get_dataset_profile`, `get_spec_brief`, `get_current_code`, `set_bindings` and the `plot_pipeline` workflow |
| `anyplot/plugins/` | `ScopeGuardPlugin`, `BudgetPlugin`, `ToolSafetyPlugin` and the request ledger they share |
| `anyplot/render/` | The render contract, the probe harness, the host gates (R1-R3, advisory G3/G5/G7/G8), PNG hardening, the render store, the `remote` (the renderer service, phase 1), `local`, `fake` and `sandbox` (an unused in-process stub) backends, and `serial.py`, the one render semaphore in front of every backend |
| `renderer/` | The `anyplot-renderer` service: `main.py` (`POST /render`, `GET /status`, one render slot), `executor.py` (one `sandbox do` per theme with the kill path, the byte watchdog and the launcher retry), `auth.py` (the caller check), `settings.py` (`RENDERER_*`), `wire.py` (the JSON contract the `remote` backend shares), `Dockerfile` and `cloudbuild.yaml`. No ADK import and no `__init__.py`, so `adk web agents` does not list it as an agent |
| `anyplot/opening.py`, `session_state.py`, `services.py`, `briefs.py` | Opening a session and taking in a dataset, the server-set session state, the process-wide stores, and the spec and dataset briefs |
| `anyplot/dev_fixture.py` | The development-only session seed from an eval fixture case |
| `anyplot/settings.py` | `AgentSettings`, read from `AGENT_*` environment variables |
| `anyplot/schemas.py` | The pipeline contracts with their size limits |
| `anyplot/data/`, `anyplot/code/` | The deterministic data and code layers, without ADK |
| `evals/fixtures/cases/` | Fixture cases: `scatter-basic-matplotlib` and `bar-grouped-seaborn` |

The unit tests are in `tests/unit/agents/`; `tests/unit/agents/runtime/` drives a full "Create plot" through `/v1` with a fake renderer and scripted models for both providers.

Three rules hold for everything here:

- **Relative imports inside `anyplot/`.** ADK's loader imports the package as the top-level module `anyplot`, while the service imports it as `agents.anyplot`. Absolute imports of `core` and of `agents.renderer.wire` (no ADK, no `anyplot` import) are fine. The other direction is closed: nothing in `renderer/` imports `agents.anyplot`, whose package import loads ADK.
- **Models only through `models.py`.** Model ids, the project and the location come from `AgentSettings`; the settings refuse `-latest` aliases, regional locations such as `europe-west4`, and model ids that do not match the provider.
- **No content in logs.** The attribution log carries ids, counts and verdicts, never message text, code or data; the service switches span content capture off.

## Settings

| Variable | Default | Meaning |
|---|---|---|
| `AGENT_PROVIDER` | `anthropic-vertex` | `anthropic-vertex` (Claude on Vertex AI) or `gemini` |
| `AGENT_MODEL` | `claude-haiku-5-5` | Model of every agent; a `gemini-` id, or for `anthropic-vertex` a model in `CLAUDE_MODELS` (forced tool use with thinking disabled) |
| `AGENT_JUDGE_MODEL` | `claude-haiku-5-5` | Model of the scope and dataset judge; same rule |
| `AGENT_LOCATION` | `eu` | Vertex AI location: `eu`, `us` or `global` |
| `AGENT_PROJECT`, else `GOOGLE_CLOUD_PROJECT` | `anyplot` | Project that serves and bills the model calls |
| `AGENT_LIBRARIES` | `matplotlib,seaborn` | Enabled libraries; each needs a phase-1 runtime (`matplotlib`, `seaborn`), others are refused at startup |
| `AGENT_RENDERER` | `remote` | `remote` (the renderer service), `local` (Docker, development only), `fake` (fixture PNGs, development and test only) or `sandbox` (an in-process stub, not used in phase 1) |
| `AGENT_RENDER_URL` | unset | The renderer service URL; the `remote` backend refuses to start without it; `http://` only in development and test |
| `AGENT_RENDER_TOKEN` | unset | Development only: an ID token for the renderer; without it the backend mints one (see [Render through the deployed renderer](#render-through-the-deployed-renderer)) |
| `AGENT_RENDER_IMAGE` | `anyplot-renderer:dev` | Image the `local` renderer runs, built from `renderer/Dockerfile` |
| `AGENT_RENDER_CONCURRENCY` | `1` | Theme renders at the same time, for every backend (`render/serial.py`); serial, because one 4 GiB instance holds one sandbox safely (spikes S and S2) |
| `AGENT_RUN_CONCURRENCY` | `1` | Pipeline runs (whole `/messages` turns) in flight; the run queue holds the rest |
| `AGENT_RUNS_PER_MINUTE` | `1` | Runs that may start within any 60 seconds (a sliding window) |
| `AGENT_QUEUE_MAX_WAIT_S` | `600` | Longest wait in the run queue, after which the run ends with `capacity`; the queue holds rate x wait / 60 entries (10) and answers `503 capacity` beyond that. Through the BFF the whole turn, this wait included, ends by `AGENT_TURN_MAX_S` (890 s, see `docs/reference/api.md`), which the full wait plus the 180 s run fits into |
| `AGENT_MAX_LLM_CALLS` | `12` | LLM calls per request |
| `AGENT_REQUEST_TOKEN_BUDGET` | `80000` | Tokens per request |
| `AGENT_DAILY_TOKEN_BUDGET` | `1000000` | Tokens per user and day |
| `AGENT_DAILY_PIPELINE_RUNS` | `40` | Pipeline runs per user and day |
| `AGENT_GLOBAL_DAILY_TOKEN_BUDGET` | `3000000` | Tokens per day for the whole service |
| `AGENT_RENDER_TIMEOUT_S` | `60` | Seconds per theme render |
| `AGENT_REQUEST_DEADLINE_S` | `180` | Hard request deadline |
| `AGENT_SOFT_DEADLINE_S` | `140` | Soft deadline inside the pipeline |
| `AGENT_JUDGE_TIMEOUT_S` | `4` | Budget of one judge verdict, its one retry included |
| `AGENT_SESSION_IDLE_S` | `3600` | Idle time after which the sweeper drops a session |
| `AGENT_ALLOWED_CALLERS` | empty | Service-account emails allowed to call `/v1` outside development |
| `AGENT_SERVICE_URLS` | empty | ID-token audiences accepted on `/v1` outside development |
| `AGENT_DEV_FIXTURE` | unset | Development only: a fixture case id that seeds every new session |
| `ENVIRONMENT` | `production` | Shared with the API; `local` rendering, the fixture seed and skipping the caller check need `development`, which is refused on Cloud Run |

## Run it locally

### Before you begin

1. Install the dependencies, including the two plotting libraries the renderer uses:

   ```bash
   uv sync --extra agents --extra test --extra lib-matplotlib --extra lib-seaborn
   ```

   Never install `openai-agents` into this environment: it ships a top-level `agents` module that shadows this package.

2. Authenticate to Google Cloud with your own account (Application Default Credentials):

   ```bash
   gcloud auth application-default login
   ```

3. Export the environment for Vertex AI on the `eu` multi-region:

   ```bash
   export ENVIRONMENT=development GOOGLE_GENAI_USE_ENTERPRISE=TRUE \
          GOOGLE_CLOUD_PROJECT=anyplot GOOGLE_CLOUD_LOCATION=eu AGENT_LOCATION=eu \
          AGENT_PROVIDER=anthropic-vertex AGENT_MODEL=claude-haiku-5-5 AGENT_JUDGE_MODEL=claude-haiku-5-5
   ```

   For the Gemini arm, set `AGENT_PROVIDER=gemini AGENT_MODEL=gemini-3.8-flash AGENT_JUDGE_MODEL=gemini-3.5-flash-lite` instead.

4. Choose a renderer:

   - `AGENT_RENDERER=remote` renders through the deployed renderer service; see [Render through the deployed renderer](#render-through-the-deployed-renderer).
   - `AGENT_RENDERER=local` renders in Docker with the image in `AGENT_RENDER_IMAGE`. Build it once from the repository root with `docker build -f agents/renderer/Dockerfile -t anyplot-renderer:dev .`; the local backend mounts the harness from your checkout.
   - `AGENT_RENDERER=fake` returns fixture PNGs and runs no code.

### Try the agents in ADK's development UI

1. Seed every new session with a fixture case, so there is a plot, a dataset and bindings to work with:

   ```bash
   export AGENT_DEV_FIXTURE=scatter-basic-matplotlib AGENT_RENDERER=fake ADK_DISABLE_LOAD_DOTENV=1
   ```

   `ADK_DISABLE_LOAD_DOTENV=1` matters: `adk web` otherwise walks up from `agents/anyplot/` and loads the first `.env` it finds, which is the repository's root `.env` with production values.

2. Start the development UI with in-memory sessions and artifacts:

   ```bash
   uv run --extra agents adk web agents --port 8002 --session_service_uri memory:// --artifact_service_uri memory://
   ```

3. Open `http://localhost:8002`, choose `anyplot`, and send "Create the plot".

`adk web` and `adk api_server` are unauthenticated and let the client choose the user id, so run them only on your own machine. Every message costs model calls: a "Create plot" is about four (root twice, the adapter, the reviewer) plus one judge call for free text. Runs that `adk web` starts bypass the run queue, which sits in the `/v1` service: the rate and concurrency limits apply only to the service. Their renders are still serial, because every render goes through `Services.backend`, which puts the one render semaphore (`render/serial.py`) in front of the backend.

### Run the service

```bash
uv run uvicorn agents.main:app --port 8001
```

The service needs the header `X-Anyplot-User` on every `/v1` route; outside `ENVIRONMENT=development` it also requires the IAM-forwarded ID token (`AGENT_SERVICE_URLS`, `AGENT_ALLOWED_CALLERS`). To drive it from the plot page, run the API with `AGENT_ENABLED=true AGENT_SERVICE_URL=http://localhost:8001` (see `api/routers/agent.py`).

At the defaults only one run may start a minute, so a second "Create plot" within a minute waits in the run queue and the stream shows `status` events with `step: "queued"`. To iterate faster on your own machine, export `AGENT_RUNS_PER_MINUTE=60`. The theme toggle (`POST /v1/sessions/{sid}/versions/{version}/render {"theme": "dark"}`) never waits in the queue.

### Render through the deployed renderer

`adk web` and the local `/v1` service can render through the deployed `anyplot-renderer`, the same sandboxes the deployed agents service uses. The renderer accepts a token only when Cloud Run IAM lets it through (`roles/run.invoker` on the service) and its claims pass the renderer's own check: the token's `aud` in `RENDERER_AUDIENCES` and its `email` in `RENDERER_ALLOWED_CALLERS`.

1. Make sure your account has `roles/run.invoker` on `anyplot-renderer` and is listed in its `RENDERER_ALLOWED_CALLERS`, and that the OAuth client id of your token (step 3) is in its `RENDERER_AUDIENCES` (owner task 14 in the design doc).

2. Point the backend at the renderer's service URL. Cloud Run accepts a service account's token only for that URL, never for a tag URL such as the deploy's `candidate`:

   ```bash
   export AGENT_RENDERER=remote \
          AGENT_RENDER_URL=$(gcloud run services describe anyplot-renderer --region=europe-west4 --format='value(status.url)')
   ```

3. Give the backend a token. Either export one from the gcloud CLI, which spike S proved against Cloud Run IAM; it is valid for one hour, and the backend refuses an expired one with a hint:

   ```bash
   export AGENT_RENDER_TOKEN=$(gcloud auth print-identity-token)
   ```

   Or leave `AGENT_RENDER_TOKEN` unset: in development the backend then refreshes your Application Default Credentials (`gcloud auth application-default login`) and sends their ID token, renewing it before it expires. With a service-account key or an impersonated service account in `GOOGLE_APPLICATION_CREDENTIALS`, it mints a token for the renderer URL instead.

   A user's ID token cannot name an audience, so its `aud` is the OAuth client id of the tool that minted it: `32555940559.apps.googleusercontent.com` for `gcloud auth print-identity-token`, and `764086051850-6qr4p6gpi6hn506pt8ejuq83di341hur.apps.googleusercontent.com` for the Application Default Credentials of `gcloud auth application-default login`. The bootstrap lists both in the deploy's `_AUDIENCES`. Whether Cloud Run IAM accepts the Application Default Credentials token was not verified before the first deploy; the gcloud token is the proven path.

4. Start `adk web` or the service as above. A render that the renderer refuses ends the pipeline run with `failed`, reason `error`, and the backend logs the cause, such as `remote renderer: the renderer refused this caller (HTTP 403, forbidden)`.

The backend rides out a cold start: it retries a connection error or a Cloud Run front-end 429 or 5xx after 1, 3, 8 and 15 seconds, within 30 seconds, because spike S saw a renderer scaled to zero answer only after about 17 seconds. It never retries the renderer's own refusals, such as `503 busy` or `500 internal`. When you stop a run, or an answer does not come in time, the backend also posts `/render/{job_id}/cancel`, so the renderer stops the sandbox and frees its only render slot.

Never set `AGENT_RENDER_TOKEN` on a deployed service: the settings refuse it outside `ENVIRONMENT=development`, because a deployed service mints its token from the metadata server.

### Run the renderer service

The renderer runs only on Cloud Run, because `sandbox do` exists only there. On your own machine the service starts, answers `GET /status` with `"sandbox": false`, and refuses every render with `503 sandbox_unavailable`:

```bash
ENVIRONMENT=development uv run uvicorn agents.renderer.main:app --port 8003
```

Its settings are `RENDERER_*` variables, documented in `renderer/settings.py`. The defaults are the deployed limits: a 64 MiB byte budget and 10,000 files per run, a 30-second wait for the one render slot, a 1,024 MiB `MemAvailable` floor before a render and a 512 MiB floor during one (below it the watchdog kills the sandbox), and the rlimits 60 s CPU, 50 MiB per file, 1 GiB address space and 64 processes.

On Cloud Run the service also checks itself: it refuses every render with `503 volume_missing` when `/tmp/runs` is not a mount of its own of at most 1 GiB (the deploy's in-memory volume), and it ends its own process when a sandbox launcher outlives its kill, so Cloud Run starts a fresh instance instead of answering `503 stuck` until the instance goes idle. `GET /status` reports both. A caller that goes away, or a `POST /render/{job_id}/cancel`, stops the render in progress. `job_id` and the requested themes are an idempotency key: a replayed `POST /render` with the same payload joins the render in flight or gets the stored answer of a finished one, and another payload under the same key is refused with `409 job_conflict`, so the `remote` backend's retries never run a job's code twice.

The image builds from the repository root:

```bash
docker build -f agents/renderer/Dockerfile -t anyplot-renderer:dev .
```

`renderer/cloudbuild.yaml` builds, deploys a `candidate` revision without traffic, smokes it (IAM refuses an anonymous caller; with `_SMOKE_RENDER=true`, `/status` reports the launcher and the volume and a real matplotlib render goes through the candidate, with a token minted for the service URL), and promotes it. The first build also creates the service; the deploy adds the service URL to `RENDERER_AUDIENCES` itself, and `_MIN_INSTANCES=1` keeps an instance warm. CI builds the same image before merge (`.github/workflows/ci-image.yml`). The deploy flags and the owner tasks are in [Agent network design](../docs/concepts/agent-network.md#serving-and-infrastructure).

### Test

```bash
uv run pytest tests/unit/agents -q
```

`tests/unit/agents/renderer/` runs the executor against a fake `sandbox` launcher that runs the real harness with this interpreter, the service in process, and the `remote` backend against the service through httpx's ASGI transport.
