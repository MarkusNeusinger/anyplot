# Agent network design

> **Status (2026-10-09):** design, with the first pieces built: the `agents/` package skeleton (ADK pin, `AgentSettings` and the Pydantic contracts in `agents/anyplot/schemas.py`), the deterministic data layer in `agents/anyplot/data/` (the parser, data roles, default bindings and the dataset store described under [Parse](#parse); `bindings.apply` and the routes that call it are not built), the two-profile AST validator in `agents/anyplot/code/validate.py`, the `/debug/agent` BFF router in `api/routers/agent.py` (shipped dark behind `AGENT_ENABLED`), and two shared building blocks, `core/canvas.py` (the canvas gate and the PNG auto-reject checks) and `core/defects.py` (the review feedback grammar). Nothing else in this document is built yet. The research behind it was verified against ADK v2.11.0 and the Vertex AI documentation on 2026-10-08; re-check version-sensitive facts (model ids, prices, ADK APIs) before you implement a section.

This document describes the agent network that lets a visitor paste their own data on a plot page and get that plot adapted, rendered and reviewed ("Use with my data"), and later helps them find the right plot type. It is built with [Google ADK](https://adk.dev) (Python) on Gemini through Vertex AI (now branded Gemini Enterprise Agent Platform) inside the `anyplot` GCP project.

## Goals and fixed decisions

| Topic | Decision |
|---|---|
| Product step 1 | "Use with my data": the user pastes data on a plot page, the network adapts the catalogue implementation for that spec and library to the data, renders it in a sandbox, reviews it once with at most one repair round, and returns the image and the code |
| Product step 2 | "Find the right plot type", built on the catalogue knowledge that also backs the MCP server |
| Result delivery | Users see and copy both the image and the code: the plot is shown inline in light and dark, can be copied to the clipboard and downloaded as PNG; the code is shown with syntax highlighting, copied with one click, and downloaded together with `data.csv` so it runs unchanged |
| Render scope | Python first (matplotlib and seaborn in phase 1), designed so the other 13 libraries are additive |
| Data input | Paste text only (CSV, TSV, semicolon CSV, JSON), hard cap 200 KB |
| Access | Visible only in local development and for admins, gated exactly like `/debug/*`; not public in phase 1 |
| Guardrail scope | Allowed: choosing plots, the user's data for them, adapting, rendering and styling, and questions about catalogue code (styling, exports). Everything else gets a fixed refusal |
| Runtime | A separate Cloud Run service. The managed Vertex code-execution sandbox is Python/JS only with a fixed library set (no kaleido, altair, plotnine, pygal, lets-plot, R, Julia, or Chromium), so it cannot render the catalogue |
| Model | Gemini `gemini-3.8-flash` pinned everywhere; the scope judge runs on `gemini-3.5-flash-lite`. Not the `gemini-flash-latest` alias: it is undocumented on Vertex, its served version is unobservable, and it returned 404 once when its target retired. "3.8" in this document always means this Gemini model, never a Python version |
| Python | Python 3.13 everywhere, the same as the pipeline |
| Location | The `eu` multi-region from day one. No Gemini 3.x Flash is served in europe-west4; `eu` keeps ML processing in the EU at +10 % price and is compatible with the privacy page's EU claim |
| Language | Replies in the user's language; code, comments and generated wording in English; labels keep the user's column names |
| Quick feedback | From phase 1, one click plus a short text on any result submits the whole case (conversation, code, images, data profile, optionally the data file, model and prompt config) for tuning; opt-in for real users later |
| Model-version testing | From phase 1, a regression harness so a newer Gemini version or a prompt change is one command or one workflow dispatch with a diff report against the pinned baseline |
| Catalogue normalisation | A parallel pipeline workstream makes catalogue code data-derived and canvas-correct at the source |
| Licensing | Everything stays open under MIT in this repository, `agents/` included; copyability is accepted. Selling AI credits to people who create plots often remains a later option. The sister project's "open core" reserves learned data rather than code, and this design does the equivalent: user data, feedback cases and promoted eval cases live only in the private bucket, never in git, so the legal page's statement that the entire codebase is MIT stays true. Before the first paid credit, the Highcharts licence must be settled (its free licence excludes platforms with direct or indirect revenue): buy one or keep Highcharts out of paid features. Source-available licences (FSL, BUSL, PolyForm) and AGPL were assessed on 2026-10-09 and rejected |

## What the research settled

- **ADK 2.11.0, 2.x idioms only.** `from google.adk import Agent, Workflow, Event, Context`; plugins on `App(plugins=[...])`; sub-agent modes `task` and `single_turn`; a `Workflow` with a Pydantic `input_schema` passed in `tools=[...]` becomes a NodeTool whose progress events reach the stream. `SequentialAgent`, `LoopAgent` and `ParallelAgent` are deprecated, `AgentTool` is discouraged (its events never reach the stream), `global_instruction` is deprecated, and `GOOGLE_GENAI_USE_ENTERPRISE=TRUE` replaces the Vertex flag. `abort_signal` is a `Runner.run_async` keyword argument, not a `RunConfig` field. `instruction` strings get `{var}` state templating (a missing key raises); `static_instruction` is sent unchanged.
- **ADK's own server is never exposed.** `adk web`, `adk api_server` and `get_fast_api_app` are unauthenticated and let the client choose the user id and write state, events and artifacts. The network embeds `Runner.run_async` in its own FastAPI routes.
- **No agent gets a `code_executor`.** ADK auto-runs the first fenced code block the model emits. Rendering is a deterministic tool that calls Cloud Run sandboxes (`gcloud beta run deploy --sandbox-launcher`, gen2, Preview, no extra cost): `sandbox do` has no egress, no environment, secrets or metadata server, and a read-only root filesystem. Region availability and Chromium, R and Julia inside the sandbox are undocumented, so a spike gates phase 1.
- **Adapting catalogue code is not a data swap.** 172 of 325 matplotlib files set axis limits with data-scale literals, 87 place annotations at numeric data coordinates, literal statistics are common, and 137 matplotlib and 138 seaborn files already fail the 3200x1800 canvas gate (`bbox_inches='tight'`). A pure swap passes the structural gates in 40 of 63 runs and 0 of 7 for date axes. Structured search-and-replace hunks of about 100 to 180 output tokens passed all gates in a proxy test. Inline data literals are infeasible beyond a few hundred rows, so data travels as a sidecar `data.csv`.
- **Catalogue access is in-process.** The six FastMCP tools in `api/mcp/server.py` are plain async functions, but they raise `ValueError` (which aborts an ADK run unless handled), and over HTTP every result reaches Gemini twice. Their category-scoped AND search, `# noqa` stripping and slimmer payloads (no review internals) landed on 2026-10-09, so the in-process wrappers only need error handling and fencing.
- **Infra constraints.** `anyplot-api` is a single Cloud Run instance (1 vCPU, 1 GiB, concurrency 40) running as the default compute service account with `roles/editor`; `anyplot-images` is a public bucket; `aiplatform.googleapis.com` is not enabled; the API image has no plotting extras, R, Julia, Node or Chromium.
- **Privacy.** The privacy policy in `app/src/pages/LegalPage.tsx` says the AI never sees a visitor's request and that everything runs in europe-west4. The owner-only phase 1 is compatible. Any non-owner use needs a legal-page PR, a retention design, and the owner's answer on the GCP agreement type (abuse-monitoring prompt logging for up to 90 days under the standard terms).
- **Cost on `eu` with Gemini 3.8 Flash.** List price $1.65 input and $8.25 output per 1M tokens; a 50 % credit makes the effective price $0.825 and $4.125 through 2026-12-31. The judge model costs $0.33 and $2.75. The lean path is about $0.035 to $0.05 per successful plot at promo prices. Spend caps count list price, not the promo. Gemini 3.8 Flash is in the short-term availability tier (no retirement date yet, at least 45 days' notice) and not on the Standard PayGo tier list, so expect 429s and plan a model bump gated by evals.

## Architecture

```
Browser ──fetchWithAuth──► anyplot-api  /debug/agent/*   (require_admin → AdminIdentity, CSRF header, AGENT_ENABLED kill switch)
                             │ ID token (roles/run.invoker) + X-Anyplot-User + X-Request-Id
                             ▼
                       anyplot-agents  (Cloud Run gen2, --sandbox-launcher, --no-allow-unauthenticated, own service account)
                         FastAPI /v1/* → Runner(app=App(plugins=[ScopeGuard, Budget, ToolSafety, ContextFilter(6)]))
                           root "anyplot" ── session tools ── plot_pipeline (Workflow NodeTool, input_schema=PipelineArgs)
                                @node run_pipeline:  adapter → apply + validate → render x2 (sandbox do) → gates
                                                     → reviewer (≤1) → repair (≤1) → Event(output=PlotResult)
```

Only one agent talks to the user. Everything the research shows an LLM does not improve (parsing, default bindings, the data loader, the canvas, safety checks, export) is plain code.

### Agents

| Agent | Kind | Model and thinking | Instructions | Tools | Output |
|---|---|---|---|---|---|
| `anyplot` (root) | `Agent` with no `mode` (chat root); the only user-facing agent | `AGENT_MODEL` (gemini-3.8-flash), `thinking_level=LOW`, `max_output_tokens` 2048 | `static_instruction` from `agents/anyplot/prompts/root.md`: scope list, fixed-refusal rule, reply-language rule, tool rules, the "never" list. An `InstructionProvider` adds only server-validated values (locale, spec id and title, library, dataset status, whether bindings are complete) | `get_dataset_profile`, `get_spec_brief`, `get_current_code(version)`, `set_bindings`, `plot_pipeline`. Phase 2 adds `find_specs`, `get_spec_knowledge`, `select_spec` | Chat text |
| `adapter_<library>` | `Agent(mode="single_turn")`, one per enabled library, run with `ctx.run_node` inside the pipeline, `include_contents='none'` | `AGENT_MODEL`, `thinking_level=MEDIUM`; `max_output_tokens` 2048 for edit-only calls, 12288 when a full file is allowed | `static_instruction` (never `instruction`, because the verbatim prompt files contain `{THEME}`, `{lang}` and `{lib}` braces that ADK would template): `prompts/adapter.md` plus `prompts/default-style-guide.md` and `prompts/library/<lib>.md` verbatim, about 8k to 10k tokens, above the 6,144-token implicit-cache minimum of Gemini 3.8 Flash | none | `AdaptPlan` |
| `reviewer` | `Agent(mode="single_turn")`, no tools; its `before_model_callback` appends both PNGs as ordinary user content at `media_resolution=MEDIUM` (560 tokens each), loaded by `render_id` from the render store, never from state | `AGENT_MODEL`, LOW | `static_instruction` from `prompts/reviewer.md`: a reduced checklist (VQ-01, VQ-02, VQ-03, VQ-06, VQ-07, SC-01, SC-03, DQ-03 for stale claims, AR-09 for clipping), the theme-readability and defect-grammar sections adapted from `prompts/workflow-prompts/ai-quality-review.md`, and the style guide | none | `Verdict{ok, defects[]}` with fixed ids, rendered into the existing `DEFECT_RE` grammar on the server |
| Scope judge (not an agent) | A direct google-genai call inside `ScopeGuardPlugin`, client built as `genai.Client(enterprise=True, project=..., location=settings.location)` | `AGENT_JUDGE_MODEL` (gemini-3.5-flash-lite), JSON schema, 4 s budget with one retry, its own safety filters off | `prompts/scope_judge.md` | none | `{verdict: in_scope|out_of_scope|attack, lang}` |

The root's "never" list, enforced by the stream translator and the evals: never write or run code (code changes happen only through `plot_pipeline`; code answers are short prose that references lines from `get_current_code`; the translator strips fenced code blocks longer than 10 lines); never invent spec ids; never quote data rows; never emit URLs, HTML or markdown images; never claim success unless `PlotResult.status` is `ok` or `needs_attention`.

Rules for every agent:

- Models come only from `make_model()`, which returns `Gemini(model=..., client_kwargs={"enterprise": True, "location": settings.location}, retry_options=HttpRetryOptions(attempts=3, initial_delay=1))`. The bare `Gemini()` default is the retiring 2.5 Flash and is never used.
- No `FallbackModel` in phase 1. A fallback would need a second model id or the `global` endpoint, which breaks the pins; persistent 429s map to `error{code:"capacity"}`. A named fallback on `eu` is an explicit owner decision.
- Explicit `safety_settings` at BLOCK_MEDIUM_AND_ABOVE, low-cardinality `labels`, and no temperature, top_p or thinking budget on Gemini 3.
- `agents/anyplot/agent.py` keeps an explicit registry `ALL_AGENTS = [root_agent, *ADAPTERS.values(), reviewer]`, because the adapters and the reviewer are started with `ctx.run_node` and a tree walk from the root would miss them. A unit test iterates the registry and `App.plugins` and asserts: no `code_executor`, `google_search`, `url_context`, `AgentTool`, `LoggingPlugin` or chat-mode sub-agents; no agent has a non-empty string `instruction`; every model string and client location comes from settings.
- Settings defaults in `AgentSettings` (`agents/anyplot/settings.py`, read from `AGENT_*` variables): `model="gemini-3.8-flash"`, `judge_model="gemini-3.5-flash-lite"`, `location="eu"`. The settings refuse `-latest` aliases, any location other than `eu`, `us` or `global`, and `renderer="local"` outside development.

Deviations from the first sketch, each evidence-backed: there is no data-intake LLM agent in step 1 (about 320 of 325 specs declare typed `## Data` role bullets, so default bindings are deterministic and confirmed in UI dropdowns; parsing must be code anyway because `thousands='.'` silently corrupts `DD.MM.YYYY` dates); the reviewer is tool-less (GA image path, native `response_schema`, nothing persisted in session events, no `load_artifacts` listing of `data.csv`); the domain knowledge lives in tools and prompts rather than in a separate expert agent.

### Request flow for "Use with my data"

1. The `.adapt()` overlay button in `SpecDetailView` does a full navigation to `/debug/agent?spec=&library=&language=`.
2. `POST /debug/agent/sessions {spec_id, library, locale}`. The BFF validates the spec and library against `core/constants.py` and the enabled libraries from anyplot-agents `GET /v1/status` (cached), loads a catalogue snapshot through `core/catalogue/queries.py` (title, description, data roles, notes, noqa-stripped code, library version), derives the user id, and forwards it. anyplot-agents normalises the code, runs the readiness scan and the SECURITY validator, and answers `422 not_eligible` for blocked pairs (the 13 map specs, validator failures, files without a `THEME` block or with a non-literal savefig target). anyplot-agents has no database access in phase 1. `GET /debug/agent/eligibility?spec=&library=` gives the button the same answer.
3. `POST .../dataset {text}` runs the deterministic parse and returns a 20-row preview, the `DatasetProfile`, default bindings and warnings. One judge call on the dataset's headers, top values and sample cells (at most 3 KB) with a data rubric refuses instruction-like datasets. No other LLM call happens.
4. The user adjusts the bindings in dropdowns (`PUT .../bindings`) and clicks **Create plot**, which sends `POST .../messages {action: "create_plot"}`. The server sets the context variable `REQUEST_KIND=action`, so the judge is skipped, and sends a fixed message.
5. Root call 1 calls `plot_pipeline({})`. `PipelineArgs` has no spec, library or dataset field; those come from server-set session state, so neither the model nor an injection can redirect the pipeline. Without a dataset or with incomplete bindings the pipeline returns `PlotResult(status="not_ready", reason=...)` before any LLM call.
6. The pipeline streams `adapting`, `checking`, `rendering`, `reviewing` and `repairing` and always ends with `Event(output=PlotResult)`. A `None` output would raise `NodeInterruptedError`.
7. Root call 2 writes a short reply in the user's language. The UI fetches the PNGs, `plot.py` and `data.csv` through the BFF.
8. Free-text follow-ups go judge → root → `plot_pipeline(change_request, base="previous")`, `set_bindings`, or a code answer through `get_current_code`. The library pills call `POST sessions/{sid}/library`, which loads a new snapshot and keeps the dataset and bindings.

The pipeline is a code-bounded loop, never a graph cycle, wrapped as `plot_pipeline = Workflow(name="plot_pipeline", input_schema=PipelineArgs, edges=[("START", run_pipeline)])` so the tool name is stable:

```python
@node(rerun_on_resume=True)
async def run_pipeline(ctx: Context, node_input: PipelineArgs):
    s = PipelineState.load(ctx)                        # spec, library, snapshot, dataset_id, bindings (server-set)
    if not s.ready:
        yield Event(output=PlotResult.not_ready(s.reason)); return
    deadline = SoftDeadline(140)                       # abort_signal at 180 s is the hard backstop
    best, best_defects, best_reviewed = None, [], False  # the best render that passed R1+R2 and whether the reviewer saw it
    review_defects, reviewer_used, feedback, reason = [], False, [], None
    try:
        for attempt in (1, 2):
            if not budget.check(ctx): reason = "budget"; break
            if attempt == 2 and not deadline.allows(adapter_p95 + render_timeout): reason = "deadline"; break
            yield Event(message="adapting" if attempt == 1 else "repairing")
            req = s.adapt_request(node_input, feedback, allow_full=(attempt == 2))   # code = latest validated working form
            plan = await ctx.run_node(adapter_for(s.library), req)
            yield Event(message="checking")
            working, feedback = apply_and_validate(s, plan)   # edits → ADAPTED-profile validator (placeholder allowed)
            if feedback: continue
            yield Event(message="rendering")
            run_form = substitute_loader(normalise(working))  # the run form is the exported code
            result = await renderer.render(s.render_job(run_form), timeout=deadline.clamp(render_timeout))
            if result.passed_host_gates:                     # R1 and R2 passed; R3 passed or was padded
                best, best_defects, best_reviewed = result, result.defects, False
            feedback = result.defects                        # R3 miss and advisory probe gates feed the single repair
            if feedback or reviewer_used: continue
            yield Event(message="reviewing")
            verdict = await ctx.run_node(reviewer, s.review_request(run_form, result))
            reviewer_used, best_reviewed = True, True
            review_defects = [d.as_line() for d in verdict.defects]
            feedback = review_defects
            if verdict.ok: break
    except Exception:
        reason = "error"
    finally:
        yield Event(output=s.finish(ctx, best, best_defects, best_reviewed, review_defects, reason))  # every path
```

`finish` returns `ok` only when `best` exists, the reviewer saw exactly that render (`best_reviewed`) and passed it, and the canvas was not padded; `needs_attention` when `best` exists but either the reviewer never saw it after giving defects (a repair that was not re-reviewed; the first review's lines become residual defects), or the canvas had to be padded, or advisory probe gates still report defects; `failed` when no render passed R1 and R2, with `reason` in `validation`, `render`, `deadline`, `budget` or `error`. The translator maps an abort without a `PlotResult` to `error{code:"deadline"}`.

Bounds: at most 2 adapter calls, 1 reviewer call and 2 render rounds of 2 themes per run; `ToolSafety` allows at most one `plot_pipeline` call per invocation; `RunConfig(max_llm_calls=12, streaming_mode=StreamingMode.NONE)` (`ADK_MAX_LLM_CALLS=20` only sets the default for runs without a `RunConfig`, such as `adk web` and evals, so the budget plugin enforces the request cap too); 60 s per render, host-enforced and clamped to the remaining soft deadline; a 180 s request deadline through `abort_signal` plus task cancellation on disconnect; one active run per user (409); two concurrent renders per instance. A typical "Create plot" costs 4 LLM calls (root twice, adapter, reviewer); a repair adds one; each free-text turn adds one judge call.

### Request flow for "Find the right plot type" (phase 2)

The compact `id|title|cat:tags` index (about 13.7k tokens, cache-eligible) is appended to the root's `static_instruction` in phase 2 only; step 1 is page-scoped and the index would cost those tokens on every root call. The root calls `find_specs` (AND across categories, OR within one, values checked against the tag vocabulary) and `get_spec_knowledge` (including the synced "What a good version looks like" bullets) for at most three candidates, derives filters from the pasted profile, and replies with `[[spec:id]]` tokens that the UI turns into cards. `select_spec` validates the choice and swaps the snapshot. Embeddings (pgvector 0.8.5 on Cloud SQL PostgreSQL 18 plus gemini-embedding on `eu`) are added only if evals show that the index is insufficient.

### anyplot-agents internal API (`/v1`)

Callable only with Cloud Run IAM; the BFF mirrors it under `/debug/agent`.

| Route | Body and result | Errors |
|---|---|---|
| `GET /v1/status` | `{libraries, model, location, version}` | |
| `POST /v1/sessions` | `{user, spec_id, library, locale, snapshot: CatalogueSnapshot{spec_id, title, description, data_roles[], notes[], code, library_version}}` (at most 64 KB) → `{session_id, eligibility}` | `422 not_eligible` |
| `POST /v1/sessions/{sid}/library` | `{library, snapshot}`; keeps dataset and bindings | `422`, `409 run_active` |
| `POST /v1/sessions/{sid}/dataset` | `{text}` → `{preview, profile, bindings, warnings}` | `413 too_long`, `422 unparseable`, `403 data_refused` |
| `PUT /v1/sessions/{sid}/bindings` | `[Binding]`, validated by `bindings.apply` | `409 run_active`, `422` |
| `POST /v1/sessions/{sid}/messages` | `{text}` (at most 2,000 chars) or `{action}` → SSE `anyplot/1` | `413 too_long`, `409 run_active` |
| `POST /v1/sessions/{sid}/cancel` | Sets `abort_signal` and cancels the task | |
| `GET /v1/sessions/{sid}/artifacts/{name}?v=` | Allowlist `plot-light.png`, `plot-dark.png`, `plot.py`, `data.csv` | `404` |
| `GET /v1/sessions/{sid}/bundle?version=&include_data=` | The server-assembled feedback case bundle | `404` |
| `DELETE /v1/sessions/{sid}` | Purges the session, the dataset store and the render store | |
| any | `404 session_expired` after scale-to-zero or the idle sweeper | |

Headers: `X-Anyplot-User` (the HMAC id from the BFF) and `X-Request-Id`. Caller check: Cloud Run IAM verifies the ID token and forwards the `Authorization` header with the signature replaced, so the app decodes the claims without signature verification and requires `aud` in `{AGENT_SERVICE_URL, candidate-tag URL}` and `email` in `AGENT_ALLOWED_CALLERS`. A missing header is rejected when `ENVIRONMENT=production`; the check is skipped only in development. This is weak while anyplot-api runs as the shared compute service account; a dedicated API service account is an owner task before public use.

## Contracts

Schemas live in `agents/anyplot/schemas.py`: `ColumnProfile{name≤64, dtype, missing, unique, min, max, top≤5}`, `DatasetProfile{rows, columns≤50, sample≤5 rows with cells≤40 chars fenced as <user_data>, source_format, decimal, warnings}`, `Binding{role ^[A-Za-z_][A-Za-z0-9_]{0,31}$, column}` (digits and capitals because 21 of 325 specs name roles such as `log2_fold_change`, `lower_95` or `temperature_K`), `PipelineArgs{change_request≤600, base: catalogue|previous}`, `AdaptRequest{code (working form), profile, bindings, loader_columns, hints, change_request, feedback, previous_plan?, allow_full}`, `Edit{find (exactly one match), replace}`, `AdaptPlan{edits≤20, full_code≤24 KB (attempt 2 only), title≤120, changes≤5}`, `ReviewRequest{render_id, code, bindings, profile_summary, spec_brief, change_request, gate_notes}`, `Defect{id ∈ fixed set, theme light|dark|both|code, observed, target, likely_cause}`, `Verdict{ok, defects≤5}`, `PlotResult{status ok|needs_attention|failed|not_ready, reason?, attempts, artifacts, changes, residual_defects}`.

### Parse

`agents/anyplot/data/parse.py` has no ADK import. Limits: UTF-8 at most 200 KB, 50 columns, 20,000 rows and 200 characters per cell. It rejects NUL and control characters, strips the BOM, applies NFC, and strips zero-width and bidi control characters. Headers are canonicalised (NFC, control characters stripped, names over 64 characters renamed, duplicates suffixed, empty names become `column_N`, each rename a warning), and the canonical names are written into `data.csv`, which is the single source of column names. Formats: JSON records or a column map (nesting depth at most 2), or delimited text with the delimiter sniffed from `, ; \t |`. Everything is read as text first, then dates with explicit formats (an ambiguous day/month order is a warning), then numbers; a decimal comma is accepted only with a date guard. The output is a canonical `data.csv` (comma, dot decimal, ISO dates) in a session-scoped dataset store (in memory, tied to the session's lifetime, the idle sweeper and the DELETE route; never a `user:` artifact, which would outlive the session and be listable by the model), plus the profile and default bindings (role dtype match, then name similarity, each column once; roles without typed bullets stay empty and the UI asks). `bindings.apply(session, bindings, source)` validates roles against the snapshot's data roles and columns against the profile; the PUT route (through `session_service.append_event` with a `state_delta`) and the `set_bindings` tool both call it, and both answer `409` while a run is active.

### Adapt and validate

`agents/anyplot/code/` has no ADK import. Every version has two forms: the **working form** contains the literal placeholder `df = load_user_data()` and is what the adapter edits; the **run form** has the loader substituted and the normaliser applied and is what runs and what the user downloads. Order of operations: apply the edits to the working form, validate with the ADAPTED profile (the placeholder is allowed), normalise, substitute the loader, then render and export the run form. `base="previous"` and attempt 2 always get the latest validated working form; if attempt 1 failed validation, attempt 2 gets the original plus the attempt-1 edits as `previous_plan`.

- **Normaliser** (per runtime; matplotlib and seaborn first): drop `bbox_inches`, keep the figure size and rescale the dpi so the output hits 3200x1800 or 2400x2400 exactly, strip the `sys.path` guard, the catalogue header and the catalogue title. The canvas is never an LLM repair target.
- **Readiness scan** on the normalised original: `blocked` (the 13 map specs, a library that is not enabled, a SECURITY validator failure, no `THEME` block, a non-literal savefig target), `coupled` (literal limits, data-coordinate annotations, literal statistics, short palettes, hard-coded date locators; these findings go to the adapter as hints), or `clean`.
- **Edits** apply in order. Each `find` must match exactly once and may not overlap a protected region. Protected regions are found by AST: the `THEME` assignment and every module-level assignment whose value tests `THEME == ...` (`PAGE_BG`, `ELEVATED_BG`, `INK*`, `GRID`, `BRAND`), the placeholder line, and the final savefig statement. The `IMPRINT` palette list is not protected: it must keep its existing entries in order and may only be extended with further positions from `core/palette.py`, which the validator checks.
- **Loader**: exactly one `df = load_user_data()` in the working form. The server replaces it with `pd.read_csv("data.csv", dtype=..., parse_dates=[...])` using a relative path, so the exported code also works in notebooks.
- **Validator profiles.** The SECURITY rules run on the normalised original (eligibility) and on every adapted working form: `ast.parse` on at most 48 KB; imports only from COMMON (numpy, pandas, math, statistics, datetime, collections, itertools, functools, textwrap, colorsys, re; not `string`) or the per-library allowlist (the plotting submodules, for matplotlib and seaborn also the bundled `mpl_toolkits.{mplot3d,axes_grid1,axisartist}`, `scipy.{stats,interpolate,signal,cluster.hierarchy,spatial,optimize,special,integrate,ndimage}`, sklearn without `datasets`, `statsmodels.{api,nonparametric,tsa,graphics}`; third-party helpers such as cartopy or adjustText stay out); never `statsmodels.formula`, `scipy.io`, `scipy.datasets`, sys, pathlib, importlib, subprocess, socket, urllib, requests, shutil, ctypes or pickle; `os` only as `getenv("ANYPLOT_THEME", ...)`; banned names `eval`, `exec`, `compile`, `open`, `__import__`, `input`, `breakpoint`, `globals`, `locals`, `vars`, `getattr`, `setattr`, `delattr`, `memoryview`, `exit`, `quit` and the three-argument `type()`; every name, attribute or keyword matching `^__\w+__$` and any string literal containing a dunder identifier; banned attributes `.format`, `.format_map`, pandas `.eval` and `.query`, `memmap`, `ctypeslib`, `f2py`, `matplotlib.use`, `show`; banned calls: pandas `read_*`, `ExcelFile`, `HDFStore` and the I/O writers (`to_csv`, `to_pickle`, `to_parquet`, `to_excel`, `to_sql`, `to_hdf`, `to_feather`, `to_json`, `to_html`, `to_clipboard`, but not `to_datetime` or `to_numpy`), `np.load*`, `save*`, `savetxt`, `fromfile`, `fromregex`, `DataSource`, `loadtxt`, `genfromtxt`, `ndarray.tofile`, `plt.imread`, `matplotlib.image.imread`, `matplotlib.cbook.get_sample_data`, `mpl.rc_file`, `load_dataset`, `fetch_*`, `urlopen`; no class, async, await, yield, global or nonlocal statements, no star or relative imports; no `http(s)://`, `ftp://`, `file:` or `data:` literals; string literals at most 200 characters and at most 2,000 characters of new literal text per plan; the savefig target is exactly `f"plot-{THEME}.png"`; `def` and `lambda` stay allowed for formatters. The ADAPTATION rules run on adapted code only: exactly one placeholder; no RNG used to create data (a seeded `np.random.default_rng(<int literal>)` is allowed for jitter and subsampling, and the row-fidelity gate catches fabricated data); numeric literal lists of at most 20 items; the palette prefix preserved. SECURITY failures reject the code and get the one repair; ADAPTATION failures become defect lines. Every bypass named here is a validator-corpus test.

### Render

`agents/anyplot/render/` defines `RenderJob{job_id, language, library, source, data_csv, themes, timeout_s}` and two protocols: `RuntimeAdapter` (`file_name`, `command` as the CI command verbatim, `env`, `loader_block`, `normalise`, `validate`, `collect`) and `RenderBackend` with the backends `sandbox` (phase 1), `local` (development only; refuses `ENVIRONMENT=production`; always `docker run --rm --network none --read-only --tmpfs /tmp -v <rundir>:/work <agents image> /app/.venv/bin/python -I /opt/anyplot/harness.py plot.py` with the production image, fails if Docker is missing, no bare-subprocess fallback), `fake` (unit tests, fixture PNGs) and `remote` (the phase-2 renderer split).

The sandbox command per theme, started with `asyncio.create_subprocess_exec` and never a shell:

```
/usr/local/gcp/bin/sandbox do --sandbox-name r-<job_id>-<theme> --write \
  --mount type=bind,source=/tmp/runs/<job>,destination=/work -w /work \
  --env ANYPLOT_THEME=<theme> --env MPLBACKEND=Agg --env MPLCONFIGDIR=/opt/mplconfig --env HOME=/tmp \
  -- /app/.venv/bin/python -I /opt/anyplot/harness.py plot.py
```

Both themes render in parallel under the semaphore. The process has its own group and is killed on timeout, followed by `sandbox delete r-<job_id>-<theme>`; the run directory is wiped; a code assertion forbids `--allow-egress`. `harness.py` sets resource limits (CPU and file size; the address-space limit is tuned in the spike), registers a `Figure.savefig` probe that writes `probe-<theme>.json`, then calls `runpy.run_path`.

Host gates: R1 (exit code and outputs present) and R2 (PNG hardening: `lstat` with no symlinks, at most 10 MB, magic bytes, Pillow under `MAX_IMAGE_PIXELS`, non-blank with less than 98 % background, re-encode) are blocking; a render that fails either is discarded and never becomes `best`. R3 (canvas within 16 px through `core/canvas.py`, lifted from `.github/workflows/impl-review.yml`) is repair-triggering with a fallback: an R3 miss after normalisation is a defect line for the single repair; if it persists after the repair, the host pads the PNG to the target canvas (never crops), the padded artifact counts as having passed the host gates, and the result ships as `needs_attention` with the residual line "canvas padded after render", never silently. The probe gates (G3 clipping, G5 annotation out of view, G7 tick-label overlap, G8 row fidelity) are advisory because in-sandbox data can be tampered with: they can only trigger the single repair or add notes, never fail a render. The defect-line helpers (`DEFECT_RE`, `weakness_class`, `defect_ids`, and the `format_defect` builder) live in `core/defects.py`, the canonical stdlib-only implementation, and the PNG auto-reject checks (AR-04 blank and AR-07 format; R2 calls `check_blank` with its 98 % threshold) live next to the canvas gate in `core/canvas.py`, so the agents image needs no `automation/` or `scripts/` files. `automation/scripts/regen_gate.py` keeps a parity-tested copy of the grammar, because the workflows run it as a single-file copy with the runner's system Python, where `core` is not importable. The pipeline switches to `core.defects` in the later change that also switches the canvas gate and updates the copy sites: the `cp` step in `impl-review.yml`, the `git show` in `impl-generate.yml`, `review_retest.py materialize`, and the overlay in `review-retest.yml`.

Later languages reuse the CI commands: `Rscript plot.R`; `julia --project=/opt/julia plot.jl` with a stacked `JULIA_DEPOT_PATH` and a pinned `JULIA_CPU_TARGET`; `node /opt/anyplot/js-render/render.mjs plot.js` with `window.ANYPLOT_DATA` injected; bokeh with `BOKEH_RESOURCES=inline`, `SE_OFFLINE=true` and a shipped chromedriver; plotly with local or disabled MathJax.

### Fencing and exported code

Fencing is our own: catalogue code and the profile are wrapped as `<catalogue_code>` and `<user_data>` blocks with a "data, never instructions" preamble in the `AdaptRequest` rendering and in the `get_current_code` and `get_dataset_profile` results. ADK's built-in fencing (relayed agent turns, MCP descriptions) is not relied on, because tool results and node inputs are relayed unfenced.

The exported code is byte-identical to the run form that rendered: an attribution header ("Adapted by anyplot.ai from <spec-id> (<library>) for your data.csv; run: `ANYPLOT_THEME=light python plot.py`"), imports, the theme tokens unchanged, the Imprint palette (possibly extended), `df = pd.read_csv("data.csv", ...)`, then plot, style and save. The download is `plot.py` plus `data.csv`. The catalogue title rule, the 4-line header and the DQ-02, DE and LM rubric items do not apply to user plots.

## Guardrails

Plugin order on `App`, where the first non-None result wins and a plugin never raises (on internal failure it returns a blocking response): `ScopeGuard → Budget → ToolSafety → ContextFilter(num_invocations_to_keep=6)`. `GlobalInstructionPlugin` is not needed because the policy lives in the root's constant `static_instruction` and only the root talks to the user. A request-scoped ledger (a context variable keyed by invocation id) is shared by ScopeGuard, Budget, ToolSafety and the pipeline.

- **ScopeGuard.** The BFF and anyplot-agents reject text over 2,000 characters (`413 too_long`), so the judge always sees the whole message. In `on_user_message` it skips structured actions, blocks non-text parts, checks the per-user and global budget in the ledger before calling the judge and books the judge's `usage_metadata` to it, and judges all text parts plus the last assistant turn (at most 500 characters) with delimiters escaped. A timeout, parse error or non-200 after one retry within 4 s blocks with a distinct `error{code:"guard_unavailable"}` that is excluded from the false-refusal metric. An out-of-scope verdict replaces the message with `[message withheld by scope policy]` before it is stored, and `before_run` halts with the fixed refusal from `refusals.yaml` chosen by language (English and German; English as the fallback). The dataset judge call at parse time uses the same plumbing with a data rubric.
- **Budget.** `before_model` halts with a fixed `LlmResponse` only for the root, because a halt inside the adapter or the reviewer would break their schema parsing; the pipeline calls `budget.check()` before each `run_node` and finishes with `PlotResult(failed, reason=budget)`. `before_tool` on `plot_pipeline` counts pipeline runs. Limits: per request 12 calls or 80k tokens (prompt plus candidates plus thoughts plus tool use; cached tokens are logged separately and never double-counted); per user per day 40 pipeline runs or 1M tokens; global per day 3M tokens, which pauses the service. Phase-1 daily counters live in memory for one instance lifetime, and the `aiplatform` spend cap is the real backstop; persisting the counters is a phase-2 item. The plugin writes one attribution JSON line per hook (request id, HMAC user, session hash, agent, tool, argument hash, verdicts, usage, `model_version`, latency) and never content.
- **ToolSafety.** `before_tool` enforces a per-agent allowlist (the root's five session tools; none for the adapters and the reviewer), Pydantic validation of the arguments (`FUNCTION_TOOL_ARG_VALIDATION` is off by default), no URLs or paths in string arguments, and at most one `plot_pipeline` call per invocation. `after_tool` applies a key allowlist and an 8 KB cap (24 KB for code). `on_tool_error` returns `{"status":"error","code":ENUM}` and never exception text.
- **Output sanitiser** in the stream translator, deterministic: `message` events only for `author == "anyplot"` final responses (adapter, reviewer and pipeline-branch events map only to `status` and `plot`); strip URLs, `data:` and `javascript:` links, HTML, markdown images and fenced code blocks longer than 10 lines; keep `[[spec:id]]` only for registry ids; cap text at 3,000 characters; final text only.

| Threat | Controls |
|---|---|
| Off-topic use, jailbreak, multi-turn drift | A judge on every free-text turn that fails closed, the 2,000-character limit, rejected text never stored, a closed tool set, policy in an untemplated `static_instruction`, the root "never" list, adversarial evals including general-programming requests framed as plot-code questions |
| Injection through pasted data | The raw dataset never reaches a prompt or a tool argument; only bounded, sanitised, fenced samples do: at most 3 KB of headers, top values and sample cells for the dataset judge at parse time, and the profile's at most 5 sample rows (cells at most 40 characters) for the root and the adapter; canonical headers; bindings validated on the server; adapter output bound to a schema and linted |
| Injection through catalogue code, comments or image labels | Own fencing; validated adapter output; a tool-less reviewer with a fixed-id schema that can trigger at most one bounded repair |
| Code escape | The two-profile AST validator; loader substitution; no executors anywhere; the sandbox (no egress, environment or metadata server, read-only root filesystem); resource limits; a host timeout plus `sandbox delete`; per-job directory wipe; a service account with no data access; the phase-0 probe suite and the sibling-directory spike |
| Resource abuse (denial of wallet) | Ledger budgets including the judge; one run per user and one `plot_pipeline` per invocation; `max-instances=1`; a CSRF header and Origin check on the cookie-authenticated BFF; a spend cap on `aiplatform.googleapis.com` only (never on `run.googleapis.com`, which would pause `anyplot-api`); the `AGENT_ENABLED` kill switch |
| Data leakage | A server-derived HMAC user id; ownership checks on every route; no content in logs or spans (`ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false`, `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT` unset); in-memory stores tied to the session lifetime plus an idle sweeper and a DELETE route; the translator drops arguments, tool outputs, thoughts and `error_details`; the `eu` endpoint; PNG only in the UI, no model HTML, no auto-loaded URLs |
| Session poisoning or BFF bypass | Our own FastAPI, never `get_fast_api_app`; clients never write state or events; the BFF allowlists bodies; the agents app checks the IAM-forwarded ID-token claims; `ToolCallIntegrityPlugin` once sessions persist |
| Phase 2 | Model Armor through direct sanitize calls on `modelarmor.eu.rep.googleapis.com` (once per user message and once per final text, failing closed, with `logSanitizeOperations=false`); `ModelArmorPlugin` only if a spike shows acceptable call counts, because it re-screens on every model call |

## Feedback capture

Every agent result can be reported with one click and a short text, and the report carries the full case, so prompts, validator rules, gates and the model pin can be tuned from real sessions. It mirrors the site feedback (`api/routers/feedback.py`, `FeedbackWidget`, triage under `/debug/feedback/*`) but stores a case bundle instead of a message.

- **UI.** On the result card and in the chat page's floating-action slot: thumbs up, thumbs down, bug and idea (the existing reaction set), an optional text of at most 500 characters, and a checkbox "include my data file" (on by default for admins in phase 1; off by default and behind an explicit consent notice for real users later). Sending is optional and never blocks the flow. One submission per result version; a later edit replaces it.
- **Route.** `POST /debug/agent/sessions/{sid}/feedback {reaction, message?, include_data, result_version}` on the BFF, behind `require_admin` in phase 1; the public phase reuses the feedback router's per-IP-hash rate limit and honeypot. The BFF calls `GET /v1/sessions/{sid}/bundle` on anyplot-agents, which assembles the case on the server so that anyplot-agents stays credential-free: the transcript of user and root messages (never tool outputs or thoughts), the catalogue snapshot id, the working and run code of every version, the adapt plans and defect lines, the plot results, the dataset profile and bindings, both PNGs, and a config stamp (`AGENT_MODEL`, `model_version` from `usage_metadata`, the judge model, prompt file hashes, validator and normaliser version, ADK version, token and cost totals, latency per step). `data.csv` is included only when `include_data` is set.
- **Storage**, written by the API, which already has database and GCS access: a row in a new table `agent_feedback` (Alembic migration) with `id, created_at, user_hash, session_hash, spec_id, library_id, language, reaction, message, include_data, status (new|in_progress|done|wont_solve), case_uri, model, model_version, prompt_hash, pipeline_status, attempts, tokens, cost_estimate`; the bundle as `cases/<id>/{manifest.json, plot-light.png, plot-dark.png, plot.py[, data.csv]}` in a new private EU bucket `anyplot-agent-cases` (public-access prevention, uniform access, lifecycle delete after 180 days by default; never `anyplot-images`). The attribution log stays content-free; the case bundle is the only place content is stored, and only on explicit submission.
- **Triage.** A new "Agent cases" section in `DebugPage` lists cases with filters by reaction, status, spec, library and model version, opens a case (transcript, code diff against the catalogue original, light and dark images, defect lines, config stamp), updates the status, and offers **Promote to eval case**, which asks for an explicit expected outcome (`accepted` or `rejected`; the form preselects `accepted` for thumbs up and `rejected` for thumbs down, and makes the owner choose for bug and idea reactions, because those do not map to a fixture outcome) and copies the case (dataset, bindings, spec and library, the chosen outcome) to the `evals/cases/<id>/` prefix of the same private bucket. The harness syncs that prefix into a gitignored `agents/evals/.cases/` directory at run time. Promoted cases are never committed: they contain users' data, and anything under `agents/evals/fixtures/` ships under the repository's MIT licence. Only synthetic fixtures (the spike-X perturbation datasets) are committed. This is the bridge from real sessions to the regression harness.
- **Analytics.** `agent_result_feedback{reaction, include_data}` with enum properties only.
- **Privacy.** Phase 1 holds owner data only. Before real users can submit: consent text on the control, a legal-page entry for the case store (purpose, retention of 180 days, EU bucket), `include_data` off by default, and a delete-my-case route keyed by the case id shown to the user.

## Model-version regression harness

Testing a newer Gemini version, a different judge model, or a prompt or validator change is one command locally or one workflow dispatch in CI, and the answer is a diff against the pinned baseline.

- **Fixture cases**, each a directory with `case.json` (spec, library, bindings, expected `accepted` or `rejected`, tags), `data.csv`, and an optional `change_request.txt`. Two sources: the committed synthetic fixtures in `agents/evals/fixtures/cases/<id>/`, seeded from spike X (10 specs times 5 perturbation datasets), and the promoted feedback cases synced from the private bucket into the gitignored `agents/evals/.cases/` directory (never committed, because they hold users' data). The scope, injection and code-escape sets stay as evalsets.
- **Harness** (`agents/evals/matrix.py`, the spike-X runner made permanent): runs every case through the real `/v1` flow in-process (httpx `ASGITransport`, the Docker local renderer, the same plugins) with candidate settings that are passed only to the harness: `--model`, `--judge-model`, `--location`, `--prompts <dir>`, `--cases smoke|full|<glob>`, `--repeats N`. Per case it records the deterministic gate results, the reviewer verdict, attempts, edit-apply failures, validator rejections, `model_version`, tokens (prompt, candidates, thoughts, cached), cost at list price and latency per step. It writes `reports/<date>-<model>.json` and prints a diff table against `agents/evals/baselines/<pinned-model>.json`: pass rate, accept-match rate (cases whose outcome matches the owner's recorded reaction), cost per successful plot, p50 and p95 latency, refusal recall and false-refusal rate on the scope set, and every case that flipped. The exit code is non-zero when the pass rate or the safety recall drops below the baseline minus a tolerance.
- **Baselines.** `agents/evals/baselines/gemini-3.8-flash.json` is committed with the pinned model. A model bump is a PR that changes the `AGENT_MODEL` default and adds the new baseline file; a unit test asserts that a baseline exists for the pinned model. The same mechanism covers judge-model bumps and ADK upgrades, because the ADK version is part of the report stamp.
- **CI.** `.github/workflows/agents-eval.yml` has `workflow_dispatch` inputs `model`, `judge_model`, `location`, `cases` (smoke or full) and `repeats`, and a nightly `smoke` run on the pinned model. It authenticates through Workload Identity Federation, sets `GOOGLE_CLOUD_LOCATION=eu`, uploads the report as an artifact and writes the diff table into the job summary. It mirrors the candidate-versus-baseline pattern of `review-retest.yml` (see [Review retest](../workflows/review-retest.md)). A lifecycle probe in the nightly run calls `models.get` on the pinned model and fails loudly on a 404 or a retirement notice, so a forced bump of the short-term Gemini 3.8 Flash tier is noticed before users are.
- **Cost.** A full run is about 50 cases times at most 3 attempts, about $3 to $8 at list price; `smoke` is about $0.50. Both fit inside the spend cap.

## Serving and infrastructure

- **`anyplot-agents`**, a new Cloud Run service deployed by `agents/cloudbuild.yaml` using the API's candidate-then-smoke-then-promote pattern with `--update-*` flags only. A one-time bootstrap deploy without `--no-traffic` creates the service, because gcloud rejects `--no-traffic` on a new service; the API side stays dark through `AGENT_ENABLED=false`. Flags: `gcloud beta run deploy anyplot-agents --region=europe-west4 --execution-environment=gen2 --sandbox-launcher --service-account=anyplot-agents@anyplot.iam.gserviceaccount.com --no-allow-unauthenticated --cpu=2 --memory=4Gi --min-instances=0 --max-instances=1 --concurrency=4 --timeout=300 --no-traffic --tag=candidate --update-env-vars=^|^...`. No secrets and no Cloud SQL in phase 1. The FastAPI app in `agents/main.py` sets `docs_url=None`. The service hosts both the runner and the sandbox launcher; splitting out a zero-role `anyplot-renderer` (the `remote` backend) is a hard gate before any non-owner use.
- **IAM** (owner tasks): the service account `anyplot-agents@` gets `roles/aiplatform.user` and `roles/telemetry.writer`; the API's runtime identity gets `roles/run.invoker` on the service; the Cloud Build identity gets `roles/iam.serviceAccountUser` on `anyplot-agents@`; the GitHub Workload Identity Federation principal gets `roles/aiplatform.user` for evals. Phase 2 adds `cloudsql.client` with a read-only role `anyplot_agents_ro` (SELECT on specs, impls, libraries and languages only, never `feedback`), `secretAccessor` on single secrets, `storage.objectAdmin` on the private bucket, and `modelarmor.user`.
- **Environment on anyplot-agents:** `ENVIRONMENT=production`, `GOOGLE_CLOUD_PROJECT=anyplot`, `GOOGLE_GENAI_USE_ENTERPRISE=TRUE`, `GOOGLE_CLOUD_LOCATION=eu`, `AGENT_LOCATION=eu` (never europe-west4), `AGENT_MODEL=gemini-3.8-flash`, `AGENT_JUDGE_MODEL=gemini-3.5-flash-lite`, `AGENT_LIBRARIES=matplotlib,seaborn`, `AGENT_RENDERER=sandbox`, `AGENT_MAX_LLM_CALLS=12`, `ADK_MAX_LLM_CALLS=20`, `AGENT_REQUEST_TOKEN_BUDGET=80000`, `AGENT_DAILY_TOKEN_BUDGET=1000000`, `AGENT_DAILY_PIPELINE_RUNS=40`, `AGENT_GLOBAL_DAILY_TOKEN_BUDGET=3000000`, `AGENT_RENDER_TIMEOUT_S=60`, `AGENT_REQUEST_DEADLINE_S=180`, `AGENT_SOFT_DEADLINE_S=140`, `AGENT_ALLOWED_CALLERS=<API SA email>`, `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false`. On anyplot-api: `AGENT_ENABLED=false` (ships dark; the routes answer 404), `AGENT_SERVICE_URL`, and `AGENT_USER_ID_KEY` from Secret Manager (the BFF also answers 404 while the key is unset, so a deploy never breaks). On the app: `VITE_ENABLE_AGENT_CHAT`, a build-time flag that tree-shakes the chunk.
- **Sessions and artifacts.** Phase 1 uses `InMemorySessionService`, `InMemoryArtifactService` and in-memory dataset and render stores; they are consistent because `max-instances=1`, and scale-to-zero shows "session expired". Phase 2 moves to `DatabaseSessionService` in a separate database `anyplot_agents` on `anyplot-db` with its own user and an hourly purge of sessions older than 24 h, because `alembic/env.py` has no `include_object` filter and ADK's `create_all` tables would read as drift; artifacts go to `GcsArtifactService` on a private EU bucket with a 1-day lifecycle, never `anyplot-images`.
- **BFF** in `api/routers/agent.py`: `APIRouter(prefix="/debug/agent", dependencies=[Depends(require_admin)])`. A small refactor `require_admin_identity()` returns `AdminIdentity(email|None, via)` and `require_admin` wraps it unchanged. `user_id = "adm_" + HMAC(key, email or "token")[:16]`. POST requests need `Content-Type: application/json`, `X-Anyplot-Client: agent-chat/1` and an allowed Origin. ID tokens come from `google.oauth2.id_token.fetch_id_token` (skipped for localhost). The messages route is an async generator declared with `response_class=EventSourceResponse` (which is what gives FastAPI's automatic 15 s pings; Cloudflare returns 524 after 125 s), reads upstream with httpx `aiter_lines()`, assembles complete events, re-validates each event type against the `anyplot/1` allowlist, and yields `ServerSentEvent(event=..., raw_data=...)`; on upstream failure it emits `error{code:"upstream"}`. Routes mirror `/v1` plus `GET eligibility`, `POST sessions/{sid}/feedback`, and the triage routes `GET /debug/agent/cases`, `GET /debug/agent/cases/{id}` and `PATCH /debug/agent/cases/{id}`. The deploy smoke test expects 401 on `/debug/agent/status`.
- **SSE protocol `anyplot/1`**, translated from ADK events and never forwarded raw: `ready{v, run_id}`, `status{step, attempt}`, `message{text}` (root final text only), `plot{PlotResult}`, `refusal{code, text}`, `error{code, ref}` with codes `capacity`, `deadline`, `guard_unavailable`, `upstream` and `internal`, and `done{llm_calls, tokens}`. The translator tolerates the ADK 2.x `node_info` and `output` fields.
- **Frontend.** A lazy `app/src/pages/AgentChatPage.tsx` at `debug/agent` with a data panel (textarea with a 200 KB counter, preview table, binding dropdowns), the chat thread, a progress timeline and a Stop button (`AbortController` plus the cancel route). The **result card** (`app/src/sections/agent-chat/ResultCard.tsx`) reuses the plot page's overlay actions: the rendered plot shown inline as a blob URL with a light and dark toggle that defaults to the site theme, **Copy image** (Clipboard API `navigator.clipboard.write([new ClipboardItem({"image/png": blob})])`, falling back to download where unsupported), **Download PNG** for both themes and **Open full size**; the adapted code in `CodeHighlighter` with **Copy code** (`useCopyCode`, one click), **Download plot.py** and **Download data.csv** (the pair runs unchanged); the change list and residual notes; the quick-feedback control; and a composer for refinements. Earlier versions stay reachable in the thread, each with its own image and code. The same card is reused unchanged when the feature goes public. `app/src/lib/sse.ts` parses the stream over `fetchWithAuth(...).body.getReader()`. The `.adapt()` button is the fourth overlay button in `app/src/sections/spec-detail/SpecDetailView.tsx`, wired through `onUseWithMyData` from `SpecPage.tsx`, and renders only when `CONFIG.features.agentChat && (CONFIG.isDev || adminHint) && eligible`, where `adminHint` is a localStorage flag that `DebugPage` sets after `/debug/status` succeeds and `eligible` comes from the eligibility route. It does a full navigation so Cloudflare Access can intercept, and public pages never probe `/api/debug/*`.
- **Analytics** (enum properties only, documented in [Plausible](../reference/plausible.md) when implemented): the pageview `/debug/agent`, `agent_open{library,source}`, `agent_data_parsed{status,size_bucket}`, `agent_plot_rendered{library,status,repaired}`, `agent_guardrail_block{reason}`, `agent_result_feedback{reaction,include_data}`, and `copy_code{page:'agent_chat',method:'agent'}`.

## Repository layout

```
agents/__init__.py  agents/main.py  agents/Dockerfile  agents/cloudbuild.yaml
agents/anyplot/{__init__.py, agent.py (root_agent, ALL_AGENTS, app = App(...)), models.py, settings.py, policy.py, schemas.py, pipeline.py}
agents/anyplot/sub_agents/{adapter.py, reviewer.py}            # relative imports only: ADK loads the package as top-level `anyplot`
agents/anyplot/tools/{session.py, catalogue.py}
agents/anyplot/plugins/{ledger.py, scope_guard.py, budget.py, tool_safety.py}
agents/anyplot/prompts/{root,adapter,reviewer,scope_judge,data_judge}.md  refusals.yaml
agents/anyplot/data/{parse.py, bindings.py, store.py}                     # no ADK import
agents/anyplot/code/{normalise.py, readiness.py, edits.py, validate.py, loader.py, export.py}   # no ADK import
agents/anyplot/render/{contract.py, gates.py, png.py, harness.py, runtimes/python.py, backends/{local.py, sandbox.py, fake.py}}
agents/evals/{scope.evalset.json, test_config.json, harness/test_flows.py, matrix.py, sync_cases.py,
              baselines/gemini-3.8-flash.json, fixtures/cases/<id>/{case.json, data.csv} (synthetic only), .cases/ (gitignored, synced from the bucket)}
core/catalogue/{__init__.py, queries.py}      # shared by api/mcp/server.py and agents/
core/canvas.py  core/defects.py                # lifted from impl-review.yml and automation/scripts/regen_gate.py (which keeps a parity-tested copy)
core/database/models.py (AgentFeedback)        alembic/versions/<rev>_agent_feedback.py
api/routers/agent.py                           # BFF, feedback and cases routes
app/src/pages/AgentChatPage.tsx  app/src/sections/agent-chat/{ResultCard,ResultFeedback,...}.tsx  app/src/hooks/useAgentSession.ts  app/src/lib/sse.ts
app/src/pages/DebugPage.tsx (Agent cases section)
tests/unit/agents/*  tests/unit/api/test_agent_router.py  tests/integration/agents/test_pipeline_offline.py
```

Files to modify: `pyproject.toml` (extras `agents = ["google-adk==2.11.0"]` and `agents-eval = ["google-adk[eval]==2.11.0"]`; setuptools include `agents*`; ruff `known-first-party`; coverage source; regenerate `uv.lock` and run `uv lock --check`; assert that the lock never contains `openai-agents`, which also installs a top-level `agents` module), `.dockerignore` (`!agents`, `!prompts/default-style-guide.md`, `!prompts/library`), `core/config.py` (`agent_*` settings with the pinned defaults, `_strip_secret` entries), `api/routers/debug.py`, `api/main.py`, `api/cloudbuild.yaml` (env vars, secret binding, 401 smoke), `automation/scripts/regen_gate.py` (switch to `core/defects.py`, loaded from a sibling copy in script mode, together with its copy sites), `.github/workflows/{ci-tests,ci-lint,ci-image}.yml`, a new `.github/workflows/agents-eval.yml`, `app/src/routes/{index.tsx,paths.ts}`, `global-config.ts`, `vite-env.d.ts`, `SpecPage.tsx`, `SpecDetailView.tsx`, `DebugPage.tsx`, `app/Dockerfile`, `app/cloudbuild.yaml`, `docs/index.md`, `docs/reference/{api,plausible,mcp,repository,database}.md`, `docs/development.md`, `CLAUDE.md` and `.github/copilot-instructions.md` (an `agents/**` routing row, kept in sync), and one `changelog.d/<slug>.md` per PR. `agents/Dockerfile` builds from `python:3.13-slim` with `uv sync --frozen --extra agents --extra lib-matplotlib --extra lib-seaborn`, bakes the matplotlib font cache into `MPLCONFIGDIR=/opt/mplconfig`, runs as a non-root user and starts `uvicorn agents.main:app --port 8080`. The `deploy-agents` trigger (an owner task) fires on `agents/**`, `core/**`, `prompts/library/**`, `prompts/default-style-guide.md`, `pyproject.toml` and `uv.lock`.

Reused code: the `api/mcp/server.py` tool bodies move into `core/catalogue/queries.py`; `core/database/repositories.py` (`SpecRepository.get_by_id_with_code`, `ImplRepository.get_code`); `core/utils.strip_noqa_comments`; `core/constants.py` (`LIBRARIES_METADATA`, `LIBRARY_LANGUAGES`, `INTERACTIVE_LIBRARIES`); `core/palette.py`; the defect grammar through `core/defects.py` and the canvas gate and PNG auto-reject checks through `core/canvas.py`; the render invocation shape of `agentic/workflows/modules/regen/render.py` (copied, not imported); `automation/js-render/render.mjs` for the JS runtime later; the per-IP-hash rate-limit pattern of `api/routers/feedback.py` and `api/request_context.client_ip` for the public phase.

## Roadmap

### Phase 0: local and spikes (about 1 to 1.5 weeks after the API is enabled)

Owner tasks 1 to 6 come first. Then run the spikes:

| Spike | Question | Pass criterion |
|---|---|---|
| M | `generateContent` on `eu` and `global` for gemini-3.8-flash, gemini-3.5-flash-lite and, for the record, the alias; `modelVersion` and `usageMetadata`; free `countTokens` on the adapter and reviewer prefixes | Recorded; under $0.01 |
| S | A Cloud Run sandbox in europe-west4: the deploy works; matplotlib and seaborn render with egress blocked; a blocked fetch fails fast; RSS and time at 2 and 4 vCPU; concurrent sandboxes before OOM; cold start; whether the IAM-forwarded ID-token claims are visible to the container and in what signature state; a probe suite (metadata server, DNS and HTTP egress, `/proc/1/environ`, writes outside `/work`, sudo, fork and memory bombs). Run `gcloud components update` first, because the local SDK 534 lacks the flag; ideally in a throwaway project | Everything blocked or contained |
| G | Can a sandbox read sibling run directories or files the host writes at runtime? | No; otherwise use `--rootfs` with a toolchain-only tree or one render per instance |
| X | Adaptation: 10 specs times matplotlib and seaborn times 5 datasets (renamed, x10, n=12, n=5000, date, decimal comma) on gemini-3.8-flash; plotly only on figure-level gates because the phase-1 image has no Chrome. Pass means all deterministic gates plus an owner blind accept or reject on a sample of 30 renders. Also reports post-normaliser eligibility under the SECURITY profile and the files blocked for a missing `THEME` block or a non-literal savefig target | Under $25 |
| C | Does a NodeTool `Event(message)` arrive before the function response under `StreamingMode.NONE`? | Yes |
| F | Does a plugin's `on_tool_error` catch a `ValueError`? Is the content returned when `before_run` halts emitted? | Both observed |
| A′ | Does the reviewer read a canary string from callback-injected images on a single-turn agent with `include_contents='none'` while the native `response_schema` still applies? | Exact match; fallback is a `view_render` tool returning Parts, which reintroduces the Preview multimodal-function-response path |

Scaffold `agents/`, run `adk web --port 8002 --session_service_uri memory:// --artifact_service_uri memory:// agents` with a development-only `fixture` state seed (snapshot, dataset store and bindings from `agents/evals/fixtures`; refused in production) and the full stack (agents on :8001, the API on :8000, the app on :3000) with `AGENT_RENDERER=local`.

Exit criteria: model and location confirmed by spike M; spikes S and G all blocked with a p95 render under 10 s at 2 vCPU; spike X at least 80 % pass after at most one repair on eligible pairs with owner acceptance of at least 75 % on the sample and a median cost of at most $0.05 per successful plot; scope evals with 100 % of adversarial cases refused and at most 5 % false refusals (guard outages excluded); the validator corpus at 100 % including every named bypass.

### Phase 1: admin-only production (about 3 to 4 weeks)

1. The design doc (this document).
2. The `search_specs_by_tags` AND and category fix plus the `docs/reference/mcp.md` drift fixes (independent and small).
3. `core/catalogue`, `core/canvas.py`, `core/defects.py`, the `AdminIdentity` refactor and the BFF, shipped dark (owner task 7 before the merge).
4. The `agents/` package, image, Cloud Build config, CI, the regression harness with the spike-X cases as the first fixtures, and the committed Gemini 3.8 Flash baseline (owner task 8 before the first deploy).
5. The React page, the button and the analytics events.
6. Quick feedback: the `agent_feedback` migration, the bucket objects, the BFF feedback and cases routes, the `ResultFeedback` control, the DebugPage "Agent cases" section and `sync_cases` (owner task 10 before the merge).
7. `agents-eval.yml` with `workflow_dispatch` inputs, the nightly smoke run on the pinned model including the lifecycle probe, the full suite weekly and on every prompt or model change, plus docs.
8. Optional: sync "What a good version looks like" into `specs.good_version` (Alembic plus `sync_to_postgres.py`) if spike X shows the reviewer flagging expected features.

Exit criteria: 401 or 403 smoke tests on both services; the spend cap active before the first deploy; the log and span canary clean; the owner completes 20 real datasets across 10 specs with at least 75 % accepted through the result button (the `ok` rate reported alongside) and at least 10 of them submitted as feedback cases; for every accepted result the image was copied or downloaded and the copied `plot.py` plus `data.csv` reproduced the shown PNG locally, verified on both viewports and themes; one candidate-model dispatch of the harness produced a diff report; an end-to-end p95 under 60 s; nightly evals green.

### Parallel workstream: catalogue normalisation (pipeline side)

Starts once spike X fixes the gates. A prompt rule plus a one-time regen pass through the existing pipeline turns literal axis limits, data-coordinate annotations, critical values and short palettes into data-derived code, adds a `THEME` block and a literal savefig target where missing, and strips `bbox_inches='tight'`, gated by the deterministic gates on perturbation datasets. It writes an `adaptation:{ready, checked, failures}` block to the metadata YAML and, through an Alembic migration and a `sync_to_postgres.py` change (`impls.adaptation`), to the database, so the eligibility route and the button only show ready pairs. The pipeline owns this workstream, not the agent network. [Adaptable catalogue code](adaptable-code.md) designs it in detail and, by the owner's decisions of 2026-10-09, replaces two parts of this paragraph: the conversion rides the normal daily regeneration instead of a one-time pass, and the status lives only in `impls.adaptation`, computed at sync time, with no metadata YAML block.

### Phase 2: toward public use, all 15 libraries and discovery

Libraries, each one `RuntimeAdapter` enabled through `AGENT_LIBRARIES` after its eval matrix reaches 80 %: first plotnine, altair, lets-plot and pygal (no browser); then plotly and bokeh (Chromium fixes); then JS through `render.mjs` with `window.ANYPLOT_DATA`, a `page.route` deny-all and a tree-sitter deny-list; then R (ragg and a readr loader); then Julia (a precompiled depot, a pinned `JULIA_CPU_TARGET`, and asynchronous submit-and-poll if renders exceed 60 s; Cloud Run jobs and worker pools also support sandboxes). Discovery follows the phase-2 flow above.

Hard gates before any non-owner use: the legal-page PR (`LegalPage.tsx` plus a pinned test per store), the `anyplot-renderer` split, anyplot-api on a dedicated service account, database sessions with a purge, GCS artifacts with a lifecycle, persisted budget counters, Model Armor and `ToolCallIntegrityPlugin`, Turnstile with server-side verification plus a Cloudflare rate rule plus per-IP-hash database quotas plus a signed anonymous identity, routes moved out of `/debug`, and owner decisions on the Vertex 24 h cache and the abuse-logging exception.

## Verification

- **Regression harness.** `uv run --extra agents-eval python -m agents.evals.matrix --model gemini-3.8-flash --cases smoke` must reproduce the committed baseline within tolerance on every PR that touches `agents/anyplot/prompts/`, `code/` or `render/` (run through `workflow_dispatch`, not automatically, because it spends money). A candidate run with `--model <new>` prints the diff table and exits non-zero on regressions.
- **Evals.** `adk eval` runs only the scope set (`uv run --extra agents-eval adk eval agents/anyplot agents/evals/scope.evalset.json --config_file_path agents/evals/test_config.json`, after confirming that the loader picks up `app` with its plugins; `judge_model_options.judge_model="gemini-3.8-flash"`, never the retiring 2.5 Flash default): 50 off-topic cases, 50 jailbreaks (German, role-play, base64, multi-turn drift), 50 in-scope cases, plus general-programming requests framed as plot-code questions; a refusal must equal the fixed string. The flow evals (`use_with_my_data`, `injection` through CSV cells, headers, image labels and catalogue-style comments, and `code_escape`) run as a pytest harness against the real `/v1` routes in-process with fixture CSVs, because the pipeline reads the snapshot, dataset and bindings from server-set state; trajectory, `token_usage_v1` and `inference_call_count_v1` are tracked as regressions. A full eval run costs about $1 to $3.
- **Unit tests on every PR.** The parser (decimal comma with `DD.MM.YYYY`, header canonicalisation, bidi and zero-width names, caps); the bindings heuristic and `bindings.apply`; the edit applier (ambiguity, protected regions by AST, palette prefix); the validator allow and deny corpus for both profiles (dunder walks, `__builtins__`, `string.Formatter`, `.format`, patsy, `pd.eval`, file-read calls); loader substitution and the working and run forms; the canvas normaliser on the 137 legacy matplotlib files; gate fixtures; the stream translator (author filter, dropped function calls, code-block stripping); the plugins with fake clients (judge timeout or garbage gives `guard_unavailable`; the budget halts the root only; tool errors are mapped; one `plot_pipeline` per invocation); the agent registry test; the BFF (401 and 403, the CSRF header, the 404 kill switch and unset key, user-id derivation, the body allowlist, ownership on artifact routes, SSE re-framing); the caller-claims check; a log and span canary; `find_specs` AND semantics; Vitest for the SSE parser, the page, the result card and button gating.
- **Run locally.**

  ```bash
  uv sync --extra agents --extra lib-matplotlib --extra lib-seaborn --extra test
  gcloud auth application-default login
  export GOOGLE_GENAI_USE_ENTERPRISE=TRUE GOOGLE_CLOUD_PROJECT=anyplot GOOGLE_CLOUD_LOCATION=eu \
         AGENT_LOCATION=eu AGENT_MODEL=gemini-3.8-flash AGENT_JUDGE_MODEL=gemini-3.5-flash-lite AGENT_RENDERER=local
  uv run adk web agents --port 8002 --session_service_uri memory:// --artifact_service_uri memory://
  uv run uvicorn agents.main:app --port 8001
  AGENT_ENABLED=true AGENT_SERVICE_URL=http://localhost:8001 uv run uvicorn api.main:app --reload --port 8000
  cd app && VITE_ENABLE_AGENT_CHAT=true yarn dev   # http://localhost:3000/debug/agent?spec=scatter-basic&library=matplotlib
  ```

- **Measure per run.** Status and reason, attempts, gate failures by gate, verdict, owner accept or reject, LLM calls, `usage_metadata` (prompt, candidates, thoughts, cached), `model_version`, cost, time to first event, end-to-end time, render wall time per theme, and refusal, `guard_unavailable` and budget counts.

## Owner tasks

These are manual steps only the owner can do; they are tracked in Todoist.

1. Enable `aiplatform.googleapis.com` in project `anyplot` and authorize spike M (under $0.01).
2. Create the service account `anyplot-agents@` with `roles/aiplatform.user` and `roles/telemetry.writer`; grant `roles/run.invoker` to the API identity and `roles/iam.serviceAccountUser` to Cloud Build.
3. Create a spend-cap budget on `aiplatform.googleapis.com` sized at list price (the promo is credited back later): about CHF 75 for phase 0, or run spike X in a throwaway project under its own cap; about CHF 60 in steady state (owner usage plus eval cost with 2x headroom); alerts at 50, 80 and 100 %. Never cap `run.googleapis.com`.
4. Authorize spike S (the Cloud Run sandbox, ideally in a throwaway project, after `gcloud components update`).
5. Authorize spike X (under $25).
6. Confirm that Cloudflare Access `anyplot.ai/debug*` and `/api/debug*` cover `/debug/agent` and `/api/debug/agent/*`, and name the Cloudflare plan (the Free plan allows one rate-limit rule).
7. Before PR 3 merges: create the Secret Manager secret `AGENT_USER_ID_KEY` (32 random bytes through `--data-file`, never `echo`) and confirm that the anyplot-api runtime service account can read it.
8. Before the first agents deploy: create the `deploy-agents` Cloud Build trigger and run the one-time bootstrap deploy without `--no-traffic`.
9. Before PR 7: grant `roles/aiplatform.user` to the GitHub Workload Identity Federation principal for this repository, conditioned on `agents-eval.yml` on `main` if possible.
10. Before PR 6 merges: create the private EU bucket `anyplot-agent-cases` (uniform access, public-access prevention, lifecycle delete after 180 days) and confirm that the anyplot-api runtime identity can write to it.
11. Confirm the GCP agreement type: the online terms mean abuse-monitoring prompt logging for up to 90 days; a Master Agreement is exempt.
12. Decide the fate of issue #5405, which proposed Claude with Find, Navigate and Create modes: supersede it with this document or update it. Register the Plausible properties and goals.
13. Before public use: move `anyplot-api` off the default compute service account, which holds `roles/editor`.

## Open decisions

Defaults apply until the owner decides otherwise.

- DQ-02 topics (politics, religion, violence) in user data: allowed as data, labels only.
- The Highcharts commercial licence for user plots (phase 2).
- An attribution header in exported code: yes.
- Disabling the Vertex 24 h in-memory cache (needs `roles/aiplatform.admin` and applies to all regions): no in phase 1.
- Retention periods for the legal page (phase 2).
- Scale-to-zero "session expired" versus `min-instances=1`: accept in phase 1.
- A named fallback model on `eu` for capacity failover, which deviates from "3.8 everywhere": none.
- Feedback-case retention and data inclusion: 180 days in the private bucket; `include_data` on by default for admins and off by default with explicit consent for real users.
- Premium positioning: [Vision](vision.md) lists "Try with your data" as premium; the licensing row in the decisions table settles that the code stays MIT regardless.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Cloud Run sandboxes are in Preview with undocumented regions, isolation technology and cross-run visibility | Spikes S and G plus the probe suite gate phase 1; the `RenderBackend` protocol; the fallback is a gen2 service with Direct VPC egress deny or `GkeCodeExecutor` with a custom image; the renderer split before public use |
| Gemini adapts poorly (only proxy evidence so far) | Spike X is the go or no-go with owner blind acceptance; an eligibility filter (statically clean data-generation pairs: matplotlib 65 of 251, seaborn 84 of 267; the dpi normaliser removes the canvas condition; plotly's 102 count only in phase 2); hints from the readiness scan; the normalisation workstream; an honest `needs_attention` status |
| Gemini 3.8 Flash is a short-term tier not on the tier list, and `eu` has its own capacity pool | One `AGENT_MODEL` value, `retry_options` with backoff from day one, `error{code:"capacity"}` on persistent 429s, no fallback model unless the owner names one, the lifecycle probe, an eval gate on every bump |
| The reviewer is a weak judge (expert correlation about 0.43) | Deterministic gates first, a short checklist, at most one repair, residual defects shown as notes, owner acceptance as the real metric |
| ADK ships weekly with feature-flag drift | An exact pin to 2.11.0; re-check `FUNCTION_TOOL_ARG_VALIDATION` and `JSON_SCHEMA_FOR_FUNC_DECL` on upgrade; plain-code modules without ADK imports; the harness report stamps the ADK version |
| Caller trust: anyplot-api runs as the shared compute service account | Acceptable while admin-only; the IAM-forwarded claims check; a dedicated service account before public use |
| Deadline overrun (2 renders times 2 themes times 60 s plus LLM calls) | A 140 s soft deadline inside the pipeline (skip the repair when short, clamp the render timeout, parallel themes), a `try/finally` that always yields a `PlotResult`, the 180 s `abort_signal` backstop |
| Long SSE streams hold anyplot-api concurrency slots on its single instance | The 180 s deadline and one run per user; the route moves out of the API before public use |
| Cloudflare 524 or Worker buffering | The generator route with automatic 15 s pings and first bytes sent immediately, verified in the phase-1 smoke test; asynchronous polling for slow runtimes later |
| Hidden CDN dependencies (bokeh, kaleido MathJax, map tiles) | The exclusion list of 13 map specs, inline and offline settings, the non-blank gate |
| Retiring defaults (`Gemini()` and the eval judge default to 2.5 Flash) | Always set `model`; the registry test asserts that every model string comes from settings |
| The spend cap trips on list price or on evals | A cap sized at list price with eval cost included; nightly smoke only; spike X in a throwaway project |
| The privacy page contradicts non-owner use | The owner-only gate; the legal PR and the retention design are hard gates |

## Evidence

The design rests on research that was fact-checked on 2026-10-08 against the ADK v2.11.0 source tree, the ADK documentation at adk.dev, the Vertex AI (Gemini Enterprise Agent Platform) model, location, pricing and data-governance pages, the Cloud Run sandbox documentation, and this repository. Measured repository facts (canvas failures, literal coupling, data-swap pass rates, prompt and implementation token sizes, catalogue index sizes) come from read-only scans of `plots/`, `prompts/` and the metadata YAML files. Re-verify model ids, prices, regional availability and ADK API names before implementing a section, because all four change on a weekly to monthly cadence.
