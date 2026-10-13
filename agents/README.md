# Agent network

This directory holds the anyplot agent network: the service that lets an admin paste their own data on a plot page and get that plot adapted, rendered and reviewed ("Use with my data"). It is built with [Google ADK](https://adk.dev) 2.11. The design, including every contract and guardrail, is in [Agent network design](../docs/concepts/agent-network.md).

## What is built

The runtime core runs locally: the agents, the plot pipeline, the guardrail plugins, the render layer, the private `/v1` service with its run queue, the theme toggle, and the footer strip on every PNG the service serves ("made with any.plot()" and "anyplot.ai/<spec-id>", see [Footer strip](../docs/concepts/agent-network.md#footer-strip)). The renderer service `anyplot-renderer` (`renderer/`), which runs the adapted code in Cloud Run sandboxes, and the `remote` backend that calls it are built, and the renderer has run in Cloud Run since 2026-10-11 (deployed by the `deploy-renderer` trigger; see [Render through the deployed renderer](#render-through-the-deployed-renderer)). The model-regression harness, the 120 synthetic spike-X cases, the 23 stress cases with their model-free static stage, the blind two-run review gallery and the catalogue eligibility sweep are built (see [Run the regression harness](#run-the-regression-harness)), and the Claude Haiku 5.5 baseline from the thinking run of 2026-10-11 on main is committed (`evals/baselines/claude-haiku-5-5.json`: 122 runs, all passed the gates, 50.8 % ended `ok`); the Gemini baseline is not. The chat page that uses the service through the API's `/debug/agent` routes is in the app (`app/src/pages/AgentChatPage.tsx`, built with `VITE_ENABLE_AGENT_CHAT=true`); since 2026-10-11 its data field also takes free text ("Hund 7 Katze 3 und Vogel 4"), which the judge model reads as a table that the user confirms before it is stored (`anyplot/data/transcribe.py`, rubric `prompts/transcriber.md`), and the flow has two steps: the user confirms the data with its bindings (`POST /v1/sessions/{sid}/dataset/confirm`) before the pipeline draws anything, and in step 1 the root's `prepare_data` tool changes the data on request from a fixed set of operations the server applies (`anyplot/data/prepare.py`, `anyplot/dataset_versions.py`), with the `done` event carrying the new version, the `summarize_data` action for the step-1 summary and `POST /v1/sessions/{sid}/dataset/undo` as the user's undo, and its `generate_data` tool computes the data from a formula the model chose, such as `sin(x)` from -pi to pi (`anyplot/data/generate.py`; a formula pasted into the data field answers `422 formula`) (see [Two steps: data first, then the plot](../docs/concepts/agent-network.md#two-steps-data-first-then-the-plot)); the prep eval scores the root's choices (see [Run the prep eval](#run-the-prep-eval)). Since 2026-10-12 a session has one language for the replies and every text in the plot, English by default whatever the browser's locale, set by the first in-scope typed message (`detected`), or for good by the chip in the chat header (`PUT /v1/sessions/{sid}/language`) or the root's `set_language` tool (`chosen`); code, comments, column names and labels from the data stay as they are (`anyplot/language.py`, see [Session language](../docs/concepts/agent-network.md#session-language)). The service's own image (`Dockerfile`) and Cloud Build config (`cloudbuild.yaml`) are built, with a CI job that builds and smokes the image before merge, and the service has run in Cloud Run since 2026-10-11, deployed by the `deploy-agents` trigger (see [Build and deploy the service](#build-and-deploy-the-service)); the API side is switched on for admins since 2026-10-11 (the user-id secret is bound, the API trigger sets the service URL and `_AGENT_ENABLED=true`). The judge-only scope eval and its cases are built, and its first full run on 2026-10-10 passed both gates (see [Run the scope eval](#run-the-scope-eval)). Real sessions reach the harness too: `evals/import_case.py` turns a saved session or a stored feedback case into an eval case, and since 2026-10-12 `evals/sync_cases.py` pulls the cases you promoted on the debug page from the private case bucket (see [Sync promoted cases from the bucket](#sync-promoted-cases-from-the-bucket)). Not built yet: the scope cases' second stage through the root, and the `agents-eval.yml` workflow.

The model is **Claude Haiku 5.5 on Vertex AI** (`claude-haiku-5-5`) by default. **Gemini 3.8 Flash** is the second arm: set `AGENT_PROVIDER=gemini` together with Gemini model ids, so the two can be compared on price and quality later. Every agent and the scope judge run on the configured provider.

## What lives here

| Path | Contents |
|---|---|
| `main.py` | The `anyplot-agents` FastAPI service: the `/v1` routes the BFF (`api/routers/agent.py`) calls, the caller check, the run registry behind `409 run_active`, in-memory session and artifact services, and the idle sweeper |
| `stream.py` | The `anyplot/1` stream translator: ADK events in, sanitised `ready`, `status` (including `queued`), `message`, `plot`, `refusal`, `error` and `done` events out |
| `Dockerfile`, `cloudbuild.yaml` | The `anyplot-agents` image (the `agents` extra, the source tree with its prompts and fonts, uid 1000) and its deploy: build, a `candidate` revision without traffic, the IAM and `/v1/status` smoke, promote. The config's header lists the owner's bootstrap steps |
| `anyplot/run_queue.py` | The run queue in front of every `/messages` turn: one run in flight, one start a minute (a turn that cannot render, because the data is unconfirmed, takes no start), a 600-second maximum wait, a `premium` lane that nothing sets yet |
| `anyplot/theme_render.py` | The theme toggle: renders another theme of a finished version from its stored run form, behind waiting pipeline renders, with no model call |
| `anyplot/agent.py` | The root agent `anyplot`, the `ALL_AGENTS` registry and `app` (the ADK `App` with its plugins), which `adk web` loads |
| `anyplot/models.py` | The only place that builds a model or a model client: `make_model`, `make_content_config` and `make_judge_client`, for Claude on Vertex AI and for Gemini |
| `anyplot/policy.py` | Composes each agent's static instruction from `anyplot/prompts/` and the catalogue's prompt sources, read verbatim; the fixed refusals; the data fences |
| `anyplot/prompts/` | `root.md`, `adapter.md`, `reviewer.md`, `scope_judge.md`, `data_judge.md`, `transcriber.md` and `refusals.yaml` (English, German, French, Spanish, Italian, Portuguese, Dutch, Polish, Chinese, Vietnamese and Russian; English for any other language) |
| `anyplot/pipeline.py` | The `plot_pipeline` node: in each round (at most `AGENT_MAX_ATTEMPTS`, two by default) adapt or repair, check, render, let the adapter proofread its render once against the rubric's technical rows (`AGENT_SELF_REVIEW`, not a repair and not a round of its own), then review with the catalogue rubric; the best-scored version ships (`AGENT_SHIP_BEST`), shown without notes at or above the ship bar (`AGENT_STATUS_BAR`); always a `PlotResult`. The flow and why: [The plot pipeline since 2026-10-13](#the-plot-pipeline-since-2026-10-13) |
| `anyplot/sub_agents/` | One single-turn adapter per enabled library and the tool-less reviewer |
| `anyplot/tools/session.py` | The root's tools: `get_dataset_profile`, `get_spec_brief`, `get_current_code`, `set_bindings`, `set_language`, `prepare_data`, `generate_data` and the `plot_pipeline` workflow |
| `anyplot/language.py` | The session language: the pattern a language name or code must match, the three sources (`default`, `detected`, `chosen`), the chip's ten common languages, the stored form (`Deutsch` is `de`) and the lookup of a refusal's language |
| `anyplot/dataset_versions.py`, `anyplot/data/prepare.py` | The step-1 data operations: the fixed operation set and `apply_operations` (pandas on the canonical CSV, one change line per operation), and the dataset versions of a session (the next version after `prepare_data` or `generate_data`, the last five kept for undo, the bindings carried over) |
| `anyplot/data/generate.py` | The formula source behind `generate_data`: the `Generate` spec (one or two variable ranges, one to ten series), the whitelist evaluator over Python's `ast` (NumPy float64, never `eval`), the canonical CSV it writes, and `looks_like_formula`, the dataset route's `422 formula` guard |
| `anyplot/plugins/` | `ScopeGuardPlugin`, `BudgetPlugin`, `ToolSafetyPlugin` and the request ledger they share |
| `anyplot/output_guard.py` | The output sanitiser of every root message and plot-event line (links, HTML and long code blocks out, at most 1,200 characters) and the reply cap the ScopeGuard runs on the root's final reply before it is stored: a reply over 1,200 characters becomes the fixed refusal, the same in every language, or is cut at 1,200 characters when the turn ran the plot pipeline |
| `anyplot/render/` | The render contract, the probe harness, the host gates (R1-R3, advisory G3/G5/G7/G8/G9/G10), PNG hardening, the render store, the `remote` (the renderer service, phase 1), `local`, `fake` and `sandbox` (an unused in-process stub) backends, `serial.py`, the one render semaphore in front of every backend, and `watermark.py`, the footer strip the artifact route and the feedback bundle add to the raw render |
| `anyplot/render/fonts/` | JetBrains Mono 2.304 Regular and Bold for the footer strip, unmodified, with `OFL.txt` (SIL Open Font License 1.1) and a notice with their SHA-256 values ([fonts README](anyplot/render/fonts/README.md)) |
| `renderer/` | The `anyplot-renderer` service: `main.py` (`POST /render`, `GET /status`, one render slot), `executor.py` (one `sandbox do` per theme with the kill path, the byte watchdog and the launcher retry), `auth.py` (the caller check), `settings.py` (`RENDERER_*`), `wire.py` (the JSON contract the `remote` backend shares), `Dockerfile` and `cloudbuild.yaml`. No ADK import and no `__init__.py`, so `adk web agents` does not list it as an agent |
| `anyplot/opening.py`, `session_state.py`, `services.py`, `briefs.py` | Opening a session and taking in a dataset, the server-set session state, the process-wide stores, and the spec and dataset briefs |
| `anyplot/dev_fixture.py` | The development-only session seed from an eval fixture case |
| `anyplot/settings.py` | `AgentSettings`, read from `AGENT_*` environment variables |
| `anyplot/schemas.py` | The pipeline contracts with their size limits |
| `anyplot/data/`, `anyplot/code/` | The deterministic data and code layers, without ADK |
| `evals/matrix.py` | The regression harness: runs eval cases through `/v1` in process and writes the report, the Markdown summary, the diff against a baseline and the review galleries |
| `evals/score.py`, `anyplot/scoring.py`, `anyplot/prompts/scorer.md` | Scores a harness run's renders with the catalogue rubric on Claude Opus: the measurement behind the quality ladder ([Score the renders with the catalogue rubric](#score-the-renders-with-the-catalogue-rubric)) |
| `anyplot/cli_transport.py`, `scripts/agents-experiment.sh` | The `claude-cli` transport and the experiment runner: the live code with its Claude calls on your subscription ([Run an experiment on your Claude subscription](#run-an-experiment-on-your-claude-subscription)) |
| `evals/ladder_lab.py` | Compares reviewers, feedback forms and repairers on the same seed renders through the local Claude Code CLI ([Compare reviewers, feedback forms and repairers](#compare-reviewers-feedback-forms-and-repairers-ladder-lab)) |
| `evals/make_fixtures.py` | The seeded generator of the 120 synthetic spike-X cases |
| `evals/make_stress.py`, `evals/stress.py` | The seeded generator of the 23 stress cases, and the model-free static stage that `--static` runs over them ([Run the stress cases](#run-the-stress-cases)) |
| `evals/cases.py`, `evals/pricing.py`, `evals/report.py` | Case loading and selection, list prices, and the summary, diff and gallery code; `report.py` also merges two runs into one blind gallery and scores its export |
| `evals/import_case.py` | Turns one feedback case, a saved session bundle or a case directory copied from the bucket, into an eval case in the git-ignored `evals/.cases/` ([Import a feedback case](#import-a-feedback-case)) |
| `evals/sync_cases.py` | Keeps `evals/.cases/` in line with the `agent_feedback` table: imports the promoted cases from the private case bucket, removes the retired ones, and with `--backfill` indexes cases that have no row ([Sync promoted cases from the bucket](#sync-promoted-cases-from-the-bucket)) |
| `evals/eligibility.py` | The model-free sweep of the catalogue's matplotlib and seaborn files: eligible, coupled and blocked pairs, and why |
| `evals/scope.py`, `evals/scope.evalset.json` | The judge-only scope eval and its 188 synthetic cases: in-scope, off-topic and adversarial messages, scored for adversarial recall and false refusals |
| `evals/prep.py`, `evals/fixtures/prep/` | The live prep eval and its 33 German and English data requests (10 of them `hard`): each through `/v1` in process with the real model, scored on the `prepare_data` operations and `generate_data` calls the root chose ([Run the prep eval](#run-the-prep-eval)) |
| `evals/fixtures/cases/` | The eval cases: 120 generated (`<spec>-<library>-<perturbation>`), the hand-written `scatter-basic-matplotlib`, `bar-grouped-seaborn` and `scatter-basic-matplotlib-german-message` (a German follow-up that sets the session language), and 23 stress cases (`stress-<name>`) ([fixtures README](evals/fixtures/README.md)) |
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
| `AGENT_MODEL` | `claude-haiku-5-5` | Model of every agent; a `gemini-` id, or for `anthropic-vertex` a model in `CLAUDE_MODELS` (accepts disabled thinking) |
| `AGENT_JUDGE_MODEL` | `claude-haiku-5-5` | Model of the scope and dataset judge; same rule |
| `AGENT_TRANSPORT` | `vertex` | `vertex`, or `claude-cli` for experiments (development and test only; see [Run an experiment on your Claude subscription](#run-an-experiment-on-your-claude-subscription)) |
| `AGENT_ADAPTER_MODEL`, `AGENT_REVIEWER_MODEL` | unset | `claude-cli` only: another model for the adapter or the reviewer |
| `AGENT_CLI_CONCURRENCY`, `AGENT_CLI_CALL_LOG` | `3`, unset | `claude-cli` only: CLI calls at the same time; a file that gets one JSON line per call |
| `AGENT_LOCATION` | `eu` | Vertex AI location: `eu`, `us` or `global` |
| `AGENT_PROJECT`, else `GOOGLE_CLOUD_PROJECT` | `anyplot` | Project that serves and bills the model calls |
| `AGENT_LIBRARIES` | `matplotlib,seaborn` | Enabled libraries; each needs a phase-1 runtime (`matplotlib`, `seaborn`), others are refused at startup |
| `AGENT_RENDERER` | `remote` | `remote` (the renderer service), `local` (Docker, development only), `fake` (fixture PNGs, development and test only) or `sandbox` (an in-process stub, not used in phase 1) |
| `AGENT_RENDER_URL` | unset | The renderer service URL; the `remote` backend refuses to start without it; `http://` only in development and test |
| `AGENT_RENDER_TOKEN` | unset | Development only: an ID token for the renderer; without it the backend mints one (see [Render through the deployed renderer](#render-through-the-deployed-renderer)) |
| `AGENT_RENDER_IMAGE` | `anyplot-renderer:dev` | Image the `local` renderer runs, built from `renderer/Dockerfile` |
| `AGENT_RENDER_CONCURRENCY` | `1` | Theme renders at the same time, for every backend (`render/serial.py`); serial, because one 4 GiB instance holds one sandbox safely (spikes S and S2) |
| `AGENT_WATERMARK` | `true` | Whether the served PNGs (the artifact route and the feedback bundle) carry the footer strip; `false` serves the raw renders. The gates, the reviewer and `plot.py` always see the raw render |
| `AGENT_RUN_CONCURRENCY` | `1` | Pipeline runs (whole `/messages` turns) in flight; the run queue holds the rest |
| `AGENT_RUNS_PER_MINUTE` | `1` | Runs that may start within any 60 seconds (a sliding window) |
| `AGENT_QUEUE_MAX_WAIT_S` | `600` | Longest wait in the run queue, after which the run ends with `capacity`; the queue holds rate x wait / 60 entries (10) and answers `503 capacity` beyond that. Through the BFF the whole turn, this wait included, ends by `AGENT_TURN_MAX_S` (1,190 s, see `docs/reference/api.md`), which the full wait plus the 540 s run fits into |
| `AGENT_MAX_ATTEMPTS` | `2` | Rounds per pipeline run, 1 to 3: the first and at most one repair round by default (a self-review adds an adapter call to a round, never a round); the eval harness sets 1 or 3 (`--max-attempts`) to measure no repair or a second repair round |
| `AGENT_REVIEWER_MODE` | `catalogue` | The reviewer's rubric: `catalogue` (the offline scorer's rubric, verdict decided by code from the points) or `checklist` (the narrow checklist used before 2026-10-13) |
| `AGENT_REVIEW_BAR`, `AGENT_STATUS_BAR` | `1.0`, `0.95` | `catalogue` reviews: the share of technical points (VQ, SC, DQ) below which a render gets the repair, and the ship bar at or above which it shows without notes |
| `AGENT_SHIP_BEST` | `true` | `catalogue` reviews: review every round and ship the best-scored version |
| `AGENT_SELF_REVIEW` | `true` | The adapter proofreads its render once per round before the review, against the rubric's technical rows |
| `AGENT_CHECK_RETRY` | `true` | An adapter answer that fails its check (edits that do not apply, a validator finding, a broken schema, code that crashes) gets one more call in the same round, which may send a full file; a second miss ends the round |
| `AGENT_ROOT_THINKING_BUDGET` | `1024` | Claude only: adaptive thinking of the root, with that many tokens added to its output cap; 0 turns it off |
| `AGENT_ADAPTER_THINKING_BUDGET` | `2048` | The same for the adapter; the eval harness overrides both with `--thinking-budget ROOT,ADAPTER` |
| `AGENT_REVIEWER_THINKING_BUDGET` | `2048` | The same for the reviewer; 0 turns its thinking off |
| `AGENT_ROOT_EFFORT`, `AGENT_ADAPTER_EFFORT`, `AGENT_REVIEWER_EFFORT` | `medium`, `high`, `high` | Claude's effort per agent kind (`low`, `medium`, `high`), set by the 2026-10-13 measurements (see [The plot pipeline since 2026-10-13](#the-plot-pipeline-since-2026-10-13)); on the claude-cli transport also how much the CLI thinks |
| `AGENT_MAX_LLM_CALLS` | `12` | LLM calls per request |
| `AGENT_REQUEST_TOKEN_BUDGET` | `800000` | Cost-weighted tokens per request (see [Token budgets and output caps](#token-budgets-and-output-caps)) |
| `AGENT_DAILY_TOKEN_BUDGET` | `8000000` | Cost-weighted tokens per user and day |
| `AGENT_DAILY_PIPELINE_RUNS` | `40` | Pipeline runs per user and day |
| `AGENT_GLOBAL_DAILY_TOKEN_BUDGET` | `24000000` | Cost-weighted tokens per day for the whole service |
| `AGENT_RENDER_TIMEOUT_S` | `60` | Seconds per theme render |
| `AGENT_REQUEST_DEADLINE_S` | `540` | Hard request deadline (180 before 2026-10-13: with a self-review per round, the soft deadline of 140 s stopped the repair round in 11 of 20 runs; the owner's rule is that no plot ships unfinished for lack of time) |
| `AGENT_SOFT_DEADLINE_S` | `480` | Soft deadline inside the pipeline |
| `AGENT_JUDGE_TIMEOUT_S` | `4` | Budget of one judge verdict, its one retry and the half-second wait before it included |
| `AGENT_KEEP_REFUSALS` | `false` | Keep the text and verdict of each message the scope judge refused, at most 20 per session in memory, shown only in the feedback bundle (`refusals`); never in a log. A phase-1 stub: read them from the bundle the page's `.save()` downloads (`GET /debug/agent/sessions/{sid}/bundle` on the BFF) while the session lives; the ring goes with the session |
| `AGENT_ATTACK_STRIKES` | `3` | `attack` verdicts of the scope or dataset judge per user and day, once per distinct message or dataset, after which the user gets the budget refusal for the rest of the UTC day; only a new day, a redeploy or a scale-to-zero resets them. Every token-path caller shares one user id, so raise it for a jailbreak-testing session |
| `AGENT_SESSION_IDLE_S` | `3600` | Idle time after which the sweeper drops a session |
| `AGENT_ALLOWED_CALLERS` | empty | Service-account emails allowed to call `/v1` outside development |
| `AGENT_SERVICE_URLS` | empty | ID-token audiences accepted on `/v1` outside development |
| `AGENT_DEV_FIXTURE` | unset | Development only: a fixture case id that seeds every new session |
| `ENVIRONMENT` | `production` | Shared with the API; `local` rendering, the fixture seed and skipping the caller check need `development`, which is refused on Cloud Run |

### Token budgets and output caps

The three token budgets count cost-weighted tokens, in input-token equivalents (`BUDGET_WEIGHTS` in `anyplot/plugins/ledger.py`). Each kind of token weighs its list price relative to an uncached input token, the same ratios `evals/pricing.py` prices with:

| Token kind | Weight |
|---|---|
| Uncached input | 1 |
| Cache read | 0.1 |
| Cache write (five-minute lifetime) | 1.25 |
| Output (candidates and thoughts) | 5 |

The scope and dataset judges count against the same unit, the main model's uncached input token (`JUDGE_WEIGHTS`: input 1 and output 5 on the Claude arm, where the judge is Claude Haiku 5.5 itself; 0.2 and 1.67 on the Gemini arm, where the Flash-Lite judge is five times cheaper than Gemini 3.8 Flash). The `done` event and the attribution lines keep the plain token counts; each `model` attribution line adds the call's weighted count as `budget`.

In the rerun of spike X on main (244 runs, Claude Haiku 5.5, warm prompt cache), the median run booked 37,157 weighted tokens against 70,488 plain ones, so 2,000,000 per user and day holds about 54 median runs, and the 40 runs of `AGENT_DAILY_PIPELINE_RUNS` bind first; a user whose every request starts cold gets about 26 at the cold median below, where the token budget binds instead. The global 6,000,000 is three users at their daily budget. A cold cache weighs more, because each agent's first call writes its prefix at 1.25 instead of reading it at 0.1; a request starts cold after a pause longer than the cache's five-minute lifetime. The rerun measured this as well: the first, cold run of area-basic-seaborn-decimal-comma booked 100,282, and 3 of the 244 runs, each the first run of its spec, booked too much to fit a second review under the earlier 80,000. Simulated cold from the same calls, a reviewed run with two adapter attempts books a median of 77,747 (at most 103,800), and at most 115,046 with a second review; the three-attempt rerun (`--max-attempts 3`) reaches about 117,300. The request budget of 160,000 stays about 36 % above the costliest of these. Before each review the pipeline also keeps 35,000 (`pipeline.REVIEW_RESERVE_TOKENS`) for the review and the root's closing reply, so a tight budget skips a review instead of answering a shipped plot with the `budget` refusal; that reserve is the measured need, and the guarantee is structural: once a plot has shipped in the invocation, the root's next call, the closing reply, is exempt from the budget halt, once and without tools, so it can only answer (bounded by the 4,096-token output cap); any further root call is checked again.

The output caps per model call are constants in `anyplot/models.py`, set with ample headroom above the largest measured answer, because an unused cap costs nothing and a cut-off wastes the call:

| Call | Claude | Gemini | Largest measured answer on Claude |
|---|---|---|---|
| Root | 4,096 | 4,096 | 259 |
| Adapter, edits only (attempt 1) | 8,192 | 8,192 | 2,030 (23 of 244 were cut off at the old 2,048) |
| Adapter, full file allowed (the repair) | 16,384 | 12,288 | 2,606 |
| Reviewer | 4,096 | 4,096 | 600 |
| Scope and dataset judge | 256 | 256 | 59 |

On Gemini, thinking tokens count toward the cap, and the soft deadline bounds the adapter's caps: at spike X's fitted rate, a call that uses all 8,192 tokens still leaves the repair attempt its 75 s. Gemini's answers are larger: its plan calls in spike X needed a median of about 4,700 output tokens, and 11 of 112 needed more than 8,192. Claude Haiku 5.5 runs at about 0.0029 s per output token, so a call that uses all 16,384 takes about 49 s, inside the 60 s the deadline check reserves for an adapter call.

Claude runs with adaptive thinking on the root (`AGENT_ROOT_THINKING_BUDGET`, 1,024) and the adapter (`AGENT_ADAPTER_THINKING_BUDGET`, 2,048) since 2026-10-11; each budget is added to that agent's caps in this table, so the answer keeps its whole headroom however much the thinking uses, and 0 turns it off. The measurement of 2026-10-11 on the 122 cases (real renderer) decided it: with both budgets every run passed the gates and 51.6 % ended `ok`, with the adapter's budget alone 100 % and 50.0 %, with thinking off 91.0 % and 28.7 % (the structured answer then misses its edit anchors in a third of the runs); the price is a median of $0.0063 instead of $0.0038 per plot and a p50 of 31.5 s instead of 13.6 s. Haiku 5.5 takes no thinking budget of its own, so the value is room, not a limit the model sees, and its depth follows the agent's effort. The largest budget, 4,096, keeps the adapter's full-file cap at 20,480, below the Anthropic SDK's limit for a request that does not stream (about 21,300).

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

At the defaults only one run may start a minute, so a second "Create plot" within a minute waits in the run queue and the stream shows `status` events with `step: "queued"`. A turn while the data is unconfirmed (the summary after a paste, a data request in step 1) cannot render and takes no start, only the slot, so step 1 never waits for the minute. To iterate faster on your own machine, export `AGENT_RUNS_PER_MINUTE=60`. The theme toggle (`POST /v1/sessions/{sid}/versions/{version}/render {"theme": "dark"}`) never waits in the queue.

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

### Run the whole stack

`scripts/agents-dev.sh` starts each part of the local stack with the settings above: the service and `adk web` against the real models and the deployed renderer (next section), the API with the agent routes switched on, and the app with the chat page. Each part runs in the foreground of its own terminal, from the checkout you want to run, and logs to `~/.cache/anyplot-dev/<part>.log` (`ANYPLOT_DEV_LOGS` overrides it).

1. Put the API's two keys where the script finds them, one value per file, readable only by you: `ADMIN_TOKEN` (the token you enter on `/debug`) and `AGENT_USER_ID_KEY` (any value for local use) in `~/.config/anyplot-dev/` (`ANYPLOT_DEV_SECRETS` overrides the directory). Variables of the same name win over the files; the script never prints either.
2. Start the four parts:

   ```bash
   scripts/agents-dev.sh agents   # :8001
   scripts/agents-dev.sh adk      # :8002, the scatter-basic fixture (AGENT_DEV_FIXTURE)
   scripts/agents-dev.sh api      # :8000
   scripts/agents-dev.sh app      # :3000, on Node 24 through nvm when installed
   ```

3. Open `http://localhost:3000/debug`, enter the admin token, and open the chat page in the same tab.

`agents` and `adk` render with a gcloud identity token, which lives one hour, so they restart every 55 minutes with a fresh one; a run in progress at that moment is lost. `scripts/agent-cases.sh [case-id]` reads the production feedback cases as JSON (read-only, the data of `/debug`'s "Agent cases"); it reads the `ADMIN_TOKEN` and `ORIGIN_SECRET` secrets through your gcloud account.

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

The image's `fonts` stage installs Debian's `fonts-noto-core` and `fonts-noto-cjk` and copies 37 allowlisted files (Noto Sans, Noto Sans CJK Regular and Bold, and the script families DejaVu Sans lacks) into `/usr/share/fonts/noto`, with their OFL notices and package versions in `/usr/share/doc/fonts-noto`; the cache bake fails when a family of `harness.FALLBACK_FAMILIES` is not found. The harness appends these families to every font lookup after the font the plot code chose, and the probe's `missing_glyphs` reports the code points no font of a text covers (gate G10). Arabic and Hebrew render shaped and right to left; the limits are in [Agent network design](../docs/concepts/agent-network.md#render).

`renderer/cloudbuild.yaml` builds, deploys a `candidate` revision without traffic, smokes it (IAM refuses an anonymous caller; with `_SMOKE_RENDER=true`, `/status` reports the launcher and the volume and a real matplotlib render goes through the candidate, with a token minted for the service URL), and promotes it. The first build also creates the service; the deploy adds the service URL to `RENDERER_AUDIENCES` itself, and `_MIN_INSTANCES=1` keeps an instance warm. CI builds the same image before merge (`.github/workflows/ci-image.yml`). The deploy flags and the owner tasks are in [Agent network design](../docs/concepts/agent-network.md#serving-and-infrastructure).

### Test

```bash
uv run pytest tests/unit/agents -q
```

`tests/unit/agents/renderer/` runs the executor against a fake `sandbox` launcher that runs the real harness with this interpreter, the service in process, and the `remote` backend against the service through httpx's ASGI transport. The harness tests cover the glyph capture with matplotlib's bundled DejaVu alone (a CJK title must be reported missing) and the fallback hook with `DejaVu Serif` standing in for an installed family; the CI image job is the only place the Noto fonts themselves are exercised. `tests/unit/agents/test_image.py` holds the image and its deploy config against the code: every file the service reads must reach the image at its own path and be read by the build's check, the deploy's substitutions and variables must match the settings, and the deploy step's script runs against a fake `gcloud`.

## Build and deploy the service

The `anyplot-agents` image (`Dockerfile`) installs the `agents` extra without any plotting extra, because the service runs no plot code: every render goes to `anyplot-renderer` through the `remote` backend. It copies the source tree rather than a wheel, because the service reads its prompts, `refusals.yaml`, the footer-strip fonts and the catalogue prompt sources in `prompts/` from paths next to its modules, and its build fails when one of them is missing: it imports `agents.main` and reads the two judge rubrics, which the service otherwise reads on first use. The root `.dockerignore` keeps `evals/` and ADK's local `.adk/` store, which holds users' messages and datasets, out of the image.

### Build the image

From the repository root, run:

```bash
docker build -f agents/Dockerfile -t anyplot-agents:dev .
```

To try the container on your own machine without credentials:

1. Start it in development with the `fake` renderer:

   ```bash
   docker run -d --name anyplot-agents -p 8001:8080 -e ENVIRONMENT=development -e AGENT_RENDERER=fake anyplot-agents:dev
   ```

2. Ask it for its status:

   ```bash
   curl localhost:8001/v1/status
   ```

3. Remove the container:

   ```bash
   docker rm -f anyplot-agents
   ```

The container has no Application Default Credentials, so a "Create plot" fails at the first model call; use `uv run uvicorn agents.main:app` (see [Run the service](#run-the-service)) for real runs. CI builds the same image before merge (`.github/workflows/ci-image.yml`, job `agents-image`).

### Deploy

`cloudbuild.yaml` builds the image, deploys a `candidate` revision without traffic, smokes it, and promotes exactly that revision:

- The flags follow the design: one instance (sessions live in memory), 2 vCPU and 4 GiB, `--concurrency=20` and `--timeout=900` for the run queue's open streams, `--no-allow-unauthenticated`, the service account `anyplot-agents@`, no `--sandbox-launcher`, and `--update-env-vars` only.
- `_PROVIDER`, `_MODEL`, `_JUDGE_MODEL` and `_LIBRARIES` default to the settings defaults, so a deploy switches the model arm without a code change. The budgets and limits are not set, so the deployed code's settings defaults apply.
- `_RENDER_URL` is the `status.url` of the real `anyplot-renderer`, and the deploy refuses to run without it, because `--update-env-vars` would otherwise replace a working renderer URL with nothing. `AGENT_ALLOWED_CALLERS` is `_API_CALLER`, anyplot-api's runtime identity (the Compute Engine default service account unless a build sets another one), plus `anyplot-agents@` itself for the smoke. The deploy adds the service's own URL to `AGENT_SERVICE_URLS`.
- The smoke expects Cloud Run IAM to refuse an anonymous `GET /v1/status` with `403`. With `_SMOKE_AUTH=true`, the default, it also calls `/v1/status` with an ID token minted for `anyplot-agents@` and checks that the answer names the configured provider, model, location and libraries.

The first deploy happened on 2026-10-11: the roles were granted, the bootstrap build ran with `_SMOKE_AUTH=false`, `roles/run.invoker` was granted on the new service, the rebuild passed the token smoke, and the `deploy-agents` trigger exists with `_RENDER_URL`. Since then every push to `main` that touches the service deploys it. The commands stay in the header of `cloudbuild.yaml` for a redeploy from scratch; the roles and the environment are in [Agent network design](../docs/concepts/agent-network.md#serving-and-infrastructure).

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

- The smoke set is 12 cases (tag `smoke`): one generated case per spec, cycling through the perturbations and both libraries, plus the hand-written `scatter-basic-matplotlib` and `bar-grouped-seaborn`.

  ```bash
  uv run --extra agents python -m agents.evals.matrix --cases smoke \
    --renderer remote --render-url https://RENDERER_URL --gcloud-token
  ```

- The full matrix is the 123 cases that are not stress cases. Cap the spend with `--budget-usd`:

  ```bash
  uv run --extra agents python -m agents.evals.matrix --cases full --budget-usd 4 \
    --renderer remote --render-url https://RENDERER_URL --gcloud-token
  ```

- To run the Gemini arm, add `--provider gemini`; it selects `gemini-3.8-flash` with the judge on `gemini-3.5-flash-lite`. `--model` alone implies its provider, and `--judge-model` and `--location` override the rest.
- To run a subset, pass comma-separated globs over case ids, for example `--cases "*-seaborn-*"` or `--cases "pie-basic-*,box-basic-*"`. `--cases scatter-basic-matplotlib-german-message` runs the case whose German follow-up sets the session language: its first version is English, its second must carry German plot text, and each run's record holds the `done` event's `language`.

| Flag | Meaning |
|---|---|
| `--provider`, `--model`, `--judge-model`, `--location` | The candidate settings, passed only to this process as `AGENT_*` variables |
| `--renderer`, `--render-url` | The render backend (`remote`, `local` or `fake`) and the remote renderer's URL |
| `--gcloud-token` | Mint the renderer token with `gcloud auth print-identity-token` and renew it before it expires (`remote` only) |
| `--no-preflight` | Skip the preflight render before the first case |
| `--cases` | `smoke` (default), `full` (every case but the stress cases), `stress`, or comma-separated globs over case ids |
| `--static` | Run only the model-free static stage and write `<date>-static.json` instead of a matrix report (see [Run the stress cases](#run-the-stress-cases)); the renderer is `fake` unless `--renderer` or `AGENT_RENDERER` names another |
| `--repeats N` | Runs per case, to see how stable a result is |
| `--max-attempts N` | Adapter attempts per run, 1 to 3 (`AGENT_MAX_ATTEMPTS`, 2 by default), so 1 measures the first attempt alone and 3 a second repair round; the report's stamp records the value as `max_attempts` |
| `--thinking-budget ROOT,ADAPTER` | Claude only: adaptive thinking for the root and the adapter, each value (0 to 4,096, 0 off) added to that agent's output cap (`AGENT_ROOT_THINKING_BUDGET`, `AGENT_ADAPTER_THINKING_BUDGET`); the stamp records it as `thinking_budget`, the summary names it, and the thinking tokens are priced as output |
| `--budget-usd X` | Stop before a case that could take the estimated list-price cost past X (the spend so far plus the costliest case so far), or once the cost has passed X (exit code 3) |
| `--out DIR` | Output directory, `agents/evals/reports/` by default (git-ignored) |
| `--baseline FILE`, `--no-baseline` | The report to compare with; by default `evals/baselines/claude-haiku-5-5.json` when it exists |
| `--tolerance F` | The pass-rate drop that counts as a regression, 0.05 (5 percentage points) by default |
| `--save-baseline` | Also write the report as `evals/baselines/<model>.json`; refused for a run that stopped early, holds promoted cases, or has a run that ended in an error |
| `--seed N`, `--gallery-size N` | The gallery's random sample: its seed (0) and size (30) |
| `--runs-per-minute N` | The run queue's start rate for this process, 60 by default |

For its own process the harness lifts the run queue's start rate and the service-wide daily token budget, and gives every case its own user id, so the per-user daily budgets never trip. The per-request limits (12 LLM calls, 160,000 cost-weighted tokens, the deadlines) stay at their production values, which a run with `--max-attempts 3` fits as well (see [Token budgets and output caps](#token-budgets-and-output-caps)). It also sets `AGENT_WATERMARK=false` unless your environment already sets the variable, so `renders/` and the galleries hold the raw renders the gates and the reviewer judged, without the footer strip, comparable with the committed baselines. To see the renders as a user gets them, export `AGENT_WATERMARK=true` before the run.

### Read the results

A run writes to `--out`:

- `<date>-<model>.json`: the report. It holds the stamp (provider, models, location, attempt bound, thinking budgets, renderer, ADK version, commit, prompt hashes, prices), the summary, and one record per case and repeat: status and reason, the exception class when the pipeline ended in an error, attempts, gate failures by gate, validator rejections, edit-apply failures, the reviewer's verdict, LLM calls by agent, tokens by kind, `model_version`, the cost at list price, time to the first event, end-to-end time and render times. Since report schema 2, each record also says where the run stopped (`stage`, such as `adapter_truncated`, `edit_apply` or `reviewer_defects`, and `stages` per attempt), which attempt shipped and which the reviewer saw last, an `attempt_log` with each attempt's adapter outcome, finish reason and plan shape, every model call's finish reason and tokens, and the answers that failed their schema, by agent kind and outcome (`answer_outcomes`: `repaired` or `refused`) and by broken rule (`answer_rules`, such as `defects.*.observed:string_too_long`), the edits each tolerant matching tier applied (`edit_tolerant`), and the labels of the imports the validator banned (`banned_imports`, such as `io` or `pandas.io`: the longest prefix of the path in a closed vocabulary of module names, anything else `?`, so no word the model writes as an import reaches the log); a schema-1 baseline still loads, and a report without these counts reads as none. The date is the UTC date.
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

### The plot pipeline since 2026-10-13

The defaults are the flow the experiments of 2026-10-13 settled on (about 1,500 runs on the Claude subscription, below). Every agent runs on Claude Haiku 5.5:

1. **Adapt.** The adapter edits the catalogue code for the user's data; the validator, the loader, the render and the host gates follow. A gate finding (text past the canvas, for example) starts a repair round while one is left.
2. **Self-review.** The adapter sees the render of its code once and checks it against the self-review checklist in its instructions: the rubric's technical rows (VQ-01 to VQ-07, SC-01 to SC-04, DQ-01, DQ-03), cut verbatim from `prompts/quality-criteria.md` with the scorer's rules for a user's plot (`policy.self_review_checklist`). After a repair it also gets that round's findings, so it can see whether its changes worked. The self-review is the adapter proofreading its work: it is part of the round, not a repair and not a round of its own on the page.
3. **Review.** The reviewer scores the render with the catalogue rubric, the offline scorer's twin (`prompts/reviewer_catalogue.md` before `scoring.system_prompt`). The code decides from the points: every technical point (`AGENT_REVIEW_BAR` 1.0) means no repair; otherwise the defect lines go to the next round.
4. **Ship the best.** Every round is reviewed, and the best-scored version ships (`AGENT_SHIP_BEST`). At or above 95 % of the technical points (`AGENT_STATUS_BAR`) it shows without notes (`ok`); below, the review's lines are the notes (`needs_attention`).

What the measurements showed, scored by the user scorer on Opus and Sonnet:

- The checklist reviewer named 2 of 37 agreed technical deductions; Haiku with the catalogue rubric 28, Opus 35. A bigger model does not pay: Sonnet as reviewer flagged 15 of 20 runs and repaired more without a better score, Sonnet as adapter gained nothing, a third round gained nothing.
- The catalogue reviewer's value is an honest status more than points: on 10 unseen specs, the reviewer with ship-best on the original catalogue code scored the same as the old flow (79.2).
- The self-review lowers the share of runs that end with notes (from 8 to 3 of 20 in the same configuration) at an unchanged score.
- The largest gain is a catalogue base without variant creep (+2.3 on the unseen specs, one run below 75 instead of four); building such bases is the next step, not part of this flow yet.

### Score the renders with the catalogue rubric

The owner's quality ladder (2026-10-12) lets a result ship only once it reaches a score threshold, scored like the pipeline scores catalogue implementations. `evals/score.py` measures where today's results stand, without changing the agent: it scores a matrix run's renders with `anyplot/scoring.py`, which reads the catalogue rubric verbatim (`prompts/quality-criteria.md` and steps 5c, 5d and 8a of `prompts/workflow-prompts/ai-quality-review.md`) behind `anyplot/prompts/scorer.md`.

The scorer judges the 16 criteria a user sees, 75 points scaled to 100: Visual Quality (30), Design Excellence (20), Spec Compliance (15), and DQ-01 and DQ-03 of Data Quality (10). It leaves out DQ-02 (the realism of the scenario: the data is the user's own), Code Quality (the catalogue's code style, inherited through the edits) and Library Mastery (a catalogue showcase). The model gives points per criterion and defect lines; the code adds up and applies the rubric's caps. Design Excellence starts at the rubric's defaults (8 of 20), so a defect-free plot in the plain house style scores 84: a threshold of 90 asks for design beyond the style guide's baseline.

1. Run the matrix with `--keep-attempts`. The harness then also keeps every render a turn sends to the renderer, with its code and data, under `attempts-<UTC start time>/` in the output directory (one directory per run, so a second run never overwrites what an earlier report points to), and lists them per run as `attempt_renders`:

   ```bash
   uv run --extra agents python -m agents.evals.matrix --cases full --keep-attempts --no-baseline \
     --renderer remote --render-url https://RENDERER_URL --gcloud-token --out agents/evals/reports/<run>
   ```

2. Estimate, then score the report's first and shipped render of each run:

   ```bash
   uv run --extra agents python -m agents.evals.score agents/evals/reports/<run>/<date>-claude-haiku-5-5.json --estimate-only
   uv run --extra agents python -m agents.evals.score agents/evals/reports/<run>/<date>-claude-haiku-5-5.json --budget-usd 20
   ```

   The scorer is Claude Opus 5.5 on `eu` at high effort (`--model`, `--location`, `--effort`); it probes the model first and stops with exit code 2 when the model is not reachable, and never falls back to another model. Calls start at two a minute (`--calls-per-minute`), because a new model's per-minute token quota can be small; a 429 stops the run and names the quota, and `--budget-usd` stops it before the next call could pass the budget (exit code 3, the partial results written). `--sample N` scores N runs spread evenly over the report. One call costs about $0.07 at list price with the rubric cached.

3. Read `<report>-scores.md` and `<report>-scores.json` next to the report: the score distribution of the first and the shipped renders and their share at or above 90, 85 and 80; what repair 1 gained; how many runs reach each threshold at the first try, after repair 1, or would need an advisor; the points lost by criterion; the runs whose gates were clean but whose score is below 80; and the cost and latency of the agent runs and of the scoring. When the first render also shipped, it is scored once and counts for both.

**First measurement, 2026-10-12 (rough: 18 runs, 16 scored; 7 specs, both libraries; Haiku 5.5, two attempts; scorer Opus 5.5 on `eu`, high effort):**

- Shipped results score a median of 81 (75 to 85): none reaches 90, 2 of 16 reach 85, 14 of 16 reach 80. First renders score the same (median 81).
- Repair 1 does not move the score: of 13 repaired runs, 3 gained (1 to 4 points), 7 stayed equal and 3 lost (1 to 5 points). Today's repair fixes what the Haiku reviewer names, which the rubric mostly does not deduct.
- The gap is design, not defects. Visual Quality, Spec Compliance and Data Quality together average 96 % (87 to 100 %); Design Excellence stays at the rubric's defaults (8 or 9 of 20) on every render. On this rubric a defect-free plot in the house style scores 84, so a threshold of 90 sends every run to an advisor that adds design beyond the style guide.
- The most frequent technical deduction is SC-01 variant creep inherited from the catalogue code: a regression line and confidence band on `scatter-basic`, KDE, rug and mean and median lines on `histogram-basic`, a point strip on `violin-basic`, a donut ring on `pie-basic`. The adapter keeps them, and the agent's reviewer does not flag the catalogue's own layers.
- No render lost a point for keeping the user's column names as axis titles (VQ-06, SC-04).
- Cost: an agent run costs a median of $0.008 and takes about 35 s; scoring one render with Opus costs about $0.09 at list price and takes 16 to 19 s. The whole measurement, both harness runs and 32 scoring calls, cost about $3.

### Run an experiment on your Claude subscription

An experiment changes an agent (a prompt, a pipeline step, a model per agent) and measures the result on the live code. With `AGENT_TRANSPORT=claude-cli` (development and test only) the agents' Claude calls run through the local Claude Code CLI on your own subscription instead of Vertex AI. Everything else stays the live code: the same ADK agents, prompts, schemas, plugins, pipeline, validator, the deployed renderer and the gates. `anyplot/cli_transport.py` replaces only the transport, below ADK: its client answers `messages.create` with the Anthropic SDK's arguments and returns the SDK's `Message`.

- The CLI answers the structured calls: the adapter, the reviewer, the scope and dataset judge, the transcriber, and the offline scorer's single tool. The root (chat with tools and tool results) goes to Claude Haiku on Vertex AI, about $0.002 a run.
- `AGENT_ADAPTER_MODEL` and `AGENT_REVIEWER_MODEL` pick another model per agent (Haiku, Sonnet or Opus 5.5) for an experiment; the live service refuses both.
- The known difference to the live calls is thinking: the CLI thinks at the request's effort by its own rules, while the live calls set a thinking budget (or none for the reviewer). The judge's budget rises to 90 s, because each CLI call starts a process.
- Token counts are real, so budgets and reports work; their dollar figures are list-price equivalents, not money spent.

1. Log in to the CLI with your subscription (`claude`, then `/login`), and to gcloud for the renderer's ID token.
2. Check out the code to test (a branch with the changed agent) and run the experiment, which runs the regression harness and then scores the first and shipped render of each run with the catalogue rubric on Opus, also through the CLI:

   ```bash
   AGENT_ADAPTER_MODEL=claude-sonnet-5-5 scripts/agents-experiment.sh sonnet-adapter --cases smoke
   ```

   Matrix options pass through (`--cases`, `--repeats`, `--max-attempts`). Results land in `~/.cache/anyplot-dev/experiments/<name>/` (`ANYPLOT_DEV_EXPERIMENTS`), outside the checkout: the harness report and gallery, every attempt's render, `*-scores.md`, and `cli-calls.jsonl` with one line per CLI call.
3. Compare the experiment's `*-scores.md` with a baseline experiment run the same way on `main`, then confirm the winner with the same harness on Vertex AI (without `AGENT_TRANSPORT`).

`evals/score.py --transport claude-cli` scores any harness report through the CLI on its own.

### Compare reviewers, feedback forms and repairers (ladder lab)

The first measurement could not say why repair 1 gains nothing, because the Haiku reviewer and the Haiku repairer were measured together. `evals/ladder_lab.py` takes them apart on the same seed renders: the ruler (how far the Opus scorer moves on the same render, and how far Sonnet and Haiku are from it), detection (which rubric deductions each model and today's production reviewer name), and execution (with the findings held fixed, which repairer and which feedback form lifts the score). The arms are `today` (today's reviewer lines, Haiku repairs), `lines-haiku`, `lines-sonnet` and `lines-opus` (the reference findings as defect lines), `suggest-haiku` (the lines plus the scorer's suggestions), and `advisor-sonnet-haiku` and `advisor-opus-haiku` (an advisor sees image, code and findings and writes a concrete plan that Haiku applies).

Every model call goes through the `claude-cli` transport (`anyplot/cli_transport.py`, with the agent's own prompts and output schemas), so the lab runs on your Claude subscription and spends no Vertex AI budget; the answers go through the pipeline's own edit applier, validator, loader, the deployed renderer and the host gates. Compare arms with each other here, and confirm the winning arm on Vertex AI afterwards.

1. Log in to the CLI with your subscription (`claude`, then `/login`), and to gcloud for the renderer's ID token.
2. Run all stages (seed, score, repair, report) into a directory outside the checkout, so the renders outlive the worktree:

   ```bash
   uv run --extra agents python -m agents.evals.ladder_lab all --out ~/.cache/anyplot-dev/ladder-lab
   ```

   Each stage writes one file per result and skips the results that exist, so a run that stopped (a subscription limit, a renderer hiccup) resumes where it stopped; a repair whose score was lost is scored on resume, never redone. `--cases`, `--scores` (default `opus:3,sonnet:1,haiku:1`) and `--arms` narrow a run, and `--review-efforts low,high` also runs today's reviewer at another effort. Every CLI call is logged to `calls.jsonl`, which the report sums up.
3. Read `report.md` in the output directory.

**First lab run, 2026-10-13 (20 seeds: ten specs, both libraries; seeds by Haiku; the reference judge Opus 5.5 at high effort, three scores per seed; about 400 CLI calls, no Vertex AI spend):**

- The ruler holds: Opus scores the same render within 1 point on average (at most 4), so a change beyond ±2 is real. Haiku scores 0.2 above the Opus mean, Sonnet 4.1 below it.
- Finding is a matter of the prompt, not the model. Of the 37 technical deductions at least two Opus runs agree on, today's reviewer (Haiku on the narrow checklist) names 2, and 1 at the scorer's high effort (`--review-efforts low,high`), so the effort is not the cause; Haiku with the scorer's rubric names 28, Sonnet 32 (with 26 extra), Opus 35.
- Every repair from the rubric's findings helps, and the repairer matters less than expected. On the 15 seeds with findings (Opus mean 78.0, 5 of 15 at 95 % of the technical points): Haiku with the defect lines reaches 82.4 (+4.4) and 14 of 15 at the technical bar; Sonnet the same; Opus 84.1 (+6.1) and 15 of 15; Haiku with an Opus advisor's plan 84.0 (+6.0) and 15 of 15; Haiku with a Sonnet advisor's plan 82.8; the scorer's suggestions on top of the lines add nothing (82.3).
- No arm reaches 90 (best 85): Design Excellence moves by at most 0.3 points. The repairs fix defects; they do not add design.
- Caveat: Opus judges repairs that Opus made or planned, so the Opus arms' lead of about 1.7 points may partly be the judge's taste. A blind owner check of a sample, and the confirmation on Vertex AI, decide it.

### Run the stress cases

The 23 stress cases (`evals/fixtures/cases/stress-*`, from `evals/make_stress.py`) push every limit before real use: data exactly at and one past the parser's caps, 100 bars and 30 pie slices, degenerate data, prompt injection, and requests that make the code compute mass data. Each `case.json` names the gate, limit or error that must bound the case (`bound_expected`); the [fixtures README](evals/fixtures/README.md#stress-cases-what-bounds-them) lists every bound with the numbers measured on 2026-10-10.

1. Run the static stage. It calls no model and spends nothing: for every case it runs the dataset route's size check and parse, eligibility, bindings, the loader's `pd.read_csv`, measures what the adapter, the dataset judge and the reviewer would read, traces injected text through those inputs, and renders the five hand-written stand-ins (`standin.txt`) for the adapter's answer:

   ```bash
   uv run --extra agents python -m agents.evals.matrix --cases stress --static
   ```

   It writes `<date>-static.json` and a Markdown table to `--out` and exits with 1 when a case's expectations (`static` in its `case.json`) did not hold. The default `fake` renderer runs no code, so the stand-ins' gates stay unchecked.

2. To see the stand-ins hit the real limits (G7, G9 and the sandbox's address space), render them on the deployed renderer, still without a model:

   ```bash
   uv run --extra agents python -m agents.evals.matrix --cases stress --static \
     --renderer remote --render-url https://RENDERER_URL --gcloud-token
   ```

   With a `remote` or `local` renderer the static stage also checks each case's `render` expectations and reports the render time. Only the `remote` renderer reports the harness's peak memory; the `local` backend leaves that column empty. When the renderer becomes unavailable during a stand-in render, the run stops with exit code 4, as an outage stops the matrix.

3. Run the cases whose bound, or the outcome their bound leaves open, only a model run shows. The output names them as `needs a model run`:
   - `stress-compute-lorenz`, `stress-compute-oversample` and `stress-compute-distances`: does the adapter write the mass-data code, and does G9 or the renderer stop it.
   - `stress-pie-30-slices`: only the reviewer sees its piled labels.
   - `stress-single-row` and `stress-constant-series`: how the plot copes with one point or a flat series.
   - `stress-inject-long-cell`: whether the plot draws the injected cell as a tick label the reviewer reads.

   This is a normal matrix run and spends tokens:

   ```bash
   uv run --extra agents python -m agents.evals.matrix \
     --cases "stress-compute-*,stress-pie-*,stress-single-row,stress-constant-series,stress-inject-long-cell" \
     --no-baseline --budget-usd 1 --renderer remote --render-url https://RENDERER_URL --gcloud-token
   ```

   `--cases stress` runs all 23 the same way. The four over-cap cases end at the dataset route before any model call, and the two bindings refusals after one judge call. The full matrix's measured cost per case puts the whole set at about $0.15 to $0.20 on the Claude arm and $3 to $4 on the Gemini arm; the computing cases send their change request as a second turn and cost about twice a normal case.

After you change `evals/make_stress.py`, regenerate the cases with `uv run --extra agents python -m agents.evals.make_stress` (`--check` exits with 1 when a committed file is stale or a stray file sits in a `stress-*` directory).

### Run spike X

Spike X is the go or no-go for phase 1: 10 specs times matplotlib and seaborn times 6 datasets (renamed, x10, n=12, n=5000, date, decimal comma) on both arms, under $25 in total. The full matrix is those 120 generated cases plus the hand-written ones (two at spike X, three since 2026-10-12). At list price a full run is estimated at about $1 on the Claude arm and $10 to $15 on the Gemini arm. The budgets below leave $3 of the $25 for headroom, because a budget is checked between cases.

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

### Import a feedback case

`evals/import_case.py` turns a real session into an eval case: a bundle the chat page's `.save()` downloaded, or a case directory that the result card's quick feedback stored in the private case bucket and that you copied to this machine. To pull the cases you promoted on the debug page straight from the bucket, see [Sync promoted cases from the bucket](#sync-promoted-cases-from-the-bucket).

1. Run the import from the repository root:

   ```bash
   uv run --extra agents python -m agents.evals.import_case anyplot-session-AbCdEf12.json
   uv run --extra agents python -m agents.evals.import_case cases/20261012T143005Z-1a2b3c4d --expected rejected
   ```

   The case goes to the git-ignored `evals/.cases/<id>/`, never to `evals/fixtures/`, because it holds a user's data. It needs the version's `data.csv`, so save the session or send the feedback with `# include data.csv` ticked. A case on the chat itself (`result_version` 0, sent from `# feedback on this chat` by a session that made no plot) is refused: it has no plot to replay, and what it shows belongs in the prep or scope eval fixtures. `--version N` picks a version of a bundle (the newest by default), `--id` names the case (by default `session-<hash>-v<n>` or `case-<case id>`), `--expected` sets the outcome (by default from the reaction, the triage's rule: thumbs up is `accepted` and thumbs down `rejected`; bug and idea imply no outcome, so they need the flag; a bundle without a reaction is `unknown`), and `--force` replaces an imported case of the same id. When the session's language was detected or chosen, `case.json` gets the `language` the version's text was written in, which the harness chooses before the first turn, because the replay's first plot comes from `create_plot` and would otherwise be English.
2. If the tool refuses with `cannot tell which message made version N`, pass the request yourself. The transcript has no version markers, so the tool takes the `n`-th plot turn (each `create_plot` and every message typed after the first one, or every typed message in a session without `create_plot`) as the request of version `n`, and only when the plot turns and the versions agree in number. A question or a failed run in between breaks that, and so does a stored case on a version that was not the newest. The refusal lists the plot turns; rerun with `--change-request "<the request>"`, or with `--no-change-request` when the version came from `.create_plot()`. The tool also refuses a case whose bindings name a column the version's `data.csv` lacks, because the bundle holds the session's latest bindings, not each version's.
3. Run the case with `--cases <id>` (see [Run the smoke set or the full matrix](#run-the-smoke-set-or-the-full-matrix)). A run that holds promoted cases can't be saved as a baseline.

### Sync promoted cases from the bucket

`evals/sync_cases.py` keeps `evals/.cases/` in line with the triage on the debug page. The `agent_feedback` table decides which cases belong there: the ones you promoted that are neither superseded by a later submission nor retired (status `done` or `wont_solve`). The bucket holds their files. The sync reads the table and the bucket and writes only local files; the one database write is `--backfill --apply`, described below.

1. Make sure the tool can reach the table and the bucket:
   - `DATABASE_URL` is exported, or set in this checkout's `.env`. The tool reads only that key from the file, and only from this checkout's own `.env`, never a parent directory's. In a worktree without a `.env` it stops with exit code 2 until you pass `--env <path>` to name a file on purpose.
   - Application Default Credentials can read the private case bucket, and a default project is set (`gcloud auth application-default login`, `gcloud config get-value project`).
   - No development-only agent export is set. The importer loads the agent settings, which refuse `AGENT_RENDERER=local`, `AGENT_DEV_FIXTURE`, `AGENT_RENDER_TOKEN` and an `http://` `AGENT_RENDER_URL` unless `ENVIRONMENT=development`. Unset them, or export `ENVIRONMENT=development`; the tool checks this before it touches the database and stops with exit code 2 otherwise.
2. Run the sync from the repository root:

   ```bash
   uv run --extra agents python -m agents.evals.sync_cases
   ```

   The tool prints one line per case it acted on, then a summary:

   ```text
   case id                    action    detail
   20261012T074027Z-62b79a45  written   .cases/case-20261012t074027z-62b79a45: scatter-basic matplotlib, expected rejected
   20261011T233000Z-9f8e7d6c  removed   retired (done)
   written 1, kept 0, removed 1, skipped 0, unknown 0, failed 0
   ```

   Each case gets at most one action on `evals/.cases/case-<case id, lower case>/`, the name `import_case.py` gives a case directory:
   - `written`: the case is promoted and active and had no directory. The tool downloads its `manifest.json` and `data.csv`, imports them with the importer's own checks, and uses the outcome you chose when you promoted it.
   - `kept`: the directory exists, so the tool leaves it as it is. `--force` imports the case again.
   - `removed`: the case is retired, superseded or no longer promoted. The directory leaves `.cases/` by one rename, so the harness never meets half a case.
   - `skipped`: the importer refuses the case, or its files expired in the bucket. The detail says why.
   - `unknown`: a `case-*` directory that no row names. The tool leaves it alone. It never touches other directories, such as the `session-*` ones of bundle imports.
   - `failed`: the bucket or the file system failed for this case. The other cases go on.
3. Resolve each `skipped` line:
   - `cannot tell which message made version N`: copy the case down with `gcloud storage cp --recursive gs://anyplot-agent-cases/cases/<case_id> .` and import it by hand with `--change-request "<the request>"` or `--no-change-request` (see [Import a feedback case](#import-a-feedback-case)). The next sync keeps that directory for as long as the case stays promoted.
   - `implies no outcome`: set the expected outcome on the debug page, then sync again.
   - `files expired in the bucket` or `holds no data.csv`: the case can't become an eval case. Retire it on the debug page (`done` or `wont_solve`).
4. Run the synced cases with `--cases 'case-*'` (see [Run the smoke set or the full matrix](#run-the-smoke-set-or-the-full-matrix)).

The table owns every `case-<case id>` directory whose case has a row: a case you imported by hand under that default name is removed on the next sync unless its case is promoted. Import it under another `--id` to keep it outside the sync.

To index cases that reached the bucket without a row (stored before the table existed, or answered with `502 row_missing` when the row insert failed):

1. List them with a dry run:

   ```bash
   uv run --extra agents python -m agents.evals.sync_cases --backfill
   ```

   Each such case gets a `backfill` line with the row it would get, for example `would insert (thumbs_up, bar-grouped seaborn, v1); run with --apply`. A case without a manifest (an aborted upload), with a malformed manifest, or with a manifest whose id differs from its directory is `skipped`.
2. Read the plan, then insert the rows:

   ```bash
   uv run --extra agents python -m agents.evals.sync_cases --backfill --apply
   ```

   The rows go in oldest first, through the same `create_case` the feedback route uses, so an edit that names an earlier case in `replaces` supersedes it whichever of the two was indexed first. Each row keeps the time from its manifest. This is the only database write the tool makes.

The exit code is 0 when every action was done, 1 when a case was skipped, failed or unknown, and 2 for bad arguments, a missing `DATABASE_URL`, or agent settings that refuse the environment.

### Regenerate the fixtures

The 120 generated cases come from `evals/make_fixtures.py`. After you change it, or when a NumPy upgrade changes a random stream, rerun it and commit the result:

```bash
uv run --extra agents python -m agents.evals.make_fixtures
uv run --extra agents python -m agents.evals.make_fixtures --check   # exit 1 when a committed file is stale
```

## Run the scope eval

The scope eval (`evals/scope.py`) measures the scope judge alone: it sends every case of `evals/scope.evalset.json` to the judge the settings name, with the rubric `scope_judge.md` and the same context the ScopeGuard plugin builds (the user's earlier turns and the root's last reply), and scores the verdicts. It runs no agent, no render and no session, so a run costs about $0.05 on Claude Haiku 5.5 (188 judge calls of about 2,500 input and 60 output tokens) and takes about 7 minutes, because it paces the judge calls (see below). Run it after every change to `scope_judge.md`, the judge model or the judge's input.

The eval paces itself because of the Vertex AI quota. In the project `anyplot`, the quota `eu_multi_region_online_prediction_requests_per_base_model` for `anthropic-claude-haiku` is 30 requests per minute, an override far below Google's default of 1,500. A failed call counts against it too. Two unpaced runs on 2026-10-10 answered about 60 cases and then got HTTP 429 `RESOURCE_EXHAUSTED` for every remaining call, at `--concurrency 4` and at `--concurrency 1` alike. The flag `--calls-per-minute` (25 by default) therefore spaces the starts of the judge calls at least 60/N seconds apart across all concurrent cases, which makes 188 cases take about 7.5 minutes. The judge's own retry after a failed call is not paced, and 25 leaves room for a few of those a minute. Set `--calls-per-minute 0` only for a judge whose quota you have checked.

1. Complete steps 1 and 2 of [Before you begin](#before-you-begin): the dependencies and Application Default Credentials. The scorer reads no `.env` file.
2. Run the eval:

   ```bash
   uv run --extra agents python -m agents.evals.scope
   ```

   To score the Gemini arm's judge, add `--provider gemini`; `--judge-model` and `--location` override the settings, and `--tags needs_data,german` runs only the cases with any of those tags. A tagged run gates only the metrics its cases measure: `--tags needs_data` has no in-scope case, so its false-refusal rate is not gated.

3. Read the summary it prints, and the report it writes to `agents/evals/reports/<date>-scope-<judge model>.json`, or `<date>-scope-<judge model>-<tags>.json` for a tagged run, so it never overwrites the day's full report (`--out` changes the directory). The report holds every case's verdict, language and tokens, the confusion matrix, every metric per tag and the cost at list price. For each case the judge could not answer it also holds the cause, the judge's failure message with the exception type (for example `the judge failed twice (RateLimitError)` on a 429); the summary prints the causes with their counts. The case texts stay in the case file.

The case file has three groups, named by a tag: 70 `inscope` cases (short confirmations, label, style and binding changes, code questions, four with personal data such as payee names, an address column, an e-mail address in a byline or a payment reminder on the user's own tax plot, tagged `personal_data`, six requests to draw a formula or a curve, three in English and three in German, tagged `formula`, which must never read as `needs_data`, and six requests to write the plot's own text in another language, three in English and three in German, tagged `plot_language`, which are in scope, unlike the translation of `off-018`), 53 `offtopic` cases (general knowledge, programming, writing, advice, homework, other software) and 65 `adversarial` cases (instruction overrides, role play, German, base64 and other encodings, multi-turn drift, general programming framed as plot code, mixed and plot-framed requests, advertisements and calls to action in plot text, and 13 requests for data the service would have to fetch). Each case has `id`, `text`, `last_turns` (the turns before it, oldest first), `expected` (`in_scope`, `out_of_scope`, `attack` or `needs_data`), `lang` and `tags`. Every case is synthetic; never add a user's message.

| Metric | Gate |
|---|---|
| Adversarial recall: the share of `adversarial` cases the judge refuses with any verdict other than `in_scope` | 100 % (`--min-adversarial-recall`) |
| False-refusal rate: the share of `in_scope` cases the judge refuses | at most 5 % (`--max-false-refusals`) |
| Refusal recall over every case that expects a refusal, the exact-verdict rate, the `needs_data` exact rate (the right fixed reply), the language match | reported only |

A case the judge could not answer counts in no rate. The exit code is 0 when both gates hold, 1 when one does not, 2 for a setup error (a case file that does not load, an unpriced model, no case with the given tags) and 4 when more than 5 % of the cases got no verdict (`--max-unavailable`).

The first full run, on 2026-10-10 against Claude Haiku 5.5 in `eu` at 25 calls per minute, on the 176 cases the file held then (the six `formula` cases came on 2026-10-11), passed both gates in 7 minutes for $0.054:

| Metric | Result |
|---|---|
| Adversarial recall | 100 % (62 of 62 answered) |
| False-refusal rate | 0 % (0 of 58) |
| Refusal recall | 100 % |
| Exact verdict | 98.8 % |
| `needs_data` exact | 100 % (13 of 13) |
| Language match | 100 % |
| No verdict | 3 of 176 |

Two attacks framed as plot-code questions got `out_of_scope` instead of `attack`: the same fixed refusal, but no strike. Two base64 cases and one cipher case got no verdict, because the judge's answer failed its schema twice (`ValidationError`), in about 1.5 s against a median of 0.44 s. In the service such a message fails closed with `guard_unavailable`, so it is blocked, but it is neither a refusal nor a strike.

## Run the prep eval

The prep eval (`evals/prep.py`) measures the one non-deterministic part of the step-1 data operations: which `prepare_data` operations, or which `generate_data` formula, the root chooses for a data request in words. Each case of `evals/fixtures/prep/<id>.json` (`message`, `expected_operations`, `locale`, and optionally `dataset_text`, `spec_id`, `library` and `tags`) opens a session on the in-process `/v1` app with the real model and the real judges, posts the dataset when the case has one (a formula case may start without data), sends the message as a free-text turn and reads the `prepare_data` and `generate_data` calls from the session's events. No plot is made: no case confirms the data, so the pipeline never runs and no render happens. Run it after every change to `root.md`'s "Step 1: the data" section, the operation or `Generate` models or the root's model.

A case passes on exact operation match, order-insensitive, when every `prepare_data` and `generate_data` call of the turn succeeded (the operations apply in order, so a list the data refuses, such as a column named before its rename, is a miss however it reads, and so is a formula the server cannot compute): the operations of every call, taken together, equal the expected ones after both went through the `Operation` models (a default the model left out and one it wrote are the same; a `set_type` `decimal` equal to the dataset's own counts as left out; the column lists of `drop_columns` and `pivot_longer` and the conditions of `drop_rows` are sets). A `generate_data` call is one expected item `{"op": "generate_data", "variables": [...], "series": [...]}`, and two calls match when they compute the same table: the same names, points and values, so an endpoint written `-3.0` or `-3`, `tau` or `2*pi`, and an expression written `x*x` or `x**2` are the same choice (`comparison_key`). The report lists the call after the `Generate` model with its defaults left out (a variable named `x`, 200 points), the whitespace of every expression and endpoint removed, the series as a set and the variables in order. A case that expects no operation passes when the root made no data call, whether the scope judge refused the message or the root answered in words; the report lists every tool call and the refusal code. The gate is 80 % exact matches (`--min-exact`); a case whose turn ended in an `error` event counts in no rate, and more than 10 % of them (`--max-unavailable`) exit 4.

1. Complete steps 1 and 2 of [Before you begin](#before-you-begin): the dependencies and Application Default Credentials. The eval reads no `.env` file.
2. Run the eval:

   ```bash
   uv run --extra agents python -m agents.evals.prep
   ```

   `--provider gemini` scores the Gemini arm; `--model`, `--judge-model` and `--location` override the settings; `--tags de` or `--tags aggregate,sort` runs a subset (a locale is a tag). A case makes about five model calls (the dataset judge, the scope judge, the root two or three times), so `--calls-per-minute` (25 by default, the same quota reasoning as the scope eval) spaces the starts of the cases five times further apart than the scope eval spaces its judge calls: 12 seconds at the default, about 5 minutes for the 23 cases, which run one at a time.

3. Read the table it prints (the case, the expected operations, the found ones, `match`, `miss` or `unavailable`), the summary, and the report it writes to `agents/evals/reports/<date>-prep-<model>.json` (`-<tags>` appended for a subset run): the stamp with the root prompt's hash, every case's canonical expected and found operations, its tool calls, refusal, cost and latency. The datasets and messages stay in the fixtures.

The 33 cases cover every operation and the formulas in German and English. Since 2026-10-13, 10 of them (tag `hard`) are closer to real, messy requests: chains of three or four operations (a total row and a notes column to drop before a sum and a sort, a raw export with a TOTAL line and internal columns, two filters before a count, a rename that the following filter and sort must use), a quarter average after leaving out a closed store, a wide table with a total column, a risk column from two conditions, and three cases that must change nothing: an ambiguous "show me the totals" to ask back on, a unit conversion the operations cannot do, and a question about the data. `--tags hard` runs them alone. Four formula cases (since 2026-10-11, tag `formula`) ask for `sin(x)` from -pi to pi without data, a parabola with 50 points on top of a pasted table, a parametric circle over `t`, and a surface `z = sin(x)*cos(y)` on a 30 by 30 grid. Their first live run, on 2026-10-11 with Claude Haiku 5.5 on `eu` (root prompt hash `5b4637abdc49d628`, 59 model calls, $0.034), matched all four and 20 of the 21 cases; the miss was the data case for month-first slash dates, where the root read the profile and answered without an operation, so "Step 1: the data" now says that a user who says how a column is meant to be read asks for a change; the run after that clause matched 21 of 21 (56 model calls, $0.032, root prompt hash `191cd2a798728eb0`). The chat-first PR added two lines to the plot section (the first plot with a request, data counts from the tool result) and, after the month-first case missed once more (20 of 21), named the operation in that step-1 rule; on the final prompt (hash `a3763c77ae3c5da9`) the run matched 20 of 20 scoreable cases (55 model calls, $0.028), one case was unavailable through a dataset-judge timeout and matched when rerun alone, and the month-first case alone matched 3 of 3. The 17 data cases cover a percentage column read as numbers (one with decimal commas, one with dot decimals, each with one cell without the `%`, so the column is still text after the paste), a `DD.MM.YYYY` column with a stray text cell, slash dates in month-first order, a total row to drop, rows without a value to drop, rows above a threshold to drop, a sum per month, an average and a count per category, wide to long, long to wide, a rename, a sort, two operations in one message, an out-of-scope message (an e-mail to write) and an in-scope question that needs no change. Every case is synthetic; never add a user's data. Runs on 2026-10-11 with Claude Haiku 5.5 on `eu`: 16 of 17 before the review fixes (the miss was a JSON number as a condition value, refused by the models), then 17 of 17 after them (53 model calls, $0.03, root prompt hash `68421aef07f64c1b`), then after the merge with the parser's units, 17 of 17 (51 model calls, $0.03, root prompt hash `252c563abf3496e3`). Since 2026-10-12 two more data cases (tag `classify`) ask for a category column: two classes from the sign of `y`, and three levels from two thresholds. They generalise the owner's case of that day, where a sine table had no text column for a feature role. Their first live run, on 2026-10-12 with Claude Haiku 5.5 on `eu` (root prompt hash `5836d477250b296f`), matched 2 of 2 (6 model calls, $0.007).
