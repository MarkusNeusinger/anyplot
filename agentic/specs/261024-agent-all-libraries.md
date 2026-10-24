# Feature: "Use with my data" for all 15 catalogue libraries

## Metadata

run_id: `session_01WbjVqBweiXjUZKp626ZFWm`
prompt: `Rebuild the AI chat mode so that generating works not only for matplotlib and seaborn but for all 15 libraries; the biggest part is that the Cloud Run renderer can also render JavaScript, R and Julia. Plan it, start implementing, get second opinions, test in local Docker where the cloud session has no gcloud access, and ask when something is not canonical.`

## Feature Description

The agent network ("Use with my data", `agents/`) adapts a catalogue implementation
to a user's table, renders it in a Cloud Run sandbox, reviews it and ships the plot.
Phase 1 serves matplotlib and seaborn. This plan takes the network to the other 13
libraries of the catalogue: six more Python libraries (plotnine, altair, pygal,
lets-plot without a browser; plotly and bokeh with Chromium), five JavaScript
libraries through the browser harness (Chart.js, D3, ECharts, Highcharts, MUI X), R
(ggplot2) and Julia (Makie).

The design already fixes the shape ([Agent network design](../../docs/concepts/agent-network.md),
"Render", "Phase 2"): later languages add `RuntimeAdapter`s, not backends; each runtime
reuses the catalogue's CI render command; the renderer image carries the toolchains; a
library is enabled through `AGENT_LIBRARIES` once its eval matrix reaches 80 %. Where
the design leaves room, this plan names the choice and marks it as an owner question
(see "Open questions").

What the code does today, and what has to change:

| Layer | Today | Change |
|---|---|---|
| `agents/anyplot/render/runtimes/` | one class, `PythonRuntime`, built in three places (`pipeline.py`, `theme_render.py`, `render/__init__.py`) | a registry `runtime_for(library)`; `RUNTIME_LIBRARIES` replaces `normalise.SUPPORTED_LIBRARIES` in the settings validator |
| `agents/renderer/wire.py`, `executor.py` | `language: Literal["python"]`; `build_argv` hard-codes `python -I harness.py plot.py` | a fixed command per language in one shared table (`agents/renderer/commands.py`), chosen by the renderer from `(language, library)`, never taken from the request; the harness gets an exec mode that sets the limits and supervises the language's own command |
| `agents/renderer/Dockerfile` | Python 3.14 venv with matplotlib and seaborn, Noto fonts | all eight Python extras, Chromium (one copy, shared by Playwright, kaleido and bokeh), Node 22 with the pinned `node_modules`, R 4.6 with ggplot2 4 and ragg, Julia 1.13 with the precompiled Makie depot |
| `agents/anyplot/code/` | Python AST everywhere: normaliser, regions, readiness, loader, validator, edits' drift check | the Python modules stay for the eight Python libraries (import surfaces per library, a save-target rule per library); JavaScript, R and Julia get a text-and-tree-sitter code profile each: markers, protected regions, loader, deny-list validator |
| `agents/anyplot/policy.py`, `prompts/adapter.md` | pandas wording (`df`, `pd.read_csv`) | a runtime section per language (how the data arrives, the placeholder spelling); the library rules already come from `prompts/library/<library>.md` |
| `agents/evals/make_fixtures.py` | 10 specs x 2 libraries x 6 perturbations | the same 10 specs for every library; the 80 % gate per library is the owner's Vertex run |
| `.github/workflows/ci-image.yml`, `agents/renderer/cloudbuild.yaml` | one 20-minute image build | a toolchain base image built rarely (owner question 1) and a fast renderer image on top |

## Requirements

- Every catalogue pair (spec, library) whose code follows the catalogue conventions is
  eligible, and the `.adapt()` button shows for it, once its library is in
  `AGENT_LIBRARIES`.
- The renderer runs the catalogue's CI render command for each language verbatim, in the
  same sandbox (no egress, read-only root, the harness's resource limits, the host
  watchdog), with the same `job_id` idempotency and cancel path.
- The host gates R1 (outputs), R2 (PNG hardening) and R3 (canvas) apply to every
  language. The probe gates (G3 to G12) stay matplotlib's: plotnine inherits them
  through matplotlib; every other runtime renders without a probe, and `evaluate`
  reports no probe line for it.
- The validator stays one guardrail layer among three (sandbox, loader substitution,
  validator). For Python the AST validator gains the import surface of each library. For
  JavaScript, R and Julia a deny-list over the parse tree refuses network, process,
  filesystem and reflection routes before the code runs.
- The exported code runs unchanged next to `data.csv` in the language's own tool
  (`python plot.py`, `Rscript plot.R`, `julia plot.jl`, `node render.mjs plot.js` with
  the harness, which the export names in its header).
- `AGENT_LIBRARIES` keeps its default `matplotlib,seaborn`; each further library is
  switched on in the deploy after its eval matrix reaches 80 % (design rule, owner run).
- No change to the catalogue pipeline, the muix regeneration or `plots/`.

## Relevant Files

### Existing Files to Modify

- `agents/anyplot/render/runtimes/__init__.py`: the registry (`runtime_for`,
  `RUNTIME_LIBRARIES`, `LANGUAGE_OF`).
- `agents/anyplot/render/runtimes/python.py`: library-aware (`library` on the instance;
  per-library env such as `BROWSER_PATH`, `BOKEH_RESOURCES=inline`, `SE_OFFLINE=true`;
  the validator and normaliser called with the library).
- `agents/anyplot/render/contract.py`: `RuntimeAdapter` gains `regions`, `readiness`,
  `validate_adaptation`, `protected_drift`, `placeholder` and `export_run_line`, so the
  pipeline stops importing the Python code modules directly.
- `agents/anyplot/render/__init__.py`, `agents/anyplot/pipeline.py`,
  `agents/anyplot/theme_render.py`, `agents/anyplot/opening.py`,
  `agents/anyplot/render/backends/local.py`, `agents/anyplot/render/backends/sandbox.py`,
  `agents/evals/matrix.py` (the preflight), `agents/evals/stress.py`,
  `agents/evals/ladder_lab.py`, `tests/unit/agents/runtime/test_service_flow.py` (the
  `pipeline.PythonRuntime` monkeypatch): use the registry instead of `PythonRuntime()`;
  backends resolve the runtime per job.
- `agents/anyplot/schemas.py` (`ArtifactName`, `artifact_names`), `api/routers/agent.py`
  (`ARTIFACT_MEDIA_TYPES`), `api/agent_cases.py`, `app/src/sections/agent-chat/ResultCard.tsx`:
  the code artifact's name per language instead of the literal `plot.py`.
- `agents/anyplot/settings.py`: `_known_libraries` checks the registry; the docstring
  table.
- `agents/anyplot/code/validate.py`: `LIBRARY_IMPORTS` for plotnine (`plotnine`,
  `mizani`), altair (`altair`, `vl_convert`), pygal (`pygal`, `cairosvg`), lets-plot
  (`lets_plot`), plotly (`plotly`, `kaleido`), bokeh (`bokeh`); the walk of their public
  submodules for `UNSAFE_SUBMODULES` and `UNSAFE_HELPERS`, pinned by the existing test.
- `agents/anyplot/code/regions.py`, `normalise.py`, `readiness.py`: the save statement
  per library (`write_image`, `chart.save`, `render_to_png`, `ggsave`, `plot.save`) next
  to `savefig`; the header and title rewrite unchanged; the canvas rewrite stays
  matplotlib-only (plotnine through `ggsave(..., dpi=, width=, height=)` later).
- `agents/anyplot/render/harness.py`: exec mode (`--exec`): start line, limits, run the
  language's command as a child, end line with the child's `rusage`; plot mode: the write
  allowlist gains `plot-<theme>.html`; the spawn allowlist for one shipped Chromium path
  (plotly's kaleido) and the bokeh screenshot path (owner question 9).
- `agents/anyplot/render/gates.py`: `CODE_FILE` per language for the error line;
  probe gates skipped without a probe.
- `agents/anyplot/code/export.py`: the run line per language.
- `agents/anyplot/policy.py`, `agents/anyplot/prompts/adapter.md`: the runtime section.
- `agents/renderer/wire.py`: `language: Literal["python", "javascript", "r", "julia"]`.
- `agents/renderer/executor.py`, `settings.py`: argv and env from the commands table;
  per-language `RLIMIT_AS` (off for Chromium, Node and Julia, which reserve address
  space far beyond their resident memory); `PATH` with the toolchain directories.
- `agents/renderer/Dockerfile`, `.dockerignore`, `agents/renderer/cloudbuild.yaml`,
  `.github/workflows/ci-image.yml`: the toolchains, the context allowlist
  (`package.json`, `package-lock.json`, `Project.toml`, `Manifest.toml`,
  `automation/js-render/render.mjs`), the smoke renders per language.
- `automation/js-render/render.mjs`: sandbox mode (`ANYPLOT_DATA_CSV` or a `data.csv`
  next to the snippet becomes `window.ANYPLOT_DATA`; `page.route` deny-all; no
  `plot-<theme>.html` outside the catalogue pipeline unless asked; `NODE_MODULES` from
  `ANYPLOT_NODE_MODULES`; the Chromium path from `PLAYWRIGHT_BROWSERS_PATH`). The CI
  pipeline's behaviour stays byte-identical without those variables.
- `agents/evals/make_fixtures.py`, `agents/evals/eligibility.py`, `agents/evals/cases.py`:
  every library.
- `app/src/pages/AgentChatPage.tsx`, `app/src/sections/agent-chat/*`: syntax
  highlighting and the download name per language (`plot.R`, `plot.jl`, `plot.js`,
  `plot.tsx`); the library pills already carry every library.
- `docs/concepts/agent-network.md` ("Render", "Adapt and validate", Phase 2 status),
  `agents/README.md` (settings, image, "Run it locally"), `agentic/docs/project-guide.md`
  (ci-image jobs), `changelog.d/<slug>.md` per PR.

### New Files to Create

- `agents/renderer/commands.py`: `LANGUAGE_COMMANDS`, the one table of code file name,
  argv and env per language, read by the executor, the local Docker backend and the
  runtimes. No ADK import.
- `agents/anyplot/render/runtimes/javascript.py`, `r.py`, `julia.py`: the three
  `RuntimeAdapter`s.
- `agents/anyplot/code/profiles/javascript.py`, `r.py`, `julia.py`: markers, protected
  regions (theme switch, theme tokens, the save statement, the placeholder), the loader
  statement, the normaliser (header strip, save target), the readiness scan
  (convention markers, security) and the deny-list validator per language.
- `agents/anyplot/code/treesitter.py`: the parser wrapper (`tree-sitter`,
  `tree-sitter-javascript`, `tree-sitter-typescript`, `tree-sitter-r`,
  `tree-sitter-julia`, all pinned in the `agents` extra), with the query helpers the
  three deny lists share.
- `agents/renderer/toolchain.Dockerfile` (owner question 1): Ubuntu 24.04 with R from
  rocker's layout and Posit binaries, Python 3.14 managed by uv, Node 22, Playwright
  Chromium, Julia 1.13 and the precompiled depot; published to GHCR by a workflow that
  runs on changes to the lock files.
- `agents/evals/fixtures/cases/<spec>-<library>-<perturbation>/` for the 13 libraries
  (generated).
- `tests/unit/agents/code/test_profiles_*.py`, `tests/unit/agents/renderer/test_commands.py`,
  `tests/unit/agents/runtime/test_runtimes.py`; renderer-image smoke scripts under
  `tests/image/` per language.

## Implementation Plan

IMPORTANT: Execute every step in order, top to bottom. Each numbered step is one PR
(the Fable review of 2026-10-24 split the former step 1 and put R before JavaScript;
see "Second opinion"). Steps 1b to 5 each end with the library's fixtures generated,
the eligibility sweep's numbers in the PR, and the matrix run documented as an owner
task; a library is enabled in the deploy only after that run. For R, Julia and
JavaScript the ten fixture specs must first carry the Data block (owner task per step:
regenerate them through the pipeline's regen), because the readiness scan blocks a file
without the marker and the matrix would otherwise have a handful of cases.

### 1a. Foundation: the runtime seam, with no behaviour change

- Add `agents/renderer/commands.py` with the command table keyed by `(language,
  library)`: the code file name, the argv (`python`: the current command; `javascript`,
  `r`, `julia`: the CI commands through the harness exec mode), the environment, the
  resource limits that differ from the defaults (`RLIMIT_AS` and `RLIMIT_NPROC` off for
  Chromium, Node and Julia; a screenshot post-step for bokeh and plotly, step 4) and the
  render p95 the repair reserve uses (`RENDER_P95_S` becomes a runtime attribute). The
  executor builds its argv from it; the library in the request is checked against the
  closed set of `core.constants` and only selects a row; the assertion that no `--write`
  or `--allow-egress` reaches a sandbox stays.
- Harness exec mode: `harness.py --exec -- <argv...>` prints the start line, sets the
  limits as today, runs the command with `subprocess.run` (the limits are inherited),
  prints the end line from `resource.getrusage(RUSAGE_CHILDREN)` and exits with the
  child's code. The start line comes before the child starts, so the launcher retry,
  the host watchdog and the kill path keep working. Python plots keep the in-process
  plot mode and the probe.
- Registry: `runtimes/__init__.py` maps every library of `core.constants` that has a
  runtime to an instance; `runtime_for(library, settings)`; `RUNTIME_LIBRARIES` is its
  key set (matplotlib and seaborn only in this step). The settings validator refuses a
  library without a runtime, as today.
- `RuntimeAdapter` grows: `placeholder`, `regions`, `readiness`, `validate_adaptation`,
  `protected_drift`, `error_summary` (the per-language error grammar: class and line,
  never the message), `export` (the run line and the artifact name) and `render_p95_s`.
  The pipeline's direct uses of the Python modules go through it; so do
  `agents/evals/matrix.py` (the preflight), `stress.py`, `ladder_lab.py`, and the
  `pipeline.PythonRuntime` monkeypatch in `tests/unit/agents/runtime/test_service_flow.py`.
- Backends resolve the runtime per job (`runtime_for(job.library)`) in `render`, while
  `run_data` and `convert` stay on the Python runtime; the local Docker backend's argv
  and the sandbox stub follow.
- The artifact name becomes a wire field: `schemas.ArtifactName` gains `plot.R`,
  `plot.jl`, `plot.js` and `plot.tsx`, `artifact_names` takes the runtime,
  `ARTIFACT_MEDIA_TYPES` in `api/routers/agent.py` and `api/agent_cases.py` carry the
  media types, and `ResultCard.tsx` reads the name from the version instead of the
  literal `plot.py`; the download, the feedback bundle and `get_current_code` follow.
- `wire.RenderRequest.language` widened; `gates.evaluate` without a probe; the renderer
  refuses a language whose toolchain the image does not carry (`503 runtime_unavailable`,
  from a startup check of the commands table, reported in `/status`).
- Tests, docs and the changelog fragment; the deploy's `_LIBRARIES` unchanged; the
  behaviour of matplotlib and seaborn is byte-identical (the catalogue corpus tests pin it).

### 1b. plotnine and altair

- `PythonRuntime(library=...)`: `LIBRARY_IMPORTS` gains `plotnine` and `mizani`,
  `altair` and `vl_convert`, each after a review of its public submodules
  (`REVIEWED_SUBMODULES`, `UNSAFE_SUBMODULES`, `UNSAFE_HELPERS`); `save` leaves
  `BANNED_ATTRIBUTES` for a per-library rule (altair's `chart.save` and plotnine's
  `plot.save` are the save statement, like `savefig`), the regions and the readiness
  scan know each library's save statement, and the normaliser's header and title
  rewrites run for both while its canvas rewrite stays matplotlib's (plotnine's
  `ggsave(dpi=, width=, height=)` later).
- altair's PIL padding block (`Image.open(f"plot-{THEME}.png")` ... `_canvas.save(...)`,
  179 catalogue files): `PIL.Image` joins altair's import surface with the reads and
  writes bound to the plot file by the harness's write allowlist; the normaliser keeps
  the block. `plot-<theme>.html` writes pass the harness (allowlist) and the file stays
  in the sandbox; the normaliser drops the HTML save from the run form (the export
  keeps it).
- Harness: the write allowlist gains `plot-<theme>.html`; a `FRAME_READERS` entry for
  `plotnine/mapping/_env.py: capture` (the spike's `call-stack is not that deep!`).
- Image: `uv sync` with `lib-plotnine` and `lib-altair`; the CI job smoke-renders one
  catalogue file per library through the harness.
- Fixtures for both libraries; the eligibility sweep's numbers in the PR; the owner's
  matrix run as a Todoist task.

### 1c. pygal and lets-plot

- The same shape: `pygal`, `cairosvg` and `cairocffi` (the harness imports `cairosvg`
  before the guard is armed when the plot names pygal: the spike's `ctypes.dlopen`),
  `lets_plot`; `render_to_png` and `ggsave` as save statements; lets-plot's
  `shutil.move`/`rmtree` of its `lets-plot-images` directory (24 catalogue files) is
  rewritten by the normaliser to `ggsave(..., path=".")`, the form the other 301 use.
  The slim image needs `libcairo2` for cairosvg.

### 2. R: ggplot2 (the exec-mode pilot)

- Toolchain: R 4.6.1 as in `.github/actions/setup-r` (Posit snapshot 2026-10-20, the same
  package list plus `readr`), `Rscript plot.R` through the exec mode;
  `R_LIBS_SITE` read-only from the image; `HOME=/tmp` for R's temp files; a baked
  `fc-cache` and `XDG_CACHE_HOME=/tmp` for ragg on the read-only root.
- Profile: placeholder `df <- load_user_data()`, loader `readr::read_csv("data.csv",
  col_types = cols(...), na = c(""), show_col_types = FALSE)` with the dtype map;
  protected regions: `THEME <- Sys.getenv("ANYPLOT_THEME", "light")`, the token
  assignments, the `ggsave(filename = sprintf("plot-%s.png", THEME), ...)` call; error
  grammar: R's `Error in <call>: ` line (the call's function name, no line number, so the
  repair gets the function and the stderr tail's `Calls:` chain); deny list (hygiene
  over tree-sitter, see "Second opinion"): `system`, `system2`, `pipe`, `file`, `url`,
  `socketConnection`, `download.file`, `source`, `sys.source`, `setwd`, `Sys.setenv`,
  `get`, `do.call`, `match.fun`, `eval(parse(...))`, `.Internal`, `dyn.load`,
  `requireNamespace`, `loadNamespace`, `::`/`:::` on `base` and `utils`, `library()`
  outside the image's set, `file.*` writes, `readLines` on a URL.
- Fixtures (after the owner regenerates the ten specs' R files under the Data block),
  the matrix, docs.

### 3. JavaScript: Chart.js, D3, ECharts, Highcharts and MUI X

- Toolchain: Node 22 under `/opt/node`, the repository's `package-lock.json` installed
  to `/opt/anyplot/node_modules`, Playwright's Chromium under `/opt/pw-browsers`
  (`PLAYWRIGHT_BROWSERS_PATH`), the harness at `/opt/anyplot/js-render/render.mjs`.
- `render.mjs` sandbox mode, every change behind an environment variable so the CI
  pipeline sees no difference: `ANYPLOT_DATA_CSV` (path) parsed to typed records as
  `window.ANYPLOT_DATA` (numbers, ISO dates, `null` for a missing cell, the dtype map
  from the profile passed as `ANYPLOT_DATA_TYPES`); `page.route("**/*", deny)` so the
  page can load nothing but the inlined bundle; `ANYPLOT_NO_HTML=1` leaves the
  interactive page out; `ANYPLOT_NODE_MODULES`; a hard cap on the snippet's console
  output (`consoleErrors` bounded). Chromium runs with `--no-sandbox` already (gVisor
  as uid 0). The sandbox file is `plot.js` or `plot.tsx`, so the command carries
  `--library=<library>` from the request, checked against the closed set.
- `RLIMIT_AS` and `RLIMIT_NPROC` off for `javascript` in the commands table: V8 and
  Chromium reserve virtual memory far beyond use, and one render runs 7 processes with
  77 tasks (processes plus threads), over the 64 of `RLIMIT_NPROC`, which counts
  threads on Linux. `RLIMIT_CPU` is per process after exec, so the host's wall clock is
  the real bound; the `MemAvailable` watchdog stays the memory control, and
  `RLIMIT_DATA` is a candidate for a bound that lets reservations pass (unverified
  under gVisor).
- Profile: placeholder `const data = loadUserData();`, loader
  `const data = window.ANYPLOT_DATA;`; protected regions: the token lines that read
  `window.ANYPLOT_TOKENS`/`window.ANYPLOT_THEME`, the `//# anyplot-orientation`
  directive; the deny list over tree-sitter (hygiene, not the boundary, see "Second
  opinion"): `fetch`, `XMLHttpRequest`, `WebSocket`, `EventSource`, `Worker`,
  `navigator.*`, `window.open`, `new Image().src`, `import()`/`require`, `eval`,
  `Function`, `.constructor`/`__proto__`, computed access on `window`, `globalThis`,
  `self`, `document` and `navigator`, `document.cookie`, `localStorage`, `postMessage`,
  `<script>`/`<iframe>` creation, `setTimeout` with a string; the readiness scan on the
  `// Data` and `// Plot` markers and a snippet that reads the tokens; the error
  grammar: the page error's class and the line in the snippet, which the harness
  reports with the scaffold's offset subtracted.
- MUI X (`.tsx`): the same profile with the TypeScript grammar, plus a static-import
  allowlist (`react`, `@mui/*`): esbuild inlines whatever a snippet imports, a JSON file
  of the image included.
- Adapter: the runtime section says the data is `window.ANYPLOT_DATA`, an array of
  records keyed by the column constants, and that the snippet never saves.
- Fixtures for the five libraries on the ten specs (after the owner regenerates their
  JavaScript files under the Data block); the owner's matrix run; docs; the Highcharts
  licence question stays open (owner question 6).

### 4. plotly and bokeh (through the JavaScript harness's Chromium)

- No browser from plot code: the plot guard replaces `fork_exec` before it is armed,
  so a spawn allowance would reopen it, kaleido's temp profile and choreographer's
  socket pair are refused too, and Selenium talks HTTP to chromedriver. The run form
  writes a page instead and a second child of the exec mode screenshots it:
  `node render.mjs --screenshot plot-<theme>.html` (the same Chromium, outside the
  Python guard, under the JavaScript row's limits).
- bokeh: the normaliser rewrites the catalogue's `export_png(...)` (plots/scatter-basic
  bokeh.py:96) or Selenium block (prompts/library/bokeh.md:99-130) to
  `output_file(f"plot-{THEME}.html"); save(p)` with `BOKEH_RESOURCES=inline`; the
  Jinja `exec` of bokeh's own templates gets a `CODE_BUILDERS` entry after a review
  (`file_html(template=...)` with a caller's template is banned by keyword).
- plotly: the normaliser rewrites `fig.write_image(...)` to
  `fig.write_html(f"plot-{THEME}.html", include_plotlyjs=True)` (never `cdn`) and
  `_plotly_utils/basevalidators.py: __init__` gets a `CODE_BUILDERS` entry after a
  review of the validator classes it builds; MathJax off.
- Deviation to name for the owner (question 10): for these two libraries the exported
  code is not byte for byte the run form (agent-network.md, "Fencing and exported
  code"): the export keeps the catalogue's own save block and runs unchanged on the
  user's machine; the run form carries the sandbox's HTML save instead.
- Fixtures, matrix, docs.

### 5. Julia: Makie

- Toolchain: Julia 1.13 under `/opt/julia`, the repository's `Project.toml` and
  `Manifest.toml` instantiated and precompiled into `/opt/julia-depot` with
  `JULIA_CPU_TARGET="generic;sandybridge,-xsaveopt,clone_all;haswell,-rdrnd,base(1)"`,
  a stacked `JULIA_DEPOT_PATH=/tmp/depot:/opt/julia-depot` so the sandbox can write
  its own compiled cache nowhere but `/tmp`; `JULIA_PKG_OFFLINE=true` and
  `JULIA_PKG_PRECOMPILE_AUTO=0`, so a cache miss fails in seconds instead of compiling
  for minutes under the timeout; `julia --project=/opt/julia plot.jl`; `RLIMIT_AS` off.
- The spike measures the cold `using CairoMakie` plus first `save` at 2 vCPU. Under
  45 s it ships synchronously under the 60 s timeout; above it, the design's
  submit-and-poll (`POST /render` answering `202` with a poll URL) is a renderer
  change of its own and this step waits for it (owner question 4). The first load of
  a multi-GB image under gVisor's gofer is a cold-start question local Docker cannot
  answer; `_MIN_INSTANCES=1` is the fallback.
- Profile: placeholder `df = load_user_data()`, loader `CSV.read("data.csv", DataFrame;
  types = Dict(...), dateformat = "yyyy-mm-dd")`; protected regions: `THEME =
  get(ENV, "ANYPLOT_THEME", "light")`, the tokens, `save("plot-$(THEME).png", fig; ...)`;
  error grammar: the exception type and the `at /work/plot.jl:<line>` frame; an
  allowlist for `using`/`import` (the Manifest's packages, never `Downloads`, `Sockets`,
  `Distributed`, `Libdl`, `Mmap`, `Pkg`), and a deny list: `run`, backtick `Cmd`
  literals, `download`, `Base.eval`, `eval`, `@eval`, `include`, `include_string`,
  `Meta.parse`, `ccall`, `@ccall`, `@cfunction`, `unsafe_*`, `getfield`, `invokelatest`,
  `open` for writing, `ENV` writes.
- Fixtures (after the owner regenerates the ten specs' Julia files under the Data
  block), the matrix, docs.

### 6. Add Tests

- `tests/unit/agents/renderer/`: the executor builds the argv of each language from the
  table; exec mode runs `node`, `Rscript` or `julia` when installed (skipped
  otherwise), the start and end lines and the exit code pass through; a language
  without a toolchain answers `503 runtime_unavailable`.
- `tests/unit/agents/code/`: each profile's regions, loader, normaliser, readiness and
  deny list on the catalogue's `scatter-basic` and `bar-grouped` files of every library
  (a corpus test per language, with the named bypass attempts refused).
- `tests/unit/agents/runtime/`: a full "Create plot" through `/v1` with the fake
  renderer for one library per language; the settings accept each library with a
  runtime; `evaluate` without a probe.
- `tests/unit/agents/test_image.py`: every toolchain file the renderer reads reaches the
  image, the `.dockerignore` admits the new context files, the deploy's substitutions
  match the settings.
- `tests/unit/agents/evals/`: `make_fixtures --check` for every library; the readiness
  scan marks each fixture pair not blocked.
- The CI image job renders one catalogue file per language inside the built image.

## Validation Commands

Execute these commands to validate the feature:

- `uv run ruff check agents tests && uv run ruff format --check agents tests`
- `uv run mypy agents`
- `uv run pytest tests/unit/agents -q -n auto`
- `uv run --extra agents python -m agents.evals.make_fixtures --check`
- `uv run --extra agents python -m agents.evals.eligibility --libraries all` (the sweep
  prints eligible, coupled and blocked pairs per library)
- `docker build -f agents/renderer/Dockerfile -t anyplot-renderer:dev .` then, for one
  catalogue file per language, `AGENT_RENDERER=local` through
  `tests/image/render_smoke.py` (new; the local backend with `--network none`)
- `cd app && yarn lint && yarn fm:check && yarn type-check && yarn test`
- `uv run python -m tools.changelog check --base origin/main`
- Owner, per library, on Vertex: `uv run --extra agents python -m agents.evals.matrix
  --model claude-haiku-5-5 --cases <library> --renderer remote --render-url <url>`; 80 %
  pass after at most one repair enables the library in `agents/cloudbuild.yaml`
  (`_LIBRARIES`).

## Measurements to take first (spikes, local Docker)

| Spike | Question | Where it decides |
|---|---|---|
| JS | Chromium under `--network none --read-only`: render time and peak RSS for chartjs, d3, echarts, highcharts, muix on `scatter-basic`; does a 1 GiB `RLIMIT_AS` kill it (expected yes) | step 2's limits |
| Python extras | plotnine, altair, pygal, lets-plot under `harness.py` plot mode: which writes, spawns or imports the guard refuses | step 1's allowlists |
| plotly, bokeh | kaleido with `BROWSER_PATH` and bokeh's HTML screenshot inside the guard | step 3's design |
| R | image size with the setup-r package set; `Rscript` render time | step 4 |
| Julia | depot size; cold `using CairoMakie` plus `save` at 2 vCPU | step 5, question 4 |

Note: the cloud session has Docker (started in-session, overlay2) but no gcloud
credentials, so nothing here can reach Vertex AI, the deployed renderer or Cloud Run
sandboxes; gVisor-specific behaviour (Chromium, Julia's memory maps) is measured only
by the owner's first deploy of the toolchain image.

### Results (2026-10-24, this session; 4 CPUs, no sandbox)

**Python extras under `harness.py` plot mode** (the plot guard armed, catalogue files of
`scatter-basic`, `bar-grouped`, `line-basic`, `heatmap-basic` as `plot.py`, unnormalised):

| Library | Result | Cause | Fix in step 1 |
|---|---|---|---|
| plotnine | every file fails in 2 s, `ValueError: call-stack is not that deep!` | `plotnine.mapping._env.Environment.capture` walks `inspect.currentframe()`, which `hide_frames` makes answer None | a `FRAME_READERS` entry for `plotnine/mapping/_env.py: capture` (it stores the plot frame's own `f_locals` and `f_globals`, no `f_back` beyond the caller), or let `inspect.currentframe` answer the real frame to that caller only |
| altair | the PNG is written (3200x1800, 2400x2400; `line-basic` 4998x2976, an R3 miss of the catalogue file itself), then `PermissionError: open` | the catalogue file also saves `plot-<theme>.html` | the write allowlist gains `plot-<theme>.html`; vl-convert needs no spawn |
| pygal | fails in 0.7 s, `PermissionError: ctypes.dlopen` | cairosvg imports cairocffi, which loads libcairo at import time | import `cairosvg` before the guard is armed when the plot names pygal (the pattern of `warm_scikit_learn`) |
| lets-plot | the PNG is written in 6 to 9 s (its native export, no browser), then `PermissionError: open` on `ggsave(..., "plot-<theme>.html")` | as altair | as altair |

**plotly and bokeh under `harness.py` plot mode** (`scatter-basic`, `bar-grouped`):

| Library | Result | Cause | Consequence for step 3 |
|---|---|---|---|
| plotly | `PermissionError: exec` inside `fig.update_layout` | `_plotly_utils/basevalidators.py` builds validator classes with `exec` on first use (`validator_cache.get_validator`) | a `CODE_BUILDERS` entry after a review of what that `exec` compiles (generated validator code from plotly's own package data) |
| plotly | kaleido fails at `socket.socketpair` | kaleido 1.x drives Chrome through choreographer: an asyncio loop with a socket pair, a spawned browser and pipes, all refused | do not run a browser from plot code: the run form writes the figure as JSON (`fig.write_json`), and the harness, after the plot returned and outside the guard, renders it with the package's own `plotly.min.js` through Playwright for Python and the shipped Chromium; the export keeps `write_image` |
| bokeh | `export_png` refused at `open`; `save(p)` refused at jinja2's template compile (`object.__getattr__` in `Template.from_code`) | `export_png` writes a temporary HTML file and starts a WebDriver; `save` compiles bokeh's Jinja templates with `exec` | the same shape: the run form writes `json_item`/`to_json`, the harness builds the page from the package's inlined BokehJS and screenshots it with Playwright; no WebDriver, no chromedriver, no Jinja `exec` under the guard. Selenium with a shipped chromedriver (the design's note) would need spawn, socket and temp-file allowances under the guard and is not recommended |

**JavaScript through `render.mjs`** (Node 22.22, Playwright 1.64.1 with Chromium 1248,
the repository's `package-lock.json`; `scatter-basic`, `bar-grouped`, `heatmap-basic`):

| Measurement | Result |
|---|---|
| Wall time per render, no limit | 0.8 to 3.8 s for chartjs, d3, echarts, highcharts, muix (ECharts' heatmap 3.8 s) |
| PNG | 3200x1800 or 2400x2400 for every render that completed |
| Largest child RSS | 144 to 152 MiB (one Chromium process; the tree is several) |
| `ulimit -v 1048576` (1 GiB) | Node aborts at startup (SIGABRT, V8 reservation) in every case |
| `ulimit -v 4194304` (4 GiB) | still fails (Chromium launch), every case |
| muix `scatter-basic` | esbuild cannot resolve `@mui/x-charts/ChartContainer`: the catalogue file is written for MUI X 7.29 and the lock pins 9.16; the running muix regeneration replaces such files, and R1 reports a failed bundle like any render error |

Consequence: `RLIMIT_AS` stays off for the JavaScript runtime; the `MemAvailable`
watchdog, `RLIMIT_CPU`, `RLIMIT_FSIZE` and the byte budget remain. The host's Chromium
tree needs about 400 to 500 MiB resident, well under the 4 GiB instance with one slot.
One ECharts render peaks at 7 processes and 77 tasks (processes plus threads), so
`RLIMIT_NPROC` 64 is off for this runtime too; the local backend's `--pids-limit 256`
holds.

**R through `Rscript`** (Docker, `rocker/r-ver:4.6.1` with the setup-r package set from
the Posit snapshot 2026-10-20 plus readr; `--network none --read-only --tmpfs /tmp`):

| Measurement | Result |
|---|---|
| Image | 1.03 GB (R 4.6.1, ggplot2 4.0.3, ragg, tidyr, dplyr, viridis, patchwork, readr, data packages) |
| Wall time per render, container start included | 1.2 to 1.9 s for `scatter-basic`, `bar-grouped`, `heatmap-basic` |
| Peak RSS | 182 to 294 MiB |
| `ulimit -v 1048576` and `ulimit -u 64`, as root and as uid 65534 | every render passes, PNGs 3200x1800 and 2400x2400 |
| stderr | only R's package attach messages and `geom_smooth()` notes; no network attempt |

Consequence: R keeps the Python defaults (`RLIMIT_AS` 1 GiB, `RLIMIT_NPROC` 64) and is
the cheapest pilot of the exec mode; `OPENBLAS_NUM_THREADS=1` changes nothing measurable.

## Second opinion (Fable, 2026-10-24)

Verdict: sound with changes. Gemini 4 Argon could not run in the cloud session (no
credentials); the owner's Todoist task carries the command. What the review changed in
this plan:

| Finding | Change |
|---|---|
| The matrix gate cannot be met for most non-Python libraries: of the ten fixture specs, the Data marker is in 5 ggplot2, 6 makie, 4 chartjs, 4 d3, 3 echarts, 1 highcharts and 2 muix files, and the readiness scan blocks the rest | An owner task per language step: regenerate the ten specs' files under the Data block through the pipeline's regen before the fixtures are generated |
| plotly and bokeh cannot spawn a browser under the plot guard (`fork_exec` is replaced before arming; kaleido needs a socket pair, temp files and `os.mkdir`; Selenium talks HTTP to chromedriver; Playwright for Python spawns its own Node driver), and `RLIMIT_AS` was keyed by language while both are `python` | Step 4 renders through the JavaScript harness's Chromium as a second exec-mode child; the command table is keyed by `(language, library)`; the export deviates from the run form for these two (question 10) |
| `gates.error_summary` reads a Python traceback (`File "plot.py", line N`, `ERROR_CLASSES`); R, Julia and the JS page error look different | An error grammar per profile on the runtime (`error_summary`), corpus-tested |
| `plot.py` is a wire literal: `schemas.ArtifactName`, `ARTIFACT_MEDIA_TYPES`, `api/agent_cases.py`, `ResultCard.tsx`, `get_current_code` | The artifact name per language joins step 1a's wire change |
| `save` is banned as an attribute and a name, so altair's `chart.save`, plotnine's `plot.save` and bokeh's `save(p)` fail SECURITY today; altair's PIL block, the `plot-<theme>.html` saves and plotly's `include_plotlyjs='cdn'` need rules | Step 1 split into 1a (the seam, no behaviour change) and one PR per library pair, each with the eligibility sweep's numbers |
| `RLIMIT_NPROC` counts threads; headless Chromium plus Node is past 64 | Measured: 77 tasks; `RLIMIT_NPROC` off for the JavaScript row |
| Missed sites: `evals/matrix.py` preflight, `stress.py`, `ladder_lab.py`, the `pipeline.PythonRuntime` monkeypatch in `test_service_flow.py`; backends hold one runtime; `RENDER_P95_S` is the repair reserve | All in step 1a; backends resolve the runtime per job; the p95 is a runtime attribute |
| Image: pin the GHCR base by digest; Highcharts in a public image is a redistribution question; bake `fc-cache`, `XDG_CACHE_HOME=/tmp`; Julia offline flags; `libcairo2` for cairosvg; the `ci-image.yml` change filter | Steps 1c, 2, 5 and question 11 |
| `render.mjs` takes the library from the file stem; MUI X imports are inlined by esbuild | `--library=` from the request against the closed set; a static-import allowlist for `.tsx` |
| Deny lists are hygiene, not a boundary: `globalThis["fe"+"tch"]`, `[].constructor.constructor`, R `get("system")`, Julia `getfield(Base, Symbol(...))` pass any identifier list | The threat model is stated: the sandbox protects the service, the list protects the person who runs the export from accidental I/O by the model; the lists grew by the review's names, and Julia's `using`/`import` is an allowlist |
| Order: R first as the smallest exec-mode pilot, then JavaScript, then plotly and bokeh on the proven Chromium path, then Julia | Adopted (question 3) |

Unverified by the review and still open: kaleido 1.x honouring `BROWSER_PATH` (moot
with step 4's design), gVisor's `RLIMIT_DATA` and `RLIMIT_NPROC` semantics, Chromium's
cold start under gVisor.

## Open questions for the owner

Defaults apply until answered; each is marked where the plan uses it.

1. **Image layout.** (A) one `agents/renderer/Dockerfile` that builds every toolchain
   (an hour-long build on each renderer change, a 20-minute CI job today), or (B) a
   public toolchain base image on GHCR built by a workflow on lock-file changes, with
   the renderer image `FROM` it (fast CI and deploys; everything in it is open source).
   Default: B.
2. **Base distribution.** R's binaries from Posit exist for Ubuntu, not Debian, so the
   toolchain image is Ubuntu 24.04 (rocker's R layout) with Python 3.14 managed by uv
   instead of `python:3.14-slim`. Default: yes.
3. **Order.** The design lists plotly and bokeh before JavaScript; this plan takes the
   seam first, then plotnine and altair, pygal and lets-plot, then R as the smallest
   exec-mode pilot, then JavaScript (five libraries, one runtime), then plotly and bokeh
   on that Chromium, then Julia. Default: this order.
4. **Julia.** Ship it in this round only if the cold render fits 45 s; otherwise defer
   it behind the submit-and-poll renderer change. Default: the spike decides.
5. **Renderer memory.** If the spikes show Chromium or Julia near the 512 MiB
   `MemAvailable` floor on a 4 GiB instance, the renderer goes to 8 GiB (cost).
   Default: measure first.
6. **Highcharts licence** for user plots is an open decision in the design; admin-only
   use stays as today. Default: Highcharts ships behind the same `AGENT_LIBRARIES`
   switch and is not enabled until decided.
7. **The 80 % matrix gate** per library needs the owner's Vertex run (Todoist task per
   library). Default: the gate stays.
8. **Non-Python validator** as a tree-sitter deny list (four grammar wheels in the
   `agents` extra), as the design names for JavaScript, with the threat model stated
   in "Second opinion". Default: yes, for R and Julia too.
9. **bokeh and plotly screenshots** through the JavaScript harness's Chromium as a
   second exec-mode child, after the plot code wrote the page; not Selenium with a
   shipped chromedriver (the design's note), and not Playwright for Python (it spawns
   a Node driver under the guard). Default: the harness child.
10. **Exported code for bokeh and plotly** keeps the catalogue's own save block while
    the run form saves HTML for the sandbox: the one place where the export is not
    byte for byte the run form (agent-network.md, "Fencing and exported code").
    Default: accept the deviation for these two libraries and document it there.
11. **Highcharts in a public toolchain image**: the free licence covers non-commercial
    use, and a public GHCR image redistributes the bundle. Default: the image stays
    private in Artifact Registry until decided (CI then needs a reader credential), or
    Highcharts is installed in the renderer image's own layer from the lock file at
    build time rather than shipped in the base.
