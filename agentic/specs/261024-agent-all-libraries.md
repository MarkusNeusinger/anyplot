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
  `agents/anyplot/render/backends/local.py`, `agents/anyplot/render/backends/sandbox.py`:
  use the registry instead of `PythonRuntime()`.
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

IMPORTANT: Execute every step in order, top to bottom. Each numbered step is one PR.
Steps 2 to 5 each end with the library's fixtures generated and the matrix run
documented as an owner task; a library is enabled in the deploy only after that run.

### 1. Foundation: the runtime registry and the four no-browser Python libraries

- Add `agents/renderer/commands.py` with `LANGUAGE_COMMANDS` (`python`: the current
  command; `javascript`, `r`, `julia`: the CI commands through the harness exec mode)
  and `code_file(language)`. The executor builds its argv from it; the assertion that no
  `--write` or `--allow-egress` reaches a sandbox stays.
- Harness exec mode: `harness.py --exec -- <argv...>` prints the start line, sets
  `RLIMIT_CPU`, `RLIMIT_FSIZE` and the optional `RLIMIT_AS` and `RLIMIT_NPROC` as today,
  runs the command with `subprocess.run` (the limits are inherited), prints the end line
  from `resource.getrusage(RUSAGE_CHILDREN)` and exits with the child's code. Python
  plots keep the in-process plot mode and the probe.
- Registry: `runtimes/__init__.py` maps every library of `core.constants` to a runtime
  instance; `runtime_for(library, settings)`; `RUNTIME_LIBRARIES` is its key set. The
  settings validator refuses a library without a runtime, as today.
- Route the pipeline's direct uses of `find_regions`, `scan`, `validate_adaptation`,
  `protected_drift`, the placeholder constant and `export_code` through the runtime, so a
  later language only adds a profile.
- `PythonRuntime(library=...)`: the validator's import surface per library; the regions
  and readiness know each library's save statement; the normaliser's header and title
  rewrites run for all eight, its canvas rewrite only for matplotlib and seaborn.
- Image: `uv sync` with `lib-plotnine`, `lib-altair`, `lib-pygal` and `lib-letsplot`
  too; the CI job smoke-renders one catalogue file per new library through the harness.
- `wire.RenderRequest.language` widened; `gates.evaluate` without a probe; the
  renderer refuses a language whose toolchain the image does not carry
  (`503 runtime_unavailable`, from a startup check of the commands table).
- Fixtures: `make_fixtures.py` for plotnine, altair, pygal and lets-plot; the
  eligibility sweep over all eight Python libraries.
- Tests, docs and the changelog fragment; the deploy's `_LIBRARIES` unchanged.

### 2. JavaScript: Chart.js, D3, ECharts, Highcharts and MUI X

- Toolchain: Node 22 under `/opt/node`, the repository's `package-lock.json` installed
  to `/opt/anyplot/node_modules`, Playwright's Chromium under `/opt/pw-browsers`
  (`PLAYWRIGHT_BROWSERS_PATH`), the harness at `/opt/anyplot/js-render/render.mjs`.
- `render.mjs` sandbox mode, every change behind an environment variable so the CI
  pipeline sees no difference: `ANYPLOT_DATA_CSV` (path) parsed to typed records as
  `window.ANYPLOT_DATA` (numbers, ISO dates, `null` for a missing cell, the dtype map
  from the profile passed as `ANYPLOT_DATA_TYPES`); `page.route("**/*", deny)` so the
  page can load nothing but the inlined bundle; `ANYPLOT_NO_HTML=1` leaves the
  interactive page out; `ANYPLOT_NODE_MODULES`; a hard cap on the snippet's console
  output. Chromium runs with `--no-sandbox` already (gVisor as uid 0).
- `RLIMIT_AS` off for `javascript` in the commands table (V8 and Chromium reserve
  virtual memory far beyond use; the `MemAvailable` watchdog stays the control).
- Profile: placeholder `const data = loadUserData();`, loader
  `const data = window.ANYPLOT_DATA;`; protected regions: the token lines that read
  `window.ANYPLOT_TOKENS`/`window.ANYPLOT_THEME`, the `//# anyplot-orientation`
  directive; the deny list over tree-sitter (`fetch`, `XMLHttpRequest`, `WebSocket`,
  `navigator.*`, `import()`/`require`, `eval`, `Function`, `document.cookie`,
  `localStorage`, `postMessage`, `<script>`/`<iframe>` creation, `setTimeout` with a
  string); the readiness scan on the `// Data` and `// Plot` markers and a snippet
  that reads the tokens.
- MUI X (`.tsx`): the same profile with the TypeScript grammar; the harness's React
  entry is unchanged.
- Adapter: the runtime section says the data is `window.ANYPLOT_DATA`, an array of
  records keyed by the column constants, and that the snippet never saves.
- Fixtures for the five libraries on the ten specs; the owner's matrix run; docs; the
  Highcharts licence question stays open (owner question 6).

### 3. plotly and bokeh (Chromium)

- plotly: kaleido 1.x with the shipped Chromium (`BROWSER_PATH`), MathJax disabled
  (`plotly.io.kaleido.scope.mathjax = None` in the normaliser or `KALEIDO_MATHJAX`),
  the plot guard allows the one spawn of that binary from kaleido's launcher and the
  temporary files kaleido writes under `/tmp`.
- bokeh: `BOKEH_RESOURCES=inline`; the screenshot through the shipped Chromium with
  Playwright for Python in a harness post-step on `plot-<theme>.html` (recommended), or
  Selenium with a shipped chromedriver and `SE_OFFLINE=true` as the design lists
  (owner question 9). Either way the exported `plot.py` keeps the catalogue's own
  save block.
- Fixtures, matrix, docs.

### 4. R: ggplot2

- Toolchain: R 4.6.1 as in `.github/actions/setup-r` (Posit snapshot 2026-10-20, the same
  package list plus `readr`), `Rscript plot.R` through the exec mode;
  `R_LIBS_SITE` read-only from the image; `HOME=/tmp` for R's temp files.
- Profile: placeholder `df <- load_user_data()`, loader `readr::read_csv("data.csv",
  col_types = cols(...), na = c(""), show_col_types = FALSE)` with the dtype map;
  protected regions: `THEME <- Sys.getenv("ANYPLOT_THEME", "light")`, the token
  assignments, the `ggsave(filename = sprintf("plot-%s.png", THEME), ...)` call; deny
  list: `system`, `system2`, `download.file`, `url`, `source`, `library` outside the
  image's set, `Sys.setenv`, `file.*` writes, `readLines` on a URL, `eval(parse(...))`,
  `.Internal`, `dyn.load`.
- Fixtures, matrix, docs.

### 5. Julia: Makie

- Toolchain: Julia 1.13 under `/opt/julia`, the repository's `Project.toml` and
  `Manifest.toml` instantiated and precompiled into `/opt/julia-depot` with
  `JULIA_CPU_TARGET="generic;sandybridge,-xsaveopt,clone_all;haswell,-rdrnd,base(1)"`,
  a stacked `JULIA_DEPOT_PATH=/tmp/depot:/opt/julia-depot` so the sandbox can write
  its own compiled cache nowhere but `/tmp`; `julia --project=/opt/julia plot.jl`.
- The spike measures the cold `using CairoMakie` plus first `save` at 2 vCPU. Under
  45 s it ships synchronously under the 60 s timeout; above it, the design's
  submit-and-poll (`POST /render` answering `202` with a poll URL) is a renderer
  change of its own and this step waits for it (owner question 4).
- Profile: placeholder `df = load_user_data()`, loader `CSV.read("data.csv", DataFrame;
  types = Dict(...), dateformat = "yyyy-mm-dd")`; protected regions: `THEME =
  get(ENV, "ANYPLOT_THEME", "light")`, the tokens, `save("plot-$(THEME).png", fig; ...)`;
  deny list: `run`, `download`, `Downloads`, `Base.eval`, `eval`, `include`,
  `ccall`, `@ccall`, `Pkg`, `Sockets`, `open` for writing, `ENV` writes, `Libdl`.
- Fixtures, matrix, docs.

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
3. **Order.** The design lists plotly and bokeh before JavaScript; this plan takes
   JavaScript first (five libraries, one runtime, and the Chromium the two Python
   libraries then reuse). Default: JavaScript first.
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
   `agents` extra), as the design names for JavaScript. Default: yes, for R and Julia too.
9. **bokeh screenshot**: Playwright for Python in a harness post-step (one Chromium, no
   chromedriver) or Selenium with a shipped chromedriver as the design lists.
   Default: Playwright post-step.
