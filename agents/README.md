# Agent network

This directory holds the anyplot agent network: the service that lets an admin paste their own data on a plot page and get that plot adapted, rendered and reviewed ("Use with my data"). It is built with [Google ADK](https://adk.dev) 2.11. The design, including every contract and guardrail, is in [Agent network design](../docs/concepts/agent-network.md).

## What is built

The runtime core runs locally: the agents, the plot pipeline, the guardrail plugins, the render layer, the private `/v1` service with its run queue, and the theme toggle. The renderer service `anyplot-renderer` (`renderer/`), which runs the adapted code in Cloud Run sandboxes, and the `remote` backend that calls it are built, with the renderer's image and Cloud Build config, but not deployed yet (status of 2026-10-10). The model-regression harness, the 120 synthetic spike-X cases, the blind two-run review gallery and the catalogue eligibility sweep are built (see [Run the regression harness](#run-the-regression-harness)), and the Claude Haiku 5.5 baseline from the first spike-X run of 2026-10-10 is committed (`evals/baselines/claude-haiku-5-5.json`); the Gemini baseline is not. The chat page that uses the service through the API's `/debug/agent` routes is in the app (`app/src/pages/AgentChatPage.tsx`, built with `VITE_ENABLE_AGENT_CHAT=true`). Not built yet: the agents image, the deploy of either service, the scope evalset, and the `agents-eval.yml` workflow.

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
| `evals/matrix.py` | The regression harness: runs eval cases through `/v1` in process and writes the report, the Markdown summary, the diff against a baseline and the review galleries |
| `evals/make_fixtures.py` | The seeded generator of the 120 synthetic spike-X cases |
| `evals/cases.py`, `evals/pricing.py`, `evals/report.py` | Case loading and selection, list prices, and the summary, diff and gallery code; `report.py` also merges two runs into one blind gallery and scores its export |
| `evals/eligibility.py` | The model-free sweep of the catalogue's matplotlib and seaborn files: eligible, coupled and blocked pairs, and why |
| `evals/fixtures/cases/` | The eval cases: 120 generated (`<spec>-<library>-<perturbation>`) and the hand-written `scatter-basic-matplotlib` and `bar-grouped-seaborn` ([fixtures README](evals/fixtures/README.md)) |
| `evals/baselines/` | Committed baseline reports, one per model ([baselines README](evals/baselines/README.md)) |

The unit tests are in `tests/unit/agents/`; `tests/unit/agents/runtime/` drives a full "Create plot" through `/v1` with a fake renderer and scripted models for both providers, and `tests/unit/agents/evals/` runs the harness the same way.

`evals/` has no `__init__.py` on purpose: `adk web agents` lists every subdirectory of `agents/` that holds one as an agent, so `evals` stays an implicit namespace package, which `python -m agents.evals.matrix` imports all the same.

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

The service needs the header `X-Anyplot-User` on every `/v1` route; outside `ENVIRONMENT=development` it also requires the IAM-forwarded ID token (`AGENT_SERVICE_URLS`, `AGENT_ALLOWED_CALLERS`). To drive it from the plot page, run the API in front of it as described under [Drive the chat page](#drive-the-chat-page).

At the defaults only one run may start a minute, so a second "Create plot" within a minute waits in the run queue and the stream shows `status` events with `step: "queued"`. To iterate faster on your own machine, export `AGENT_RUNS_PER_MINUTE=60`. The theme toggle (`POST /v1/sessions/{sid}/versions/{version}/render {"theme": "dark"}`) never waits in the queue.

### Drive the chat page

The chat page is the app's `/debug/agent?spec=&library=&language=`. Build or serve the app with `VITE_ENABLE_AGENT_CHAT=true`; local development shows it without an admin sign-in, and the plot page then shows the `.adapt()` button for eligible pairs.

- **Against this service:** the API's agent routes need all three of `AGENT_ENABLED`, `AGENT_SERVICE_URL` and `AGENT_USER_ID_KEY`, or every route answers `404 not_enabled`; and the admin gate has no development bypass, so you sign in with an admin token:

  1. Run the service as above.
  2. In a second terminal, run the API with the agent routes switched on and an admin token of your choice:

     ```bash
     AGENT_ENABLED=true AGENT_SERVICE_URL=http://localhost:8001 AGENT_USER_ID_KEY=dev-key \
       ADMIN_TOKEN=<token> uv run uvicorn api.main:app --reload --port 8000
     ```

  3. In a third terminal, start the app with `cd app && VITE_ENABLE_AGENT_CHAT=true yarn dev`.
  4. Open `http://localhost:3000/debug`, enter `<token>`, and open the chat page in the same tab: the token lives in that tab's session storage.

- **Without any backend:** the mock BFF serves the documented `/debug/agent/*` routes, a scripted stream (two queue positions, the pipeline steps, a plot and a reply) and PNGs drawn from the pasted data, plus the catalogue routes the plot page needs for `scatter-basic` and `line-multi` (a series family `y1, y2, ...`). It listens on the loopback interface only, needs no sign-in, touches no database and calls no model:

  1. Start the mock:

     ```bash
     node app/scripts/agent-bff-mock.mjs
     ```

  2. In a second terminal, start the app against it:

     ```bash
     cd app && VITE_ENABLE_AGENT_CHAT=true VITE_API_URL=http://localhost:8010 \
       VITE_DEBUG_API_URL=http://localhost:8010 yarn dev
     ```

  3. Open `http://localhost:3000/scatter-basic/python/matplotlib` and select the `.adapt()` button, or open `http://localhost:3000/debug/agent?spec=scatter-basic&library=matplotlib&language=python` directly. Paste `agents/evals/fixtures/cases/scatter-basic-matplotlib/data.csv` as your data.

  The header of `app/scripts/agent-bff-mock.mjs` lists the scripted replies (a refusal, a capacity error, a question, a refinement with a repair round) and the timing variables.

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

## Run the regression harness

The harness (`evals/matrix.py`) runs eval cases through the real `/v1` flow in process: the same plugins, run queue, dataset judge, pipeline and gates as a user's request, with the models the settings name. Use it to compare a newer model version, the other provider's arm, or a prompt or validator change against the pinned baseline. Every run calls the configured models and spends tokens; the harness estimates the cost at list price as it goes.

### Before you begin

1. Complete steps 1 and 2 of [Before you begin](#before-you-begin): the dependencies and Application Default Credentials. The harness reads no `.env` file. With the `remote` or `local` renderer it runs as `ENVIRONMENT=development` whatever your shell exported (only development accepts your renderer token and the `local` backend); with `fake` it keeps your `ENVIRONMENT` and sets `development` when it is unset.
2. Choose a renderer with `--renderer`:
   - `remote` renders on the deployed `anyplot-renderer` service; pass its URL with `--render-url` (the harness sets `AGENT_RENDER_URL`). The `remote` backend comes with the renderer change (`agents/renderer/`); in a checkout without it, the harness stops with exit code 2.
   - `local` renders in Docker with the image in `AGENT_RENDER_IMAGE`.
   - `fake` returns fixture PNGs and runs no plot code. The models are still real, so a `fake` run costs as much as any other; use it to check everything except the render.
3. For `remote`, give the harness a token the renderer accepts. Your account needs `roles/run.invoker` on `anyplot-renderer` and must be listed in its `RENDERER_ALLOWED_CALLERS`, and the gcloud CLI's client id `32555940559.apps.googleusercontent.com` must be in its `RENDERER_AUDIENCES` (see "Render through the deployed renderer" above). Then either:
   - pass `--gcloud-token` (recommended): the harness runs `gcloud auth print-identity-token` before the first case and again whenever the token is within 10 minutes of expiry, so a full run outlasts the token's hour. The token stays in the harness's own environment and is never printed; or
   - export `AGENT_RENDER_TOKEN=$(gcloud auth print-identity-token)` yourself. That token is valid for one hour; the harness prints how long it has left, and a run that outlasts it stops with exit code 4.

Before the first case the harness renders the catalogue file of the first case of each library once (a preflight, no model call). A renderer that is unreachable, refuses your token or lacks a library ends the run with exit code 2 before any token is spent; `--no-preflight` skips the check.

### Run the smoke set or the full matrix

- The smoke set is 12 cases (tag `smoke`): one generated case per spec, cycling through the perturbations and both libraries, plus the two hand-written cases.

  ```bash
  uv run --extra agents python -m agents.evals.matrix --cases smoke \
    --renderer remote --render-url https://RENDERER_URL --gcloud-token
  ```

- The full matrix is all 122 cases. Cap the spend with `--budget-usd`:

  ```bash
  uv run --extra agents python -m agents.evals.matrix --cases full --budget-usd 4 \
    --renderer remote --render-url https://RENDERER_URL --gcloud-token
  ```

- To run the Gemini arm, add `--provider gemini`; it selects `gemini-3.8-flash` with the judge on `gemini-3.5-flash-lite`. `--model` alone implies its provider, and `--judge-model` and `--location` override the rest.
- To run a subset, pass comma-separated globs over case ids, for example `--cases "*-seaborn-*"` or `--cases "pie-basic-*,box-basic-*"`.

| Flag | Meaning |
|---|---|
| `--provider`, `--model`, `--judge-model`, `--location` | The candidate settings, passed only to this process as `AGENT_*` variables |
| `--renderer`, `--render-url` | The render backend (`remote`, `local` or `fake`) and the remote renderer's URL |
| `--gcloud-token` | Mint the renderer token with `gcloud auth print-identity-token` and renew it before it expires (`remote` only) |
| `--no-preflight` | Skip the preflight render before the first case |
| `--cases` | `smoke` (default), `full`, or comma-separated globs over case ids |
| `--repeats N` | Runs per case, to see how stable a result is |
| `--budget-usd X` | Stop before a case that could take the estimated list-price cost past X (the spend so far plus the costliest case so far), or once the cost has passed X (exit code 3) |
| `--out DIR` | Output directory, `agents/evals/reports/` by default (git-ignored) |
| `--baseline FILE`, `--no-baseline` | The report to compare with; by default `evals/baselines/claude-haiku-5-5.json` when it exists |
| `--tolerance F` | The pass-rate drop that counts as a regression, 0.05 (5 percentage points) by default |
| `--save-baseline` | Also write the report as `evals/baselines/<model>.json`; refused for a run that stopped early, holds promoted cases, or has a run that ended in an error |
| `--seed N`, `--gallery-size N` | The gallery's random sample: its seed (0) and size (30) |
| `--runs-per-minute N` | The run queue's start rate for this process, 60 by default |

For its own process the harness lifts the run queue's start rate and the service-wide daily token budget, and gives every case its own user id, so the per-user daily budgets never trip. The per-request limits (12 LLM calls, 80,000 tokens, the deadlines) stay at their production values.

### Read the results

A run writes to `--out`:

- `<date>-<model>.json`: the report. It holds the stamp (provider, models, location, renderer, ADK version, commit, prompt hashes, prices), the summary, and one record per case and repeat: status and reason, the exception class when the pipeline ended in an error, attempts, gate failures by gate, validator rejections, edit-apply failures, the reviewer's verdict, LLM calls by agent, tokens by kind, `model_version`, the cost at list price, time to the first event, end-to-end time and render times. The date is the UTC date.
- `<date>-<model>.md`: the Markdown summary, with pass rates by perturbation, library and spec, and the diff against the baseline.
- `renders/`, `gallery.html` and `gallery-all.html`: the shipped PNG of every run, a review page with 30 renders sampled at random from the runs that passed, and a list of every run. On the review page, tick **Accept** or **Reject** for each plot and select **Export judgements as JSON**; the export counts your accepts and rejects. The page never names the model, but its folder may, so compare two arms with the blind gallery instead (see [Run spike X](#run-spike-x)). The next run in the same directory rewrites both pages, so give each run its own `--out` when you want to keep its gallery.

The rates mean the following:

- **Pass rate**: runs that shipped a render (`ok` or `needs_attention`) that passed every deterministic gate: the host gates without a padded canvas, and no ADAPTATION validator finding. Every run counts, so a run that crashed in the harness is a run that did not pass. The reviewer and the advisory probe gates do not decide a pass; your gallery judgement does.
- **Accept-match rate**: runs whose outcome (`ok` counts as accepted) matches the case's `expected` value; cases that expect `unknown` are left out.
- **Cost per successful plot**: the whole run's list-price cost divided by the passed runs; the summary also gives the median cost of a passed run.

The diff against a baseline compares the cases both reports hold, with every repeat of each, so a smoke run is measured against the same 12 cases of a full baseline. Each report's pass rate over all of its own runs is an extra row. With 12 cases one run is 8.3 percentage points, more than the 5-point tolerance, so a single case that flips from pass to fail is a regression on the smoke set.

The exit code is one of the following:

| Code | Meaning |
|---|---|
| 0 | The run finished |
| 1 | The run did not hold: its pass rate on the shared cases fell more than the tolerance below the baseline's, or a run crashed in the harness |
| 2 | A setup error: settings, the renderer or its token, the preflight render, an unpriced model, or no matching case |
| 3 | `--budget-usd` stopped the run |
| 4 | An outage stopped the run: the renderer became unavailable (the pipeline's `RendererUnavailable`), or 3 runs in a row ended in an error |

Ctrl-C, exit codes 3 and 4 all write the partial report before the harness stops.

### Run spike X

Spike X is the go or no-go for phase 1: 10 specs times matplotlib and seaborn times 6 datasets (renamed, x10, n=12, n=5000, date, decimal comma) on both arms, under $25 in total. The full matrix is those 120 generated cases plus the two hand-written ones. At list price a full run is estimated at about $1 on the Claude arm and $10 to $15 on the Gemini arm. The budgets below leave $3 of the $25 for headroom, because a budget is checked between cases.

1. Count the catalogue files the network can adapt at all (no model call, about 10 seconds). The report lists the eligible, coupled and blocked pairs per library, the blocked ones by reason (SECURITY findings by rule id, a missing `THEME` block, a savefig target other than `f"plot-{THEME}.png"`, the map specs):

   ```bash
   uv run --extra agents python -m agents.evals.eligibility --out agents/evals/reports/spike-x
   ```

2. Run the Claude arm in its own directory and write the first baseline:

   ```bash
   uv run --extra agents python -m agents.evals.matrix --provider anthropic-vertex --location eu \
     --cases full --renderer remote --render-url https://RENDERER_URL --gcloud-token --budget-usd 4 \
     --out agents/evals/reports/spike-x-claude --no-baseline --save-baseline
   ```

3. Run the Gemini arm and write its baseline. It compares itself with the Claude baseline from step 2, so exit code 1 here means "Gemini passed more than 5 points less often than Claude", which is a result, not a failed run:

   ```bash
   uv run --extra agents python -m agents.evals.matrix --provider gemini --location eu \
     --cases full --renderer remote --render-url https://RENDERER_URL --gcloud-token --budget-usd 18 \
     --out agents/evals/reports/spike-x-gemini --save-baseline
   ```

4. Merge both runs into one blind gallery. It samples 30 case runs that passed in both arms and shows both renders of each, shuffled, without saying which arm made which; the key goes into a separate file:

   ```bash
   uv run --extra agents python -m agents.evals.report blind \
     --report agents/evals/reports/spike-x-claude/<date>-claude-haiku-5-5.json \
     --report agents/evals/reports/spike-x-gemini/<date>-gemini-3.8-flash.json \
     --out agents/evals/reports/spike-x-blind
   ```

5. Open `agents/evals/reports/spike-x-blind/blind.html`, judge every render, and export the judgements. Do not open the two arms' own galleries or `blind-key.json` before you have judged.
6. Score the export per arm:

   ```bash
   uv run --extra agents python -m agents.evals.report score \
     --key agents/evals/reports/spike-x-blind/blind-key.json ~/Downloads/judgements-<id>.json
   ```

7. Check the exit criteria in the design: at least 80 % pass after at most one repair, an owner acceptance of at least 75 % on the sample, and a median cost of at most $0.05 per successful plot.
8. Commit `agents/evals/baselines/claude-haiku-5-5.json` and `gemini-3.8-flash.json` once you accept the runs. From then on, `tests/unit/agents/evals/test_baselines.py` requires a baseline for the pinned model. If `--save-baseline` refused a run because a case ended in an error, fix the cause and rerun that arm.

### Regenerate the fixtures

The 120 generated cases come from `evals/make_fixtures.py`. After you change it, or when a NumPy upgrade changes a random stream, rerun it and commit the result:

```bash
uv run --extra agents python -m agents.evals.make_fixtures
uv run --extra agents python -m agents.evals.make_fixtures --check   # exit 1 when a committed file is stale
```
