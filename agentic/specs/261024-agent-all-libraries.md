# Feature: "Use with my data" for all 15 catalogue libraries

> **Status (2026-10-28):** plan, in progress. Steps 1a (the runtime seam) and 1b
> (plotnine and altair) merged with PR #12404; see "What 1b built" under step 1b. Step 1c
> (pygal and lets-plot) merged with PR #12405; see "What 1c built" under step 1c. The
> harness's kernel filter against program starts merged with #12410 and is mandatory
> for every in-process run since #12414. The deploy serves all six Python libraries for
> the admin's live tests, because only the admin reaches the chat yet (owner decision of
> 2026-10-28); `AGENT_LIBRARIES` keeps its default `matplotlib,seaborn`, and each
> library's matrix run gates the public release (lets-plot: 60 of 60 on 2026-10-28).
> Steps 2 (R) and 5 (Julia) were revised on 2026-10-28 after a second opinion (the
> section at the end). Step 2 serves ggplot2 since 2026-10-29 (PR 3b, "What PR 3b built"
> under 2c), and the admin deploy names it with the six Python libraries; every other
> library in this document is planned, not shipped. Step 5 (Julia) was revised on
> 2026-10-29 after a second opinion on it; its first PR, J1 (the toolchain stage and the
> command row, Makie not served), is built ("What J1 built" under step 5).

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
  a per-library environment where a library needs one, such as `BOKEH_RESOURCES=inline`;
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
  (`lets_plot`), plotly (`plotly`; never `kaleido`, which the run form does not call),
  bokeh (`bokeh`); the walk of their public
  submodules for `UNSAFE_SUBMODULES` and `UNSAFE_HELPERS`, pinned by the existing test.
- `agents/anyplot/code/regions.py`, `normalise.py`, `readiness.py`: the save statement
  per library (`write_image`, `chart.save`, `render_to_png`, `ggsave`, `plot.save`) next
  to `savefig`; the header and title rewrite unchanged; the canvas rewrite stays
  matplotlib-only (plotnine through `ggsave(..., dpi=, width=, height=)` later).
- `agents/anyplot/render/harness.py`: exec mode (`--exec`): start line, limits, run the
  language's command as a child, end line with the child's `rusage`; plot mode: the write
  allowlist gains `plot-<theme>.html`. No spawn allowance: a browser never starts from
  plot code (step 4 screenshots through the JavaScript harness instead).
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
  Chromium, Julia 1.13 and the precompiled depot; built by a Cloud Build trigger on
  changes to the lock files and pushed to the private Artifact Registry repository
  `anyplot` in `europe-west4`, next to the renderer image (owner question 1).
- `agents/evals/fixtures/cases/<spec>-<library>-<perturbation>/` for the 13 libraries
  (generated).
- `tests/unit/agents/code/test_profiles_*.py`, `tests/unit/agents/renderer/test_commands.py`,
  `tests/unit/agents/runtime/test_runtimes.py`; renderer-image smoke scripts under
  `tests/image/` per language.

## Implementation Plan

IMPORTANT: Execute every step in order, top to bottom. Steps 1a to 5 are one PR each,
seven PRs in all (the Fable review of 2026-10-24 split the former step 1 and put R
before JavaScript; see "Second opinion"); step 6 lists the tests those PRs carry, not a
PR of its own. Steps 1b to 5 each end with the library's fixtures generated,
the eligibility sweep's numbers in the PR, and the matrix run documented as an owner
task; a library is enabled in the deploy only after that run. ~~For R, Julia and
JavaScript the ten fixture specs must first carry the Data block (owner task per step:
regenerate them through the pipeline's regen), because the readiness scan blocks a file
without the marker and the matrix would otherwise have a handful of cases.~~
Superseded by the owner decision of 2026-10-29: in every language a file without the
`# Data` marker is `coupled`, never `blocked`, so the adapter rewrites its data creation
with the readiness hints. Regenerations under the Data block remain useful for the eval
fixtures, but no language step waits for them.

### 1a. Foundation: the runtime seam, with no behaviour change

- Add `agents/renderer/commands.py` with the command table keyed by `(language,
  library)`: the code file name, the argv (`python`: the current command; `javascript`,
  `r`, `julia`: the CI commands through the harness exec mode), the environment, the
  resource limits that differ from the defaults (`RLIMIT_AS` off for the JavaScript and
  Julia rows, `RLIMIT_NPROC` off for the JavaScript row alone; a screenshot post-step for
  bokeh and plotly, step 4) and the
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
  runtime to an instance; `runtime_for(library, cpu_seconds=)`; `RUNTIME_LIBRARIES` is
  its key set (matplotlib and seaborn only in this step). The settings validator refuses
  a library without a runtime, as today.
- `RuntimeAdapter` grows: `placeholder`, `regions`, `readiness`, `security`,
  `adaptation`, `apply_plan`, `restore_protected`, `new_literals`, `error_summary` (the
  per-language error grammar: class and line, never the message), `export` (the run
  line), `code_artifact` (the artifact name) and `render_p95_s`.
  The pipeline's direct uses of the Python modules go through it; so do
  `agents/evals/matrix.py` (the preflight), `stress.py`, `ladder_lab.py`, and the
  `pipeline.PythonRuntime` monkeypatch in `tests/unit/agents/runtime/test_service_flow.py`.
- Backends resolve the runtime per job (`runtime_for(job.library)`) in `render`, while
  `run_data` and `convert` stay on the Python runtime; the local Docker backend's argv
  and the sandbox stub follow.
- The artifact name becomes a wire field: `schemas.ArtifactName` gains `plot.R`,
  `plot.jl`, `plot.js` and `plot.tsx`, `artifact_names` takes the runtime's code artifact,
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

#### What 1b built (2026-10-25)

- **A save rule per library.** `regions.SAVE_RULES` holds one `SaveRule` per library:
  matplotlib and seaborn `savefig`; plotnine `save`, `ggsave` (the file is its second
  positional or `filename=`) and `savefig` after `fig = plot.draw()`; altair `save`
  with `fp`, the keywords `scale_factor`, `ppi`, `inline`, `embed_options` and
  `format`, a second allowed target `f"plot-{THEME}.html"` and `.open` of the PNG for
  the PIL block. `find_regions`, the normaliser's save-target rewrite, the readiness
  scan and `edits.apply_plan`, `restore_protected` and `protected_drift` take the
  library. The protected final save is the last module-level statement that writes
  the PNG, because altair's files end on the HTML save and pad the PNG inside an `if`.
  `normalise.SUPPORTED_LIBRARIES` is the rules' key set, and `PythonRuntime` serves
  `PYTHON_LIBRARIES`: matplotlib, seaborn, plotnine and altair.
- **Validator.** `LIBRARY_IMPORTS` gains plotnine (the matplotlib stack, `plotnine`,
  `mizani`) and altair (`altair`, `PIL.Image`). The walk of both public surfaces
  (2026-10-24) and an adversarial pass over it (2026-10-25) added denied submodules
  (`plotnine.data`, `watermark` and `animation`; `altair.datasets`, `jupyter`,
  `utils.execeval`, `utils.server` and `utils.html`), re-exported modules (`quarto`,
  jsonschema, narwhals, jinja2, vl_convert, pyarrow, polars and others), unsafe
  helpers (plotnine's `save_as_pdf_pages`, `Environment` and every plot's
  `.environment`; altair's image mark, `limit_rows`, `transformed_data`,
  `topo_feature`, `UrlData` and the plugin and renderer registries), altair-only bans
  (`from_dict`, `from_json`), the `pathlib.Path` and polars writers in `BANNED_IO`,
  and `theme_matplotlib` as a settings consumer that reads no settings file.
  `_check_save(rule)` replaces the savefig rule.
- **Harness.** The write allowlist gains `plot-<theme>.html`. `FRAME_READERS` gains
  plotnine's `Environment.capture`, and `inspect.currentframe` answers its caller's
  frame to a reader and None to everyone else (`frame_for_readers`), so both options
  of the spike's table are taken. The probe gives plotnine's canvas-less figure an Agg
  canvas. altair draws no matplotlib figure and writes no probe, so the host gates
  alone judge it.
- **Renderer.** The image installs `lib-plotnine` and `lib-altair` and links
  matplotlib's DejaVu Serif and DejaVu Sans Mono into `/usr/share/fonts`, which
  vl-convert needs for `serif` and `monospace`; the altair row of the command table
  runs without `RLIMIT_AS`; `ci-image.yml` renders a minimal plotnine and a minimal
  altair plot through the harness in the built image.
- **Evals.** `make_fixtures.py` writes the ten specs for plotnine and altair (240
  generated cases in all); the smoke set gains `scatter-basic-plotnine-renamed` and
  `scatter-basic-altair-renamed` (14 cases); `eligibility.py` sweeps all four
  libraries. The readiness scan blocks none of the ten fixture specs for either
  library.
- **Verified by hand.** The normalised catalogue `scatter-basic` files of plotnine (a
  3200x1800 PNG and the probe) and altair (the PNG and the HTML) render under the
  guard with the test venv; `test_harness_guard.py` renders both where the libraries
  are installed.

#### Decisions that change or settle the text above

| Text above | Built | Why |
|---|---|---|
| The normaliser drops altair's HTML save from the run form; the export keeps it | The HTML save stays in the run form: the validator admits exactly `f"plot-{THEME}.html"` as altair's second target, the harness allowlist takes the write, and the file stays in the sandbox, where nothing collects it | The export stays byte for byte the run form ("Fencing and exported code" in the design), which question 10 leaves to bokeh and plotly alone |
| The PIL block's reads and writes are bound to the plot file by the harness's write allowlist; the normaliser keeps the block | The block is kept, not stripped, and admitted by rule as well: `PIL.Image` (the module, not `ImageDraw` or `ImageFont`) in altair's import surface, `.open` only in altair's profile and only on the PNG, and the second `.save` (`_canvas.save(f"plot-{THEME}.png")`) checked by the save rule | The exported code runs unguarded on the user's machine, so the validator, not only the sandbox, holds the block to the plot file |
| Not covered | plotnine's expression strings are parsed and walked as code (every rule of the profile, the save and buffer-writer rules included): every string literal passed to `aes`, `after_stat`, `after_scale`, `stage`, `facet_wrap` or `facet_grid`, which take only literals the walk can read (a string, a number, a list of them, a nested expression call, a name bound once at module level to a string, `**` from a dict literal); `qplot` and `from_formula` are banned by name, `formula=` is a banned keyword on every call. The plot guard lets plotnine's `Environment.eval` run those strings (`CODE_BUILDERS`): what they reach stays refused there | plotnine evaluates a string that is not a column name with real builtins and the plot's namespace (survey of 2026-10-24), and patsy `exec`s Python while it parses a formula, which the plot guard would refuse anyway |
| `save` leaves `BANNED_ATTRIBUTES` for a per-library rule | `save` left `BANNED_IO`, where it was; the save rule refuses a save name it does not list as a `banned-call`, so `np.save` is refused by the rule, not by the set | Every save name (`SAVE_NAMES`) is checked in every profile, allowed or not; the DATA profile refuses all of them |
| Not covered | The probe attaches an Agg canvas to a figure that has none | plotnine builds its figure with `Figure()`, whose base canvas has no renderer; a PNG `savefig` switches it to Agg anyway, so the probe does the same first |
| The canvas rewrite stays matplotlib's | As planned: `SaveRule.canvas` is off for plotnine and altair, their readiness reasons carry a `canvas:` note, and their renders rely on the R3 gate | plotnine sizes its canvas on the save and altair through the chart's size times `scale_factor`; plotnine's own rewrite is next |
| `vl_convert` joins altair's import surface | `vl_convert` stays out | altair reaches it internally, and its own functions read files and open sockets for `<image>` hrefs |
| Not covered | The adversarial pass over the import surveys (2026-10-25) closed four routes by name: an altair image mark whose `file://` href vl-convert's SVG renderer reads from disk in native code (`mark_image`, `Url*`, the `url=` keyword, `Chart.from_dict` and `from_json` in altair's profile); the narwhals frame `alt.limit_rows` hands out, whose `.implementation.to_native_namespace()` is the pyarrow module; VegaFusion's `transformed_data`; and plotnine's `.environment`, the captured namespace every plot carries, whose `.namespace["os"]` is the `os` module as a value. altair's `data_transformers.enable("json")` and the registries' `.register` are banned in its profile too; `np.save` is refused under every rule by its receiver; a save's `format` and `path` by position are findings | The surveys' walk missed them; each was shown live in the scratchpad before the ban |
| Not covered (Python keeps the default limits) | altair's command row runs without `RLIMIT_AS` | vl-convert's embedded V8 aborts at start under any `RLIMIT_AS` up to 64 GiB (measured on 2026-10-25 through the harness); its resident set is about 270 MiB, and the `MemAvailable` watchdog, `RLIMIT_CPU`, `RLIMIT_FSIZE` and the byte budget remain |

#### Eligibility after 1b

`uv run --extra agents python -m agents.evals.eligibility` on 2026-10-25; matplotlib
and seaborn are unchanged against main.

| Library | Files | Eligible | Clean | Coupled | Blocked |
|---|---|---|---|---|---|
| matplotlib | 325 | 285 (87.7 %) | 15 | 270 | 40 |
| seaborn | 325 | 287 (88.3 %) | 18 | 269 | 38 |
| plotnine | 321 | 264 (82.2 %) | 58 | 206 | 57 |
| altair | 325 | 269 (82.8 %) | 57 | 212 | 56 |

Why the plotnine and altair files are blocked, counted in files from the readiness
reasons (a file can have several causes):

| Cause | plotnine | altair |
|---|---|---|
| One of the 13 map specs (altair's also carry URL literals and `topo_feature`) | 13 | 13 |
| Old-form file: no `THEME` block and a single-theme `plot.png` (altair's also `plot.html`) | 8 | 11 |
| A guard, path or `os` shape the normaliser does not strip yet: `sys.modules`, `importlib.util`, `import_module`, `SourceFileLoader`, a `pathlib` output directory or a target built from `__file__`, a bare `import sys`, `os` beyond `getenv` | 10 | 11 |
| `sklearn.datasets` for the example data | 8 | 8 |
| `.format` on a string | 4 | 5 |
| A module outside the surface: `contourpy` (2 each, one a map spec), `qrcode`; for altair also `circlify`, `zlib`, `PIL.ImageColor`, `statsmodels.regression`, `stats` and `tools`, and `vega_datasets` (a map spec) | 3 | 8 |
| A URL literal or `topo_feature` outside the map specs (`qrcode-basic`; altair's `chessboard-pieces` and `hexbin-map-geographic` too) | 1 | 3 |
| A string literal over 200 characters | 2 | 1 |
| `.query` | 1 | 1 |
| `formula=` | 1 | 0 |
| An aesthetic or facet argument the validator cannot read as a literal (a variable, a concatenation, `**mapping`; the adversarial pass of 2026-10-25) | 10 | 0 |
| An image mark (`mark_image`, `url=`), in a map spec | 0 | 1 |

#### Next

- Normaliser rules for the guard shapes it does not strip yet (the third row above:
  about 10 files per library).
- plotnine's own canvas rewrite through `save(dpi=, width=, height=)` and `ggsave`, so
  its canvas is exact before the R3 gate.
- The readiness coupling scan knows only matplotlib's limit and tick calls: plotnine's
  `coord_cartesian(xlim=, ylim=)`, `scale_*_continuous(limits=, breaks=)` and altair's
  `alt.Scale(domain=)` and axis `values=` go unflagged, so the adapter gets no `limits`
  hint for them (the `x10` fixture cases measure exactly this).
- altair writes no probe, so the advisory gates (G3 to G12, the row-fidelity check G8
  among them) never run for it; whether a row count read from the Vega spec's data
  should replace G8 is open.
- The normaliser blanks the catalogue title to `""`; code that divides by `len(title)`
  (11 plotnine, 5 altair, 54 matplotlib files) fails a raw render with ZeroDivisionError
  unless the adapter writes a new title. A non-empty placeholder would avoid it.
- A `plot-<theme>.html` of an altair chart with `disable_max_rows()` can hit
  `RLIMIT_FSIZE` (heatmap-mandelbrot: 50 MB); nothing collects the file, so the
  normaliser could drop the HTML save after all.
- `matrix.py` warns when `AGENT_LIBRARIES` does not enable a selected case's library
  (the two new smoke cases need `AGENT_LIBRARIES=matplotlib,seaborn,plotnine,altair`);
  whether the harness should enable the cases' libraries itself is open.
- The owner's matrix run per library on Vertex (question 7); since 2026-10-28 it gates
  the public release, and `_LIBRARIES` already names both (see step 1c, "Next").

### 1c. pygal and lets-plot

- The same shape: `pygal`, `cairosvg` and `cairocffi` (the harness imports `cairosvg`
  before the guard is armed when the plot names pygal: the spike's `ctypes.dlopen`),
  `lets_plot`; `render_to_png` and `ggsave` as save statements; lets-plot's
  `shutil.move`/`rmtree` of its `lets-plot-images` directory (24 catalogue files) is
  rewritten by the normaliser to `ggsave(..., path=".")`, the form the other 301 use.
  The slim image needs `libcairo2` for cairosvg.

#### What 1c built (2026-10-26)

- **Two more save rules.** `regions.SAVE_RULES` gains pygal: `render_to_png` (the file
  as its positional or `filename=`, plus `dpi=`), `render_to_file` for the HTML twin
  (`filename` only), and `cairosvg.svg2png`, which takes every argument by keyword
  (`SaveRule.keyword_only`: the file is `write_to=`). lets-plot saves through `ggsave`
  with the file second and `path="."` on every save (`SaveRule.directory`, the one
  literal every save passes). `SaveRule.writes` pairs a save name with the one file
  type it writes (pygal: `render_to_png` and `svg2png` only the PNG, `render_to_file`
  only the HTML; `SaveRule.writes_suffix`), which the validator, the readiness scan and
  the canvas step check. `SaveRule.canvas` names each library's canvas rewrite
  (`figure`, `pygal`, `letsplot`, or none for plotnine and altair). `SAVE_NAMES` gains
  `render_to_png`, `render_to_file` and `svg2png` in every profile, and `PythonRuntime`
  serves `PYTHON_LIBRARIES`: matplotlib, seaborn, plotnine, altair, pygal and
  `letsplot`.
- **Validator.** `LIBRARY_IMPORTS` gains pygal (`pygal`, `cairosvg`) and lets-plot
  (`lets_plot`), after a walk of both public surfaces that `REVIEWED_SUBMODULES` pins
  (pygal 3.1.3, cairosvg 2.9.1, lets-plot 4.11.0, `lets_plot.plot` included).
  - pygal: `cssselect2`, `tinycss2`, `webencodings` and `cairocffi` are unreachable,
    and so are cairosvg's `Path`, `parser`, `surface`, `url`, `image`, `css`,
    `features`, `test_api` and `ROOT`; pygal's `etree` is an unsafe submodule;
    `LIBRARY_BANS["pygal"]` holds the browser, pyquery and tree renderers,
    `add_xml_filter`, cairosvg's PDF, PS, EPS and SVG exporters, the cairo surfaces,
    the fetchers, `cut` and `_update` (which merges any dict into the chart's config).
    The config rule: `defs=` is refused, `js=` takes only `[]` or `()`, `css=` takes
    only inline entries and pygal's three package stylesheets (exempt from the URL rule
    at that node only), `.css` and `.js` are only ever the single target of a plain
    assignment, every `**` is a dict literal with string keys or a name bound once and
    used only as `**name`, and a `googlefont:` string is a URL literal. The SVG namespace names are exempt from the
    URL rule in pygal's profile only. `file_obj`, `unsafe` and `url_fetcher` are banned
    keywords on every call.
  - lets-plot: `geo_data`, `tilesets`, `settings_utils`, `frontend_context` and
    `plot.geom_livemap_` are denied, its 23 helpers (geocoding, map tiles, `to_png`,
    `to_svg`, `to_pdf`, `setup_show_ext`, `LazyModule` and others) are unsafe
    everywhere, and `LetsPlot.set`, `setup_show_ext` and `cfg` are module escapes.
    `LetsPlot` is only ever the receiver of a `setup_html()` with no arguments, and
    `.props` is banned. The `.format` exemption for builder chains is described in the
    table below.
  - Every profile: the save-name rule (`_check_save_names`), also inside plotnine's
    expression strings and in the DATA profile; plotnine's expression rule counts a
    name's bindings strictly (`_bindings`, match captures included). The SECURITY
    profile of every library pins `THEME` to its theme block and `os` to its import
    (`_check_theme_bindings`; see the table below), and a pygal save whose name does
    not write its target's file type is a `savefig-target` finding.
- **Normaliser.** Four guard rules for every library (`importlib.util.find_spec`
  tests, a `try` whose `finally` only restores `sys.path`, `del sys.modules[...]` and
  `sys.dont_write_bytecode` in a guard, `import_module("m").ATTR`). For pygal: the
  html-open rewrite (158 files), html-drop with its feeder cleanup (103 files, feeders
  in 41) and the canvas rewrite (94 files: 76 `render_to_png` saves become `svg2png`
  with `import cairosvg` added, 13 `svg2png` saves get the output size, and 5 hand-built
  SVGs get it from their root `<svg>`; 89 land at 3200x1800 and 5 at 2400x2400). A
  chart's size and an output size may be a module-level name bound once to a number; a
  size set after the constructor leaves the save alone with a note. For lets-plot:
  the `export_ggsave` alias rename (17 files), the star-import expansion (151 files,
  from `letsplot_names.py`, a static copy of `lets_plot.__all__` 4.11.0 that a test
  pins, in ruff's natural import order; a name the file may read before it binds it
  keeps the star import with a note), `path="."` on 62 saves in 31 files, 25 epilogues
  removed, one returned path unwrapped, the `f"{d}/plot-{THEME}.png"` target form, and
  the scale-only canvas rewrite (117 files; mosaic-categorical fits inside the target
  at 3000x1800 with `scale=1.875`, and three grids and two aspects keep a note). The
  header step strips every catalogue header at the top, because three lets-plot files
  carry two. The readiness scan reports a missing `path="."` and a save name that does
  not write its target's file type as `savefig-target` reasons, and for a pygal or
  lets-plot canvas of unknown size says that R2 refuses a PNG over its pixel cap
  instead of promising R3's padding. The normalised matplotlib and seaborn output is
  byte-identical to main on all 650 files, and all 1,946 catalogue files of the six
  libraries normalise idempotently.
- **Harness.** `warm_cairo` imports cairosvg before the guard is armed when the plot
  names pygal or cairosvg. `CODE_BUILDERS` gains `("cssselect2/compiler.py",
  "__init__")`, the compiler that turns each CSS selector of a pygal SVG into one
  `eval("lambda el: ...")` (87 per chart) and quotes every string the CSS controls with
  `repr`; its docstring holds the security argument. lets-plot needed no harness change:
  its native bridge loads at import, and its guarded renders wrote only the two
  allowlisted files.
- **Renderer.** `RuntimeCommand.rlimit_as_mb` is a row's own `RLIMIT_AS` in place of
  the configured one; it refuses to exist unless `rlimit_as` is on and the size is
  positive, and a configured limit of 0 still switches the limit off for every row.
  The letsplot row sets 2048 MiB, `ARROW_DEFAULT_MEMORY_POOL=system`,
  `FONTCONFIG_FILE=/opt/anyplot/fonts.conf` and `render_p95_s` 15. The pygal row keeps
  the Python defaults (its heaviest catalogue render, bifurcation-basic, peaks at
  682 MB resident; the guarded wall p95 is 3.75 s). `executor.sandbox_env` passes an
  in-process row's environment and own limit after the matplotlib keys and before
  `PATH`, `HOME` and the limit variables, which a row can no longer replace, and
  `PythonRuntime.env` gives the local Docker backend the same. The image installs
  `lib-pygal`, `lib-letsplot` and `libcairo2` (without recommends), links DejaVu Sans
  next to Serif and Mono, and copies `agents/renderer/fonts.conf` to
  `/opt/anyplot/fonts.conf`: 1,174,874,816 bytes, 49.2 MB (4.4 %) more than 1b's.
  `ci-image.yml` renders a pygal plot in both save forms (`render_to_png` at 3200x1800,
  and a 4800x2700 chart through `svg2png` at 3200x1800, the canvas rewrite's form) and
  a lets-plot plot through the harness in the image; the lets-plot step takes its
  environment and limit from the command table's row and also fails on "Fontconfig
  error" in stderr. The image build itself fails when any of 39 programs (those the
  bridge's ImageMagick delegates to, such as `gs`, `curl`, `soffice` and `ffmpeg`,
  ImageMagick's own tools, `fc-list`, `fc-match`, `java` and `node`;
  `agents/renderer/delegates.py`) is on the sandbox's `PATH` (`executor.SANDBOX_PATH`),
  so the Cloud Build deploy enforces it as well as the CI job, which runs the check once
  more in the built image (the Copilot review of #12405: a CI-only check would let a
  base-image change reach production unseen).
- **Host gates.** R2's blank check refuses a canvas that is 99.7 % one colour, not 98 %,
  for every library (see the table below).
- **Evals.** `eligibility.py` sweeps all six libraries. `make_fixtures.py` writes the
  ten specs for pygal and lets-plot (360 generated cases in all, 367 in a full run); the
  smoke set gains `scatter-basic-pygal-renamed` and `scatter-basic-letsplot-renamed`
  (16 cases). pygal has no column syntax, so its `renamed` case tests the axis titles
  the adaptation must pass itself. The readiness scan blocks two of the ten pygal
  fixture files, which `test_make_fixtures.py` pins: `histogram-basic` composites an
  annotation layer onto the PNG with PIL (`io`, `PIL.Image`, `ImageDraw`,
  `ImageFont`), and `line-timeseries` draws its random walk with the standard `random`
  module, which no plot profile admits and none will: the adapter must not fabricate
  data, which the ADAPTATION rules enforce. Their 12 cases are written anyway and open
  blocked sessions until the catalogue files change; every lets-plot fixture file is
  eligible. Since the regenerations of 2026-10-28 only `line-timeseries` is blocked
  (6 cases); `histogram-basic` is `coupled` (see the pygal gate under "Next").
- **Verified by hand.** The literal `ci-image.yml` steps against the 1c image: the
  seaborn, plotnine and altair PNGs, the altair HTML and the multi-script render are
  byte-identical to the 1b image's; pygal renders in 1.6 to 1.8 s at 185 to 189 MB, and
  lets-plot in 5.0 to 5.3 s at 663 to 667 MB with an empty stderr. Through the local
  Docker backend, the normalised `scatter-basic` of pygal (1.4 s per theme) and of
  lets-plot (6.0 s per theme) render both themes at 3200x1800, and pygal's
  `line-basic`, a 4800x2700 chart, renders at 3200x1800. `test_harness_guard.py`
  renders the same three files under the guard where the libraries are installed. After
  the review fixes, every renderer-image step of `ci-image.yml` passed three times
  against the rebuilt image with the round-one PNG sizes (the pygal `svg2png` form
  3200x1800 too), and the normalised hand-built-SVG files (dendrogram-radial,
  histogram-2d, upset-basic, ternary-density), heatmap-basic and lets-plot's
  mosaic-categorical render at their target in both themes, which R2 accepts.

#### Decisions that change or settle the text above

| Text above | Built | Why |
|---|---|---|
| The canvas rewrite stays matplotlib's (1b) | Canvas rewrites for both libraries. pygal: a chart at another literal size with the target's aspect (in the catalogue only 4800x2700 and 3600x3600) saves through `cairosvg.svg2png(bytestring=chart.render(), write_to=f"plot-{THEME}.png", output_width=3200, output_height=1800)` or 2400 by 2400, the chart itself unchanged. lets-plot: only `scale=` on the PNG save changes (the PNG is the `ggsize` times the scale, floored) | R2's pixel cap (`MAX_IMAGE_PIXELS`, 11.52 MP) refuses a 4800x2700 or 3600x3600 PNG outright, and R2 is blocking: 123 of the 322 lets-plot files that render (108 of the 284 eligible) and about a third of the pygal files are that size, and lets-plot's scale sits in the protected save, out of the adapter's reach. After the rewrite 268 of 273 lets-plot renders are on target and none is over R2's pixel cap, and the guarded wall p95 falls from 25.9 s to 12.5 s; `svg2png` gives pygal's exact canvas with the same layout |
| lets-plot's `shutil.move`/`rmtree` (24 catalogue files) is rewritten to `ggsave(..., path=".")`, the form the other 301 use | `path="."` is added to 62 saves in 31 files, one computed `path=` becomes `"."`, 25 epilogues are removed and one returned path is unwrapped; the save rule requires `path="."` on every `ggsave` (`SaveRule.directory`), and readiness reports its absence | 31 files save without `path=`, not 24, and 292 pass `path="."`, not 301: 21 files move their outputs afterwards, 4 pass `path="."` and keep a dead `rmtree`, and others write straight into `./lets-plot-images` or compute the directory. Without `path=`, `ggsave` creates that directory, which the guard refuses (`os.mkdir`) |
| Not covered | The star import (`from lets_plot import *`) becomes one explicit import of the names the file uses, from the static list in `letsplot_names.py` | 151 files use it, not the survey's 158 (counted by AST and by grep). The validator refuses star imports; the expansion alone unlocks 132 files. A static list keeps the normaliser from importing lets-plot (the agents image does not install it, and an import runs its side effects); a test fails an upgrade that changes `__all__` |
| `render_to_png` and `ggsave` as save statements | pygal's rule also lists `render_to_file` (the HTML twin, `filename` only) and `cairosvg.svg2png` with a keyword-only `write_to=` and without `url=`, `file_obj=` and `unsafe=`; `render_to_png` takes only `filename` and `dpi` | 87 catalogue files end on `svg2png`. libcairo writes the PNG with its own `fopen`, which the audit hook never sees, so the static pin is the only thing that holds the path. `render_to_png` and `render_to_file` hand their `**kwargs` to the chart's config (`css=`, `js=`, `defs=`), and `svg2png`'s `url=` and `file_obj=` read through cairosvg's unrestricted fetcher |
| `pygal`, `cairosvg` and `cairocffi` in the import surface | `pygal` and `cairosvg` only; `cairocffi`, `cssselect2`, `tinycss2` and `webencodings` are unreachable. `xml.etree` and `Graph` subclasses stay out of pygal's profile, and PIL out of both | cffi's library loads and calls into libcairo raise no audit event. A forged token handed to cssselect2's selector compiler is the one route to an unquoted slot in the lambda it builds, so the CSS stack stays out of reach. `xml.etree`, class definitions and PIL change the security surface and wait for the owner ("Next"): `xml.etree` and `Graph` subclasses block 45 pygal files, PIL 4 lets-plot files |
| Not covered | `CODE_BUILDERS` gains cssselect2's `CompiledSelector.__init__` | Every pygal PNG export compiles the chart's stylesheet into one `eval("lambda el: ...")` per selector. The spike fed 339 selectors with quotes, escapes, newlines and Python text through every pygal channel: the generated source only compares `el`'s name, classes, id, attributes and `lang` |
| Not covered (pygal's HTML writes) | html-open: a write of exactly the chart's `render()` output to `f"plot-{THEME}.html"` becomes `chart.render_to_file(f"plot-{THEME}.html")` (158 files). html-drop: every other module-level HTML or SVG write (hand-built pages, post-processed SVG, `.svg` files) is removed with the assignments that only fed it (103 files) | Dropping alone would unlock the same files; the rewrite is chosen for the export: its HTML and PNG are byte-identical to the catalogue file's on all 156 runnable files (apart from pygal's generation-date comment), and `render_to_file` is a save name the validator pins while `open` stays banned. The dropped writes have no pinnable form, and the guard refuses `.svg` writes anyway; the export loses those pages |
| Not covered (Python keeps the default limits) | lets-plot's row has its own `RLIMIT_AS` of 2048 MiB (`RuntimeCommand.rlimit_as_mb`) with Arrow's system allocator and a minimal fontconfig file in its environment; not the Python default and not off as for altair | lets-plot rasterises in its Kotlin/Native bridge with ImageMagick linked in. An allocation it cannot make kills the process ("Out of memory trying to allocate"): SIGABRT (exit 134) on a developer machine, SIGSEGV (exit 139) in the renderer image, with either Arrow pool. pyarrow's default pool reserves another 1 GiB arena on the first pandas string column, which kills even a minimal 3200x1800 chart at 1024 and 1536 MiB; with the system allocator 18 of the 42 spike renders still die at 1024 MiB. With it, 2048 MiB held all 42 spike renders up to 4800x2700 and 3600x3600 (peak 1697 MiB) and still stops a 6400x3600 export (2580 MiB). No catalogue file renders at 6400x3600: the `ggsize(1600, 900)` files use `scale=3`, so the survey's worst case does not occur. Off, a runaway scale would meet only the `MemAvailable` watchdog |
| The slim image needs `libcairo2` | As planned, without recommends (a 13.8 MB layer), plus DejaVu Sans linked next to Serif and Mono and `/opt/anyplot/fonts.conf` | lets-plot draws its default text in DejaVu Sans and falls back to a Noto Sans face without it; its bridge's own fontconfig finds no configuration in the image and writes "Fontconfig error" on every export. `libcairo2` brings Debian's DejaVu faces and `/etc/fonts`, which left every seaborn, plotnine and altair render of `ci-image.yml` byte-identical |
| Not covered | In every profile a save name imported under another name, anything imported under a save name, and a bare save name that is not a call's callee are a `banned-call`; a `match` capture counts as a binding of a plotnine expression name | Both routes passed the shipped plotnine profile with no finding: `from plotnine import ggsave as keep` (or `g = ggsave`, `[ggsave][0]`, `functools.partial(ggsave, plot)`) reaches any path in the exported code, and `COLUMN = "x"` followed by `match '<code>': case COLUMN: pass` hands plotnine code to evaluate in `aes(x=COLUMN)`. The normaliser renames the `export_ggsave` alias in 17 lets-plot files; no eligible file is lost, and the raw findings of the four shipped libraries are unchanged |
| Not covered (`.format` is a banned attribute) | lets-plot's profile exempts a `.format` with string-literal arguments (positional, `field=`, `format=`) at the end of a chain of builder methods (`LETSPLOT_BUILDER_METHODS`, each checked to return the builder in 4.11.0) whose root is `layer_tooltips()`, `layer_labels()` or `smooth_labels()`, imported from `lets_plot` under a name bound once whose attributes are never stored | 59 catalogue files use it 128 times, and the exemption is worth 53 eligible files (284 instead of 231). `str.format` stays refused, and so do a builder held in a variable, a rebound builder name, a non-literal argument and `lets_plot.layer_tooltips = str` |
| Not covered (R2's blank check refuses a canvas 98 % one colour, since phase 1) | `MAX_BACKGROUND_RATIO` is 0.997 for every library: R2 refuses a canvas that is 99.7 % one colour, and its message gives the share to one decimal | Measured on 2026-10-26 with `core.canvas.dominant_color`: the sparsest eligible pygal render (network-directed) is 99.44 % one colour, 33 of the 195 eligible pygal renders are at 98 % or more, and lets-plot's point-basic is at 98.38 %, so 0.98 refused about one pygal plot in six on every render. A pygal chart with only a title is 99.78 % and a bare pygal canvas 99.93 %. A pygal chart with axes and guides but no data is 98.62 % and passes; R2 never caught empty axes, because matplotlib's stay under 98 % too. A higher threshold refuses nothing that 0.98 accepted |
| `render_to_png` and `ggsave` as save statements (pygal's three save names, the row above) | `SaveRule.writes` gives each pygal save name the one file type it writes: `render_to_png` and `svg2png` the PNG, `render_to_file` the HTML. The validator reports a mismatch as `savefig-target` (`render_to_file writes only f"plot-{THEME}.html"`), and a PNG save under the wrong name does not count as the PNG save; the readiness scan reports it through `SaveRule.writes_suffix`, and the canvas step and `measure_canvas` leave such a save alone | The rule took any of the three names with either target, so `chart.render_to_file(f"plot-{THEME}.png")` wrote SVG text into the PNG and `render_to_png(f"plot-{THEME}.html")` a PNG into the HTML, both with no finding, and the canvas rewrite turned the first into `svg2png` (correctness review of 2026-10-26). No catalogue file changes |
| Not covered (`THEME` is a protected region, not a pinned name) | The SECURITY profile of every library pins `THEME` (rule `savefig-target`): its one binding is the first module-level theme block that `regions.is_theme_assignment` accepts, after `import os`. Every other binding is a finding at its own line: a second, augmented or annotated assignment, an unpacking, a `for`, `with`, `except`, `match`, walrus or comprehension target, an import, a `def` or parameter, `del`, a type alias and a `global` or `nonlocal` declaration. Once `import os` binds `os`, any other binding of `os` is an `os-use` finding | Every save target is `f"plot-{THEME}..."`, so a rebound `THEME` moves the write. The security review of 2026-10-26 passed the validator with `THEME` reassigned to a traversal literal before `svg2png`, whose native write the guard never sees; it failed only because no `plot-` directory existed. The pin refuses three theme blocks the validator passed (`os.environ.get`, an `os` alias, `.lower()`), which the readiness scan already blocked as `no-theme`. No catalogue file binds `THEME` twice, eligibility is unchanged, and only heatmap-polar (pygal, already blocked) gains a finding. The block's default value stays unpinned ("Next") |
| html-drop removes the HTML and SVG writes with the assignments that only fed them (the HTML row above) | html-drop also removes a module-level `with open(...)` of the theme's `.html` or `.svg` target whose body assigns names that nothing outside it reads and whose values hold no save call, as long as it writes at least once; html-open still rewrites only a single-write body | heatmap-basic writes its hand-built page from a two-statement body (`pygal_svg = chart.render(...)`, then `fout.write(...)`), which left `open` and a 216-character literal in the run form and blocked the file and its six fixture cases. The extension unlocks exactly that file (blocked to coupled); no other catalogue file's output changes |
| The pygal canvas rewrite reads the chart's literal size (the first row) | Where the `svg2png` bytestring traces to no chart, the normaliser reads the root `<svg>`'s `width=` and `height=` from the string literals that build the bytestring (through names, `+=`, `.append`, `.extend` and `.insert`), as numbers, `px` lengths or module-level names bound once, and sets the output size as for a traced chart. Several `<svg>` tags, a computed or `%` size, or a name bound twice leave a note. A size set after the constructor (`.width` or `.height` stores, `chart.config(...)`, `config=`, a positional `pygal.Config`, a `render()` keyword) makes the size unknown: a note, no rewrite, and no fallback to pygal's 800x600 | Four eligible pygal files (dendrogram-radial, histogram-2d, upset-basic, ternary-density) pass a hand-built 4800x2700 or 3600x3600 SVG to `svg2png` with no output size, so R2's pixel cap refused every render while the readiness reason promised R3's padding. They now render at 3200x1800 or 2400x2400 in both themes, and heatmap-adjacency gets the same rewrite but stays blocked by a function-level guard. Module-level size names turned 6 of the 7 unknown-size notes on eligible pygal files into known on-target sizes; heatmap-stripes-climate (`**_base`) keeps its note. No eligible pygal or lets-plot file now has a known size over the cap |

#### Eligibility after 1c

`uv run --extra agents python -m agents.evals.eligibility` on 2026-10-26; matplotlib
and seaborn are unchanged against main. plotnine and altair gain seven files from 1c's
library-agnostic rules: plotnine's bar-horizontal and spiral-timeseries and altair's
chessboard-basic, voronoi-basic, waffle-basic and scatter-ashby-material through the
guard rules, and plotnine's candlestick-volume through the `f"{d}/plot-{THEME}.png"`
target form. The review fixes moved one file: html-drop's extension makes pygal's
heatmap-basic eligible (208 before). The `THEME` pin and the save-name pairing change
no status.

| Library | Files | Eligible | Clean | Coupled | Blocked |
|---|---|---|---|---|---|
| matplotlib | 325 | 285 (87.7 %) | 15 | 270 | 40 |
| seaborn | 325 | 287 (88.3 %) | 18 | 269 | 38 |
| plotnine | 321 | 267 (83.2 %) | 59 | 208 | 54 |
| altair | 325 | 273 (84.0 %) | 58 | 215 | 52 |
| pygal | 325 | 209 (64.3 %) | 64 | 145 | 116 |
| lets-plot | 325 | 284 (87.4 %) | 53 | 231 | 41 |

Why the pygal and lets-plot files are blocked, first cause per file (each column sums to
its blocked count):

| Cause | pygal | lets-plot |
|---|---|---|
| One of the 13 map specs | 13 | 13 |
| `xml.etree` post-processing of the SVG | 23 | 0 |
| A subclass of pygal's `Graph` (a class definition) | 18 | 0 |
| Old-form file: no `THEME` block and a single-theme `plot.png` | 13 | 7 |
| `io` or PIL compositing of the PNG | 12 | 4 |
| `sklearn.datasets` for the example data | 6 | 10 |
| `.format` on a string (lets-plot: hex colours) | 6 | 4 |
| matplotlib, outside pygal's surface | 4 | 0 |
| A guard shape the normaliser does not strip | 3 | 0 |
| A string literal over 200 characters | 3 | 1 |
| `.query` | 0 | 1 |
| `qrcode` and a URL literal | 0 | 1 |
| Other one-offs | 15 | 0 |

By SECURITY rule (a file can have several): pygal `banned-import` 62, `savefig-target`
30, `banned-statement` 22, `dunder` 22, `banned-keyword` 19, `banned-attribute` 16,
`string-length` 12, `banned-call` 7, `os-use` 6, `banned-name` 5, `url-literal` 2;
lets-plot `banned-import` 18, `banned-call` 11, `savefig-target` 8, `banned-attribute`
7, `url-literal` 1, `string-length` 1. 216 normalised pygal files and 293 lets-plot
files pass SECURITY; the map specs and the files without a `THEME` block make up the
rest of the gap. The static count includes files that fail their first render anyway:
13 pygal and 10 lets-plot files divide by the length of the emptied title,
waveform-audio (pygal) runs past `RLIMIT_CPU` in cairosvg's path parser, and two
lets-plot files do not render with lets-plot 4.11.0: calibration-curve raises a
MagickWand error in the export, and line-confidence writes an almost fully transparent
PNG, which R2 refuses as 100 % one colour. R2's blank check, at 99.7 %, passes every
eligible pygal render measured (the sparsest is 99.44 %).

#### Next

Settled by 1c: normaliser rules for the guard shapes of 1b's third blocked row. The four
library-agnostic rules and the new target form took plotnine from 264 to 267 and altair
from 269 to 273. The rest of that row stays, altair's two `"site-packages" in X.origin`
loaders among it, which the find-spec rule leaves alone. Also settled: the fixtures and
smoke cases for pygal and lets-plot ("What 1c built"), and the review of the lets-plot
bridge (the owner questions below). What stays from 1b's list, and what 1c adds:

- plotnine's own canvas rewrite through `save(dpi=, width=, height=)` and `ggsave`.
  plotnine and altair are now the only Python libraries whose canvas rests on the R3
  gate.
- The readiness coupling scan knows only matplotlib's limit and tick calls: plotnine's
  `coord_cartesian(xlim=, ylim=)` and `scale_*_continuous(limits=, breaks=)`, altair's
  `alt.Scale(domain=)` and axis `values=`, pygal's `range=` (111 files) and `xrange=`
  (75 files), and lets-plot's literal `limits=` and `breaks=` (126 files, of which the
  scan flags 10) go unflagged, so the adapter gets no `limits` hint for them.
- altair, pygal and lets-plot write no probe, so the advisory gates (G3 to G12, the
  row-fidelity check G8 among them) never run for them; whether a row count read from
  the chart's own spec should replace G8 is open.
- The normaliser blanks the catalogue title to `""`; code that divides by `len(title)`
  (11 plotnine, 5 altair and 54 matplotlib files, and among the eligible files 13 pygal
  and 10 lets-plot ones) fails a raw render with ZeroDivisionError unless the adapter
  writes a new title. A non-empty placeholder would avoid it.
- HTML saves stay in the run form, uncollected: altair's `disable_max_rows()` heatmap
  writes 50 MB and can hit `RLIMIT_FSIZE`, and pygal's and lets-plot's reach 25 MB
  (lets-plot's heatmap-mandelbrot 25.3 MB, about 40 % of the 64 MiB run budget; pygal's
  ice-basic 21.7 MB). The normaliser could drop the HTML save after all.
- `matrix.py` warns when `AGENT_LIBRARIES` does not enable a selected case's library;
  whether the harness should enable the cases' libraries itself is open.
- Arrow's system allocator for every plot row: pyarrow's default pool reserves a 1 GiB
  address-space arena on the first pandas string column, which counts against
  `RLIMIT_AS` in every Python row, and only lets-plot's row and the conversions avoid
  it. The CI lets-plot step takes its variables from the command table's row but cannot
  tell whether the allocator took effect, because its minimal chart passes at 2048 MiB
  with either pool; only unit tests pin it. A second run at 1536 MiB would tell (the
  system pool exits 0, the default pool 139).
- A resource-error grammar for lets-plot: under `RLIMIT_AS` the bridge dies by a signal
  after "Out of memory trying to allocate" (SIGABRT, exit 134, on a developer machine;
  SIGSEGV, exit 139, in the renderer image) or raises a MagickWand `ValueError` from the
  export, and `gates.error_summary` hands that `ValueError` to the repair as a code
  error on the `ggsave` line. All three should read as resource errors.
- Three eligible files always fail R2's pixel cap: matplotlib's dot-matrix-proportional
  and timeseries-decomposition and seaborn's heatmap-clustered crop a 4800x3000 or
  4800x3600 canvas with `bbox_inches="tight"` at an aspect that no dpi brings onto a
  target. Their readiness reason says so since 2026-10-26. A fit inside the target, as
  lets-plot's rewrite does, or blocking a known over-cap canvas in the readiness scan
  would change what matplotlib and seaborn do today.
- pygal's cairo writes a fontconfig cache of about 184 KB (7 files) into
  `$HOME/.cache/fontconfig`, the sandbox's private `/tmp`, on every render: native
  writes the guard cannot see, inside the sandbox boundary and at no measurable time.
  Accept it, or bake a cache, which needs Debian's `fontconfig` package (`fc-cache`) in
  the image.
- Validator questions from the build: no rule refuses an attribute store on an imported
  module (`np.x = ...`; closed only where the builder exemption depends on it); the
  SECURITY profile bans a private attribute only on a receiver that resolves through an
  import (`chart.config._update(...)` passed until `_update` was banned by name in
  pygal's profile; the DATA profile bans every private attribute); and the URL rule
  does not match `javascript:` URLs, which pygal's value metadata (`xlink` hrefs) and
  altair's href channel can put into the exported HTML (the sandbox is not affected).
  The `THEME` pin leaves the theme block's default unpinned:
  `regions.is_theme_assignment` accepts any second argument to `os.getenv`. The
  renderer always sets `ANYPLOT_THEME`, so the default never reaches a render, but an
  exported file run without the variable names its files from it.
- Owner questions:
  - The 80 % matrix gate for pygal: 12 of its 60 generated cases (the `histogram-basic`
    and `line-timeseries` files) open blocked sessions, so pygal reaches at most 48 of
    60, exactly the gate, and only if every eligible case passes. Count only the
    eligible pairs in the gate, regenerate the two catalogue files through the pipeline
    (the annotation drawn by pygal instead of PIL, `np.random.default_rng` instead of
    `random`), or accept it. Decided by the owner on 2026-10-28: regenerate. Both
    regenerations merged the same day with the change request in the generator's prompt:
    `histogram-basic` (#12416) draws with pygal alone and is `coupled` now, while
    `line-timeseries` (#12415) kept `random` and stays blocked, so pygal can reach 54 of
    60 (90 %).
  - pygal's `xml.etree` post-processing (26 files) and `Graph` subclasses (23 files),
    45 blocked files as the groundwork counted the first cause. Admitting `xml.etree`
    with a ban list on its readers and writers would unlock 14; a class definition is
    refused in every profile today.
  - PIL for lets-plot: 4 files post-process the PNG with PIL (chord-basic,
    heatmap-chromagram, rose-basic, windrose-basic); altair's reopen rule could extend
    to them.
  - CJK and Arabic text in pygal: cairo's toy font API resolves one face per text run
    and never falls back per glyph, and cairosvg takes only the first family of
    `font-family`, so such text in user data draws as DejaVu's empty boxes; the
    harness's fallback families and G10 are matplotlib's. Accept it, or have the
    adapter put `Noto Sans CJK JP` or `Noto Sans` first when the data's script needs it.
  - The lets-plot native bridge before enabling: it imports `execvp`, `fork`, `popen`,
    `system` and `mkstemp` (ImageMagick's delegates and temp files), which the audit
    hook cannot see. The adversarial security review of 2026-10-26 (real renders under
    the harness with `strace -f`) found no escape and no validator bypass with an effect:
    titles, labels and font families with ImageMagick coder prefixes (`@`, `caption:`,
    `label:`, `msl:`) never reach a coder, and `geom_imshow` builds an in-memory
    `data:` href from an array and reads no file, so admitted code cannot steer the
    native layer. The bridge's native process starts are bounded by the image's `PATH`,
    `RLIMIT_NPROC` and the sandbox, and since 2026-10-26 every build of the renderer
    image, the Cloud Build deploy included, fails when any of 39 delegate programs is on
    the sandbox's `PATH` (`agents/renderer/delegates.py`). No ImageMagick policy ships:
    the bridge's ImageMagick is a zero-configuration build that reads no `policy.xml`
    and no `MAGICK_*` variable (a policy denying every coder and delegate changed no
    export, on the host or in the image). The two `fc-list` starts in the review's
    traces come from matplotlib's font manager, not the bridge, whose plain export
    started no process in a host trace; the image has no `fc-list`. Decided by the owner
    on 2026-10-26: add the seccomp filter. Since 2026-10-28 the harness arms every
    in-process run with a filter under which the kernel refuses every `execve` and
    `execveat` (`install_exec_deny`, every thread and child included), and the end line
    reports it, which the renderer logs per launch (`exec_deny`). Cloud Run's
    `sandbox do` admits it: the first renderer revision with the filter logged
    `exec_deny: on` (gcloud check of 2026-10-28). On the owner's decision every
    in-process run requires it (`ANYPLOT_DENY_EXEC=required` from `executor.sandbox_env`
    while `RENDERER_EXEC_DENY` is `required`, with `optional` as the switch back): a
    render without it stops before the plot (exit code 3), a data run ends as
    `exec_deny`, a conversion as `503 convert_unavailable`. Docker's default seccomp
    profile admits it, and `ci-image.yml` checks the routes in the built image.
    Exec-mode rows (R, JavaScript, Julia) start their toolchain with `execve` and need
    another design.
- The owner's matrix run per library on Vertex (question 7), now the gate for the public
  release of all four libraries of steps 1b and 1c: since 2026-10-28 `_LIBRARIES` in
  `agents/cloudbuild.yaml` names all six Python libraries, because only the admin
  reaches the chat yet (owner decision), so the admin tests each one live.

### 2. R: ggplot2 (the exec-mode pilot)

Revised on 2026-10-28 (draft for the owner and the second opinion): the toolchain image
of owner decision B, the base distribution, and the exec filter for exec-mode rows, which
#12414 made mandatory for every in-process run. The image and the filter are built so
that Julia (step 5) and JavaScript (step 3) add a stage and a command row, not a new
design.

#### 2a. The toolchain base image (owner decision B, 2026-10-25)

- `agents/renderer/toolchain.Dockerfile` builds `anyplot-toolchain` into the private
  Artifact Registry repository `anyplot` (`europe-west4`). Its base is the renderer's own
  `python:3.14-slim`, pinned by digest: Debian 13 (trixie), glibc 2.41, measured on
  2026-10-28 (see question 2 for the comparison with Ubuntu). One stage per toolchain,
  each into its own prefix, so a later toolchain adds a stage and a `COPY`:
  - R (this step): Posit's R 4.6.1 build for `debian-13` (`cdn.posit.co/r/debian-13`)
    under `/opt/R/4.6.1`, and the packages of `.github/actions/setup-r` plus `readr`
    from the Posit Package Manager snapshot `__linux__/trixie/2026-10-20` as binaries
    (checked on 2026-10-28: the same ggplot2 4.0.3 and ragg 1.5.2 builds exist for
    trixie, noble and resolute, as compiled binaries), into a site library that the
    renderer mounts read-only. The toolchain's package list is
    `agents/renderer/toolchain/r-packages.txt`; `setup-r` keeps its own
    `install.packages(c(...))` list, and `tests/unit/agents/renderer/test_toolchain.py`
    fails when the toolchain's list is not exactly setup-r's plus `readr`, so the
    pipeline and the renderer cannot drift unnoticed. The snapshot URL and its
    `# Snapshot <date> ships ggplot2 <version>.` note stay in `setup-r`, which
    `core/library_versions.py` parses; the toolchain reads the same date from its own
    file (`r-repos.txt`), and the same test fails when the two differ.
  - The runtime libraries the trixie binaries link (among them `libtiff6`,
    `libjpeg62-turbo`, `libharfbuzz0b`, `libfribidi0`, `libicu76`, `libgomp1`), which
    `python:3.14-slim` lacks; the build fails when `ldd` of R's binary or of any
    package's `.so` reports `not found`, and when R's or Julia's binary is static
    (`LD_PRELOAD` would be ignored).
  - The fontconfig cache: `fc-cache` runs in a builder stage and only its output is
    copied, so `fc-list` and `fc-match` never reach `SANDBOX_PATH`, where
    `agents/renderer/delegates.py` fails the build. `/bin/sh` stays: R's `popen` needs it
    to return a stream (2b).
  - Julia (step 5), Node with Playwright's Chromium (step 3): later stages, unchanged
    in shape.
  - The exec filter's preload library (2b), compiled in a builder stage with `gcc`, which
    the final image does not carry.
- Builds (owner decision of 2026-10-28, after the second opinion): the deploy builds the
  toolchain when it needs one, with no trigger of its own and no lock file to bump.
  `deploy-renderer` (its `includedFiles` already cover `agents/renderer/**`) hashes the
  toolchain's inputs (`agents/renderer/toolchain.py`), asks Artifact Registry for
  `anyplot-toolchain:<hash>`, builds and pushes it only when it is missing, and builds
  the renderer with `--build-arg TOOLCHAIN_IMAGE=<repository>` and
  `--build-arg TOOLCHAIN_TAG=<hash>@<digest>`. The renderer's Dockerfile starts
  `FROM ${TOOLCHAIN_IMAGE}:${TOOLCHAIN_TAG}` (two arguments rather than one reference, so
  the FROM line names a tag, which hadolint's DL3006 asks for; the digest rides in the
  tag, `name:tag@digest`), and both its builder and its runtime stage build on it, so the
  venv and the runtime see one Python. A deploy that changes the toolchain takes longer
  (R about 2 minutes, measured locally on 2026-10-29). With Julia (step 5, J1) the
  toolchain build gained a registry cache (`buildx --cache-from type=registry`, because
  Cloud Build keeps no layer cache and an R package bump must not rerun Julia's
  precompile), and the whole deploy runs on `E2_HIGHCPU_8` with a 3600 s timeout (owner
  decision of 2026-10-29, 5b).
- CI (`ci-image.yml`, job `renderer-image`): the job computes the same hash; when the tag
  exists it pulls it through the Workload Identity Federation login that `ci-tests.yml`
  uses (pool `github-actions`, the job gains `id-token: write`), which needs
  `roles/artifactregistry.reader` on the repository for the repository's principal set;
  when the tag is missing (a PR that changes a toolchain input) or no login is possible
  (Dependabot runs without secrets), it builds the toolchain itself into a local registry
  (`localhost:5000`, the builder on the host network) and the renderer FROM it.
- Verified on 2026-10-29 with the first toolchain (R 4.6.1 and its packages, 312 MB):
  the renderer image grows from about 1.17 GB to 1.35 GB, and a seaborn, a plotnine, an
  altair, a pygal and a lets-plot render through the harness are byte-identical to the
  main branch's image, non-ASCII titles included. R's package's dependencies were
  replaced by the runtime libraries `ldd` asks for: its Depends pull in compilers, `-dev`
  packages, Tcl/Tk and X11, and Pango's dependency on the `fontconfig` package would put
  `fc-list` and `fc-match` on the sandbox's `PATH` (the delegates check refused it), so
  grDevices' cairo devices go with Pango (every catalogue file saves through ragg).
  Dependabot bumps the base's digest (docker ecosystem, digest and patch releases only),
  which changes the hash, so the base's security updates reach the next deploy.
- Owner task, named with its exact command before it runs (CLAUDE.md, external writes):
  the reader binding for CI. The first toolchain build is the first deploy's.

#### 2b. The exec filter for exec-mode rows

The plot, data and conversion modes install the filter in the harness's own process
(`install_exec_deny`); exec mode cannot, because the filter would also refuse the start
of the language's own program. Instead:

- `agents/renderer/execdeny/execdeny.c` (about 80 lines) is a preload library whose
  constructor installs a BPF program in the new program before its `main` runs, that is
  before any user code: the same architecture checks as `exec_deny_program` (x86-64 and
  aarch64, the x32 bit), `PR_SET_NO_NEW_PRIVS` first, `seccomp(2)` with
  `SECCOMP_FILTER_FLAG_TSYNC` (a linked library's constructor, which runs before a
  preload's, may have started threads already, as OpenBLAS does). Unlike the in-process
  program, `execve` and `execveat` answer `SECCOMP_RET_KILL_PROCESS`, not `EPERM`: R's
  `utils` package computes the OS version through `Sys.which("uname")` when it loads,
  whose `popen` reports a child's `EPERM` as an error, so neither `utils` nor `stats`
  (and with them ggplot2) loads under `EPERM` (second opinion of 2026-10-28, measured
  on R 4.3.3 with a prototype and reproduced). Under `KILL_PROCESS` the `posix_spawn`
  child dies with `SIGSYS` before it runs anything, R sees a dead child (`system("true")`
  returns 159, `Sys.which` answers `""`, `pipe()` reads nothing), and every package
  loads. The constructor proves the filter as `install_exec_deny` does: a forked child's
  `execve` of a missing path answers `ENOENT` before the install and dies with `SIGSYS`
  after it.
- It reads `ANYPLOT_DENY_EXEC`: unset, it does nothing; `required` and the install
  fails, it ends the process with exit code 3 before `main` (the plot mode's code). It
  writes its state (`on`, `unavailable`, `unsupported`) to the file descriptor named in
  `ANYPLOT_EXEC_DENY_FD`, then closes it and drops the variable, so user code cannot
  forge it. The harness reads the pipe after the child ended and refuses the result
  whenever the pipe did not say `on`, whatever the child's exit code: a missing or
  unloadable preload object is only a warning to `ld.so`, and a static binary ignores
  it silently, so the child would run unfiltered (fail closed; it also tells the
  constructor's exit 3 from a script's own `quit(status = 3)`).
- The harness builds the child's environment itself (`main_exec`): `LD_PRELOAD`,
  `ANYPLOT_DENY_EXEC` and `ANYPLOT_EXEC_DENY_FD` (`pass_fds`, the parent closes its
  write end) go to the child only. In the sandbox's own environment they would preload
  the library into the harness's Python too and refuse its `subprocess.run`. The local
  Docker backend gets the same row environment.
- The command row runs the language's binary directly, so that no wrapper needs a second
  exec: for R the `exec/R` binary with `--no-echo --no-restore --no-save --file=plot.R`
  and the variables R's own `bin/R` script sets (`R_HOME` is mandatory,
  `LD_LIBRARY_PATH=$R_HOME/lib` from `etc/ldpaths`, because Posit's layout has no
  `libR.so` on the system path, `R_SHARE_DIR`, `R_INCLUDE_DIR`, `R_DOC_DIR`), plus
  `LANG=C.UTF-8`, which the sandbox does not set and R, unlike Python, does not coerce
  (the catalogue's runner renders under `C.UTF-8`; non-ASCII labels go through ragg).
  Not `Rscript`, which execs `bin/R`, a shell script that runs `uname` and `sed` and
  then execs the binary: under the filter, `Rscript` ends with "execution error:
  Operation not permitted".
- `ci-image.yml` asserts it in the built image, next to the existing kernel
  exec-refusal check: an R plot that calls `system("true")` (non-zero) and still writes
  its PNG, with a non-ASCII label.
- `RuntimeCommand` gains `exec_deny: bool` (default true), the one source of truth for
  `executor.sandbox_env` and the local backend instead of a check by language name.
  JavaScript (step 3) is the row that sets it false: Node starts Chromium and Chromium
  starts its renderer and GPU processes, so the row cannot refuse `execve`; user code
  runs inside the page, which has no process API.
- Unverified until the first deploy: gVisor's support of `SECCOMP_RET_KILL_PROCESS`
  (the in-process `EPERM` program is proven on Cloud Run). The pipe state of the first
  R render shows it; if gVisor refuses it, the fallback keeps the kernel filter at
  `EPERM` and adds `popen` and `system` interposers in the preload library for the
  cooperative callers.
- Found by the first deploy (2026-10-29, build `6bf765c6`): the toolchain's R check died
  with "Bad system call" in Cloud Build, though it passed locally and in GitHub Actions.
  R's `popen` and `system()` start their child with `vfork` (`CLONE_VM`), the filter
  kills that child with `SIGSYS`, whose default action dumps core, and before Linux 5.16
  a core dump kills every process sharing the dumping one's memory, R included (Cloud
  Build's workers run 5.10.0-32-cloud-amd64; the developer machine's 6.18 and the
  Actions runners kill the child alone). The library now makes the process non-dumpable
  (`PR_SET_DUMPABLE` 0) before it installs the filter, so the child dumps no core and
  dies alone on every kernel; the test pins it (`PR_GET_DUMPABLE` is 0 under the filter),
  and an owner-approved diagnostic Cloud Build of the toolchain with the fix (build
  `f079a4e4`, no push) passed the R check on that 5.10 kernel.

#### 2c. The R runtime

- Toolchain: R 4.6.1 as in `.github/actions/setup-r` (Posit snapshot 2026-10-20, the same
  package list plus `readr`), the `exec/R` binary through the exec mode (2b);
  `R_LIBS_SITE` read-only from the image; `HOME=/tmp` for R's temp files; a baked
  `fc-cache` and `XDG_CACHE_HOME=/tmp` for ragg on the read-only root. The spike's limits
  hold: `RLIMIT_AS` 1 GiB and `RLIMIT_NPROC` 64 (renders peaked at 294 MiB).
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
- Fixtures (after the owner regenerates the ten specs' R files under the Data block: on
  2026-10-28 4 of the 10 ggplot2 files carry it, `line-basic`, `bar-grouped`,
  `box-basic`, `area-basic`, `pie-basic` and `line-timeseries` do not), the matrix, docs.
  The regeneration is no prerequisite any more (owner decision of 2026-10-29, see the
  plan's introduction): a file without the marker is `coupled`.

#### What PR 3a built (2026-10-29): the R code profile, not served yet

PR 3 is split: 3a builds the deterministic modules, 3b the `RRuntime`, the registry entry,
the pipeline and policy changes, the fixtures and the admin deploy. Nothing in 3a is
served.

- **Parser.** `tree-sitter` 0.26.0 and `tree-sitter-language-pack` 0.13.0, pinned
  exactly in the `agents` extra (owner decision of 2026-10-29: 0.13.0 bundles r-lib's R
  grammar, MIT, and downloads nothing; 1.x downloads grammars at run time).
  `agents/anyplot/code/treesitter.py` parses, lists ERROR and MISSING nodes, walks without
  recursion and holds the R helpers (strings with escapes and raw strings, backtick names,
  callees, arguments, assignments, bindings). All 325 catalogue files parse with no error
  node. The pack's `Point.row` and `.column` free an int past 256 under Python 3.14 (a
  segfault at the next collection), so the code indexes the point and a test refuses the
  attribute form. `agents/Dockerfile` keeps only the grammars the profiles load
  (`TREE_SITTER_GRAMMARS`, R alone; 184 MB down to 0.6 MB), and a test ties that list to
  `GRAMMARS`. The renderer image does not install the `agents` extra.
- **Regions and normaliser** (`code/profiles/r/`). The protected regions are the exact
  theme statement (its default pinned to `"light"`), 1,322 theme tokens, the palette, the
  final `ggsave` with `sprintf("plot-%s.png", THEME)` and `ragg::agg_png`, the placeholder
  `df <- load_user_data()`, the loosely matched markers (both in 247 files) and column
  constants with a role comment (4 files). The normaliser strips the roxygen header, inlines
  logistic-regression's `output_file`, blanks the catalogue title with the Python rule
  (`normalise.is_catalogue_title`; 5 `paste0` splits and 1 `sprintf` format get a note; 67
  files size the title font from `nchar(title)`, a known issue) and rewrites only the save's
  dpi: ragg truncates (measured in the toolchain image: 13.333 in at 240 dpi gives 3199 px),
  so the dpi is the shortest decimal with `t <= inches * dpi < t + 1`. 34 saves are
  rewritten; all 325 files land on 3200x1800 (251) or 2400x2400 (74), and the corpus test
  recomputes `floor(inches * dpi)` from every rewritten save.
- **Validator.** SECURITY over tree-sitter with the Python profile's rule ids and the named
  bypasses of the design pass as tests. Owner decisions of 2026-10-29 on the first pass's
  findings: a denied name is refused as a callee and as a function-valued argument
  everywhere, and as any other value outside a data mask; inside the arguments of the
  data-masking and tidy-select calls (`DATA_MASK_CALLS`) and in the operands of `~` it is
  a column; a string equal to a denied name is refused only where a string becomes a
  function (a callee, a function-valued argument, a parsed code string), so a user's
  column called `source`, `file` or `load` passes. After the Fable and Gemini review of
  2026-10-29, `with` and `within` are no mask, every protected statement is bound once and
  alone on its lines (by node, so `THEME <- ...; THEME <- "dark"` is refused), and the
  call shapes that would run a function held in a mask are refused: a function literal
  called at once, an index or field as callee, a call to a parameter, `do.call` as a value
  and a call's result unless it is a builder such as `colorRampPalette(...)(n)` (catalogue:
  0, 1 in plotmath, 0 and 12 builders). The residual left, a function that calls a value
  it receives through an argument the list does not name (a condition handler), is
  documented in `validate.py`; the sandbox and the exec filter are the boundary. A formula position takes only a `~`
  literal, a string literal or a name bound once to one, so a formula built with `paste0`
  or `sprintf` is refused. gapminder and palmerpenguins pass SECURITY and are the
  ADAPTATION finding `dataset-package`. `<<-` stays refused.
- **Readiness.** `coupling.py` (stdlib, tree-sitter, `core.*` and the R regions only, so
  the regen gate's adapt route can use it from `core/` later) and `readiness.py`: blocked
  only for real reasons, a missing marker is `coupled`. Over the 325 normalised files: 4
  clean (area-basic, box-basic, line-basic, line-timeseries), 306 coupled, 15 blocked (the
  13 map specs, qrcode-basic, maze-circular's `<<-`).
- **Loader, kinds, errors, edits, export.** `readr::read_csv` typed from the column kinds
  of `data/kinds.py` (`col_integer`, `col_double` past 32 bits, `col_logical`,
  `col_character`, `col_date`, `col_datetime` in UTC; `na = ""`), measured in the
  toolchain image: `True`/`False`, microseconds and offsets read correctly, text `NA` and
  `001` stay text. `col_double()` is exact only to 2^53, so `read_kinds` counts the
  integer cells beyond it per column for 3b to announce (data-fidelity rule). The error
  grammar reads R's stderr only (the erroring function, rlang's cause and layer, the last
  `Calls:` names, memory, recursion, a missing package), never the message. The edit
  applier is one core with a `Dialect` per language, and the export takes the run command
  (`Rscript plot.R`); Python's output is byte-identical.

Open for 3b: `dataset-package` is an ADAPTATION finding, which the pipeline treats as a
defect line, not a refusal (`pipeline.BLOCKING_RULES`); for the adapter's working form to
be refused while it keeps a dataset package, 3b adds the rule to the R runtime's blocking
set. Settled by 3b (next section).

#### What PR 3b built (2026-10-29): ggplot2 served

- **Runtime.** `agents/anyplot/render/runtimes/r.py`, `RRuntime`, implements the whole
  `RuntimeAdapter` contract with the 3a modules: `plot.R`, the renderer's R row as the
  command (the harness in exec mode in front of `exec/R --no-echo --no-restore --no-save
  --file=plot.R`), the row's environment key for key as `sandbox_env` builds it (`R_ENV`,
  the deployed limits, `ANYPLOT_DENY_EXEC=required`; the local backend leaves
  `RLIMIT_NPROC` to the container's `--pids-limit`, as for Python), the R normaliser,
  loader, validator, readiness scan and error grammar, the edit applier's R dialect, the
  PNG and no probe, and the export with `Rscript plot.R`. Data runs and conversions stay
  Python's, because `run_data_code` runs Python whatever the plot's language. The repair
  reserve is 15 s, set in the R row of `commands.py`.
- **Registry and contract.** `RUNTIME_LIBRARIES` is `PYTHON_LIBRARIES | R_LIBRARIES` and
  `runtime_for` picks the class by the library's language (`RUNTIME_CLASSES`);
  `render/__init__.py` lost its Python-only assert. `RuntimeAdapter` gained
  `blocking_rules` (the shared `contract.BLOCKING_RULES`; R adds `dataset-package`),
  `adaptation_targets` (Python's moved from the pipeline unchanged; R's are written in R),
  `kinds` on `loader_block` and `loader_notes`; `regions` returns a `CodeRegions` protocol
  (the Imprint palette), which both languages' `Regions` satisfy.
- **Pipeline.** The column kinds are read once per run (`column_kinds_of`) and handed to
  every runtime's loader. `loader_notes` comes first in the shipped version's "what
  changed" list: R reads integer cells beyond ±2^53 as the nearest double, and the line
  counts them per column (the columns that fit a 200-character change note, the rest
  counted), and `root.md` has the root name it in every reply to that result. Owner
  decision of 2026-10-29: "what changed", not a residual note, so the status stays the
  render's (`ok` stays `ok`). A working form that keeps gapminder or palmerpenguins is refused as
  `validator dataset-package`, while the readiness scan still calls such a catalogue file
  `coupled`.
- **Prompts.** `adapter.md` keeps every rule the languages share and names a slot
  (`{{data_statement}}`, `{{protected_lines}}`, `{{safe_code}}` and 13 more) wherever the
  code differs; `adapter_python.md` and `adapter_r.md` fill them (`policy.adapter_prompt`,
  which refuses a missing, unused or doubled slot). The Python prompt is byte for byte the
  one before the split (a test pins its SHA-256, and another that no runtime prompt repeats
  a shared paragraph). The R passages tell the adapter the placeholder and how readr types
  each column, the column constants read through `.data[[...]]`, the protected statements,
  the packages it may attach, that dataset packages and `readr` stay out, and what the
  validator refuses; a test runs those idioms through both R validator profiles.
  `root.md` names `plot.R` next to `plot.py`, and `gates.py` lost `fig.savefig` from a
  feedback line. The agents image's build check composes one adapter instruction per
  language.
- **Python-only paths.** `dev_fixture.snapshot_from_repo` and the eligibility sweep find a
  file under its language with its extension; the sweep scans through the runtime. The
  admin deploy's `_LIBRARIES` names ggplot2.
- **Evals.** `make_fixtures.py` writes the ten specs for ggplot2 (60 cases, 420 in all,
  427 in a full run) with the smoke case `scatter-basic-ggplot2-renamed` (17 smoke cases).
  Four of the ten ggplot2 files are `clean` and six `coupled`.
- **App.** The result card highlights each version in its library's language; before, a
  thread with versions of two libraries (after a library switch) highlighted all of them in
  the page's current language. The download name, `.download('plot.R')` and `.plot_all()`
  needed no change.
- **CI.** The agents-image job loads every kept grammar in the built image and runs the R
  runtime's readiness scan on the catalogue's `scatter-basic` ggplot2 file, piped in from
  the checkout.
- **Verified locally, without a model.** A scripted identity adaptation of
  `line-basic-ggplot2-renamed` (the column constants set to `t [min]` and `T_tank [°C]`,
  the data block replaced by the placeholder, a German title) passed the pipeline's check,
  took the readr loader and rendered through `LocalDockerBackend` on the renderer image of
  #12428: 3200x1800 in both themes, 1.5 s of wall time per theme, R1 to R3 passed. The same
  container with its stdout kept reported `exec_deny: on`, 0.85 s of CPU and 177 MiB.

| Text above | Built | Why |
|---|---|---|
| A runtime section per language in `policy.py` and `adapter.md` (the table at the top) | Slots in `adapter.md`, filled per language | Appending an R section would leave the Python rules in the R prompt for the adapter to override; slots keep one copy of each shared rule and a Python prompt that does not change |
| The session announces R's inexact integers | The first entry of the shipped version's "what changed" list, from `RuntimeAdapter.loader_notes`, which the root names in its reply; the status stays the render's | The parser's warnings, where other data changes are announced, belong to the dataset, which a session keeps across a library switch, while the pipeline's lists are per render and reach the page and the root. The first build put the line among the residual notes, which made every such plot `needs_attention`; the owner decided on 2026-10-29 for "what changed", with the status left as the render earns it |
| The R row keeps the Python defaults (2b) | `render_p95_s` 15 s, written into the row | One Cloud Run measurement (5.7 s) is close to the Python p95 of spike X (5.5 s); the matrix run measures R's p95 |

#### Eligibility after 3b

`uv run --extra agents python -m agents.evals.eligibility` on 2026-10-29: the sweep covers
all seven libraries; the six Python rows are those of 1c, pygal with `histogram-basic`
regenerated.

| Library | Files | Eligible | Clean | Coupled | Blocked |
|---|---|---|---|---|---|
| matplotlib | 325 | 285 (87.7 %) | 15 | 270 | 40 |
| seaborn | 325 | 287 (88.3 %) | 18 | 269 | 38 |
| plotnine | 321 | 267 (83.2 %) | 59 | 208 | 54 |
| altair | 325 | 273 (84.0 %) | 58 | 215 | 52 |
| pygal | 325 | 210 (64.6 %) | 64 | 146 | 115 |
| lets-plot | 325 | 284 (87.4 %) | 53 | 231 | 41 |
| ggplot2 | 325 | 310 (95.4 %) | 4 | 306 | 15 |

ggplot2's 15 blocked files are the 13 map specs (four of them with SECURITY findings too),
qrcode-basic and maze-circular; by SECURITY rule `banned-import` 3, `url-literal` 2,
`banned-name` 2, `banned-statement` 1. `test_eligibility.py` pins the ggplot2 counts.

#### Next

- The owner's matrix run for ggplot2 on Vertex (60 cases), the gate for the public release,
  and with it R's render p95 for the reserve.
- Settled in the same PR: the scope judge's rubric named matplotlib and seaborn as the
  only libraries the assistant adapts, so since 2026-10-25 plotnine, altair, pygal and
  lets-plot, and now ggplot2 and questions about R code, could be refused as
  `other_library`. `scope_judge.md` now has one injected passage
  (`policy.libraries_passage`): the served libraries from `AGENT_LIBRARIES` and the
  catalogue's others, grouped by language; a request for this plot in a served library is
  `in_scope`. The sentences only matplotlib's probe makes true (the VQ-03 and VQ-06 gate
  lines, the drawn-text check of requested texts, the polar hint) moved into the Python
  slots, and R's slots say that the host gates judge an R render without a probe;
  `adapter_highlights.md` has a slot for its code example too (`highlights_prompt`).
  Both Python prompts stay byte-identical.
- Also settled in the same PR (owner's request of 2026-10-29): the fixed `other_library`
  reply (`refusals.yaml`, eleven hand-written languages) said the assistant adapts "only
  in Python, with matplotlib or seaborn". Each translation now carries a `{{libraries}}`
  slot in place of that clause, filled with the served libraries by name from the scope
  judge's source (`policy.refusals_for`, `adapted_names`); the rest of each text is
  unchanged.
- The 67 catalogue files that size the title font from `nchar(title)` (3a, known issue).

#### 2d. Order of the PRs

1. The toolchain image with the R stage and the preload library, the deploy's
   build-if-missing step, the renderer `FROM ${TOOLCHAIN_IMAGE}:${TOOLCHAIN_TAG}` and the
   CI path (pull the tag, or build it); the R row is not served yet. Before the merge,
   the owner-approved reader binding; the merge's deploy builds and pushes the first
   toolchain. Merged as #12423 on 2026-10-29; its first deploy failed in the toolchain's
   R check on Cloud Build's 5.10 kernel (2b, "Found by the first deploy"), fixed by #12427.
2. The R command row, the exec mode's child environment, preload and pipe, the
   `exec_deny` field, the CI checks in the built image (an R render, the refused
   `system()`); the first deployed R smoke proves `KILL_PROCESS` under gVisor; the
   deploy keeps `AGENT_LIBRARIES` as it is. Built on 2026-10-29: `RuntimeCommand` gains
   `exec_deny` (off for JavaScript alone) and `code_flag` (`--file=` for R); the R row runs
   `R_BINARY` with `R_ENV` (`R_HOME`, the share, include and doc directories,
   `LD_LIBRARY_PATH`, `LANG=C.UTF-8`, the caches); `executor.sandbox_env` sets
   `ANYPLOT_DENY_EXEC=required` for every row with `exec_deny`, and `harness.main_exec`
   hands `LD_PRELOAD` and the pipe to the child alone. Before any user code it runs a
   preflight: the language's program alone, with `ANYPLOT_EXEC_DENY_PREFLIGHT`, which the
   library's constructor ends before `main` after it reported, so a library `ld.so` cannot
   load or a static binary stops the run before the code is read (the Copilot review of
   #12428: checking only after the run let the code run unfiltered first). After the run it
   reads the pipe without blocking and returns `EXEC_DENY_EXIT` unless it said `on` (a
   command that never started keeps 127). In the built image the CI step renders a ggplot2 plot with a
   non-ASCII title at 3200x1800 in 0.85 s of CPU and 180 MiB with `exec_deny: on`.
3. The R runtime and code profile (2c), fixtures, docs; ggplot2 joins the admin deploy's
   `_LIBRARIES` for the live test; the matrix gates the public release. Built on
   2026-10-29 as two PRs: 3a the code profile (#12443), 3b the runtime, the prompts, the
   fixtures and the deploy ("What PR 3b built" under 2c).

### 3. JavaScript: Chart.js, D3, ECharts, Highcharts and MUI X

Revised on 2026-10-30 after the second opinion on steps 3 and 4 (Gemini 4 Argon and Fable;
the section at the end): the corrections both reviewers agree on, and those Fable
verified, are in the text below; the two owner decisions it left open were taken on
2026-10-30 (questions 12 and 13: the export carries the PNG, the self-contained page and
the code file; MUI X files written for 7.29 are served coupled with a note). Four PRs, none
of which serves a library before JS-4: JS-1 (the toolchain stage, the command row, the
build inputs, the smokes and the render sweep; built, see "What JS-1 built"), JS-2 (the
harness's sandbox mode; built, see "What JS-2 built"), JS-3 (the code profile; built, see
"What JS-3 built") and JS-4 (the runtime, the registry, the fixtures and the admin
deploy). `AGENT_LIBRARIES`, `RUNTIME_LIBRARIES` and the admin deploy's `_LIBRARIES` stay
as they are until JS-4; the renderer can render a JavaScript job, and the agents service
sends none.

#### 3a. The toolchain stage (JS-1)

- A `node` stage in `agents/renderer/toolchain.Dockerfile`, `FROM base` like R's and
  Julia's, so a Node change rebuilds neither of them and the registry cache keeps their
  stages. It downloads the official Node 22 build for Linux on x86-64 (22 is the major
  the catalogue pipeline renders with, `.github/actions/setup-node`, which a test pins;
  `package.json` says `>=22`) and checks it against the SHA-256 that nodejs.org
  publishes next to its downloads, under `/opt/node`. npm, npx, corepack, the headers
  and the docs leave the install once the packages are in.
- The packages are the repository's `package.json` and `package-lock.json`, installed
  with `npm ci --ignore-scripts` into `/opt/anyplot/node_modules`: the whole lock,
  because the harness's own esbuild and Playwright are its `devDependencies`, so
  `--omit=dev` would drop them; no install script runs (esbuild's, the lock's only one,
  checks its binary, which esbuild's API finds without it). Type declarations and
  source maps go (98 MB of 262 MB).
- Playwright's CLI from that install puts the Chromium headless shell alone under
  `/opt/pw-browsers` (`--only-shell`; a headless launch runs the shell, 273 MB against
  403 MB with the full Chromium), at the revision the lock's `playwright-core` pins.
  The final stage installs the libraries the shell links, found with `ldd`
  (`NODE_RUNTIME_LIBS`), none of which brings the `fontconfig` package or Pango, and a
  build check fails on any library Node, the shell or the shell's own libraries cannot
  resolve. libgbm is unpacked from its package without its dependencies: the package
  depends on Mesa's drivers and LLVM (about 200 MB), which only its backend module
  links, and a headless page never opens a GBM device.
- The harness, `automation/js-render/` (the pipeline's own; `render.mjs` is its only
  file), is copied to `/opt/anyplot/js-render/`. It finds the packages through
  `ANYPLOT_NODE_MODULES`, the one harness change of JS-1: in a checkout they sit two
  levels above it, in the image they do not, and without the variable the pipeline's
  behaviour is unchanged.
- The import allowlist of MUI X snippets (second opinion, finding 1):
  `agents/renderer/toolchain/import_allowlist.py` derives it at build from the
  `exports` maps of the installed `react`, `react-dom`, `@mui/material` and
  `@mui/x-charts` into `/opt/anyplot/js-render/import-allowlist.json`, the one file the
  bundle step's resolve plugin (JS-2) and the validator (JS-3) read:
  `{"schema": 1, "packages": {name: version}, "specifiers": [...]}`, sorted, the package
  name for the key `.`, the name and path for `./<path>`, without `./package.json` and
  null targets. A package that exports a pattern (`./*`) or has no `exports` map fails
  the build, because a list cannot close it. A test pins the shape.
- Fonts: the catalogue's page font stack asks for Helvetica and Arial, which the
  pipeline's runner resolves to Liberation Sans through fontconfig's metric aliases
  (`playwright install --with-deps` installs `fonts-liberation`); the image has DejaVu
  and Noto only. Installed system-wide, Liberation changes Python renders that name
  Arial (measured, "What JS-1 built"), so the stage copies Liberation Sans, Serif and
  Mono with their copyright notice to `/opt/anyplot/js-fonts`, which only the
  JavaScript row's fontconfig file names (`agents/renderer/toolchain/js-fonts.conf`: the
  system configuration and that directory).
- The final stage copies Node's lines after Julia's, so a Node change reruns only its
  own lines there, and renders a Chart.js chart and a MUI X component through the
  harness with the row's binary and environment (`smoke.js`, `smoke.tsx`), each a
  3200x1800 PNG.

#### 3b. Build inputs, CI and the deploy (JS-1)

- `package.json`, `package-lock.json` and `automation/js-render/` join the toolchain's
  hash (`toolchain.py`, `INPUTS`), the root `.dockerignore` (root-anchored, so
  `app/package.json` stays out) and the `renderer-image` job's change filter
  (`RENDERER_CHANGES`); tests fail when an input misses the hash, the build context or
  the filter. A lock bump by Dependabot therefore rebuilds the toolchain, as a
  Manifest bump does.
- The `deploy-renderer` trigger's included files live in GCP and were not read; they
  likely lack the three as they lacked `Project.toml` and `Manifest.toml`, so the owner
  task of step 5b covers them too. Until then a lock-only change reaches the renderer
  with its next deploy.
- CI (`renderer-image`): the built image renders the catalogue's `scatter-basic` Chart.js
  file and `bar-basic` MUI X file (written for MUI X 9.16) through the harness in exec
  mode with the row's argv and environment at 3200x1800, and checks that Node is in the
  image and not on `SANDBOX_PATH`.
- The deploy's candidate smoke renders a Chart.js chart after the Makie one and prints
  its wall time, CPU time and peak memory, so the first deploy with Node measures a
  cold Chromium under gVisor, which no local run can. No agent sends a JavaScript job
  before JS-4, so a failed render there is a warning in the build log, not a refused
  promotion; JS-4 makes it a gate like the Makie render.

#### 3c. The command row (JS-1)

- `NODE_BINARY` (`/opt/node/bin/node`) by its path, as `R_BINARY` and `JULIA_BINARY`:
  `SANDBOX_PATH` does not carry it, and `agents/renderer/delegates.py` keeps refusing a
  `node` there. Argv: `NODE_BINARY /opt/anyplot/js-render/render.mjs --library=<library>`
  and the code file (`plot.js`, `plot.tsx` for MUI X); the library comes from the
  request's closed set, never from the file name.
- Environment (`JS_ENV`): `PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers`,
  `ANYPLOT_NODE_MODULES=/opt/anyplot/node_modules`,
  `FONTCONFIG_FILE=/opt/anyplot/js-fonts.conf`, `TZ=UTC`, `LANG=C.UTF-8`,
  `XDG_CACHE_HOME=/tmp` and `XDG_CONFIG_HOME=/tmp`; `HOME=/tmp` and `PATH` are the
  sandbox's fixed keys. No `NODE_OPTIONS`: Node runs only the harness, and the snippet
  runs in Chromium's V8.
- `exec_deny` off: Node starts esbuild's service and Chromium, and Chromium starts its
  own processes. The plot code runs in the page, which has no process API; the
  boundary is gVisor (no network, a read-only root, the run's own `/tmp`) and, with
  JS-2, the harness's page rules.
- `RLIMIT_AS` and `RLIMIT_NPROC` off: V8 and Chromium reserve virtual memory far beyond
  use, and one render runs 7 processes with 77 tasks (processes plus threads), over the
  64 of `RLIMIT_NPROC`, which counts threads on Linux. `RLIMIT_CPU` is per process after
  exec, so the host's wall clock is the real bound; the `MemAvailable` watchdog stays the
  memory control (the whole container peaked at 1,178 MiB in the sweep).
- `render_p95_s` 15 s, from JS-1's sweep ("What JS-1 built").

#### 3d. The harness's sandbox mode (JS-2)

Every change sits behind an environment variable, so the catalogue pipeline sees no
difference.

- Data: Python writes the table as typed JSON from the canonical CSV and its
  `ColumnKinds`, so the canonical CSV keeps one reader (adopted from Fable; Gemini
  proposed a JavaScript parser baked into the source); `render.mjs` injects it as
  `window.ANYPLOT_DATA` with `<` escaped, so a cell cannot close the script; a missing
  cell is `null`. The job carries the JSON next to `data_csv`, so a second theme
  renders from the stored job as for the other languages (Gemini's point about
  `theme_render.py`); the field and its writer are JS-4's.
- Time: `newPage({timezoneId: "UTC"})`, since `new Date("2026-03-01T00:00")` is local
  midnight otherwise (the row's `TZ=UTC` since JS-1).
- Boundary: `page.route("**/*")` aborts every request before `setContent`, `sendBeacon`
  included; `page.routeWebSocket("**", ws => ws.close())`, because the route does not
  see WebSockets; Chromium's `--block-new-web-contents`, so `window.open` returns null
  instead of a popup outside the route. Blob workers and `import("data:...")` still run
  inside the page, which has no network. Gemini's content security policy and
  Chromium flags (`--disable-dev-shm-usage`, `--disable-gpu`, a V8 heap cap) are
  measured against the sweep before any is adopted; the deploy smoke of JS-1 measures
  Chromium under gVisor first.
- Console: page errors and console errors are capped in count and bytes (the
  unbounded list reached 4.2 MB for 20,000 lines), and the bounded tail is printed on
  failure too, not only on success.
- Imports: an esbuild `onResolve` plugin admits only the allowlist's bare specifiers,
  resolved under `ANYPLOT_NODE_MODULES`, and refuses every relative and absolute path,
  because esbuild otherwise bundles any file of the image (`import x from
  "/etc/os-release"`, Fable, verified).
- `ANYPLOT_NO_HTML=1`: no interactive page in the sandbox.

#### 3e. The code profile (JS-3, not served)

- tree-sitter's JavaScript, TypeScript and TSX grammars from the pinned
  `tree-sitter-language-pack`, as for R and Julia.
- Placeholder `const data = loadUserData();`, loader `const data = window.ANYPLOT_DATA;`;
  protected regions: the token lines that read `window.ANYPLOT_TOKENS`,
  `window.ANYPLOT_THEME` and `window.ANYPLOT_SIZE`, and the `//# anyplot-orientation`
  directive, which the edits' drift check must keep although it is a comment; the edit
  applier's JavaScript dialect reads `//` and `/* */` as comments and a `#` inside a
  string (CSS colours, SVG) as text (Gemini).
- The deny list over tree-sitter (hygiene, not the boundary, see "Second opinion"):
  `fetch`, `XMLHttpRequest`, `WebSocket`, `EventSource`, `Worker`, `navigator.*`,
  `window.open`, `new Image().src`, `import()`/`require`, `eval`, `Function`,
  `.constructor`/`__proto__`, computed access on `window`, `globalThis`, `self`,
  `document` and `navigator`, `document.cookie`, `localStorage`, `postMessage`,
  `<script>`/`<iframe>` creation, `setTimeout` with a string. MUI X's static imports
  are checked against the image's import allowlist; the agents image has no
  `node_modules`, so JS-3 carries a copy of the JSON that CI compares with the
  renderer image's.
- The readiness scan on the `// Data` and `// Plot` markers and a snippet that reads
  the tokens.
- The error grammar: the page error's class and line, numbered within the snippet's own
  `<script>`, whose offset is exactly 1 (the `try {` line; measured by Fable, where
  Gemini expected the bundle's lines in front); MUI X's bundle is minified, so its
  errors name the class only, and esbuild's compile errors name `plot.tsx:<line>`.
- Export: the header in `//` comments for JavaScript and TSX, because `#` is a syntax
  error there (Gemini); the run line follows question 12.

#### 3f. The runtime, the registry and the fixtures (JS-4)

- `JavaScriptRuntime`, `adapter_javascript.md` filling `adapter.md`'s slots
  (`adapter.md` itself does not change, Gemini), `review_texts` on, as for R and the
  Python libraries without the text probe (a JavaScript render writes no probe, so the
  reviewer checks the requested texts in the image), and the deploy smoke's Chart.js
  render as a gate.
- Data notes as R's: integers past 2^53 counted in the version's "what changed" list
  (JavaScript numbers are doubles), booleans as `true`/`false`, dates as `YYYY-MM-DD`
  strings, datetimes as UTC ISO strings with the truncated sub-milliseconds counted,
  and the adapter prompt warns that `+null === 0` (Gemini).
- Fixtures on the ten specs for Chart.js, D3 and ECharts first; MUI X after its
  regeneration or per question 13; Highcharts behind the `AGENT_LIBRARIES` switch until
  question 6 is decided. The owner's matrix run gates each library; docs.
- JS-4 is two PRs (2026-10-30): JS-4a, the runtime, the registry, the prompt, the
  fixtures and the admin deploy of Chart.js, D3, ECharts and Highcharts (question 6
  decided the same day), with the PNG and the code file; JS-4b, the export's `plot.html`
  with its sandboxed preview and its download (question 12, "Found for JS-4" under JS-3).
  MUI X follows them with its fixtures.

#### 3g. The export page (JS-4b)

Reviewed by Gemini 4 Argon and Fable on 2026-10-31 (the section "Second opinion on JS-4b's
design" at the end). JS-4b is two PRs: JS-4b-1, the downloadable page, and JS-4b-2, its
preview in the chat, whose delivery is an open owner decision.

- **Page only, no browser.** In sandbox mode the harness's switch `ANYPLOT_PAGE_ONLY=1`
  builds the page exactly as a render would (`buildHtml` with the sandbox policy and the
  typed table of `ANYPLOT_DATA_JSON`; MUI X still bundles through the closed import plugin),
  writes `plot-<theme>.html` whatever `ANYPLOT_NO_HTML` says, and exits 0 without starting
  Chromium, so the plot code never runs on the renderer. A broken data file still fails as
  `data DataError` with the final error line. Without the switch nothing changes.
- **The renderer's `POST /page`.** The caller check, the sandbox and the JavaScript row of
  `/render`, with `ANYPLOT_PAGE_ONLY=1` added to the row's environment. The request
  (`wire.PageRequest`, `extra="forbid"`) is `{job_id, language: "javascript", library,
  source, data_json, theme, timeout_s}`; another language is `422 invalid_job`. The answer
  is the page as `text/html; charset=utf-8` under a byte cap, with `/render`'s failure
  mapping (busy, low memory, ...) and a JSON body for a build that left no page. A build
  may hold the render slot (accepted for now).
- **The agents' backends.** `RenderBackend.page(...)` returns the page's text. The remote
  backend posts to `/page`, and a `404` raises a typed `PageUnsupported`, as `/run-data`
  does with `DataRunUnsupported`: the agents service deploys before the renderer, and an old
  renderer's request models forbid unknown fields. The local Docker backend runs the same
  harness run and mounts the checkout's `automation/js-render/render.mjs` over the image's,
  as it mounts the checkout's `harness.py`. The fake backend returns a deterministic stub;
  `SerialRenderer` passes the build through in the `toggle` lane.
- **The download is a wrapper** that the agents service builds in pure, deterministic Python:
  an outer document with no script of its own, a meta policy that is exactly the harness's
  `CONTENT_SECURITY_POLICY` plus `frame-src 'none'`, and `<iframe sandbox="allow-scripts"
  srcdoc="...">` with the page escaped for the attribute. A `srcdoc` child inherits the
  wrapper's policy (Fable measured it in Chromium): the draft's stricter wrapper policy,
  `default-src 'none'` without `script-src 'unsafe-inline'`, blanks the plot. Never
  `allow-same-origin`, `allow-top-navigation`, `allow-popups`, `allow-modals`,
  `allow-forms` or `allow-downloads`. The 1600x900 (or 1200x1200) page is not clipped on a
  laptop screen: the wrapper scrolls or scales it by CSS alone. A unit test pins the
  wrapper's policy to the harness's constant, read from `render.mjs`, plus `frame-src
  'none'`, so the policy has one owner. Measured by Fable: `frame-src 'none'` does not block
  the `srcdoc` itself, it blocks the child's navigation of itself to http(s); inside the
  child, `top.location`, `window.open`, cookies, storage, `fetch` and workers are refused or
  blocked.
- **The artifact.** `plot.html` joins `ArtifactName` and a JavaScript version's artifacts,
  and `PlotResult.artifacts` holds five (two PNGs, the code, the page, the data; Gemini: a
  JavaScript version with both themes would fail validation at four).
  `GET /v1/sessions/{sid}/artifacts/plot.html?v=&theme=` builds the page on demand, never
  stored (up to about 17 MB a page), from the version's run form, library, `data_json` and
  the theme asked for (default: the version's; the frontend asks for the card's shown
  theme), wraps it and answers `text/html; charset=utf-8` with `Content-Disposition:
  attachment; filename="plot.html"`, `Content-Security-Policy: sandbox`,
  `X-Content-Type-Options: nosniff`, `Cache-Control: private, no-store` and
  `Referrer-Policy: no-referrer`; `404` for a version that is not JavaScript,
  `PageUnsupported` as `503 page_unavailable`, busy as `503` like the theme toggle. The BFF
  adds `plot.html` to its allowlist, forwards `theme` and sets the same headers itself (it
  never forwards upstream media types); `plot.html` stays out of the feedback case's files.
- **The frontend.** A version whose artifacts include `plot.html` gets
  `.download('plot.html')` next to the code download, which downloads the page of the theme
  the card shows (a blob through the authenticated artifact fetch, with the theme). Its
  telemetry outcome was to be `downloaded_code`, because a new action changes the closed set
  and the BigQuery views; the review of JS-4b-1's code reversed that: `downloaded_page`, with
  the views' re-creation left to the owner (the section "Second opinion on JS-4b-1's code").
- **The root prompt** lists `.download('plot.html')` for a Chart.js, D3, ECharts or
  Highcharts plot and says that `plot.js` runs by opening `plot.html` (topic 4).
- **A probe in CI.** The `renderer-image` job builds a page with the image (a small Chart.js
  snippet that reads `window.ANYPLOT_DATA`), wraps it with the agents' wrapper, opens it from
  `file://` in the image's Chromium and asserts that the chart drew in the inner frame, that
  the frame's origin is `null`, and that the snippet's attempts to set `top.location`, call
  `window.open` and `fetch`, and navigate its own frame to an http URL all fail; a unit-test
  image variant runs the same probe.
- **JS-4b-2, the preview,** reaches the chat through a relay page on the API (route A of
  "Second opinion on JS-4b's design", the owner's decision of 2026-10-31); "What JS-4b-2
  built" describes it.

#### Order of the PRs

JS-1 → JS-2 → JS-3 → JS-4; PB-1 and PB-2 (step 4) follow JS-2, whose harness they reuse.

#### What JS-1 built (2026-10-30)

Everything in 3a to 3c; nothing served. Measured in local Docker on the developer machine
(32 CPUs, WSL 2, kernel 6.18, the host shared with another agent's Julia tests), the
renders with `--network none --read-only`, `--cpus 2 --memory 4g` as on Cloud Run, an
unprivileged user, the sandbox's environment and the harness in exec mode with the
JavaScript row's argv:

| Measurement | Result |
|---|---|
| Node stage, cold | 21 s for the whole toolchain build with R's and Julia's stages cached: Node's download and check, `npm ci` with the headless shell's download (11 s), libgbm, the allowlist; the final stage's libraries, copies, `ldd` check and smoke |
| Sizes | Node 120 MB, `node_modules` 164 MB, the headless shell 273 MB; the toolchain image 2.84 → 3.41 GB, the renderer image 3.89 → 4.45 GB (+565 MB each) |
| The build's smoke (Chart.js and MUI X through the harness, the row's environment) | 0.8 and 0.7 s |
| The CI step's renders, container start included | `scatter-basic` Chart.js 1.1 s, `bar-basic` MUI X 1.1 s; 0.6 s of CPU each; the largest process 151 and 153 MiB; 3200x1800 |
| The import allowlist | 219 specifiers: `@mui/material` 155, `@mui/x-charts` 47, `react` 4, `react-dom` 13 (Fable's 156, 48, 5 and 14 with `./package.json`) |
| Chromium's font matching with the row's file (canvas `measureText`) | the catalogue's stack, Helvetica, Arial and `sans-serif` measure as Liberation Sans, `serif` as Liberation Serif; without the file, Helvetica and Arial match no installed face and the stack falls through to another `sans-serif` face (309 against 296 px for the probe text); `new Date("2026-03-01T00:00")` is midnight UTC |
| Liberation installed system-wide, 66 sampled catalogue files rendered in the image with and without it (the changed ones twice more) | 3 of the 40 Python renders change, every time: pygal `band-basic` and `heatmap-adjacency` (of 18 that render) and altair `spectrum-nmr` (of 10), each naming Arial or Helvetica; none of the 12 matplotlib, seaborn, plotnine and lets-plot renders, the 20 ggplot2 and the 4 Makie renders changes (one ggplot2 file draws unseeded random numbers and differs run to run in either image) |
| The R and Makie CI steps in this image | unchanged: `exec_deny: on` for both, the strict cache miss fails in 1 s; the six Python steps, the conversions, the delegate check and the kernel's refusal of program starts pass |

**The render sweep**: every catalogue JavaScript file once, unchanged, through the same
path, four renders at a time at 2 CPUs each (under 10 minutes in all):

| | Result |
|---|---|
| Rendered | 1,565 of 1,617: Chart.js 321 of 321, D3 325 of 325, ECharts 325 of 325, Highcharts 323 of 323, MUI X 271 of 323; every PNG 3200x1800 (1,201) or 2400x2400 (364) |
| MUI X by the version the file was written for | 9.16.0: 127 of 127; 7.29.1: 144 of 196 |
| Failed | 52, all MUI X 7.29.1 files: 51 import `@mui/x-charts/ChartContainer`, which 9.16 no longer exports (`Could not resolve`), and 1 imports `ChartContainer` from the package root (`No matching export`) |
| Wall time, container start included | p50 1.2 s, p95 2.4 s, p99 3.9 s, max 10.1 s (MUI X `heatmap-geographic`); per library p95 2.0 to 3.7 s (ECharts the slowest) |
| CPU time (the harness's children) | p50 0.7 s, p95 1.1 s, max 2.3 s |
| Memory | the whole container (harness, Node, Chromium) p50 372 MiB, p95 440 MiB, max 1,178 MiB (MUI X `bifurcation-basic`); the largest single process p95 159 MiB |

For question 13: the 52 failures are the MUI X 7.29 files that a hint derived from the
allowlist would name (`@mui/x-charts/ChartContainer` is not in it); the other 144 of 196
7.29 files render under 9.16 unchanged. The raw table stays out of the repository.

Also found:

- Playwright validates the shell's libraries with `ldd` over a `chrome-linux` directory
  that the headless shell does not have, so the check costs nothing at launch, and its
  marker file is written at install; no environment variable is needed to skip it.
- The renderer's font-cache step ran `chmod -R` over `/opt/anyplot`, which would have
  copied the toolchain's 164 MB of packages into another layer; it now names the
  renderer's own files there.
- Chromium writes its fontconfig cache to `/tmp/fontconfig` in every render, as R's and
  Julia's fontconfig do; a baked cache (Gemini) was not measured.

| Text above (2026-10-24) | Built | Why |
|---|---|---|
| `node` by name, `toolchain=("node",)` | `NODE_BINARY` by its path | `delegates.py` refuses a `node` on `SANDBOX_PATH` (both reviewers) |
| Playwright's Chromium | the headless shell alone, libgbm unpacked without Mesa | 273 against 403 MB, and about 200 MB of Mesa and LLVM that nothing loads |
| `ANYPLOT_NODE_MODULES` and `ANYPLOT_NO_HTML` in the row, the harness unchanged | `ANYPLOT_NODE_MODULES` read by the harness since JS-1; `ANYPLOT_NO_HTML` with JS-2 | the harness at `/opt/anyplot/js-render/` finds no packages two levels up; a variable the harness ignores would only mislead |
| No font change | Liberation for the JavaScript row alone | the catalogue's stack names Helvetica and Arial; system-wide, the fonts change pygal's and altair's renders |
| `render_p95_s` 20 s | 15 s | the sweep's wall p95 of 2.4 s; the deployed factor and Chromium's cold start under gVisor are the first deploy's to measure |

#### What JS-2 built (2026-10-30)

Everything in 3d; nothing served. The harness's sandbox mode sits behind environment
variables that only the JavaScript row sets (`JS_ENV`); the catalogue pipeline sets none
and renders as before (measured below).

| Variable | What it switches on |
|---|---|
| `ANYPLOT_SANDBOX=1` | the page rules, the import plugin, the console guard and the final error line |
| `ANYPLOT_NO_HTML=1` | no `plot-<theme>.html` |
| `ANYPLOT_DATA_JSON=<path>` | the typed table as `window.ANYPLOT_DATA`; the executor sets it to `/work/data.json` for a JavaScript job that carries `data_json` |
| `ANYPLOT_IMPORT_ALLOWLIST=<path>` | the allowlist the import plugin reads (`/opt/anyplot/js-render/import-allowlist.json`, the default next to the harness) |

- **Data.** `agents/anyplot/data/typed_json.py` writes the canonical CSV as
  `{"columns": [...], "data": [[...], ...]}` (pandas' split orientation; records would
  repeat every column name in every row), each cell typed by its column's kind: integers
  as written, numbers as floats, `true` and `false`, text verbatim, dates `YYYY-MM-DD`,
  datetimes as UTC ISO strings with milliseconds (offsets converted, a cell without one
  read as UTC as in R and Julia, the fraction truncated), `null` for a missing cell. The
  counts the runtime announces stay `ColumnKinds.inexact` (JavaScript's `JSON.parse` reads
  `9007199254740993` as `9007199254740992`) and `ColumnKinds.submillisecond`, which a test
  pins to the cells the truncation changes. The harness parses the file in Node (a broken
  one fails as `data DataError` before the browser starts), puts the text into a
  `<script type="application/json">` element with `<`, U+2028 and U+2029 escaped, and
  builds one object per row with `.columns` in the page, the shape `d3.csvParse` returns;
  `Object.fromEntries` keeps a column named `__proto__` an own property. The wire's
  `RenderRequest.data_json` is optional, at most 16 MiB (`MAX_DATA_JSON_CHARS`, four times
  the CSV cap; the worst tables at the parser's 20,000 rows and 50 columns measure 9.04
  million characters), and `422` on a job in another language; the executor writes it as
  `data.json` next to the code file. The agents side that fills it is JS-4's.
- **Page rules.** `page.context().route("**/*")` aborts every request,
  `routeWebSocket("**")` closes every socket, `--block-new-web-contents` makes
  `window.open` return null, the context has `timezoneId: "UTC"` and blocks service
  workers, whose requests no route sees. The content security policy is adopted as
  proposed, with `form-action 'none'; base-uri 'none'` added (Gemini Flash's review of
  JS-2: neither falls back to `default-src`): every catalogue file renders under it (the
  sweep), so no library needs `'unsafe-eval'` or `blob:` workers; a blob worker cannot
  start under it (`worker-src` falls back to `script-src`). The route still matters where
  the policy does not apply: a top-level navigation (`location.href`) passes the policy
  and is aborted by the route, after which Chromium's error page replaces the plot and
  the render fails as `draw NoOutput` (the CI step and a test check it). A page the
  snippet writes into a `blob:` URL and navigates to passes no route but inherits the
  policy (hygiene, tested). Preconnect and DNS prefetch hints reach no listener (the
  closed proxy). From the page's load on, every answer the harness waits for shares one
  15 s deadline, so a snippet that replaces `requestAnimationFrame` or `document.fonts`
  fails as `timeout TimeoutError` instead of holding the job to its timeout; the page's
  own error records cross into Node cut in the page (10,000 characters, the location as
  two scalars).
- **WebRTC (found).** Neither the route nor the policy sees WebRTC: a page's
  `RTCPeerConnection` reached a local STUN server over UDP and a TURN server over TCP.
  `--force-webrtc-ip-handling-policy=disable_non_proxied_udp` with a proxy on a closed
  port (`--proxy-server=http://127.0.0.1:9 --proxy-bypass-list=<-loopback>`, the last
  because a proxy otherwise skips the loopback) leaves no candidate and no connection.
  Under gVisor there is no network either way; the flags keep the page's rules whole.
- **Console (found).** Playwright keeps a page's recent console messages in Node whether
  or not a listener reads them, so a cap on the harness's own list did not bound Node:
  400,000 one-line errors held 1.3 GB in Node and took 18 s, and 100 errors of 10 MB each
  ended Node with "Invalid string length" inside Playwright's close handler, after the
  harness's own output. A guard in the page (the context script for the main frame, an
  init script for every child frame, one counter on the top window) lets the first five
  `console.error` calls leave the page, each argument cut to 300 characters, counts the
  rest and silences the other console methods: both floods take 1.4 s and 150 MiB.
  Chromium's `console.context()` returned a fresh console past the guard (20 of 20 of its
  errors reached Node, found after Gemini Flash's review asked whether the guard could be
  bypassed); it now returns the guarded console. The console's prototype is empty, so
  `delete console.error` leaves nothing to call; the console is not frozen, since a
  library may assign its methods. The guard and the page's error listeners run before
  `window.ANYPLOT_DATA` is built, so a failure there is caught like the snippet's.
  Messages the browser writes itself pass by it: 200,000 refused `fetch` calls took 20 s
  (Node 194 MiB, Chromium 721 MiB), which the timeout and the watchdog bound. The
  summary prints at most five messages and the count, on success and on failure.
- **Memory flags, measured** (the toolchain image, 2 CPUs, 4 GiB, the row's environment):

  | Runaway in the page | `--js-flags=--max-old-space-size=1024` | without |
  |---|---|---|
  | an array of arrays | `crash PageCrashed` after 3.8 s, container peak 1,620 MiB | crash after 8.4 s, 3,345 MiB |
  | strings | `crash PageCrashed` after 15.6 s, 1,235 MiB | 4,096 MiB (the container's limit), then `setContent`'s 30 s timeout |
  | typed arrays | `page RangeError` (array buffer allocation failed) after 2.1 s, 214 MiB | the same |

  Adopted: 1,024 MiB for the page, which ends a runaway of JavaScript objects well
  before the renderer's `MemAvailable` floor (512 MiB of 4 GiB) and holds the catalogue's
  heaviest render (MUI X `bifurcation-basic`, 1,108 MiB for the whole container). It
  bounds the V8 heap only: Fable's review allocated 3 GiB of `ArrayBuffer`s under it, so
  the watchdog stays the bound on the run's memory. Not adopted: Node's
  `--max-old-space-size`. At 256 MiB Node aborted the console flood with a core dump
  (exit 134) and no final line, and with the guard Node stays near 150 MiB, because it
  runs only the harness. `--disable-dev-shm-usage` and `--disable-gpu` are not adopted
  either: no render in the sweep needed them, and the headless shell draws without a GPU;
  JS-1's deploy smoke measures Chromium under gVisor first.
- **esbuild.** An `onResolve` plugin admits from the snippet only the allowlist's bare
  specifiers, resolved from the packages, and refuses relative, absolute, `node:` and URL
  imports, `require` calls and literal dynamic imports included (`import ImportRefused
  plot.tsx:<line>`). The packages' own imports resolve as before (a nested
  `build.resolve` per import cost 2.5 s for one chart's 3,391 imports). An `onLoad` hook
  sees every file esbuild would read and refuses any outside `ANYPLOT_NODE_MODULES` before
  it is read: Fable's review showed that an import with a template
  (``import(`../etc/${name}`)``) matches a directory's files without the resolve hook, so
  esbuild read every file under `/etc`, and the build error quoted a file's first word.
  The metafile check of every bundled file stays as the backstop, and an esbuild error
  about a file outside the snippet and the packages no longer quotes its text. The hook
  also hands esbuild the snippet without its `sourceMappingURL` comments, lines kept:
  with the bundle's source map on, esbuild reads an input's own map, and
  `//# sourceMappingURL=/dev/zero` held a render for 32 s (Fable). Unused imports are
  dropped by esbuild before resolution, so only an import the snippet uses is refused. `absWorkingDir` and `resolveDir` are the
  packages' parent where `ANYPLOT_NODE_MODULES` is set (`/opt/anyplot`, no longer `/opt`;
  the Gemini Flash finding on #12465). The bundle stays minified; an external source map,
  no comment in the bundle, maps a MUI X error's frame back to the snippet's line.
- **The final error line**, the last line on stderr after the bounded summary, for JS-3's
  error profile: `render: error: <kind> <Class> <file>:<line>: <message>`, or `-` without
  a line in the snippet. `<kind>` is one of `page` (an uncaught error in the page),
  `import` (`ImportRefused`, `ImportNotFound`: esbuild's "Could not resolve" and "No
  matching export"), `build` (`SyntaxError` in the snippet, `BuildError` elsewhere),
  `draw` (`NoOutput`), `crash` (`PageCrashed`), `data` (`DataError`), `timeout`
  (`TimeoutError`) and `harness` (anything else, `UsageError`, `AllowlistError`);
  `<Class>` an identifier, the error's own name for `page`; `<file>` the code file's name
  (`plot.js`, `plot.tsx`); `<message>` at most 200 characters on one line, which can
  quote the user's data, so the profile reads the kind, the class and the line. Measured:
  the snippet's `<script>` starts two lines before it (a line break and `try {`), so a
  throw on line 4 is reported at line 6, not at 5 as 3e says; the harness subtracts the
  offset, names the script's frames with `//# sourceURL=plot.js` apart from the bundle's,
  and takes a snippet that does not parse from the window's error event (setContent
  writes the page with `document.write`, which names `about:blank` and prefixes the
  message). An uncaught exception outside the render's chain (Playwright's own) ends with
  the line too.

**The sweep in sandbox mode**: all 1,617 catalogue JavaScript files through the row of
the built image, its environment with the sandbox variables, no data injection, four at a
time at 2 CPUs and 4 GiB, compared file by file with JS-1's sweep:

| | JS-1 | JS-2 |
|---|---|---|
| Rendered | 1,565 of 1,617 | the same 1,565 (Chart.js 321, D3 325, ECharts 325, Highcharts 323, MUI X 271) |
| Failed | 52 MUI X 7.29 files | the same 52, now `import ImportRefused plot.tsx:<line>` for the 51 that import `@mui/x-charts/ChartContainer` (not on the allowlist) and `import ImportNotFound` for the one that imports it from the root |
| PNG byte for byte as JS-1's | | 1,560 of 1,565; the other 5 are ECharts files whose PNG varies between renders in one image (below) |
| Wall time, container start included | p50 1.18 s, p95 2.44 s, max 10.1 s | p50 1.17 s, p95 1.82 s, p99 3.73 s, max 6.1 s (MUI X `contour-filled`); per library p95 1.2 to 1.3 s, ECharts 3.7 s, MUI X 2.0 s |
| CPU time | p50 0.7 s, p95 1.1 s | p50 0.72 s, p95 0.93 s |
| Memory | the container p50 372 MiB, p95 440 MiB, max 1,178 MiB; the largest process p95 159 MiB | the container p50 372 MiB, p95 507 MiB, max 1,104 MiB (MUI X `bifurcation-basic`); the largest process p95 184 MiB |

The five ECharts files differ between renders in either image: rendered three times in
each, `network-force-directed` (the force layout starts from random positions) gave a new
PNG every time, and `eye-diagram-basic`, `manhattan-gwas`, `spectrogram-mel` and
`treemap-basic` one or two PNGs each, the same in both images. No library needs a change
of the page rules or the policy, and no new failure appeared. The whole sweep ran with
the import plugin's first form, a nested resolve per import, which took MUI X's wall p50
from 1.5 to 4.3 s; MUI X's 323 files ran again with the metafile check (the numbers
above): the same 271 renders and 52 failures, every PNG as JS-1's. After the reviews'
fixes (the `onLoad` gate, the policy's `form-action` and `base-uri`) they ran a third
time: the same 271 renders and 52 failures, every PNG as JS-1's, wall p50 1.78 s and
p95 2.01 s. No catalogue file has a form or a `<base>`, which alone the policy's addition
could touch.

**The pipeline without the variables**: 50 catalogue files (10 per library, a seeded
sample with two of the MUI X 7.29 failures) rendered by JS-1's harness and by this one
with no variable set: the 48 HTML pages and PNGs byte for byte the same, the two failures
the same failures, and the output on stdout and stderr the same once the temporary
directory's name and the harness's own line numbers are normalised. The host test module
pins it byte for byte: without a variable, the page for the build smoke's Chart.js file
equals the page JS-1's harness wrote, stored with the bundle and the snippet as
placeholders (`tests/unit/automation/fixtures/js-render-page-light.html`).

**Tests**: `tests/unit/agents/data/test_typed_json.py` (28 cases),
`tests/unit/automation/test_js_render_sandbox.py` (32 cases, rendered through Node and
Chromium, skipped where `node`, the lock's packages or the browser are missing: a clean
Chart.js and MUI X render, the pipeline's page byte for byte, every way out of the page
against a local HTTP and UDP listener with and without the sandbox mode, preconnect and
DNS prefetch included, a navigation, a `blob:` navigation, a page that never settles,
UTC, the console cap and `console.context`, the import refusals, an import with a
template over a sibling directory, a source map comment, the data round trip with
`</script>` and the line separators in a cell, a huge error record, the final error
line), the renderer's row, wire and executor tests, and the CI step in
`ci-image.yml`, which renders through the row in the built image: the two catalogue files
without an interactive page, the data injection, the route's abort of a navigation and
the plugin's refusal of `/etc/os-release`.

| Text above | Built | Why |
|---|---|---|
| 3d: Gemini's policy and flags measured before any is adopted | the policy and `--js-flags=--max-old-space-size=1024` adopted; Node's heap cap, `--disable-dev-shm-usage` and `--disable-gpu` not | every catalogue file renders under the policy; the measurements above |
| 3d: the route, `routeWebSocket` and `--block-new-web-contents` | also the WebRTC policy with a closed proxy, blocked service workers, a console guard in the page, an `onLoad` gate on every file esbuild reads and one deadline for the page's answers | WebRTC passes the route and the policy, Playwright buffers console messages in Node, an import with a template reads files without the resolve hook (measured; the last two by the reviews of JS-2) |
| 3d: console errors capped in count and bytes | capped in the page as well | the harness's cap alone left Node at 1.3 GB |
| 3e: the snippet's offset is exactly 1; MUI X errors name the class only | the offset is 2, and the harness subtracts it; MUI X errors name the snippet's line through the source map | measured; JS-3 reads `<file>:<line>` as printed |
| 3d: `window.ANYPLOT_DATA` with `<` escaped | the split orientation in a JSON element, one object per row with `.columns` in the page | the column names travel once, not in every row, and no `__proto__` key becomes a prototype |

#### What JS-3 built (2026-10-30): the JavaScript code profile, not served yet

Everything in 3e; `AGENT_LIBRARIES`, `RUNTIME_LIBRARIES`, the runtime registry, the
prompts and `_LIBRARIES` are untouched, as for J2a. The profile lives in
`agents/anyplot/code/profiles/javascript/` (regions, normalise, coupling, validate,
readiness, loader, errors, and `allowlist.py` with its JSON copy), takes the library
everywhere (`regions.grammar_for`: `tsx` for MUI X, `javascript` for the other four) and
mirrors the Julia profile's modules, names and test layout
(`tests/unit/agents/code/test_profile_javascript_*.py`, `test_treesitter_javascript.py`;
2,064 cases, 1,617 of them the parse of every catalogue file).

- **Parser.** `GRAMMARS` is `("r", "julia", "javascript", "tsx")`; `agents/Dockerfile`
  keeps `r julia javascript tsx` (0.5 MB and 1.6 MB more) and still prunes the pack's
  `typescript` grammar, TypeScript without JSX, which no catalogue file needs. All 1,617
  files parse with no ERROR or MISSING node. `treesitter.py` gained the JavaScript
  helpers: string and template values (escapes, surrogate pairs, `None` for a template with
  a substitution, a legacy octal or a lone surrogate), numbers (hex, binary, octal,
  separators, BigInt; `None` past a double), dotted callees, and the scopes: every binding
  with the node it is visible in (`var` its function, `let`, `const`, classes and function
  declarations their block, parameters their function, imports the program, a function
  expression's name itself), so `js_references` resolves each identifier to the innermost
  binding around it or calls it free. TSX's type positions are skipped.
- **Regions.** The token lines, 2,342 over the catalogue (`const t =
  window.ANYPLOT_TOKENS;` in 1,602 files; destructured sizes, `THEME`, `isDark`, `MUTED`,
  ...), at the top level: a value built only from literals, the three globals' members,
  earlier tokens, comparisons, arithmetic, `||`, `&&`, `??`, `!` and ternaries, which reads
  a global itself or tests an earlier token. The orientation directive as the harness reads
  it (`orientationFromSource`: the first line anywhere that matches, after any JavaScript
  line terminator); it is the protected `savefig` region. The markers (`// Data` in 1,344
  files, `// Plot` in 134, loosely as in R and Julia), column constants (121 files), the
  placeholder, a written-out Imprint palette (none in the catalogue: it reads
  `t.palette`), and MUI X's imports with the names each brings in.
- **Normaliser.** Header (1,617), one directive in the canonical form on the first line
  (723 files carry one right after the header, violin-split's Highcharts file at line 14,
  and the 893 without one get `landscape`, the harness's default, written out), the
  catalogue title (1,614; JSX text becomes `{""}`; three titles in a template with a
  substitution stay, as Python's f-strings do). No rewrite reads a number, so none can
  overflow; idempotent and parsing over the corpus. `measure_canvas` is the harness's:
  3200x1800, or 2400x2400 for `square`. No MUI X 7.29 to 9 rewrite (question 13).
- **Validator.** Refuses by shape (module docstring of `profiles/javascript/validate.py`).
  The deny list of 3e stands on a closed world: a free name must be one of `GLOBALS` (the
  catalogue's 33, the four library globals among them, and built-ins of the same kind) or
  the file's own library global, so
  anything a list forgets is refused too, read or written, through an alias (`const f =
  fetch`), a shorthand property (`{ fetch }`) or optional chaining; `DENIED_NAMES` gives
  the reason. `window` and `document` are only the object of a named member from a short
  list (`window.ANYPLOT_*`, `__anyplotReady` the only write, listeners, `devicePixelRatio`;
  `document.getElementById`, `createElement`, `head`, `body`, ...), never a value and never
  indexed by code; a literal index reads as the member. `constructor`, `__proto__`, the
  accessor helpers, `defaultView`, `ownerDocument`, `contentWindow` and the like are
  refused on any value, as a literal index, a destructured key and a string of their own;
  `Object` lends only `keys`, `entries`, `fromEntries`, `assign` and their kind; D3's file
  loaders and Highcharts' AJAX helpers are refused. Also `import()`, `import.meta`,
  `setTimeout`/`setInterval` without a function literal, elements that run or load
  (`script`, `iframe`, `object`, `embed`, `link`, `base`, `form`, ...) created by
  `document.createElement` (only with a literal tag), `createElementNS`, `d3.create`, a
  selection's `append` and `insert` or JSX, `dangerouslySetInnerHTML`, `with`, top-level
  `this`, URLs (the XML namespaces excepted), markup that runs in a string (an opening
  `<script` or a tag with an inline handler; a user's column name with `</script>` passes),
  strings past 200 characters, a second or a misplaced directive, writes to the tokens
  (by name, member, mutating method or `Object.assign`) and imports in a classic script. A
  parameter or local that shadows a token name inside a function is no rebinding (D3's
  callbacks name `t` freely). MUI X imports: a module outside the four packages is SECURITY
  (`banned-import`, labelled from a closed vocabulary), a module of them that the image does
  not export, or a name of `allowlist.REMOVED_EXPORTS`, is the ADAPTATION finding
  `unavailable-import`, which JS-4 puts in the runtime's blocking set. SECURITY finds
  something in 7 of the 1,617 normalised files: qrcode-basic in all five libraries (the
  encoded `https://anyplot.ai`), line-parametric's Chart.js legend (a 683-character HTML
  string) and the MUI X flowmap-origin-destination, a map spec (coastlines as long
  strings). After the review below, 205 named bypasses (182 in a script, 23 in a MUI X
  module), 61 admitted idioms and 6 pinned escapes are tests.
- **Readiness.** Per library, of the normalised files:

  | Library | Clean | Coupled | Blocked | Blocked for |
  |---|---|---|---|---|
  | Chart.js | 0 | 306 | 15 | 13 map specs, qrcode-basic (`url-literal`), line-parametric (`string-length`) |
  | D3 | 0 | 311 | 14 | 13 map specs, qrcode-basic |
  | ECharts | 0 | 311 | 14 | 13 map specs, qrcode-basic |
  | Highcharts | 0 | 310 | 13 | 12 map specs, qrcode-basic |
  | MUI X | 93 | 218 | 12 | 11 map specs, qrcode-basic |

  The 93 clean files are MUI X files regenerated for 9.16 with both markers and column
  constants. Hints: `data-block` 1,434, `synthetic-data` 815 (`Math.random`, D3's random
  sources and the hand-written generators' constants, `1664525` in 470 files), `limits`
  549, `annotations` 153, `statistics` 90, `color-scale` 23, `deprecated-api` 51 (MUI X),
  `palette` 1. No file is blocked for a missing marker, its token style or its MUI X
  version.
- **Loader.** `const data = window.ANYPLOT_DATA;` for the placeholder, one line for one
  line, so error lines need no shift; `loader_span` names it as the data loader in a
  summary.
- **Errors.** Only the last line on stderr counts, the harness's final error line: the
  kind, the class (`page` errors name a class of `PAGE_CLASSES`, ECMAScript's and the
  DOM's; a class of the snippet's own is "an error") and the line in `plot.js` or
  `plot.tsx`; fixed texts for the other kinds. Corpus-tested with the final lines of real
  failed renders through the harness's sandbox mode (Node 24, the lock's packages and the
  headless shell): a `TypeError` and a `ReferenceError` in a script, a script that does not
  parse, a class of the snippet's own (`Berlin4711`), nothing drawn, an import off the
  allowlist, a name MUI X 9 lacks, a TSX syntax error, a MUI X `TypeError` mapped through the
  source map, a broken data file and a page that never settles; the console summary above
  the last line, which the snippet can fill with lines that look final, is never read.
- **Edits and export.** The edit applier's JavaScript dialect: the token lines, the
  placeholder and the directive protected (the directive as the orientation it picks in the
  drift check's meaning, so a respelling passes and `landscape` for `square` is
  `drift:savefig`, which `restore_protected` puts back); only top-level bindings count as a
  rebind, and `THEME` is no special name; `//` and `/* */` are comments, a block comment may
  span lines and opens no literal, templates span lines, and a `#` in a string is text. The
  literal budget counts JSX text. Python's, R's and Julia's behaviour and tests are
  unchanged. The export's header is two `//` comments with the run line of question 12.
- **The allowlist copy.** `profiles/javascript/import-allowlist.json` is byte for byte the
  image's file (the script's `json.dump(..., indent=1)`). A unit test regenerates the list
  with the image's own script from the repository's `node_modules` and compares it (skipped
  without `npm ci`), and a second one imports every allowlisted `@mui/x-charts` module in
  Node and checks that every name a catalogue MUI X file imports exists, but the names of
  `REMOVED_EXPORTS`, which none exports (`ChartContainer`, `ResponsiveChartContainer`,
  `DefaultChartsLegend`). The `renderer-image` job of `ci-image.yml` compares the built
  image's file with the copy (`cmp`, the regeneration command in the error), and the copy
  joined its change filter; the same step feeds the profile's error grammar the final lines
  of its sandbox checks. The `agents-image` job runs the readiness scan on the catalogue's
  scatter-basic Chart.js and bar-basic MUI X files through the pruned grammars.
- **Verified end to end, without a model.** Two scripted identity adaptations passed both
  validator profiles and the drift check, took the loader and rendered through the harness
  in sandbox mode with the typed data (`typed_json`), Node 24 and the headless shell, in
  both themes: MUI X `lollipop-basic` (the data block swapped for the placeholder, the
  column constants renamed to `Genre · Sorte "A" — </script><b>` and `Umsatz (Mio. €)`, a
  row with both cells missing) at 3200x1800 in 0.9 s, and the tests' Chart.js miniature
  (square) at 2400x2400 in 0.5 s, wall time with Chromium's start.
- **The review of JS-3 (Fable and Gemini 3.8 Flash, 2026-10-30).** The exported `plot.html`
  runs in the user's own browser, where a content security policy stops a request but not
  a top-level navigation, so the validator was tightened where a review found an escape,
  each rule narrowed until no catalogue file changed status (the split above is the one
  after the review; the shapes the reviewers proposed literally would have blocked 63, 7 and
  11 more files):
  - `this` as a value (returned, assigned, passed, spread, destructured) or read by a
    computed key only where it is known not to be the window: a method or class member, an
    object's value (Highcharts' `load` and `formatter`), a callback of D3's `each` and `on`
    (`THIS_BINDING_METHODS`), or a function the file only hands to those. Refusing it in
    every plain function, as proposed, would block 63 files (47 D3 callbacks pass `this` to
    `d3.select`, 41 Highcharts handlers keep the chart); `function g() { return this } g()`,
    an array's `map`, a timer and D3's `call` are refused.
  - A computed key built from strings is refused when its written fragments could spell a
    member of `DENIED_MEMBER_STRINGS` (`[]["con" + "structor"]`, and through a name given
    such a value), and a key a string builder returns (`.join()`, `String.fromCharCode`,
    `atob`). Refusing every concatenated, templated or called key would block 7 files
    (andrews-curves, chernoff-basic, area-stacked-confidence, parallel-categories-basic,
    psychrometric-basic) for the template keys and 121 for the call results (`Math.floor`,
    `indexOf`); a template of substitutions alone (chessboard-pieces' `` `${f}${r}` ``) is
    as opaque as a name and passes. A written key also must not spell a URL or navigation
    member (`el["hr" + "ef"] = url`).
  - Protocol-relative URLs (`"//example.org/p?" + x`) are `url-literal`; `src` and `href`
    are written (by assignment, `setAttribute`, `setAttributeNS`, D3's `attr`) only with a
    data URL the code drew (`canvas.toDataURL()` or a `const` of one: heatmap-mandelbrot's
    and recurrence-basic's rasters), and `location`, `action`, `cookie`, `srcdoc`,
    `formAction` never; `.write()` and `.writeln()` on any receiver, and `cookie` read on any
    receiver, are refused. JSX attributes (`<img src={url} />`, contour-decision-boundary's
    raster through a helper) and a library's own image calls stay, pinned below.
  - Tags: `script`, `iframe`, `frame`, `frameset`, `embed`, `applet` and `portal` are
    refused as a string literal anywhere; the full `DENIED_TAGS` (with `object`, `link`,
    `base`, `meta`, `form`, words the catalogue writes as text in 11 files: D3's `"link"`
    class, a waterfall's `"base"`) only where a tag is made, as a literal, a ternary of
    literals or a `const` of one, by any receiver's `append`, `insert` or `createElement`
    (React's too) and React's `jsx` runtime. `dangerouslySetInnerHTML` is refused as an
    object's key, so a spread `<div {...p} />` cannot carry it.
  - `setTimeout(draw, 0)` passes when `draw` is a function the file declares and never
    writes again (Flash).
  - The edit applier reads a JavaScript regular expression literal as one word, so its quote
    (`/a"b/`) opens no string (Fable; a find failed to match, nothing was corrupted).
  - Still passing and pinned as tests (`test_still_passes_contained_by_the_sandbox`): a key a
    function returns or a parameter carries, a method called off its object (its `this` is
    the window), markup assembled at run time, a URL a JSX attribute or a library's image
    call takes. Flash's "`undefined` is no global" was a false positive (`undefined` is a
    literal of the grammar; a test keeps it allowed).
  - The Copilot review of #12473: a call through a literal index (`d3["create"]("script")`,
    `el["setAttribute"]("href", u)`, `x["write"](...)`) is read as the named call by the
    tag, attribute and write rules; a setter's attribute name is checked for every literal a
    ternary can give it, and a computed name is refused (none in the catalogue); where `this`
    may be the window, `this.document` and `this.window` are refused; `arguments` left the
    globals and is bound only inside a function that is no arrow; and a directive's span is
    its JavaScript line, which a lone `\r`, U+2028 or U+2029 ends, not tree-sitter's `\n`
    line, so moving it no longer takes the code that shares that line. The split did not
    change.
  - Its second round: the names a write may not set are checked on every object that
    writes onto an element (`Object.assign` sources whose target is no fresh `{}`, a `const`
    holding one, spread objects, Highcharts' `attr({...})`), where `innerHTML`, `outerHTML`
    and an inline handler without a function written in place are refused too, and an
    inline handler attribute is never set; `this.window`, `this.document`, the window-only
    names and `this[...]` are refused on `this` in every context, since a method handed to
    a browser callback runs with the window as `this`; a computed key, also an object
    literal's, must not spell `dangerouslySetInnerHTML`, a write-checked name or (by a written
    `on` start) a handler, and a key the literals decide (`["con", "structor"].join("")`,
    `String.fromCharCode(...)` of numbers) is read as the string it is. Three files forced the
    narrowings: chernoff-basic's `r[m + "Norm"]` (an unknown start is no handler) and the
    `sx` selectors of andrews-curves and bar-diverging-likert in MUI X (an object's key from
    a builder the run decides passes; pinned). The split did not change.

  The validator is defence in depth over source text and will always have spellings left:
  two Copilot rounds found eight. The exported page's boundary is JS-4's: a content
  security policy without network; the preview iframe with `sandbox="allow-scripts"` and
  neither `allow-same-origin`, `allow-top-navigation` nor `allow-popups`; and for the
  downloaded `plot.html`, a page that itself loads the plot into such a sandboxed `srcdoc`
  iframe under a parent policy that restricts `frame-src` and navigation, because a content
  security policy does not stop a page's own top-level navigation. JS-4 verifies that
  design with a probe like JS-2's.

Found for JS-4:

- **The exported page needs its own boundary.** `plot.html` (question 12) runs in the
  user's browser and in the chat's preview: it must carry a content security policy without
  network (the harness's sandbox policy: `default-src 'none'`, no `connect-src`, images and
  fonts from `data:` only, no `'unsafe-eval'`), and the preview iframe
  `sandbox="allow-scripts"` without `allow-same-origin`. A policy does not stop a top-level
  navigation, which is why the validator refuses `location`, `open` and the URL and
  navigation writes above. JS-4 should also consider wrapping the exported script in a
  function with `"use strict"`: a plain function called without a receiver would then see
  `undefined`, not the window, as `this`. Not the harness: the catalogue pipeline renders
  through it, and a directive inside its `try` block has no effect.

- **`+null === 0` in the catalogue's own code.** The lollipop's all-missing row drew as a
  category `null` at 0.0: the file converts with `String(...)` and `Number(...)`, as many
  catalogue files do. The adapter prompt's warning (3f) should name both conversions and
  ask for a filter on `null` before them.
- **A thrown value that is no `Error` names the harness's wrapper.** `throw "text"` in a
  three-line snippet ends with `page Error plot.js:7`: without a stack the window's error
  event points at the wrapper's `throw err`. `error_summary` takes `line_count` and drops a
  line past the code's end; the runtime passes the run form's line count with
  `loader=loader_span(run_form, library=...)`.
- **Titles in a template.** Three catalogue titles are templates with a substitution
  (`${SYMBOL} · indicator-sma · javascript · muix · anyplot.ai`) and stay; the adapter
  retitles them like any other title.

| Text above (3e) | Built | Why |
|---|---|---|
| tree-sitter's JavaScript, TypeScript and TSX grammars | `javascript` and `tsx`; `typescript` pruned | no catalogue file is `.ts`; `tsx` is TypeScript with JSX |
| The deny list over tree-sitter | the deny list as reasons over a closed world of free names, with real scopes | a list misses what it does not name; the catalogue reads 33 globals, and scopes keep a local `open`, `top` or `window` (indicator-bollinger's moving window) from being refused |
| Protected: the token lines that read the three globals | also a line that tests the theme through an earlier token; a line that also reads another name is plot code | `const MUTED = isDark ? ... : ...` is a token as Julia's `THEME == "light" ? ...` is; `CELL_W = (window.ANYPLOT_SIZE.width - MARGIN) / N_COLS` depends on the data's shape |
| The directive kept by the drift check | the normaliser writes one on the first line of every file | 893 files had none, and a directive the adapter adds later would change the canvas past a check that compares nothing |
| `new Image().src` refused | `Image` refused as a name; `img` and SVG `image` elements allowed | five catalogue files draw a canvas raster through them with a data URL the code computes; a literal URL is refused anyway |
| MUI X imports checked against the allowlist | outside the four packages SECURITY, a module or name of them that MUI X 9 lacks ADAPTATION | question 13: a 7.29 file is coupled with a note, never blocked for its version |
| The run line follows question 12 | `// run: open plot.html in a browser, ...` | decided on 2026-10-30 |
| A snippet that reads the tokens | `no-theme` blocks a file that reads neither `ANYPLOT_TOKENS` nor `ANYPLOT_THEME` | the counterpart of Julia's missing theme statement; no catalogue file is blocked by it |

#### What JS-4a built (2026-10-30): Chart.js, D3, ECharts and Highcharts served for the admin

3f without the export's page, which is JS-4b's, and without MUI X, which follows with its
fixtures.

- **Runtime.** `JavaScriptRuntime` (`agents/anyplot/render/runtimes/javascript.py`)
  mirrors `JuliaRuntime` on JS-3's profile: the command and the environment are the
  renderer's JavaScript row's, key for key (no `RLIMIT_AS`, no `RLIMIT_NPROC`, no exec
  filter); the file name and the code artifact come from the row, so the class takes MUI X
  as `plot.tsx`; `review_texts` is on; `unavailable-import` joins the blocking rules; the
  soft findings get JavaScript targets; the export is JS-3's. `JAVASCRIPT_LIBRARIES` holds
  the four libraries, and the admin deploy's `_LIBRARIES` names them.
- **Data.** `RuntimeAdapter.data_json` (None on every other runtime) types the canonical
  CSV once per run; `RenderJob.data_json` carries it (refused on another language's job, as
  the wire refuses it) and `CodeVersion.data_json` keeps it for the theme toggle. The
  remote backend sends it, the local backend writes `data.json` and sets
  `ANYPLOT_DATA_JSON` as the renderer's executor does, and the eval harness's own render
  jobs (`ladder_lab`, `stress`) carry it too. Without the kinds the loader refuses the run
  form, as R's does, and so it does for a cell the typing cannot hold: `data_json` raises,
  the pipeline drops the kinds, and the attempt ends as `loader` with the reason (the first
  draft left the page without a table, so the repair blamed the plot code's first
  `data.map`; second opinion below).
- **Notes.** Up to three "what changed" lines with counts per column, first in the list,
  the status left as the render earns it: integers past 2^53, timestamps cut to the
  millisecond, timestamps converted to UTC (`notes.offset_note`).
- **Errors.** `error_summary` with the run form names a line on the loader as the data
  loader and drops a line past the code's end (JS-3's findings).
- **Prompt.** `prompts/adapter_javascript.md` fills every slot. Measured in the JS-2
  renderer image before it was written: D3's `scaleUtc` with `utcFormat`, ECharts'
  `useUTC` with a `time` axis and Highcharts' `datetime` axis show the dates in UTC (the
  exported page runs in the user's time zone); the page has no Chart.js date adapter, so a
  `type: "time"` axis fails the render and the prompt puts dates on a category or linear
  axis, the category labels sliced from the cell (`slice(0, 10)`, `slice(11, 16)`),
  because a timestamp cell is the whole ISO string (the end-to-end check below found
  `01T07:00:00.000Z.01.2025` where the first draft reversed the cell's parts); Highcharts writes `8k` and a space for thousands unless its labels go through the
  `fmt` helper, which every value axis uses. The idioms pass both validator profiles per
  library and render 3200x1800 in both themes from a table with missing cells and a column
  name with a quote and a backslash (`test_profile_javascript_image.py`, skipped without
  the image).
- **Scope judge.** Its `other_library` example was "JavaScript with Chart.js", which the
  chat now adapts: it is MATLAB now, outside the catalogue (the test said the step that
  serves Chart.js changes it).
- **Fixtures.** 240 cases (`*-chartjs-*`, `*-d3-*`, `*-echarts-*`, `*-highcharts-*`) and
  one smoke case each; all forty matrix files are `coupled`. Across the catalogue 306 of
  321 Chart.js, 311 of 325 D3, 311 of 325 ECharts and 310 of 323 Highcharts files are
  eligible, none `clean`.
- **Deploy.** The renderer's candidate smoke renders a Chart.js chart from a typed table
  and refuses the promotion when it fails, like the Makie render. The agents image's CI
  step scans through the runtime and the image carries `adapter_javascript.md`.
- **Docs.** `docs/concepts/agent-network.md` lost J2b's eight lines about Makie in the
  merge of JS-1 (#12465); JS-4a restores them with its own.
- **End to end without a model** (2026-10-30, the JS-2 renderer image through the local
  Docker backend): a pasted table of 60 rows with a text group, two number columns with a
  gap, a timestamp column with `+01:00`, microseconds and two gaps, and an integer column
  past 2^53, through the parser, each library's prompt-idiom form, the loader, the typed
  table and the host gates: all four libraries pass R1 to R3 in both themes, 3200x1864
  with the footer strip, 1.2 to 1.6 s per two-theme job; the notes count 60 integers, 57
  cut timestamps and 58 converted ones.

| Text above (3f) | Built | Why |
|---|---|---|
| Fixtures for Chart.js, D3 and ECharts first; Highcharts behind the switch | all four libraries | question 6 decided on 2026-10-30 |
| The deploy smoke's Chart.js render as a gate | a gate, and the page reads the job's typed table | the deploy proves the data path every agent job takes |
| `+null === 0` warned in the prompt | `+null`, `Number(null)`, `null * 2`, `String(null)` and `Math.max` named, with the filter before any conversion | JS-3's lollipop finding |
| Not in the text | time axes in UTC; Chart.js on a category or linear axis | measured: the exported page runs in the user's zone, and the page has no date adapter |

#### What JS-4b-1 built (2026-10-31): the downloadable `plot.html`

Everything in 3g but the preview (JS-4b-2).

- **Harness.** `ANYPLOT_PAGE_ONLY=1` works only with `ANYPLOT_SANDBOX=1` (without it the
  harness stops with a usage error, exit 2), because the page leaves the sandbox as a
  download and so must carry the policy. The page-only run writes the very page a render
  writes (a host test compares them byte for byte, the snippet's own text aside) and starts
  no browser: a run with a browser path that holds no browser passes, and a snippet that
  throws builds its page all the same.
- **Renderer.** `POST /page` with `wire.PageRequest` (`data_json` required: a JavaScript run
  form reads `window.ANYPLOT_DATA`), `executor.run_page` (the code file and `data.json`, no
  `data.csv`; the JavaScript row's argv; `ANYPLOT_PAGE_ONLY=1` in its environment) and a
  `422 {"detail": "page_failed", ...}` body (`wire.PageFailure`: the exit code, the reason
  with the measured value and the limit, the stderr tail) for a build without a page. The
  page is read after exit code 0 under `MAX_PAGE_BYTES`, 24 MiB (the bundle, ECharts' 1.1 MB
  the largest, plus at most 16 MiB of typed table with every `<` escaped to six bytes, and
  8 MiB under Cloud Run's 32 MiB cap on a response that is not streamed), as strict UTF-8.
  The idempotency key is the `job_id`, `page` and the theme; a replay joins a build in
  flight, but a finished page is not kept in the replay cache (16 answers of up to 24 MiB
  would hold 384 MiB of a 4 GiB instance, and a second build runs no code).
- **Agents.** `PageJob`, `PageUnsupported`, `PageFailed` and `RenderBackend.page` in
  `render/contract.py`; the remote backend's `page` (a `404` is `PageUnsupported`, `422
  page_failed` is `PageFailed`, `503 busy` and `low_memory` are `RenderBusy`, a launcher
  failure is the renderer's); the local backend's `page`; the fake's `fixture_page`;
  `SerialRenderer.page` in the `toggle` lane. `render/page.py` wraps the page and imports
  only the standard library, so the CI step loads it by its path. `page_export.page_download`
  builds and wraps on demand, waits for a slot as long as the theme toggle does, and logs a
  failed build by its error summary (kind, class, line), never its message.
- **Decisions taken in the build.**
  - The wrapper writes the page into a single-quoted `srcdoc` with only `&` and `'` as
    references: they are the only characters a single-quoted attribute value treats
    specially, so the frame gets the page character for character (a test parses it back),
    apart from the normalisation the HTML input stream applies to any load of a page (CR LF
    and a lone CR become LF, NUL becomes U+FFFD), and the typed table's many `"` do not grow
    sixfold as they would in a double-quoted attribute.
  - The frame scales by media queries in steps (1, 0.9, 0.8, ..., 0.25) to the largest that
    fits the window with a 16-pixel margin, and the wrapper scrolls below a quarter: a
    1440x900 laptop's window of about 1440x790 shows the landscape plot at 0.8 (1280x720)
    without a scroll bar. Pure CSS: `transform: scale()` on the frame inside a box of the
    scaled size; pointer events reach the plot through the transform (the probe hovers it).
  - The wrapper's margin is the page's background per theme (`pageBg`, pinned to the
    harness by a test), and its title names the spec, the library and the version.
  - The download is registered in the session's run registry while it builds, like the
    theme toggle, so it and a turn or a toggle of the same session refuse each other with
    `409 run_active`; the page holds the whole session back while the page builds
    (`pageBusy` in `useAgentSession.ts`, after the review of the code), so the composer, the
    theme toggles and the data edits wait as for a theme render. Error codes: `503 page_unavailable` also for a renderer that cannot
    be reached, `500 page_failed` for a build that left no page; the BFF passes both.
  - The local Docker backend mounts the checkout's `render.mjs` for renders too, not only
    for page builds, so a version's PNG and its page come from the same harness; a checkout
    without the file (an agents image) keeps the image's.
  - The probe sits at `agents/renderer/page_probe.mjs`, outside the toolchain's inputs
    (`toolchain.py`, `INPUTS`): an edit of the probe reruns the `renderer-image` job but
    does not rebuild the toolchain image. It prints its snippets (`snippet chartjs`, `d3`,
    `echarts`, `highcharts`) for the harness and checks a wrapper (`check plot.html --hover
    --attempts`).
    Its hover moves the window's own pointer over the scaled plot: Playwright's
    `hover({position})` maps a point into the frame without the frame's transform, and its
    events missed the plot (measured).
  - The result card's code label reads `# plot.js runs in plot.html` for a JavaScript
    version (it said `runs next to data.csv`, which only the other languages do).
- **Measured** (local Docker, the JS-2 renderer image with the checkout's harness mounted, the
  local backend's `page`, five runs each):

  | Library | Build, container start included | Page, 40 rows | Wrapped | Page, 20,000 rows (a 574 KB CSV, 730 KB of typed JSON) |
  |---|---|---|---|---|
  | Chart.js | p50 0.61 s | 214 KB | 223 KB | 943 KB, built in 0.63 s |
  | D3 | p50 0.60 s | 288 KB | 297 KB | 1.02 MB, 0.61 s |
  | ECharts | p50 0.60 s | 1.13 MB | 1.18 MB | 1.86 MB, 0.65 s |
  | Highcharts | p50 0.61 s | 288 KB | 308 KB | 1.02 MB, 0.62 s |

  Without the container (Node on the host), a Chart.js page builds in 0.23 s.
- **The probe** (`page_probe.mjs` in the image's Chromium, the window at 1440x790) passed for
  Chart.js, D3, ECharts and (after the review) Highcharts pages built through the local
  backend and wrapped by `page_download`: the chart drew in the frame (Chart.js 588,975
  painted pixels, ECharts 383,132, D3 six shapes, Highcharts SVG shapes), a hover changed the
  frame (a Chart.js tooltip, D3's `mouseover` text, ECharts' axis tooltip, Highcharts'
  tooltip), the frame's origin is `null`, `top.location` and storage and
  cookies are `SecurityError`, `window.open` returns `null`, `fetch` is a `TypeError` (the
  policy), the frame's navigation of itself to http ends on `chrome-error://chromewebdata/`,
  and a listener on the loopback saw no request, with no popup, download or dialog. The
  prompt idioms of all four libraries download as pages that draw, in both themes. Two
  controls: with `allow-same-origin allow-top-navigation allow-popups` the snippet
  navigated the window away and the probe failed; without `frame-src 'none'` the
  navigation was blocked all the same, because the wrapper's `default-src 'none'` is the
  fallback of `frame-src`, so the explicit directive is a second line, not the only one.
- **Tests.** The harness's page-only mode (`test_js_render_sandbox.py`), the wire, the
  executor through the fake launcher and the real harness in exec mode, the service route
  (`test_service.py`, `TestPage`), the remote backend (`TestPage`), the wrapper and
  `page_download` (`test_page_export.py`), the artifact names and both copies of the page's
  headers (`test_artifact_names.py`), the service flow (a D3 session downloads its page in
  both themes; the error codes; `409 run_active` while a build runs), the BFF route, and the
  image test (`test_profile_javascript_page_image.py`, skipped without the image): the
  probe and the idioms for all four libraries.
- **In the browser** (2026-10-31, the agent chat against the local BFF mock, which serves
  JavaScript versions with a stand-in page since then): the button waits while the run
  streams, the light card downloads the light page and the dark card the dark one, and each
  file opened from disk draws in its frame (origin `null`) and answers a hover, at 1440 and
  390 pixels, in both site themes, with a clean console.

| Text above (3g) | Built | Why |
|---|---|---|
| `ANYPLOT_PAGE_ONLY=1` in sandbox mode | refused without `ANYPLOT_SANDBOX=1` | the download must carry the sandbox's policy |
| `/page`'s failures with `/render`'s mapping and the final error line in a JSON body | `422 page_failed` with `wire.PageFailure` | a built page is the body itself, so a failure needs another status; `422` is never retried by the front end and carries the renderer's own `detail` |
| The page escaped for the attribute | a single-quoted `srcdoc` with `&` and `'` as references | the exact escape for that attribute state, without growing every `"` of the table sixfold |
| Scroll or scale | both: stepped CSS scales to a quarter, a scroll bar below | a laptop shows the whole plot at 0.8 without scrolling; pure CSS cannot compute a free scale |
| Not in the text | the download holds the session's registry entry; `500 page_failed` | like the theme toggle, one sandbox job per session at a time; a failed build has a code of its own |
| The probe under `agents/renderer/toolchain/` or next to the harness | `agents/renderer/page_probe.mjs` | both of those are toolchain inputs, so every edit of the probe would rebuild the toolchain image |

#### What JS-4b-2 built (2026-10-31): the interactive preview in the chat

The owner chose route A on 2026-10-31 ("Second opinion on JS-4b's design"): a relay page on
the API that the chat posts the page into. No token and no cookie reaches the relay, and the
site's policy is unchanged (it already allows `frame-src https://api.anyplot.ai`).

```
the chat (anyplot.ai)
  <iframe sandbox="allow-scripts" src="https://api.anyplot.ai/preview/relay">
    the relay: an opaque origin (`sandbox allow-scripts` in its policy), its own script only
      <iframe sandbox="allow-scripts" srcdoc=<the wrapper, set as a property>>
        the wrapper of JS-4b-1: no script
          <iframe sandbox="allow-scripts" srcdoc=<the harness's page>>
            the plot code
```

- **The relay.** `GET /preview/relay`, served by the API (`api/routers/preview.py`) from
  `api/preview_relay.py`, which imports only the standard library, so the renderer image's CI
  step loads it by its path. Outside `/debug/*`, unauthenticated and the same for every
  caller: 1,131 bytes, no markup of its own, one inline script. Its headers:
  `Content-Security-Policy: sandbox allow-scripts; <the harness's policy>; frame-ancestors
  <the site's origins> http://localhost:*`, `X-Content-Type-Options: nosniff`,
  `Referrer-Policy: no-referrer` and `Cache-Control: public, max-age=300`. The harness's
  policy is copied once more and pinned to `render/page.py`'s `PAGE_POLICY` by a test, so it
  keeps one owner; every frame inside the relay inherits it, so none of them reaches the
  network.
- **What the relay accepts.** The first message whose `event.source` is `window.parent` and
  whose `event.origin` is one of the framing origins, holding a non-empty string of at most
  32 Mi characters (the agents service answers a wrapper of at most 30 MiB). It writes the
  string into a new `<iframe sandbox="allow-scripts">` through the `srcdoc` property and
  ignores every later message.
- **What the relay says** (after the review of its code). Once its listener is in place, it
  posts the constant `"anyplot-relay-ready"` (`READY_MESSAGE`) to `window.parent` with the
  target origin `*`: a signal without content, which tells any parent nothing, and the only
  message it ever sends. The chat's `PREVIEW_RELAY_READY` and the probe's `RELAY_READY` are
  pinned to it by a test.
- **The chat.** A version whose artifacts include `plot.html` gets `.interactive()` on the
  image (next to copy, download and open) and, while the preview is open, `.preview()` to go
  back to the image. Nothing is fetched before the click. The click fetches the shown theme's
  `plot.html` through the authenticated artifact route, the same request as the download, so
  the session waits while the server builds it (`pageBusy`, from JS-4b-1). Then the card
  mounts the relay and posts the page once per mount, on the ready signal from that frame's
  own window, with the target origin `*`, because an opaque origin cannot be named. A page
  that stands in at the relay's URL (an error or challenge page of the edge, a route that
  shadows the path) sends no signal and so never receives the user's page, and the design no
  longer depends on how many `load` events the frame fires; a signal from another window (the
  plot, a sibling) starts nothing. Without the signal within 10 seconds the card shows "could
  not show the interactive plot (relay_unavailable)" instead of a blank frame, and a click on
  a theme mounts a fresh relay. A theme switch while the preview is open fetches that theme's
  page and mounts a new relay; the PNG of a theme the preview showed first renders when the
  image comes back. The pages stay in the card while the preview is open (the download takes
  the shown one instead of building it again) and are dropped when it closes and when the card
  collapses, by a click or because a newer version arrived; a build still under way then ends
  unseen, without `opened_preview`. A failed build shows "could not show the interactive plot
  (<code>)".
- **Sizing without changing the wrapper.** The chat posts the very wrapper the download
  serves. The relay frame has the wrapper's size at scale 1, 1632x932 for a landscape plot and
  1232x1232 for a square one (the canvas at half its pixels plus the 16-pixel margin),
  which the wrapper's first media query just misses, so it shows the plot at scale 1. The
  card scales the whole relay frame to its width with CSS `transform: scale()`, as the
  wrapper scales its own frame, and pointer events reach the plot through both transforms.
  The size comes from the page itself (after the review; at first from the PNG's aspect, so
  a square plot whose PNG had not loaded or had failed was framed as a landscape one):
  `pageFrameSize` in `app/src/lib/agent.ts` reads the first `.frame { width: Npx; height:
  Npx; }` rule of the wrapper's style, which precedes the page, plus `PAGE_MARGIN_PX`, and a
  test pins that pattern and the margin to `render/page.py`'s output, so the frame and the
  wrapper cannot disagree. A page without the rule gets the landscape frame, inside which the
  wrapper scales a square plot to fit.
- **Telemetry.** Opening the preview reports `opened_preview` once per opening, when its
  first page arrived: a new action in the closed set of the agents service, the BFF, the page
  and the BFF mock (pinned equal by the existing test). It is a look, not a keep, so the API's
  usage card and the BigQuery views do not count it, and no view file changes.
- **The root prompt** lists `.interactive()` and `.preview()` among the result card's
  controls for a Chart.js, D3, ECharts or Highcharts plot.
- **The BFF mock** serves the API's own relay (`GET /preview/relay`, built by running
  `python3 api/preview_relay.py`), so the browser check runs the real relay against the mock.
- **The probe** gained a relay mode: `page_probe.mjs relay <relay.json> <plot.html>
  [--hover]`, where `relay.json` is `python3 api/preview_relay.py <origins>`. It serves the
  relay with its real headers on its own origin (`http://127.0.0.1:18732`, the API's part), a
  parent at an allowed origin (`http://localhost:18733`, the chat's part) frames it at scale
  0.75 and, with the chat's side of the handshake, posts the wrapper on the relay's signal,
  after two sibling frames (one at the parent's origin, one at another) posted a page of their
  own. Then the parent posts a second page, which the relay must ignore. A last case frames a
  stand-in at the relay's URL, a 404 page with a listener of its own. The `renderer-image` job
  runs it on the CI probe's Chart.js wrapper with the production origins; the image test runs
  it for all four libraries.
- **The probe's result** (local Docker, `anyplot-renderer:js`): every check passed for
  Chart.js, D3, ECharts and Highcharts. The plot drew in the frame (Chart.js 588,975 painted
  pixels, D3 six shapes, ECharts 383,132 pixels, Highcharts 47 SVG shapes) and a hover changed
  it. The relay, the wrapper and the plot's frame all have the origin `null`. The relay's own
  frame says `sandbox="allow-scripts"` and has no `src`. `top.location`, storage, cookies and
  navigating the wrapper (`parent.location`) or the relay (`parent.parent.location`) are
  `SecurityError`; `window.open` returns `null`; `fetch` is a `TypeError`; the plot frame's
  navigation of itself left `about:srcdoc` and ended on `chrome-error://chromewebdata/`. The
  siblings' pages, a second page from the parent and a page the plot posted into the relay
  were ignored, the relay kept its URL and the parent its location, and no request reached the
  loopback listener, with no popup, download or dialog. The relay's signal was the only message
  it sent; the plot's own ready signal reached the parent (two signals counted there) and
  started no post. A parent at `http://127.0.0.1:18733` could not frame the relay
  (`frame-ancestors`); with that header lifted for the test, the relay still ignored that
  origin's page and took the same page from `http://localhost:18733` (the control). The
  listening 404 page at the relay's URL received nothing, while a post on its load, the chat
  before the handshake, handed it the whole page (220,031 characters for Chart.js, the
  control).
- **Negative controls** (a scratch copy of the relay or of the probe, each one change):
  without the source check, a sibling's page was shown (`siblings_ignored` failed); without the
  origin check, another origin's page was shown (`another_origins_page_ignored`); with
  `frame-ancestors *`, another origin framed it (`frame_ancestors_refuses_another_origin`);
  with `allow-same-origin` on the relay's frame, `relay_frame_sandboxed_to_scripts` failed.
  After the review: without the one-shot flag the parent's second page was shown
  (`second_page_ignored`; before the review no check could fail there); with a second message
  from the relay, `relay_sent_only_the_signal` failed; without the signal, nothing was shown
  (`relay_signalled_ready`, `page_shown`); without the chat's source check, the plot's signal
  counted as the relay's (`ready_from_the_plot_ignored`).
- **In the browser** (2026-10-31, the agent chat against the BFF mock with the API's relay):
  `.interactive()` waits while the run streams; during the build the composer and the other
  theme wait and the card says "building the interactive light plot…"; the relay loads from
  the mock's origin, the plot's frame has the origin `null`, the dark theme shows the dark
  page, and `.preview()` brings back the dark PNG. A hover changed the plot's readout through
  the scaled relay at 1440 pixels (the frame 884 pixels wide, scale 0.54) and at 390 pixels
  (295 pixels wide, scale 0.18, no horizontal scroll), in both site themes, with a console
  free of errors and warnings. On a phone the plot is as small as its PNG in the card; the
  download stays the way to see it full size.
- **Tests.** The relay's route, headers, policy and script (`tests/unit/api/test_preview_relay.py`:
  the local origins equal the BFF's, the site's policy already frames the API, the policy
  equals `page.py`'s, origins that are not plain origins are dropped, the one message is the
  signal after the listener, the chat and the probe wait for the same signal, the CLI's JSON);
  the frame's pattern and margin against the wrapper (`test_page_export.py`); the card
  (`ResultCard.test.tsx`, ten tests: no fetch before the click and the image again on
  `.preview()`, one fetch per theme on a switch, the download of the shown page without a
  second build, the wait while the session is busy, the error, the PNG of a theme the preview
  showed once the image is back, a square frame from the page before the PNG loaded, the
  relay that does not answer, the collapse with a build under way, the newer version) and
  `InteractivePreview.test.tsx` (the post only on the frame's own signal and once, no post on
  a load or on a signal from another window, the timeout, nothing after unmount, the size from
  the page, `pageFrameSize` with a decoy rule inside the page); the image test's relay probe
  for the four libraries.

| Brief | Built | Why |
|---|---|---|
| The site's origins and the BFF's local origins | `settings.cors_origins` filtered to plain origins, plus `http://localhost:*` | a configured value with a space or `;` could end the directive; the local expression is the BFF's regex, pinned by a test |
| Post the download's wrapper, deviate only for a measured reason | the wrapper unchanged; the chat sizes the relay frame from the page | at 1632x932 the wrapper shows scale 1, and a CSS transform scales the frame to any card width |
| Post only into the frame just loaded, once (`load`) | on the relay's ready signal from that frame's window, once per mount (after the review) | a stand-in at the relay's URL never gets the page, and the count of `load` events no longer matters |
| Not in the brief | `relay_unavailable` after 10 seconds without the signal | the relay is a 1 KB static page on an API with a warm instance, so 10 seconds only passes when something else answers |
| Not in the brief | `opened_preview`, not a keep | opening the preview is a look at the plot, not taking it home |
| Not in the brief | `Cache-Control: public, max-age=300` | the page is the same for every caller and holds no data |
| Not in the brief | the relay is served whatever `AGENT_ENABLED` says | it holds nothing, and only the chat frames it |

#### What JS-4c built (2026-10-31): MUI X served for the admin

3f's last library, per question 13 (decision A): MUI X joins `JAVASCRIPT_LIBRARIES` and the
admin deploy's `_LIBRARIES`, so 13 of the 15 catalogue libraries are served. The runtime
class needed no change: it took MUI X as `plot.tsx` since JS-4a. The download and the
in-chat preview needed none either; the page probe needed one fix (below).

- **Readiness.** Of the 323 catalogue MUI X files 311 are eligible: 93 `clean`, 218
  `coupled`, 12 blocked (the 11 map specs and qrcode-basic). By the version a file was
  written for: 196 for MUI X 7.29 (139 `coupled` without a version note, 51 `coupled` with
  `deprecated-api`, 6 blocked) and 127 for 9.16 (93 `clean`, 28 `coupled`, 6 blocked). The
  one file that imports `ChartContainer` by name from the package root is qrcode-basic,
  blocked anyway (`url-literal`); four more files name `ChartContainer` in a comment only.
- **Fixtures.** 60 cases (`*-muix-*`, 780 generated in all) on the ten matrix specs. The
  five files regenerated for 9.16 (box, heatmap, area, violin, pie) are `clean`; the five
  written for 7.29 (scatter, line, bar-grouped, histogram, line-timeseries) are `coupled`
  with the `data-block` hint, and scatter-basic's also with `deprecated-api`. The smoke case
  is `pie-basic-muix-renamed`, not `scatter-basic` (table below). A test pins the split
  (`test_the_muix_files_split_by_the_version_they_were_written_for`).
- **Measured in the renderer image** (`anyplot-renderer:muix`, built from this branch on
  the local `js2-toolchain:dev`, the checkout's `render.mjs` mounted as the local backend
  does; MUI X 9.16.0, `@mui/material` 9.5.0, React 19.3.1), each a page built with the
  JavaScript row and opened in the image's Chromium with a time zone of its own:
  - A `scaleType: "time"` axis is d3's `scaleTime`: in `America/New_York` its ticks sit at
    New York's midnights, five hours off the data's UTC dates, and its tooltip wrote the
    point of 2 January as `Thu Jan 01 2026 19:00:00 GMT-0500 (Eastern Standard Time)`. A
    `"utc"` axis (`scaleUtc`) with
    `valueFormatter: (v) => v.toISOString().slice(0, 10).split("-").reverse().join(".")`
    wrote `02.01.2026` in its ticks and its tooltip in both zones. The default tick count
    (one per 50 pixels) put two ticks on each day of a week of dates, so the formatter wrote
    every date twice; `tickMinStep: 24 * 60 * 60 * 1000` leaves one per day.
  - MUI X's default number format writes `1,240,000` on the axis and `1,300,000` in the
    tooltip; an axis's `valueFormatter` writes both.
  - Which formatter can see `null` (after the pre-PR check, every formatter instrumented to
    record what it got, the pointer swept over a grid of each chart and the keyboard stepped
    through it): the value axis's `valueFormatter` is called only for its ticks, with numbers,
    in a line chart with gaps (20 calls), a horizontal bar chart (`layout="horizontal"`, the
    value axis on x, 31 calls) with gaps, a vertical one, and stacked areas with gaps; MUI X
    makes only the category or date axis a tooltip axis (`axisTooltipGetter`: x for lines,
    the band axis for bars), so the value axis's formatter never runs in a tooltip. The
    tooltip calls the series' own formatter with the gap's `null` (26 times in the line chart,
    16 in the horizontal bars) and the category or date axis's formatter with that axis's own
    value, which is `null` only where the axis's `data` holds one (a `null` category: once at
    its tick, which the static render already meets, and 12 times in the tooltip). So the
    prompt keeps the value axis's formatter unguarded and guards the series' formatter, and
    its rule against `null` categories covers the axis's.
  - A series' own `valueFormatter` is called with the `null` of a gap when the pointer is
    over it: `fmt(null)` threw `TypeError: Cannot read properties of null (reading
    'toFixed')`, and React removed the whole chart (the container empty, no svg left). The
    static render never hovers, so no gate sees it; the guarded form
    `(v) => (v == null ? "" : fmt(v, 1))` swept over all 60 points of the idiom page in New
    York shows 60 tooltips, the two gaps empty, and no error.
  - A `null` in a band axis's `data` is drawn as the category `null`; a scatter point with a
    `null` coordinate is left out without a word; a pie slice whose value is `null` takes
    its palette position and draws nothing, so the next slice gets the third colour.
  - Errors: a `TypeError` in the component names its line through the bundle's source map
    (`page TypeError plot.tsx:9`), and the 7.29 import fails at the bundle
    (`import ImportRefused plot.tsx:7: import "@mui/x-charts/ChartContainer" refused: it is
    not on the image's import allowlist`).
  - The scatter-basic file with only the import renamed to `ChartsContainer` renders, but
    its x tick labels vanish (the axis band's default height, at 14-pixel ticks) and its
    trend line and frame, drawn at pixel positions computed from `margin`, miss the plot
    area: MUI X 9 places `margin` outside the axes' bands.
- **Prompt.** `adapter_javascript.md` adds MUI X's passages to the slots the four
  libraries read, whose rules keep their meaning for those four (the safe-code slot's
  "never `import`, `export` or `require`" now reads "never `require`, and `import` and
  `export` only in MUI X's module"): the TSX module with its imports and one default export
  (`data_statement`, `safe_code`), MUI X 9.16's names for MUI X 7's and the rewrite a `deprecated-api` hint
  asks for, `colors={t.palette}` and an ordinal `colorMap` on a band axis, `skipAnimation`,
  axis bands sized with `height` and `width`, overlays through `useXScale()`, `useYScale()`
  and `useDrawingArea()` from `@mui/x-charts/hooks`, the value axis's `valueFormatter` with
  `fmt`, the guarded series formatter, the `"utc"` axis above, and MUI X's own ways of
  showing `null`. The idiom form (`conftest.JS_PROMPT_IDIOMS["muix"]`: a line chart of the
  dated values with gaps, an overlay through the scales, per-group totals as bars) passes
  both validator profiles and renders 3200x1800 in both themes from the table with missing
  cells and the column name with a quote and a backslash, in 1.2 to 1.3 s a theme.
- **The 7.29 path.** scatter-basic's catalogue file, hand-adapted as the prompt teaches to
  the `scatter-basic-muix-renamed` case (150 rows, `Werbebudget in Tsd. CHF`): the import
  and its uses renamed to `ChartsContainer`, the data block replaced by the placeholder and
  two column constants, the literal axis limits dropped, the trend line, the frame and the
  `r` note drawn in a component through the chart's scales, the axis bands sized, `fmt` on
  both axes and in the guarded series formatter. As a `full_code` plan it applies to the
  normalised file without drift, `_check` lets it render with no finding, and through the
  local Docker backend it passes R1 to R3 in both themes, 3200x1800 (3200x1864 with the
  footer strip), 1.7 s for the two-theme job; the trend line stays inside the plot area and
  every tick label shows.
- **Export and preview.** The probe's MUI X snippet (a `BarChart` of the typed table, its
  escape attempts appended to the module) builds through the local backend's page in 0.85
  to 1.0 s with the container's start: a page of 694 KB, wrapped 722 KB. `check --hover
  --attempts` and the relay mode passed every check in both themes: the chart drew (50 SVG
  shapes), a hover changed the frame, the origin is `null`, `top.location`, storage,
  cookies and the wrapper's and relay's navigation are `SecurityError`, `window.open` is
  `null`, `fetch` a `TypeError`, the self-navigation ends on `chrome-error://chromewebdata/`,
  and the relay showed the page only on its signal. No MUI X fix to the harness, the CSP or
  the frames was needed. The probe needed one: its hover took the first canvas or svg in
  the frame, which in a MUI X page is a legend entry's 10x10 mark; the unchanged probe
  failed `hover_changes_the_frame` there (measured), and it hovers the largest now, which
  the four other libraries pass as before (the image tests, 28 in 30 s).
- **End to end without a model** (2026-10-31, the branch image through the local Docker
  backend): a pasted table of 60 rows, semicolon-separated with decimal commas, with a text
  group, two number columns with a gap each, a timestamp column with `+01:00`,
  microseconds and two gaps, and an integer column past 2^53, through the parser (text,
  datetime, number, integer, integer), MUI X's prompt-idiom form, `_check`, the loader, the
  typed table (3,999 bytes) and the host gates: R1 to R3 pass in both themes, 3200x1864 with
  the footer strip, 1.4 s for the two-theme job; the notes count 60 integers, 58 cut and 58
  converted timestamps. Its `plot.html` downloads at 749 KB in a p50 of 0.85 s (five builds
  a theme) and passes the probe with a hover in both themes (152 SVG shapes).
- **CI.** The renderer image's page step builds, wraps and probes a MUI X page after the
  Chart.js one (`work-page/muix/`); the relay step keeps Chart.js's. The step ran locally
  against the branch image with the checkout's harness mounted, since the local toolchain
  carries JS-2's: Chart.js 0.6 s and 220 KB wrapped, MUI X 0.8 s and 722 KB, both probes
  and the relay passed. The agents image's file check lists `prompts/library/muix.md`.

| Text above (3f) | Built | Why |
|---|---|---|
| MUI X after its regeneration or per question 13 | served now, the 7.29 files `coupled` with `deprecated-api` and the rewrite taught in the prompt | owner decision A of 2026-10-30 |
| One smoke case per library on `scatter-basic` | `pie-basic-muix-renamed` | scatter-basic's MUI X file is written for 7.29 and fails the bundle, and the eval harness's preflight renders the catalogue file of a library's first case unchanged |
| Not in the text | the preflight takes the library's first selected case whose file has no `unavailable-import` finding, else the library's smoke case from the committed fixtures, else the first | the preflight checks the renderer and evaluates no case; a selection starting with scatter-basic stopped before any case, and one of MUI X 7 files alone (`scatter-basic-muix-*`, the matrix run spec by spec for the Vertex quota) could never evaluate the case that tests the `ChartContainer` rewrite (the first version fell back to that file; the pre-PR check found it); no file of another library has the finding, so their preflight is unchanged |
| Not in the text | the page probe hovers the largest canvas or svg | MUI X's legend draws an svg per entry before the chart's own |
| Not in the text | the CI page probe builds MUI X's page too | it is the only React bundle among the five, and the only page an import plugin builds |
| The frontend's library selector | unchanged | it reads the served list from the agents service's status; `plot.tsx` and its `plot.html` existed since JS-4b |
| The BFF mock's JavaScript libraries | unchanged (the four) | its page is a stand-in without a library bundle; a MUI X session there would need `plot.tsx` in four places for no new check |

Found for later (not decided here):

- **The catalogue's own MUI X habits work against the exported page.** 17 catalogue MUI X
  files use `scaleType: "time"` and none `"utc"`, and about 45 of the 159 lines with a
  `valueFormatter` guard against a missing value. Catalogue data has no gaps and the
  harness runs in UTC, so the catalogue renders are right; a user's adapted plot inherits
  the habits unless the adapter applies the prompt's rules, and no gate sees either (the
  render never hovers, and runs in UTC). A validator hint for an unguarded series formatter
  or a `"time"` axis, or a hover sweep of the page in the eval matrix, would catch them.
- **The 139 files written for 7.29 without a version note** render, but MUI X 7's CSS class
  names and legend props in them match nothing in 9.16 (`prompts/library/muix.md`, "MUI X
  v9 API"), so their styling may silently go; the adapter reads that section with the
  library rules, and the eval matrix's MUI X run will show how often it matters.

### 4. plotly and bokeh (through the JavaScript harness's Chromium)

Revised on 2026-10-30 after the second opinion on steps 3 and 4. Two PRs after JS-2: PB-1
(the two-step exec mode) and PB-2 (the profiles, the normaliser rules and the fixtures).

- No browser from plot code: the plot guard replaces `fork_exec` before it is armed,
  so a spawn allowance would reopen it, kaleido's temp profile and choreographer's
  socket pair are refused too, and Selenium talks HTTP to chromedriver.
- No exec after the plot either (both reviewers): arming the guard installs the kernel
  filter against program starts (`install_exec_deny`, with `SECCOMP_FILTER_FLAG_TSYNC`)
  on the harness's process and every later child, so the 2026-10-24 text's "second child
  of the exec mode" cannot start once the plot ran. PB-1 adds a two-step exec mode: the
  harness forks the plot's child before anything is armed; the child arms its guard and
  filter, runs the plot and writes the figure; the parent, never armed, then runs
  `render.mjs --screenshot` under the JavaScript row's limits and environment.
- What the plot writes: the figure as JSON, `fig.write_json` for plotly and
  `bokeh.embed.json_item` for bokeh, from which the harness builds the page with the
  vendored `plotly.min.js` or BokehJS inside `#container` at the canonical canvas (the
  spike of 2026-10-24 and Gemini). That needs no `CODE_BUILDERS` entry for bokeh's Jinja
  templates, which would give any path to `jinja2.Template` an `exec` under the guard,
  puts no model-written HTML in front of the unfiltered Chromium, and fixes the canvas
  that the catalogue's bokeh files set to 4800x2700, past R2's pixel cap. bokeh's
  `CustomJS` is refused by the validator. PB-2 measures the route on the catalogue
  before it writes the normaliser rules.
- plotly: `_plotly_utils/basevalidators.py: __init__` gets a `CODE_BUILDERS` entry after
  a review of the validator classes it builds; MathJax off.
- Deviation to name for the owner (question 10): for these two libraries the exported
  code is not byte for byte the run form (agent-network.md, "Fencing and exported
  code"): the export keeps the catalogue's own save block and runs unchanged on the
  user's machine; the run form carries the sandbox's JSON save instead.
- Fixtures, matrix, docs.

#### What PB-1 built (2026-10-31): the two-step exec mode, not served yet

The renderer's plotly and bokeh rows render in two steps; `AGENT_LIBRARIES`,
`RUNTIME_LIBRARIES`, the runtime registry and the admin deploy's `_LIBRARIES` are
unchanged, so the agents service sends no plotly or bokeh job before PB-2.

- **Harness, figure mode** (`harness.py --figure <package> plot.py -- <screenshot
  command>`). The start line, then `CPU` and `FSIZE` limits for both steps, then
  `os.fork` before anything is armed. The child sets `RLIMIT_AS` and `RLIMIT_NPROC`, arms
  `PlotGuard` with the kernel filter first (`ANYPLOT_DENY_EXEC=required` holds as in plot
  mode), runs the plot, which may write nothing but `plot-<theme>.json`, and ends with
  `os._exit`, so no `atexit` callback and no thread of the plot outlives it. The parent is
  never armed: it checks the figure (a regular file opened without following a link, not
  empty, at most `FIGURE_MAX_BYTES`, 16 MiB, the wire's cap for a typed table) and starts
  the screenshot command, the JavaScript row's harness with `--figure=plot-<theme>.json`
  appended, in the sandbox's environment without the plot step's variables
  (`ANYPLOT_DENY_EXEC`, `ANYPLOT_RLIMIT_AS_MB`, `ANYPLOT_RLIMIT_NPROC`) and with
  `ANYPLOT_FIGURE_PACKAGE`, the package's directory as the harness's own interpreter would
  import it (`importlib.util.find_spec`, which runs no package code). The child reports
  through a pipe opened before the fork. Its first line is the harness's own and comes
  before any plot code, so the plot cannot forge it: `armed <state>` after the arming, or
  `refused <state>` when a required filter is not in place and the plot never runs. Only
  after `refused` is `EXEC_DENY_EXIT` (3) the harness's `ExecDenyUnavailable`; a plot that
  ran and ended with the same code (`sys.exit(3)`) fails as a `plot` error like any other
  code. The error record after the first line is advisory. The end line carries both
  steps' totals, the plot step's `exec_deny`, and `steps` with each step's peak, CPU and
  wall time.
- **The final error line** of JS-2 for the plot step as well: `plot <Class> plot.py:<line>`
  for an exception (its traceback before it, as the interpreter prints it), `figure`
  (`NoFigure`, `FigureError`, `FigureTooLarge`), `crash PlotCrashed` for a signal and
  `harness` (`UsageError`, `PackageMissing`, `ExecDenyUnavailable`, `SpawnError`); the
  screenshot step's own line otherwise. The exit code is the failed step's.
- **`render.mjs --library=<plotly|bokeh> --figure=<file>`**, sandbox mode only. The figure
  is read without following a link, capped again, parsed and shape-checked in Node, and
  carried as data: a `type="application/json"` element with `<`, U+2028 and U+2029
  escaped, parsed in the page and handed to `Plotly.newPlot` (`staticPlot`,
  `typesetMath: false`) or `Bokeh.embed.embed_item`. The bundles are the packages' own:
  plotly's `package_data/plotly.min.js` (plotly.js 4.1.1 in plotly 7.1.0) and bokeh's
  `bokeh.min.js` with its WebGL, widget and table bundles (bokeh 3.10.1; its MathJax bundle
  is not loaded). The page is sandbox mode's, routes, console guard and heap cap included,
  under a stricter policy: scripts by a nonce of the page instead of `'unsafe-inline'`.
- **The canvas.** The figure's own size in CSS pixels (plotly's layout width and height,
  bokeh's root width and height; a bokeh layout, which has none, is drawn once at scale 1
  and measured) picks the orientation, landscape at 4:3 and wider, and the device scale
  makes the box exactly 3200 x 1800 or 2400 x 2400: plotly 800 x 450 draws at scale 4,
  1600 x 900 at 2, bokeh 4800 x 2700 at 2/3. A figure narrower than its box is centred on
  the page's background; a plotly figure without a size gets 1600 x 900, and one that
  names a single side keeps it and gets the other at 16:9 (width 1200 draws at 1200 x
  675); a side outside 320 to 6400, the derived one included, is `figure FigureError`. A screenshot of any other size fails as `harness
  CanvasError` instead of leaving a PNG.
- **plotly's `CODE_BUILDERS` entry** is `_plotly_utils/basevalidators.py:
  build_validator`: `InfoArrayValidator.__init__` calls it for each item of an info-array
  property (`xaxis.range`, a `domain`), and it evaluates the item's validator class name,
  `datatype.title().replace("_", "") + "Validator"`. plotly's schema names five types
  (`angle`, `any`, `enumerated`, `number`, `subplotid`); a plot that calls the builder
  itself gets title-cased text without underscores, which reaches only capitalised names
  (the module's 23 validator classes, the builtins' classes and constants) and runs under
  the guard. Every plotly plot that sets an axis range needs it.
- **Renderer.** `RuntimeCommand.figure` names the package of a two-step row; plotly's and
  bokeh's rows run `NODE_BINARY render.mjs --library=<library>` as the screenshot command
  with `JS_ENV`, and keep the Python limits and the filter for the plot step.
  `executor.build_argv` passes `--figure <library> plot.py -- <argv>`, `sandbox_env` a
  Python row's settings plus `JS_ENV`. The image installs the `lib-plotly` and `lib-bokeh`
  extras without their export stacks (kaleido, choreographer, logistro, Selenium,
  webdriver-manager, trio and the WebSocket clients) and trims what neither step reads
  (plotly's JupyterLab and widget bundles, bokeh's TypeScript compiler, ES module sources
  and unminified bundles): plotly and bokeh take 68 MB, and the renderer image grows from
  4,451 to 4,520 MB (+69 MB, against main on the same toolchain image).

Measured in local Docker on the developer machine (32 CPUs, WSL 2, kernel 6.18), as the CI
step runs it: `--network none --read-only`, `--cpus 2 --memory 4g`, an unprivileged user,
the row's environment, `RLIMIT_AS` 1 GiB and `ANYPLOT_DENY_EXEC=required`; a hand-written
figure per library and the catalogue's `scatter-basic`, `bar-basic`, `line-basic` and
`heatmap-basic` with the save block swapped by hand for the JSON save (and Selenium's
imports dropped), each in both themes:

| Measurement | Result |
|---|---|
| Rendered | 20 of 20, every PNG 3200 x 1800 or 2400 x 2400 (the heatmaps), `exec_deny` `on` in every plot step |
| Wall time, container start included | plotly 1.93 to 2.35 s, bokeh 1.60 to 1.85 s |
| Plot step | 0.14 to 0.54 s wall, 0.14 to 0.53 s CPU, 53 to 156 MB peak (bokeh's heatmap the largest) |
| Screenshot step | plotly 1.40 to 1.47 s wall, 0.74 to 0.77 s CPU, 186 to 193 MB for its largest process; bokeh 0.91 to 0.97 s, 0.68 to 0.73 s, 166 to 170 MB |
| The whole container (`memory.peak`) | plotly 399 to 416 MiB, bokeh 518 to 561 MiB |
| Under gVisor (`runsc-ptrace`, release-20261026.0), 12 of the renders | all 12 rendered, `exec_deny` `on`: wall 4.65 to 5.78 s, the plot step 0.40 to 1.15 s, the screenshot step 3.68 to 4.63 s; the same image's Chart.js render takes 3.68 s there and 1.06 s under runc |
| Against the published catalogue PNGs (light) | bokeh `bar-basic` and `heatmap-basic` a mean difference of 0.01 of 255 (no pixel off by more than 40); plotly `bar-basic` 0.54 %, `line-basic` 0.11 %, `heatmap-basic` 1.09 % and `scatter-basic` 0.68 % of the pixels off by more than 40; bokeh `scatter-basic` 0.67 % and `line-basic` 2.03 %. The two largest are drift between the files and their published PNGs (the published bokeh `line-basic` has a band and an annotation the file does not draw; the published plotly `scatter-basic` has axis lines its `showline: False` turns off) |
| Canvas against the catalogue's | plotly `line-basic` (1600 x 900 at scale 3) and bokeh `scatter-basic` and `line-basic` (4800 x 2700) publish 4800 x 2700 PNGs; this route draws the same layouts at 3200 x 1800 |
| Fonts | the page resolves the files' Helvetica and Arial to Liberation Sans through the JavaScript row's fontconfig file; plotly's `Inter` first in a stack is not in the image and falls through to it |

Also found:

- **No WebGL in the headless shell.** plotly draws a notice in place of a WebGL trace
  ("WebGL is not supported by your browser"), so the page now fails such a render as
  `draw NoWebGL` instead of passing with the notice for a plot. In the catalogue that is
  `Scattergl` (4 files), `Scatter3d` (5), `Surface` (2), `Mesh3d`, `Parcoords` and
  `Densitymap` (1 each) and `Scattermap` (8, which also needs map tiles); plotly express
  switches `scatter` to WebGL above 1,000 points. bokeh's `output_backend="webgl"` falls
  back to its canvas (no catalogue file uses it). WebGL would need a software renderer
  in Chromium (`--enable-unsafe-swiftshader`), an owner decision for PB-2.
- **Markup in a figure.** bokeh's `Div` renders its HTML into the page: under sandbox
  mode's `script-src 'unsafe-inline'` an `<img onerror>` in it ran (its fetch then stopped
  at the policy). The figure page admits scripts by its nonce alone, so the handler does
  not run; `CustomJS` and `CustomJSTickFormatter` cannot compile without
  `'unsafe-eval'` (a render with the formatter fails as `page EvalError`). Markup in a
  plotly title stays text.
- kaleido's `write_image` is refused at choreographer's socket pair (`socket.__new__`) and
  bokeh's `export_png` at its temporary HTML file (`open`), both under the guard on a
  developer machine where both stacks are installed; the image installs neither.
- **Fixed on the way: user code while a guard is paused.** Every place the harness pauses
  a guard was checked for code the snippet or plot defined. Two ran there and wrote files
  the armed guard refuses: data mode's `print_snippet_error` read `exc.__traceback__`,
  which the snippet's exception class can make a property, and plot mode's
  `writes_elsewhere` ran `realpath` on a path that subclasses `str`, whose `split` and
  `startswith` it called. The traceback is now read through `BaseException`'s own
  descriptor, the path is copied into an exact `str` while the guard is armed, and the
  frame-name comparisons take exact `str` only (`plain_name`); regression tests in
  `test_harness_guard.py` and `test_figure_mode.py` write a marker on the old harness.
- **Guard hardening found on the way** (Fable's review of PB-1 rated F6 high, Flash's
  review added the descriptor flags; built 2026-10-31):
  - F6, import trust. The plot guard trusted any code the import machinery ran, and the
    frames it read. A plot drove that machinery itself and supplied the module body,
    which walked the frames to the guard and disarmed it. Three rules now hold:
    an import reads code only from the install (`install_prefixes`: the stdlib with
    `lib-dynload` and its zip, the site packages, from `sysconfig` before arming), refused
    at the read of a file loader's `get_data` or zipimport's archive
    (`IMPORT_CODE_READERS`), whoever drives the loader; an import earns trust only when
    its first import frame is the interpreter's `_call_with_frames_removed` under the
    `exec_module` or `create_module` of exactly `SourceFileLoader`,
    `SourcelessFileLoader`, `ExtensionFileLoader` or `zipimporter` (instance state
    `name` and `path`, or `archive` and `prefix`, nothing else, the file in the install,
    the class as it was before arming),
    under `BuiltinImporter`, or is `FrozenImporter.exec_module` (`ImportMachinery`);
    and an extension module loads only from the install, refused at the `import` event
    that `_imp.create_dynamic` raises with its file before the library's native code runs.
  - Native loads: an `ExtensionFileLoader` on a plot-written file raises that `import`
    event (measured under runc and gVisor); `ctypes.CDLL` raises `ctypes.dlopen`, refused
    already; cffi's `FFI().dlopen(path)` raises no audit event at all, so no guard rule
    can see it (an open question for the owner: a `noexec` run directory, as Docker's
    `tmpfs` already is; the validator refuses `cffi`).
  - Descriptor flags: `fcntl.*` and `os.set_blocking` (no event, replaced) are refused in
    plot mode, figure mode's plot step included, because stdout and stderr are one open
    file description across the fork.
  - The validator (F7 and the walk): a walk over every public attribute of the admitted
    modules (1,331 modules in the image) found import machinery the validator admitted:
    matplotlib's bundled `dateutil.zoneinfo.get_data` (`pkgutil.get_data`, a read of any
    file relative to a package it imports by name) and `dateutil.tz.six.spec_from_loader`,
    and the `types` module's `new_class` (a class from a callable body, where class
    statements are refused), `ModuleType` and `LambdaType`. `dateutil` and `six` are
    banned as module re-exports, `get_data`, the spec builders, `new_class`,
    `prepare_class` and `ModuleType` as helpers, `LambdaType` with `FunctionType`; the
    walk is now a test, and of the image's 222 machinery paths none is admitted.
  - Measured: every catalogue file of the six served Python libraries (1,946) rendered
    in the renderer image with the previous harness and with this one, 12 at a time:
    1,771 render under both, 175 fail under both (the guard's earlier refusals, out of
    memory), no file changes outcome, and no run called `fcntl` or `os.set_blocking`. The
    ten plotly and bokeh inputs above render as before under runc, two of them under
    gVisor. The F6 routes (stock source, bytecode and zip loaders on a plot-written file,
    the loader class of an admitted module, Fable's loader of its own, an instance that
    overrides `get_code`, `exec` as a path hook, an extension module written by the plot)
    each wrote a marker through the previous harness and are refused now, in plot and
    figure mode; they are tests in `test_harness_guard.py`.
  - Known limits of the in-process layer. The guard shares the interpreter with the
    plot, so it is defense in depth behind the validator, the kernel's exec filter
    (seccomp, on every thread and inherited by every child), the resource limits and the
    per-job gVisor sandbox (spikes S and S2: no egress, as the metadata server, DNS and
    TCP all fail; none of the service's environment or tokens; a read-only root
    filesystem without `--write`; no view of the sibling sandboxes; one job's lifetime).
    The harness's module docstring states the same. Two limits are known and stay: F8,
    plot code that reaches the harness's own objects through state the interpreter
    shares can change the guard's decisions, which no audit event sees; and cffi's
    `dlopen`, which raises no audit event (above). The validator refuses what both need
    (`cffi`, `sys` and every dunder name), and no structural change to the harness is
    planned for F8. A class attribute changes without an audit event as well, so the
    stock loaders' classes are read before arming, and a loader whose class no longer
    resolves every attribute to the same object earns no trust (`ImportMachinery.intact`:
    the same method resolution order, each class's own entries unchanged but the two
    Python 3.14 adds when annotations are first read): Fable's review of the fix measured
    a `get_code` set on `SourceFileLoader` itself, with a clean instance on a stdlib file,
    running the plot's module body with an import's trust, and a `source_to_code` set
    there did the same. Both wrote the marker through the first fix and are refused now;
    the 1,946 catalogue files render with the class check exactly as without it (1,771
    render, 175 fail, the same refusals).
    Deeper patches of the machinery (the module globals of `_frozen_importlib_external`,
    `_bootstrap._call_with_frames_removed`, `builtins.compile`) are F8's kind and
    knowingly out of the in-process layer's reach; the validator, which refuses every
    name that reaches them, is the barrier there.
- **A two-step row needs Node.** `GET /status` still lists the toolchains per language,
  but a render or page job is checked against its row (`executor.serves`): the language's
  toolchain and the row's own binaries, so a plotly or bokeh job on a renderer without
  Node is `503 runtime_unavailable` before any sandbox starts, not exit 127 with a
  `harness SpawnError` line. Every renderer image has Node (the toolchain base).

**Tests**: `tests/unit/agents/renderer/test_figure_mode.py` (92 cases without plotly or
bokeh: the package's lookup and the screenshot command stood in): fork before arm (both
steps children of one harness, the plot step one seccomp filter and the no-new-privileges
bit more than the harness, the screenshot step none more and able to start a program),
the limits and variables per step, a refused spawn, fork, exec, socket pair and PNG write,
the kernel's refusal when the audit hook is blind to `os.exec`, nothing of the plot after
it (`atexit`, a thread), the step-1 failures and their lines, a signal death, the cap at
one byte over, a filter that is not in place, a plot that exits with the filter's code
itself, the screenshot step's own failure and a command that cannot start, the rows, the
argv, the environment and Node's check, and the executor's one timeout over either step
(the launcher's process group killed with both children). The fork, the arming and the
kernel filter run only in those subprocess cases, which coverage does not see; in-process
cases, with `os.fork`, `os._exit`, the guard and the plot stood in, cover the parent's
verdict, the child's codes and report, the error record, the screenshot step's start and
the steps' order. `tests/unit/automation/test_js_render_figure.py` (41 cases, skipped
without Node, the lock's packages, the browser and plotly): the canvas rule, a plotly
figure with one side, a measured bokeh layout, markup
and handlers, `CustomJS`, WebGL, the figure checks, the usage errors, and the whole two
steps through the Python harness in both themes for both libraries. `ci-image.yml`
renders a plotly and a bokeh figure through the rows in the built image and checks that
the export stacks are absent.

| Text above | Built | Why |
|---|---|---|
| `render.mjs --screenshot` | `render.mjs --library=<plotly\|bokeh> --figure=<file>`, refused without sandbox mode | the input is the figure; the page's rules must apply to it |
| `_plotly_utils/basevalidators.py: __init__` | `_plotly_utils/basevalidators.py: build_validator` | the `eval` sits in the static method that `InfoArrayValidator.__init__` calls (plotly 7.1.0, the lock's version); the guard judges the frame that calls `eval` |
| The page built inside `#container` at the canonical canvas | the figure's own CSS size, the device scale making the canvas | the catalogue's plotly files write 800 x 450 at scale 4 (146), 1600 x 900 at 3 (116), 600 x 600 at 4 (43) and 1200 x 1200 at 3 (9), and its bokeh files pass `width=4800` (113), `3200` (121) and `2400` (35): one CSS size would change every other file's type size against its plot |
| The vendored `plotly.min.js` or BokehJS | the installed packages' own bundles, BokehJS's WebGL, widget and table bundles included, found by the harness | the page's version is the plot's; a model of another bundle would not draw |
| Sandbox mode's page rules | the same with a nonce for scripts instead of `'unsafe-inline'` (tighter) | a bokeh `Div`'s handler ran under `'unsafe-inline'` (measured) |
| The `lib-plotly` and `lib-bokeh` extras | without the export stacks, and trimmed | they start browsers, which the guard refuses; 27 MB of Selenium drivers; the image grows by 69 MB |

#### What PB-2a built (2026-10-31): plotly and bokeh served for the admin

plotly and bokeh join `PYTHON_LIBRARIES` and the admin deploy's `_LIBRARIES`, rendered by
PB-1's figure mode: all 15 catalogue libraries are served. The interactive `plot.html` and
`.interactive()` for the two (question 10's second half) are PB-2b; WebGL is PB-2c.

- **The figure save** (`agents/anyplot/code/figure.py`). The run form ends on one pinned
  statement that writes the figure as `f"plot-{THEME}.json"`:
  `fig.update_layout(width=800, height=450).write_json(f"plot-{THEME}.json")` for plotly
  (the size is the catalogue's `write_image(width=, height=)`, moved into the figure, so the
  figure mode's device scale draws the catalogue's layout: 800 x 450 at 4, 1600 x 900 at 2,
  600 x 600 at 4), and `with open(f"plot-{THEME}.json", "w", encoding="utf-8") as
  figure_file: json.dump(json_item(p), figure_file)` for bokeh (the figure keeps its own
  `width` and `height`). Nothing in either but the plot's name is free. The save rules of
  both libraries name no save call (`SaveRule.figure`), so `SAVE_NAMES`, and with it every
  other profile, is unchanged; the regions protect the pinned statement as the final save.
- **The export** (question 10, decided): `figure.export_form` swaps the statement back for
  the library's normal save, `fig.write_image(f"plot-{THEME}.png", width=800, height=450,
  scale=4)` and `fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")`, or
  `export_png(p, filename=...)`, `output_file(...)` and `save(p)` with bokeh's imports
  swapped (`import json` and `json_item` out, `from bokeh.io import export_png, output_file,
  save` in). plotly's scale is the figure mode's, so the exported PNG has the chat's pixels.
  Everything else stays the run form byte for byte; the export of an export is the export.
- **Normaliser** (step 7 of `code/normalise.py`, after the guard steps so a guard's hoisted
  imports are seen). plotly: the last module-level theme-PNG `write_image` becomes the
  figure save (318 of 325 files; the other 7 save a single-theme `"plot.png"`), every
  `write_image`, `write_html` and `show()` above it goes, every statement after it goes (the
  HTML save, and a range slider in 4 files that only the HTML showed), and an unread
  `kaleido`, `plotly.io` or `plotly.offline` import goes; plotly express's `scatter`, `line`,
  `scatter_polar`, `line_polar` and `ecdf` get `render_mode="svg"` unless they name one (they
  switch to WebGL above 1,000 points). bokeh: the first module-level `save`, `export_png` or
  `show` of a named plot (through `bokeh.io`, `bokeh.plotting`, an import alias or a
  `save = bokeh.io.save` assignment) becomes the figure save and everything after it goes,
  the catalogue's screenshot block (306 files open Selenium's Chrome and crop the PNG with
  PIL); `output_file` above it, unread aliases of the saving names and unread imports of the
  block's modules go, and `import json` and `from bokeh.embed import json_item` are added in
  sorted order (321 of 325 files; 4 save no named plot at module level). The sys.path step
  runs once more after it (the save block was the last reader of `html_path = Path(...)`).
  For both, `"<literal>".format(<arguments>)` becomes the f-string it stands for (19 bokeh
  files build hex colours that way; 9 with a `*` argument stay). The normalised output of
  the other 13 libraries is unchanged: their normalised code, SECURITY findings and
  readiness are identical to `origin/main` on all 4,213 catalogue files.
- **Validator.** plotly admits `plotly.graph_objects` (and `graph_objs`), `plotly.express`,
  `plotly.subplots`, `plotly.colors` and `plotly.figure_factory`, never the package root, so
  `plotly.io`, `plotly.offline` and `plotly.tools` stay out of reach; `plotly.express.data`
  (bundled CSVs) is banned on its module. bokeh admits `bokeh.plotting`, `bokeh.models`,
  `bokeh.layouts`, `bokeh.palettes`, `bokeh.transform`, `bokeh.colors`, `bokeh.util.hex`,
  `bokeh.core.properties` and `bokeh.embed.json_item`; its `callbacks`, `css`, `dom`,
  `map_plots` and `tiles` submodules and `plotting.gmap` are banned on their modules.
  `LIBRARY_BANS` holds plotly's `write_image`, `write_html`, `to_image`,
  `full_figure_for_development`, the widget, the bundle getter, the map token,
  `create_county_choropleth`, `optional_imports` and `get_module`, and bokeh's JavaScript
  (every `CustomJS...` model, `CustomAction`, `OpenURL`, `HTMLTemplateFormatter`, the `js_*`
  callbacks), its markup models (`Div`, `Paragraph`, `PreText`, the HTML labels and title,
  dialogs, menus), its URL fetchers (the remote data sources, `ImageURL`, `image_url`,
  imported stylesheets, tile sources, `add_tile`, Google Maps) and the writers
  `bokeh.plotting` re-exports. bokeh's `tooltips` are `(label, value)` pairs, never a string,
  which bokeh renders as an HTML template (`banned-keyword`). `_lift_figure_save` takes the
  pinned statement out of the scanned tree in exactly its shape (and bokeh's `import json`
  when nothing else reads the name); a missing or second save, a plot name bound by an
  import, and a binding of `json`, `json_item` or `open` are findings. The import-machinery
  walk (`test_no_admitted_module_hands_out_import_machinery`) passes with both surfaces
  admitted, and `REVIEWED_SUBMODULES` pins their public submodules.
- **Readiness.** A plotly WebGL trace (`Scattergl`, `Scatter3d`, `Surface`, `Mesh3d`,
  `Parcoords`, `Splom`, the map traces, plotly express functions that make one,
  `render_mode="webgl"`, a dict trace of such a `type`) blocks as `webgl`. The coupling scan
  flags plotly's literal `range`, `tickvals` and `dtick` (keywords and dict keys) and shapes
  and annotations at data coordinates, and bokeh's literal `x_range`/`y_range`, `Range1d`,
  `FixedTicker`, range stores, `Span`, `Label`, `BoxAnnotation`, `Arrow` and a colour
  mapper's `low`/`high`; the other libraries' scan is unchanged. The canvas is never a
  note: the figure mode draws every figure on its canvas or fails.
- **Runtime.** `PythonRuntime` runs plotly and bokeh with the row's two-step argv
  (`--figure <library> plot.py -- <screenshot command>`, `executor.build_argv`'s) and
  environment (`sandbox_env` key for key, pinned by the existing row test),
  `review_texts` on (no probe), `figure_error_summary` for the figure mode's final error
  line (a plot exception's class and line from its traceback, every other kind a fixed text,
  `draw NoWebGL` naming the 2D trace instead), and the export above. The local Docker
  backend mounts the checkout's `render.mjs` for a figure row too.
- **Harness.** A plotly figure with a WebGL trace type fails as `draw NoWebGL` before the
  page is drawn (`render.mjs`, `PLOTLY_WEBGL_TYPES`): a 3D scene draws no notice in the
  headless shell, which hands out a WebGL context, but nothing but its colour bar, and the
  host gates passed that render (scatter-3d, measured). No CSP, page or frame change.
- **Prompt.** plotly and bokeh read a section of their own right after the Python adapter
  prompt (`prompts/adapter_plotly.md`, `adapter_bokeh.md`, `policy.LIBRARY_PROMPTS`), which
  replaces the matplotlib conventions for them; the Python prompt's pinned SHA-256 and every
  other library's instruction are unchanged. Measured in the renderer image: the save and its
  size, the theme tokens on the figure, Helvetica and Arial (Liberation Sans in the image),
  rows a mark needs dropped before a statistic, plotly drawing a tz-aware timestamp's clock
  time as given (07:00 for `+01:00`), so the idiom converts to UTC, bokeh's datetime axis in
  UTC, plotly's `separators` writing the plot language's marks in every d3 format, BokehJS's
  formatters writing English marks whatever their `language` (`NumeralTickFormatter(format=
  "0,0", language="de")` wrote `2,800,000`), so bokeh's idiom puts the ticks on fixed values
  with Python-written labels, `render_mode="svg"`, and no WebGL. Each library's idiom form
  (`conftest.FIGURE_PROMPT_IDIOMS`) passes both validator profiles and renders 3200 x 1800
  in both themes from a table with missing dates, numbers, an integer and a text cell, a
  `+01:00` timestamp and a column name with a quote and a backslash
  (`test_profile_python_figure_image.py`). The scope judge's `other_library` example "Gibt es
  das auch in Plotly?" became Excel, and root.md says how the exported `plot.py` writes its
  PNG.
- **Fixtures.** 120 cases (`*-plotly-*`, `*-bokeh-*`, 900 generated in all) and the smoke
  cases `scatter-basic-plotly-renamed` and `scatter-basic-bokeh-renamed` (25 in all). All
  ten plotly files are `coupled`, nine bokeh files `coupled` and `bar-grouped` `clean`;
  bokeh's `histogram-basic` is eligible through the `.format` rewrite.
- **Deploy.** The renderer's candidate smoke renders a plotly figure from `data.csv` with an
  axis range (plotly's `build_validator` under the guard) through both steps as a gate, with
  the Chart.js render's two tries. The agents image's CI scans a plotly and a bokeh file and
  checks their export; the image's build check reads both new prompt files.

Readiness of the catalogue (`agents.evals.eligibility`, 2026-10-31):

| Library | Files | Eligible | Clean | Coupled | Blocked |
|---|---|---|---|---|---|
| plotly | 325 | 273 (84.0 %) | 12 | 261 | 52 |
| bokeh | 325 | 253 (77.8 %) | 11 | 242 | 72 |

Blocked, first cause per file: plotly 13 map specs, 10 WebGL traces (15 files carry a
`webgl` reason, 4 of them map specs and 1 blocked for its `THEME` too), 10 sklearn
datasets, 6 single-theme `"plot.png"` saves, 6 `sys` imports a guard shape leaves, 3
strings over 200 characters, 4 one-offs (seaborn, qrcode, matplotlib, a second `THEME`);
bokeh 13 map specs, 13 old-form files without a `THEME` block, 10 `CustomJS` models
(7 `CustomJSTickFormatter`), 8 sklearn datasets, 8 `.format` with a `*` argument, 4 HTML
tooltip templates, 2 `Div`, and 14 one-offs (`time`, `base64`, `bokeh` root, matplotlib,
contourpy and qrcode imports, dunders, long strings, `__import__`, `add_tile`).

**The catalogue sweep** (2026-10-31, `anyplot-renderer:figure`, built from this branch on
`pb1-toolchain:dev`; every catalogue file normalised and rendered through the local Docker
backend's figure mode in both themes, ten jobs at a time on 32 CPUs, the checkout's
harnesses mounted):

| Measurement | plotly | bokeh |
|---|---|---|
| Eligible files that render on target in both themes | 254 of 273 (93.0 %) | 246 of 253 (97.2 %) |
| Failures among them | 19, all `ZeroDivisionError`: the code divides by the length of the emptied catalogue title | 7, the same |
| Canvas | 452 PNGs 3200 x 1800, 96 2400 x 2400, no other size | 472 and 108 |
| Wall time per theme, container start included, under the sweep's load | p50 4.0 s, p95 5.1 s, max 11.0 s | p50 3.7 s, p95 5.5 s, max 21.1 s |
| Blocked files | 20 of 52 render; 15 fail `draw NoWebGL` (exactly the 15 with a `webgl` reason), 7 `page Error` (map specs: no topojson offline), 7 `RuntimeError` (the files the normaliser leaves on `write_image`, whose kaleido the image does not install), 3 others | 44 of 72 render; 14 `NameError` (no `THEME`), 6 `page EvalError` (`CustomJS`), 5 `ModuleNotFoundError` (Selenium), 1 timeout, 2 others |

**End to end without a model** (2026-10-31, the same image through the local Docker
backend): 60 pasted rows, semicolon-separated with decimal commas, with a text group, two
number columns with gaps, an integer column with a gap, a timestamp column with `+01:00`,
microseconds and two gaps, and an integer column past 2^53, through the parser (datetime,
number, number, integer, text, integer), each library's idiom form, `pipeline._check` (no
finding), the Python loader, the figure mode and the host gates: R1 to R3 pass in both
themes at 3200 x 1800, 2.8 s for plotly's two-theme job and 2.7 s for bokeh's; the export
ends on the normal save.

| Text above | Built | Why |
|---|---|---|
| PB-2: the profiles, the normaliser rules and the fixtures | PB-2a serves both; the interactive page (PB-2b) and WebGL (PB-2c) follow | owner decisions of 2026-10-31 |
| bokeh's JSON save through `json_item` | the pinned `with open(...)` block, lifted out of the scan in exactly that shape | no admitted call writes a file; `open`, `json` and `.dump` stay refused everywhere else, and the renderer's plot step may write that one file alone |
| plotly's `fig.write_json` | `fig.update_layout(width=W, height=H).write_json(...)`, one protected statement | the size must reach the figure for the device scale, and the adapter must not be able to drop it |
| Not in the text | every statement after the save goes (plotly's range sliders, bokeh's screenshot block) | the PNG is the figure as the save saw it; the save stays the last statement the prompt names |
| Not in the text | `.format` to an f-string for plotly and bokeh | 19 bokeh files; the same rule would unlock pygal's and lets-plot's hex colours, which is the owner's call (it changes served libraries) |
| Not in the text | a WebGL trace fails before the page draws | a 3D scene drew a blank plot with its colour bar, which passed R1 to R3 |
| Not in the text | HTML tooltip templates and markup models refused for bokeh | the exported HTML runs them in the user's browser without a policy |

Found for later (not decided here):

- **The emptied title divides by zero** in 19 plotly and 7 bokeh eligible files (and 13
  pygal, 10 lets-plot, 54 matplotlib as 1c counted): code that sizes the title by
  `len(title)`. The adapter writes a title and fixes it, but a non-empty placeholder in the
  normaliser would spare the repair; it changes every library's normalised form.
- **The `.format` rewrite for every library**: 6 pygal and 4 lets-plot files are blocked
  for the same hex-colour `.format`.
- **bokeh's 13 old-form files** without a `THEME` block and plotly's 6 single-theme saves
  stay blocked until their regeneration.
- **PB-2b's seams**: `schemas.PAGE_CODE_ARTIFACTS` keys the page artifact by the code
  file, so plotly and bokeh (`plot.py`) need it by library; `render.mjs` refuses
  `ANYPLOT_PAGE_ONLY` with `--figure`; the export's HTML save is the library's own and
  carries no script policy, which the validator's bokeh rules guard.
- **PB-2c**: the 10 files blocked for WebGL alone (and the users' 3D plots) wait for a
  software renderer; the `webgl` readiness reason and `PLOTLY_WEBGL_TYPES` go with it.

### 5. Julia: Makie

Revised on 2026-10-29 after the second opinion on step 5 (Gemini 4 Argon and Fable; the
section at the end) and the owner's decisions of the same day, which the text below
carries. Julia is the toolchain image's next stage and the second user of the preload
filter; it needs no other image or filter design. Four PRs: J1 (the toolchain stage, the
command row, the build and deploy changes; built, see "What J1 built"), the measurement
stage, J2a (the Julia code profile) and J2b (the runtime, the prompts, the fixtures and the
admin deploy). Makie is not served before J2b: J1 leaves `AGENT_LIBRARIES`,
`RUNTIME_LIBRARIES` and the admin deploy's `_LIBRARIES` (`agents/cloudbuild.yaml`) as they
are; the renderer can render a Makie job, and the agents service sends none.

#### 5a. The toolchain stage (J1)

- A `julia` stage in `agents/renderer/toolchain.Dockerfile` (2a), `FROM base` like R's, so
  a Julia change never rebuilds R's packages and an R change never reruns Julia's
  precompile. It downloads the official Julia 1.13.2 build for generic Linux on x86-64
  (the version `Manifest.toml` was resolved with) and checks it against the SHA-256 that
  julialang publishes next to its downloads
  (`https://julialang-s3.julialang.org/bin/checksums/julia-1.13.2.sha256`), under
  `/opt/julia-1.13.2`. Julia brings its own libraries and CairoMakie's JLL artifacts theirs
  (FreeType, HarfBuzz, Cairo, Fontconfig), so the base distribution does not change a
  render.
- The project is the repository's `Project.toml` and `Manifest.toml`, the pipeline's own
  (`.github/actions/setup-julia`), under `/opt/julia-project`, instantiated and
  precompiled (`Pkg.precompile(strict = true)`) into `/opt/julia-depot` with
  `JULIA_CPU_TARGET="generic;sandybridge,-xsaveopt,clone_all;haswell,-rdrnd,base(1)"`;
  the registries go after the precompile, because nothing at run time resolves a package.
  A test pins the Dockerfile's version and CPU target to the Manifest's `julia_version`
  and to the row's values.
- The final stage copies the install, the project and the depot after R's lines, checks
  that the launcher is dynamically linked (a static one would ignore `LD_PRELOAD`), and
  runs `agents/renderer/toolchain/smoke.jl` exactly as the row will: the launcher by its
  path, the row's flags (`--compiled-modules=strict` among them) and environment, the
  preload filter in required mode. The smoke loads every package of `Project.toml`, sees
  ``success(`true`)`` false, reads a fixed offset through TimeZones offline, and writes a PNG
  with a non-ASCII title; a package image that does not load fails the build, which then
  reruns the load with `JULIA_DEBUG=loading` and prints the rejected images.

#### 5b. Build inputs, CI and the deploy (J1)

- `Project.toml` and `Manifest.toml` join the toolchain's hash (`toolchain.py`, `INPUTS`),
  the root `.dockerignore` (an allowlist, which lacked them, so the stage's `COPY` would
  have failed) and the `renderer-image` job's change filter (`RENDERER_CHANGES` in
  `ci-image.yml`); a test fails when the toolchain Dockerfile copies a context file that no
  input covers, and another when the `.dockerignore` keeps an input out. The job's
  `timeout-minutes` goes from 25 to 60, sized from the cold toolchain build (the numbers
  are in "What J1 built"), and before it builds a toolchain itself the job removes the
  runner's unused SDKs, because Julia's 2.5 GB sit in the builder, the local registry, the
  cache export and the loaded renderer image at once.
- The `deploy-renderer` trigger's included files lack `Project.toml` and `Manifest.toml`:
  an owner task, because the trigger's configuration lives in GCP. Until then a
  Manifest-only change (a Makie bump) reaches the renderer with its next deploy, not its
  own.
- Cloud Build (owner decision of 2026-10-29): the whole renderer deploy runs on
  `E2_HIGHCPU_8` with a 3600 s timeout, not a nested toolchain build on a larger machine.
  The toolchain build uses BuildKit's registry cache: `docker buildx` with the
  docker-container driver (the builder image ships buildx 0.23; the daemon's own builder
  exports no cache), `--cache-from` and `--cache-to type=registry,mode=max` on the fixed
  ref `anyplot-toolchain:buildcache` in the toolchain's own repository and package,
  `ignore-error=true` on the export (a cache that cannot be written is a warning, never a
  failed deploy), and `--provenance=false`, so the image stays one image manifest and the
  digest the renderer pins names it, not an index with an attestation. Writing that ref needs the rights the build already uses for the
  `t-<hash>` tags and for moving the renderer's `:latest`; no IAM change.
- The candidate smoke renders a Makie plot through the Julia row after the matplotlib
  one and prints its wall time, CPU time and peak memory, so the first deploy proves that
  the depot's package images load under gVisor with `--compiled-modules=strict` and the
  preloaded filter, or nothing is promoted.
- CI (`renderer-image`): the built image renders the catalogue's `scatter-basic` Makie
  file through the harness in exec mode with the row's argv and environment
  (`exec_deny: on`, 3200x1800), and a forced cache miss (the row plus
  `--check-bounds=yes`, one of the cache flags) must fail with "not available with flags"
  within 30 s.

#### 5c. The command row (J1)

- `JULIA_BINARY` (`/opt/julia-1.13.2/bin/julia`) by its path: `SANDBOX_PATH` does not
  carry it, as it does not carry `R_BINARY`. Flags: `--project=/opt/julia-project
  --startup-file=no --history-file=no --compiled-modules=strict --heap-size-hint=1536M`,
  and since J1.1 `-L /opt/anyplot/toolchain/warmup.jl` before `plot.jl` (the precompile
  workload, "What J1.1 built").
  Environment: `LANG=C.UTF-8`, `XDG_CACHE_HOME=/tmp`, `JULIA_NUM_THREADS=1`,
  `OPENBLAS_NUM_THREADS=1`, `JULIA_DEPOT_PATH=/tmp/depot:/opt/julia-depot` (the sandbox
  writes logs and scratch spaces nowhere but `/tmp`), the pinned `JULIA_CPU_TARGET`,
  `JULIA_PKG_OFFLINE=true`, `JULIA_PKG_PRECOMPILE_AUTO=0`.
- The exec filter is preloaded as for R (2b): the launcher is dynamically linked, so
  `LD_PRELOAD` applies, and Julia starts no program before `main`. `run`, backtick
  commands and `Distributed`'s workers die with `SIGSYS` (`ProcessSignaled(31)`);
  `Sys.which` is pure Julia, and CairoMakie's JLLs exec nothing.
- `--compiled-modules=strict`, never `existing` (verified on 2026-10-29): on a cache miss
  `existing` loads the package from its source in process, with exit 0 and no message,
  for minutes in CairoMakie's case; `strict` fails in about a second with "Precompiled
  image ... not available with flags CacheFlags(...)". The 2 s spawn kill under the filter
  that the 2026-10-28 text measured belongs to the default `yes`, which starts a compile
  worker. `JULIA_PKG_PRECOMPILE_AUTO` governs only `Pkg`.
- `RLIMIT_AS` off (LLVM reserves address space far beyond its resident set and dies
  under 1 GiB, spike of 2026-10-24); `--heap-size-hint` makes the collector work before
  the 4 GiB instance runs short. `RLIMIT_NPROC` 64 holds with one thread.
  `render_p95_s` is 25 s, from J1's sweep (below).

#### 5d. Data and the code profile (J2a)

- Datetimes (owner decision of 2026-10-29): Julia's `DateTime(s)` refuses microseconds,
  `+01:00`, `Z` and a space separator (verified in julia:1.13.2). Datetimes go through
  TimeZones.jl: offsets to UTC as readr does, microseconds truncated to milliseconds and
  announced with counts in the version's "what changed" list, the status staying the
  render's (R's 2^53 precedent). TimeZones 1.22.3 was a transitive dependency; J1 makes it
  a direct one in `Project.toml` (`[deps]`, and `[compat]` at the Manifest's version;
  `Pkg` changed the Manifest's `project_hash` and nothing else), so the toolchain
  precompiles it, and the build's smoke parses an offset offline under `strict`. The
  catalogue prompts' Julia blocks do not name it (`tests/unit/prompts/test_prompts.py`
  lists it as loader-only). The loader itself is J2a.
- Loader: placeholder `df = load_user_data()`; `CSV.read("data.csv", DataFrame; types =
  Dict(...), missingstring = "", strict = true, truestrings = [...], falsestrings = [...],
  normalizenames = false, pool = false)` typed from `data/kinds.py`, the true and false
  strings named explicitly (the canonical CSV's `True` and `False`). `integer` and
  `big-integer` read as `Int64`, exact to 2^63, so Julia needs no integer note (R's 2^53
  line has no Julia counterpart). `missingstring = ""` keeps a text `NA` (Namibia) as text.
  No catalogue Makie file builds its data with DataFrames (they build vectors), so the
  adapter must introduce the column access `df[!, COL]` in every adaptation, which
  `adapter_julia.md` teaches.
- Validator (tree-sitter-julia from the pinned `tree-sitter-language-pack` 0.13.0): it
  refuses by shape, as R's does: a call through a computed value (a callee that is not a
  name or a dotted name), `getfield` and `getproperty` on a module, every `import … as`
  and `using … : x as y`, string interpolation walked as code (`"$(run(cmd))"` runs when
  the string is built), broadcast calls (`f.(x)`) checked like calls, `Core.eval`,
  `Base.Libc` and file writes (`open` with a write mode, `write`, `rm`, `cp`, `mv`,
  `mkdir`, `touch`). On top, the 2026-10-28 deny list (`run`, backtick `Cmd` literals,
  `download`, `eval`, `@eval`, `include`, `include_string`, `Meta.parse`, `ccall`,
  `@ccall`, `@cfunction`, `unsafe_*`, `invokelatest`, `ENV` writes) and the
  `using`/`import` allowlist (never `Downloads`, `Sockets`, `Distributed`, `Libdl`,
  `Mmap`, `Pkg`). RDatasets and PalmerPenguins stay in the project, because the catalogue
  and the pipeline load them, and the adaptation refuses them as the finding
  `dataset-package`, in the Julia runtime's blocking set like R's.
- Error grammar, from stderr only: the first `ERROR: LoadError:` line, the first frame in
  the plot (`@ Main /work/plot.jl:N` inside a function, `@ /work/plot.jl:N` at the top
  level, measured in J1), and the last `in expression starting at /work/plot.jl:N` line.
- Regions and normaliser: `THEME` and the tokens as `const` or plain assignments (both
  forms are in the catalogue), the final `save("plot-$(THEME).png", fig; ...)`, and the
  four saves through `joinpath(@__DIR__, ...)` rewritten to the plain file name.

#### 5e. Measurement stage between J1 and J2a

- A render sweep of all 325 catalogue Makie files in the J1 image (run locally with J1;
  the numbers are in "What J1 built"), so J2a knows which files fail under Makie 0.24
  before it writes a normaliser rule or a readiness hint.
- On the deployed J1, through the renderer's `POST /render`: `using CairoMakie`, the
  first `save` and a second `save` timed, cold (the first render after a scale from zero)
  and warm. The probe is a plot that prints `time()` deltas to stderr, which the response's
  `stderr_tail` returns; the deploy's candidate smoke prints the first cold render. Above
  about 25 s for a cold render at 2 vCPU, a `PrecompileTools` workload of the catalogue's
  common calls joins the project (Gemini's fallback); the 45 s line of question 4 stays
  the gate for submit-and-poll.

#### 5f. Fixtures, matrix, docs (J2b)

- `JuliaRuntime`, `adapter_julia.md` filling `adapter.md`'s slots, the ten specs'
  fixtures (60 cases), the admin deploy's `_LIBRARIES` gains `makie`, the docs, and the
  owner's matrix run for the public release.

#### Order of the PRs

J1 → the measurement stage → J2a → J2b. J1's deploy is the first that builds the Julia
toolchain (its tag is missing); the owner task for the trigger's included files can land
any time.

#### What J1 built (2026-10-29)

Everything in 5a to 5c; nothing served. Measured in local Docker on the developer machine
(32 CPUs, WSL 2, kernel 6.18), the renders with `--network none --read-only`, `--cpus 2
--memory 4g` as on Cloud Run, an unprivileged user with `RLIMIT_NPROC` 64, the sandbox's
environment from `executor.sandbox_env` and the harness in exec mode with the Julia row's
argv:

| Measurement | Result |
|---|---|
| Julia stage, all 32 CPUs | download and check 20 s, instantiate 59 s, precompile 198 s (311 packages; Makie 115 s, CairoMakie 41 s); the final stage's copies, launcher check and smoke 16 s |
| The whole toolchain, cold, 8 pinned CPUs (`E2_HIGHCPU_8`), the deploy's buildx command | 420 s with R, the registry cache's export and the push; instantiate 73 s, precompile 245 s (Makie's chain is the critical path, so 32 CPUs gain little) |
| Sizes | Julia's install 1.1 GB, the depot 1.4 GB; the toolchain image 312 MB → 2.74 GB, the renderer image 1.35 → 3.78 GB |
| The build's smoke (every package, `strict`, the filter, TimeZones, a PNG) | 12 s |
| `scatter-basic`, `bar-grouped`, `heatmap-basic`, container start included | 4.7, 7.5 and 8.6 s of wall time (two runs each, within 0.1 s); 4.5 to 8.5 s of CPU; peak RSS 942, 1,021 and 1,008 MiB; 3200x1800 (174 KB, 102 KB) and 2400x2400 (228 KB); `exec_deny: on` |
| `using CairoMakie`, first `save`, second `save` (one process, the probe of 5e) | 2.4 s, 1.3 s and 0.14 s (three runs within 0.1 s); 4.5 s of wall time with the container's start and the harness |
| A forced cache miss (`--check-bounds=yes`) | `strict`: exit 1 in 1.4 s, container start included, "Precompiled image ... CairoMakie not available with flags CacheFlags(...)"; the same miss under `existing` was still loading, silently, after 60 s |
| ``run(`ls /`)`` in a plot | the child dies with `SIGSYS` before it lists anything, the plot fails with ``failed process: Process(`ls /`, ProcessSignaled(31))`` at `plot.jl:4`, the end line says `exec_deny: on` |

**The render sweep** (5e): every catalogue Makie file once, as `plot.jl` and unchanged,
through the same path, four renders at a time at 2 CPUs each (15 minutes in all):

| | Result |
|---|---|
| Rendered | 320 of 325, every one with `exec_deny: on`; 252 at 3200x1800 and 68 at 2400x2400 |
| Wall time, container start included | p50 10.2 s, p95 20.6 s, max 36.8 s (`biplot-pca`); four at a time cost up to twice the time of one alone (`bar-grouped` 15.4 s against 7.5 s) |
| The eight slowest, one at a time | 12.8 to 30.7 s; five of them (`biplot-pca`, `contour-decision-boundary`, `scatter-matrix`, `contour-density`, `dendrogram-basic`) load RDatasets, which J2a refuses in an adapted plot |
| Peak RSS | p50 1,035 MiB, p95 1,137 MiB, max 1,439 MiB |
| Failed: Makie 0.24 changed the API the file was written for | `area-mountain-panorama` and `line-parametric` (`rowgap!`/`colgap!` on a gap the 0.24 layout does not have: "Can't set size of invalid row gap 1"), `circos-basic` ("Failed to construct plot: No plot arguments given"), `feynman-basic` (a recipe over `arrows`: "no method matching `_is_3d_arrows`") |
| Failed: a package the project does not carry | `qrcode-basic` (QRCoders, which the generator prompt lists as not loadable) |
| Warnings that still render | `arrows` deprecated in favour of `arrows2d`/`arrows3d` (16 files), `resolution` in the theme (122 files), `arrowsize`, `linecolor`, `arrowcolor` renamed; `map-tile-background` loads `Downloads` and renders without its tiles offline (J2a's allowlist refuses `Downloads`) |

For J2a: the four API failures are regeneration candidates or `blocked` with a reason, and
`resolution` and `arrows` are readiness hints the adapter can apply, as Gemini proposed.
The raw table stays out of the repository.

Also found:

- Loading touches every package image it reads (Julia records cache use); in the
  read-only depot of a sandbox the touch fails silently, and in the build it leaves a
  1.3 MB layer of copied `.ji` files.
- Cairo's fontconfig (Fontconfig_jll) scans `/usr/share/fonts` with its cache in
  `/var/cache/fontconfig`, which the build's smoke wrote and now removes: the renderer adds
  fonts after the toolchain, and a sandbox cannot write there. No render baked a font cache
  before Julia either (ragg and lets-plot scan too); a baked cache for the renderer's fonts
  is a possible later gain, not measured.
- `Pkg` changed nothing in `Manifest.toml` but its `project_hash` when TimeZones became a
  direct dependency; the edit is byte-identical to what `Pkg.add` with
  `preserve = PRESERVE_ALL` writes. The pipeline's Julia depot cache (`julia-actions/cache`,
  keyed on both files) misses once.
- The registry cache of 5b, run with the deploy's own builder image
  (`gcr.io/cloud-builders/docker`: Docker CLI 20.10.24, buildx 0.23.0) and the step's
  exact `buildx` flags against a local registry: the cold build exported a 1.74 GB cache
  manifest (29 layers) next to the image; after an R-only change a fresh builder, as Cloud
  Build starts every build with one, took Julia's whole stage from the cache and finished
  in 70 s. The image goes out as one OCI image manifest. In Artifact Registry the cache
  ref is unverified until J1's deploy; a refused export only warns.

| Text above (2026-10-28) | Built | Why |
|---|---|---|
| `julia --project=/opt/julia` with `--compiled-modules=existing` | The launcher by its path (`/opt/julia-1.13.2/bin/julia`), the project under `/opt/julia-project`, `--compiled-modules=strict` | `SANDBOX_PATH` lacks the launcher; `/opt/julia` was the project's name and now names nothing, so the install, the project and the depot are three named siblings under `/opt`; `existing` hides a cache miss (5c) |
| The build check runs `ldd` on every library | The launcher, `libjulia` and `libjulia-internal`/`-codegen` | The system image and Julia's own test libraries name libraries the running process provides (`libjulia.so.1.13`, `libccalllazyfoo.so`), so `ldd` reports them missing in any install |
| `render_p95_s` 45 s | 25 s | The sweep's wall p95 of 20.6 s, rounded up; the slowest files load RDatasets, which an adaptation removes, and the measurement stage's deployed numbers revise it |

#### What J2a built (2026-10-29): the Julia code profile, not served yet

Everything in 5d; `AGENT_LIBRARIES`, the runtime registry, the prompts and `_LIBRARIES`
are untouched, as for R's PR 3a. Measured in the J1 images (`anyplot-renderer:julia`,
the row's flags and environment, `--network none`, 2 CPUs and 4 GiB).

- **Parser.** `GRAMMARS` is `("r", "julia")`; `agents/Dockerfile` keeps `r julia`
  (`TREE_SITTER_GRAMMARS`, 0.6 MB and 2.7 MB), and the agents-image job of
  `ci-image.yml` loads every kept grammar and runs the Julia readiness scan on the
  catalogue's `scatter-basic` Makie file through the profile's modules. `treesitter.py`
  gained the Julia helpers (string values with Julia's escapes, `None` for an
  interpolated or triple-quoted string; string macros; dotted names; positional and
  keyword arguments; assignments and every binding site); all 325 catalogue files parse
  with no ERROR or MISSING node, and the comment types of both languages are skipped.
- **Regions** (`profiles/julia/regions.py`). The theme statement in both forms (281
  `const`, 44 plain), 1,213 theme tokens over the catalogue (a token's branches are
  literals, `colorant"..."`, symbols, tuples, THEME and earlier tokens; the 12 that call
  `RGBAf(...)` are plot code), the palette in 196 files, the top-level save with the
  standard target in 322 (the other three save inside `with_theme(...) do`), the markers
  matched loosely as in R (both in 218 files), no column constants anywhere, and the
  placeholder at the top level only, because the loader that replaces it imports
  packages.
- **Normaliser.** Header (325), title (325, the shared `is_catalogue_title`), the four
  `joinpath(@__DIR__, ...)` saves, `resolution =` renamed to `size =` (122; Makie 0.24
  accepts `resolution` and renders the same 3200x1800 but warns on every run, which would
  fill the stderr tail), and the canvas, decided like R's dpi: only `px_per_unit` of the
  protected save changes, never the figure's size, so the layout in Makie's units stays.
  Measured: CairoMakie rounds the figure size to whole units and then `size *
  px_per_unit` to whole pixels (`(1600, 900)` at 1.9999 gives 3200x1800, at 2.0004
  3201x1800; `(1000, 562.5)` at 3.2 gives 3200x1798), and a save without `px_per_unit`
  renders at 2. The step changes no catalogue file: of the 325 normalised files, 250
  measure 3200x1800 and 69 2400x2400 at 2, and 6 have no static canvas (3 saves in
  `with_theme`, one `set_theme!`, one `resize_to_layout!`, one computed size); J1's
  sweep rendered 252 and 68 of the 320 that render. Idempotent over the corpus. The review found that
  `Figure(; resolution)`, the keyword shorthand, raised `IndexError`: it becomes
  `Figure(; size = resolution)`, the same value, and a test runs the normaliser over 242
  odd but valid shapes (shorthands, splats, a size under one unit or infinite, a zero,
  negative or infinite `px_per_unit`, and after the Copilot review of #12459 integer
  literals of hundreds and thousands of digits, `big"..."`, hex and underscored
  literals), which leave notes, never exceptions; a side past 100,000 units or a
  `px_per_unit` past 1,000 is left alone with a note.
- **Validator.** Refuses by shape (module docstring of `profiles/julia/validate.py`): a
  denied name wherever it is read, also as the member after a `.` on a module or any
  value (`x.Base.run`, `Base.:run`); a package as a value; calls through a parenthesised
  value, an index, a field of a value, a `var"..."` name or a call's result (except
  `cgrad`, `Fix1`, `Fix2`, `Returns`, `ComposedFunction`); macros outside `MACROS` and
  string macros outside `colorant`, `L` (without `%$`), `dateformat`, `r`, `raw`;
  command literals; `macro` and `module` definitions; `import ... as`; any `using` or
  `import` outside the plotting packages and the catalogue's standard libraries. `CSV`
  and `TimeZones` are refused in the plot code too: they are the loader's alone, and the
  adapter never imports them. `getfield`, `getproperty`, `setfield!`, `setproperty!`, `getglobal` and
  `setglobal!` are refused on any value (a superset of "on modules"; no catalogue file
  calls them). One exception keeps histogram-capability eligible: a lowercase denied
  name the file makes its own variable by one top-level assignment before any other
  mention (its `cp`, the process capability index) may be read, never called. SECURITY
  finds something in 5 of the 325 normalised files: the 3 `with_theme` saves,
  qrcode-basic (QRCoders) and map-tile-background (Downloads, PNGFiles, `mktempdir`, a
  URL). 121 named bypasses are tests; three tests run the admitted idioms, the loader and
  the working miniature in the J1 image (skipped without Docker and the image). The
  review of the same day (Gemini 3.8 Flash and Fable) found that a dotted callee passed
  with any root of the attribution vocabulary (`FileWatching.watch_file(...)`): a root
  now comes from `MODULE_ROOTS`, called or handed on; `invoke`, `atexit`, `finalizer`
  and the file-touching submodules `Cairo`, `FileIO`, `TOML` and `CoreLogging` joined
  the denied names. The split did not change. The Copilot review of #12459 found that an
  alias still carried such a member (`f = Unlisted.dangerous; f()`): a dotted name now
  starts at a root of `MODULE_ROOTS` or at a name the file binds above it (after an
  assignment, from a parameter, a loop, `let`, `do` or `catch` variable, from the start
  of a comprehension for its `for` variable), and every other module a plot reaches by a
  name, measured in the image (`MODULE_NAMES`: `names(Main)` after the catalogue's
  `using` lines and the module members of every root), is refused as a value and as a
  member. All 2,145 dotted names of the catalogue start at a root or a name bound above;
  the split did not change. Its second round found that the import rule read only a
  path's first name (`using CairoMakie.Cairo` passed): an import path is now one package
  name, which every catalogue import is (the 325 files load single names; one selects
  `using Statistics: mean`), and the names a selected import brings in are checked like
  any name (denied names, modules outside the roots, macros outside `MACROS`, operators).
  The split did not change.
- **Readiness.** 0 clean, 308 coupled, 17 blocked: the 13 map specs, qrcode-basic and the
  3 `with_theme` saves (area-mountain-panorama, bifurcation-basic, scatter-lag). Every
  eligible file carries the `data-block` hint; 16 carry `deprecated-api` (`arrows!`).
- **Loader.** `import CSV, DataFrames[, Dates[, TimeZones]]` and `CSV.read(...;
  types = Dict(...), missingstring = "", truestrings = ["True"], falsestrings =
  ["False"], strict = true, normalizenames = false, pool = false, stringtype = String,
  ntasks = 1)`; a `big-integer` or `datetime` column is read as `String` and converted
  in a `let` block. Measured: `Float64` exact on 249,964 values against Julia's
  `parse`; `Int64` wrong on exactly 8 values, -9223372036854775807 to
  -9223372036854775800, which CSV.jl 0.10.17 (Parsers 2.8.8) reads as positive (of
  200,782 boundary and random values), so wide integers go through `parse(Int64, ...)`,
  which reads them exactly (the image test pins two of them);
  `Dates.DateTime(s)` refuses a space separator, `Z`, `+01:00` and more than three
  fraction digits, so a cell is rewritten to `yyyy-mm-ddTHH:MM:SS.sss` (the fraction
  truncated) and an offset or `Z` read with TimeZones' `zzzz` (`+01:00`, `-05:30`,
  `+0100`, `+01`, `Z`) and converted to UTC; `T` and space, minutes without seconds,
  year 1 with an offset (year 0 in UTC), `NA`, `001`, blanks, quotes and a column name
  with `$`, `"`, `\`, a line break and non-ASCII letters all read back exactly.
  `ColumnKinds.submillisecond` counts the cells per column whose truncated digits are
  not all zero; there is no integer count for Julia.
- **Errors.** The first `ERROR:` line's exception type from a closed list (with an
  `UndefVarError`'s variable and a `MethodError`'s function when they are names), the
  innermost plot frame's line and the function the plot called there, and the last `in
  expression starting at` line; fixed texts for the exec filter's kill, a strict cache
  miss, memory, recursion and a missing package. Corpus-tested with real stderr of the
  J1 image: a MethodError, an UndefVarError, a BoundsError in a function, `error()`, a
  missing DataFrame column, a strict CSV read, the loader's datetime, a ParseError, the
  exec filter's kill (through the harness) and a deep Makie failure.
- **Edits and export.** The edit applier's Julia dialect (meaning as R's token stream,
  `const` counted; literals `"`, triple quotes and commands, never `'`), Python's and
  R's tests unchanged. The export's run line is the catalogue's own convention,
  `julia --project=. plot.jl` (`prompts/library/makie.md`, the landing page's terminal);
  without a `Project.toml` next to the file, Julia falls back to the default environment
  (checked in the image with a stacked load path).
- **Verified end to end, without a model.** Scripted identity adaptations of
  `line-basic` (a timestamp x axis with `+01:00` and `-05:30` offsets and microseconds,
  16 cells counted below the millisecond, column constants `Zeit · $Messung "lokal"`
  and `Temperatur (°C)`, the literal ticks, span and x limit dropped) and `scatter-basic`
  (`Größe (cm)` and `Gewicht "kg" — $`, an unplotted timestamp column, 59 cells
  counted) passed both validator profiles and the drift check, took the loader and
  rendered through the harness in exec mode in the renderer image: 3200x1800 in both
  themes, `exec_deny: on`, 15.2 to 17.2 s of wall time and 1,234 to 1,249 MiB peak.

Found for J2b and the toolchain:

- **Loading DataFrames, CSV or TimeZones costs a Makie render about 5 s.** A plot that
  loads any of them (in either order) recompiles Makie's first save: `using CairoMakie`
  and a `lines!` save took 3.8 s alone and 8.5 to 9.4 s with one of them loaded; the
  typed `CSV.read` takes another 2.2 s and the first TimeZones parse 1.3 s. An adapted
  render (the loader and `df[!, COL]`) therefore takes about 15 s at 2 CPUs where the
  catalogue file took 4.7 s, which the 25 s repair reserve and the J1 sweep's p95 of
  20.6 s do not leave room for on the slow files. A precompile workload in the toolchain
  that loads CairoMakie with DataFrames, CSV and TimeZones together and runs a typed read
  and a save (a small package in the project with `PrecompileTools`, or a system image)
  would keep that code compiled; J2b measures and decides it before the matrix.
- **The stderr tail may lose the `ERROR:` line.** A deep Makie failure printed 7,551
  characters; the renderer keeps the last 2,000, so the summary reads "an error (the tail
  cut off its first line) at line N; in text!()". Keeping Julia's first error line next
  to the tail would name the exception.
- **Line numbers count the run form.** The loader replaces one placeholder line with 15
  lines plus one per column, and 12 more with a timestamp column, so the error summary's
  lines after the placeholder lie that far behind the working form's; the runtime can
  subtract the statement's line count (Python's loader shifts lines too, less).
- **Regeneration candidates**: the 4 files Makie 0.24 rejects (J1's sweep) and the 3 that
  save inside `with_theme`; none is blocked by a list, so a regenerated file becomes
  eligible without a code change.

| Text above (5d) | Built | Why |
|---|---|---|
| `integer` and `big-integer` read as `Int64` | `integer` as `Int64`; `big-integer` read as text and converted with `parse(Int64, ...)` | CSV.jl's typed read drops the sign of eight values next to -2^63 (measured); a 32-bit column cannot hold them |
| The four `joinpath(@__DIR__, ...)` saves rewritten | Rewritten, and `resolution =` renamed to `size =` | The deprecation warning on 122 files would fill the stderr tail the repair reads; Makie maps the one to the other unchanged |
| `getfield` and `getproperty` refused on a module | Refused on any value, with `setfield!`, `setproperty!`, `getglobal` and `setglobal!` | Whether a value is a module is unknown statically; no catalogue file calls them |
| `` `qrcode-basic` `` and the map specs blocked | Also the three saves inside `with_theme(...) do` | The protected save must be a top-level statement of its own lines; the regeneration list above |

#### What J1.1 built (2026-10-29): the precompile workload

The deployed J1 took 12 to 21 s for the three test files on Cloud Run, wall about equal to
CPU time: Julia compiled Makie's calls in every fresh process. Owner decision of the same
day: a `PrecompileTools` workload, shipped only if it clearly helps; a sysimage only if the
workload is not enough. It helps, and no sysimage was built.

- **The package.** `agents/renderer/toolchain/AnyplotWarmup` runs one `@compile_workload`
  at precompile time. It makes the calls the catalogue's Makie files make most (a survey of
  the 325 files: `Figure`, `Axis` with the theme's keywords, `Label`, `scatter!`, `lines!`,
  `band!`, `hlines!`/`vlines!`, `text!`, `poly!`, `barplot!` dodged, `heatmap!` with a
  `Colorbar`, `hist!`, `density!`, `boxplot!`, `violin!`, `errorbars!`, `stairs!`,
  `contour!`/`contourf!`, `pie!`, legends, layout calls, `save` to PNG with
  `px_per_unit = 2`), Statistics and Random calls, and J2a's loader statement verbatim
  (`agents/anyplot/code/profiles/julia/loader.py`, PR #12459: every column kind, datetimes
  with and without offsets, `parse(Int64, ...)`), then plots from the table's columns,
  DateTime and Date axes included. If the loader changes its keywords, a render recompiles
  only the outer call.
- **Where it lives.** The Julia stage copies it into the image's project, develops it
  offline with `PRESERVE_ALL` after the catalogue's precompile, precompiles it, and only
  then removes the registries. The image's `Manifest.toml` differs from the repository's
  by the package's entry and `project_hash`, its `Project.toml` by the package's `[deps]`
  and `[sources]` lines; the repository's files, which
  `.github/actions/setup-julia` shares, do not change. Its files sit under
  `agents/renderer/toolchain/`, so they are toolchain inputs (`toolchain.py`, `INPUTS`).
- **How a render loads it.** The workload's native code is stored in its own package image
  and used only while that package is loaded. The row adds `-L
  /opt/anyplot/toolchain/warmup.jl` (`import AnyplotWarmup`) before `plot.jl`. Verified
  against J1's image: `PROGRAM_FILE` stays `plot.jl`, the error frames (`@ Main
  /work/plot.jl:3`, `@ /work/plot.jl:6`, `in expression starting at /work/plot.jl:N`), a
  `ParseError`'s position and the exit codes (1, and 3 for `exit(3)`) are unchanged, and
  ``run(`ls /`)`` still dies with `SIGSYS` under `exec_deny: on`. A forced cache miss
  under `strict` still fails in 1.8 s with "not available with flags", now on the
  workload's image, which `-L` loads first. The only visible difference is a binding
  `AnyplotWarmup` in `Main`. The build's smoke and the CI step run the row's exact argv.
- **Why the workload loads CSV, DataFrames and TimeZones itself.** Each of them pulls in
  InlineStrings, whose methods invalidate much of Makie's precompiled code: in J1's image,
  loading any of them made a catalogue Makie render 5 to 6 s slower (CSV +5.8 s,
  TimeZones +4.9 s, InlineStrings alone +5.9 s), and the typed read compiled for another
  2.2 s. An adapted render always loads them, so the workload is compiled in that world.
  A Makie-only variant of the workload was 0.6 s faster on unchanged catalogue files but
  barely helped once CSV and DataFrames loaded (`scatter-basic` 10.1 s against 10.9 s
  without any workload).

Measured in local Docker as J1 measured (`--cpus 2 --memory 4g --network none`, the harness
in exec mode with the row's argv and environment), on J1's image with and without the
workload. The host was shared with another agent's builds, so each file ran before, after,
after, before, and the table keeps the faster run of each; the first five rows ran on a
quiet host (load about 1.1). An adapted render is the catalogue file with J2a's loader in
place of its data block, reading a CSV with a datetime column with offsets (`scatter-basic`
with 150 rows, `line-basic` with 24 hourly readings on a DateTime axis).

| File | Before: wall, CPU, peak RSS | After | Change |
|---|---|---|---|
| `scatter-basic`, adapted | 15.9 s, 15.6 s, 1,234 MiB | 5.0 s, 4.9 s, 1,001 MiB | -68 % |
| `line-basic`, adapted | 18.0 s, 17.9 s, 1,263 MiB | 5.1 s, 4.9 s, 998 MiB | -72 % |
| `scatter-basic` | 5.3 s, 5.1 s, 922 MiB | 4.9 s, 4.6 s, 995 MiB | -9 % |
| `bar-grouped` | 8.5 s, 8.3 s, 997 MiB | 4.9 s, 4.7 s, 1,001 MiB | -42 % |
| `heatmap-basic` | 9.8 s, 9.7 s, 984 MiB | 5.3 s, 5.2 s, 1,014 MiB | -46 % |
| 20 more catalogue files, median | 11.3 s | 7.1 s | -37 % |

The 20 files are `line-basic`, `area-basic`, `histogram-basic`, `box-basic`,
`violin-basic`, `pie-basic`, `contour-basic`, `density-basic`, `errorbar-basic`,
`step-basic`, `bar-stacked`, `scatter-color-mapped`, `bubble-basic`, `lollipop-basic`,
`hexbin-basic`, `polar-basic`, `treemap-basic`, `waterfall-basic`, `line-timeseries` and
`subplot-grid`; they gained between 6 % (`line-timeseries`) and 63 % (`violin-basic`), none
got slower, and the peak RSS stayed at or below 1,118 MiB. With J1's loader approximation
prepended to all 23 files, the median went from 16.2 to 5.5 s. After the workload, about
0.9 s of compiling remains in an adapted render; 0.24 s of it is the loader's own `utc`
broadcast, which is new code in every render.

The target was a third off each of the three files. The catalogue's `scatter-basic` misses
it, and the miss is accepted: about 3.9 s of its 4.9 s is a fixed cost no workload reaches
(0.5 s for the container and Julia's start, 2.4 s to load CairoMakie's package images,
0.9 s for CSV, DataFrames, TimeZones and the workload's image), and the agent never renders
a catalogue file unchanged. Only a sysimage would cut the load.

Cost: the workload's step adds 70 s to the Julia stage on 32 CPUs (64 s of it the one
package's precompile, so about the same on Cloud Build's 8), and the catalogue's precompile
reruns once, because the registries now go in a later step; the cold toolchain build took
339 s locally. The depot grows by 101 MB (the workload's image), the toolchain and
renderer images by 104 MB each. The real images rendered as the prototype did (adapted
`scatter-basic` 5.1 s, `bar-grouped` 5.0 s), and the CI step's forced cache miss failed in
2 s. `render_p95_s` stays 25 s: the deployed renderer ran about 2.5 times slower than local
Docker, and no deployed sweep with the workload exists yet.

Found for J2b's adapter prompt (Makie 0.24.16, in J1's image):

- A Date column with a missing cell reads as a `SentinelVector{Date}`, which Makie cannot
  plot: `MethodError: no method matching create_dim_conversion(::Type{Union{Missing,
  Dates.Date}})`. A Float64 column with a missing cell plots.
- `vspan!` with DateTime bounds registers a conversion that a following `lines!` refuses:
  "Plotting unit Float64 into axis with type Dates.DateTime not supported".
- `barplot!` refuses String x values ("Conversion failed for BarPlot ... Tuple{Vector{String},
  Vector{Float64}}"): categories need integer positions and `xticks`, as the catalogue does.

#### What J2b built (2026-10-30): Makie served

Everything in 5f, on J2a's profile and J1.1's image, as PR 3b did for ggplot2.

- **Runtime.** `agents/anyplot/render/runtimes/julia.py`, `JuliaRuntime`, implements the
  whole `RuntimeAdapter` contract with J2a's modules: `plot.jl`, the renderer's Julia row
  as the command (the harness in exec mode in front of the launcher with `JULIA_FLAGS`,
  `-L` and the workload included), the row's environment key for key as `sandbox_env`
  builds it (`JULIA_ENV`, no `RLIMIT_AS`, `ANYPLOT_DENY_EXEC=required`; locally
  `RLIMIT_NPROC` left to `--pids-limit`), the Julia normaliser, loader, validator,
  readiness scan and error grammar, the edit applier's Julia dialect, the PNG and no
  probe (`review_texts`), the export with `julia --project=. plot.jl`, and Python's data
  runs and conversions. `blocking_rules` adds `dataset-package` as R's does, and the
  `adaptation_targets` are written in Julia. `render_p95_s` is the row's 25 s.
  The registry gains `JULIA_LIBRARIES = {"makie"}` (pinned equal to
  `edits.JULIA_LIBRARIES`) and `RUNTIME_CLASSES["julia"]`.
- **The loader note.** `loader_notes` writes one "what changed" line from
  `ColumnKinds.submillisecond`: "Julia keeps time to the millisecond, so the plot cuts the
  digits below it from N timestamps: n in '<column>', ...", the columns that fit 200
  characters and the rest counted. The fitting is R's, moved into
  `runtimes/notes.counted_note`, which both runtimes call (R's line is unchanged, its tests
  pin it). The pipeline puts it first and leaves the status alone, as for R; `root.md`
  has the root name it in every reply to that result, as it names R's.
- **The stderr tail.** `RuntimeCommand.stderr_head` (empty for every row but Julia's,
  `"ERROR:"`) and `executor.stderr_tail`: the last 2,000 characters, and with a head the
  first line that starts with it, cut to 300 characters, in front of them when the tail
  lost its start, with the tail shortened by that line, so the answer stays within
  `MAX_STDERR_CHARS` and `wire.py` is unchanged. `run_theme` passes the job's row, and
  the local Docker backend cuts by the runtime's row in the same function. A row without a
  head, a stderr within 2,000 characters, a head line inside the tail and a stderr
  without one all give the plain tail, byte for byte what every row returned before; a
  test pins that only the Julia row has a head. Safe for Python and R because their
  rows carry no head, and for Julia because the line is the run's own output, which the
  tail already carried, and the grammar reads it in a closed shape.
- **Line numbers.** R's grammar names no line, so R has no offset to take off; Python's
  names the run form's line, a few lines past the working form's after its loader. Julia's
  loader adds 15 lines plus one per column, and about 12 more with a timestamp column (30
  in the end-to-end run below), which would send the repair to the wrong statement. So
  `RuntimeAdapter.error_summary` takes the run form as a keyword (`run_form`), which the
  pipeline passes; Python's and R's summaries leave it unread. The Julia runtime finds the
  loader's span in the run form (`loader.loader_span`: the top-level `import CSV,
  DataFrames...` line, which plot code cannot contain, and the statement after it) and
  the grammar names the working form's lines; a line inside the loader is the
  placeholder's, "(the data loader)". The theme toggle and the eval report keep the run
  form's lines, which no adapter reads.
- **Prompts.** `adapter_julia.md` fills every slot of `adapter.md` and the highlights
  slot: the placeholder and the loader's types (`CSV` and `TimeZones` never imported),
  column constants as Julia strings (`\$` for a dollar sign) read as `df[!, COL]`, the
  rewrite of the catalogue's plain vectors, `using DataFrames` for its functions, the
  protected statements, `save`/`get` never bound, the canvas (`size`, `px_per_unit`, no
  `resolution`, no `resize_to_layout!`), the palette as colour literals, the package
  allowlist and the validator's refusals in short, `dropmissing` (never `filter`, which
  keeps the `Union{Missing, Date}` type Makie refuses), categories as integer positions
  with `xticks`, a number formatter with `DECIMAL` and `THOUSANDS` (Julia's `Printf` has no
  grouping flag: measured, `%'.2f` is an `InvalidFormatStringError`), time axes and
  English month names. The library rules (`prompts/library/makie.md`) are appended
  verbatim, as for every library. `tests/unit/agents/runtime/test_policy.py` runs the
  prompt's idioms through both Julia validator profiles (`JULIA_PROMPT_IDIOMS`), and
  `test_profile_julia_image.py` renders them from a `data.csv` with missing cells. The
  Python prompt is byte-identical (its SHA-256 pin holds). The agents image's build check
  composes the Julia adapter instruction and highlights section; `ci-image.yml` checks
  `adapter_julia.md` and `makie.md` in the image and runs the readiness scan through the
  runtime. The scope judge and the `other_library` reply already read `AGENT_LIBRARIES`
  (no change).
- **Evals.** `make_fixtures.py` writes the ten specs for Makie (60 cases, 480 generated,
  487 in a full run) with the smoke case `scatter-basic-makie-renamed` (18 smoke cases);
  all ten Makie files are `coupled`. `eligibility.py` sweeps Makie; `dev_fixture`,
  `matrix.py` and `stress.py` needed nothing beyond 3b's generalisation. `ladder_lab.py`
  summarised a failed render with Python's grammar for every library; it now uses the
  runtime's, as the pipeline does.
- **Deploy and app.** `agents/cloudbuild.yaml` `_LIBRARIES` gains `makie`;
  `AGENT_LIBRARIES`' default stays `matplotlib,seaborn`. The app already mapped `makie` to
  Julia, highlights Julia, has `.download('plot.jl')` and lays out `.plot_all()` for any
  number of libraries: no change.
- **Verified locally, without a model.** A scripted identity adaptation of
  `scatter-basic-makie-renamed` (the data block replaced by the placeholder and two column
  constants, the vectors read from `df`, a German title) with an added timestamp column
  `Erfasst am` (offsets `+01:00`, `-05:30`, `+02:00`, `Z`, microseconds and missing cells)
  passed the pipeline's check, took the Julia loader and rendered through
  `LocalDockerBackend` on `anyplot-renderer:julia` (J1.1's workload): 3200x1800 in both
  themes, 3200x1864 with the footer strip, R1 to R3 passed, 5.7 s of wall time per theme
  (both themes at once); the same container with its stdout kept reported `exec_deny: on`,
  6.1 s of CPU and 1,014 MiB. The kinds counted 60 timestamps below the millisecond, the
  note named them first in "what changed" and the result stayed `ok`. Two forced failures
  after the loader (30 lines past the working form's):

| Forced failure | stderr | Summary before J2b | After |
|---|---|---|---|
| `Legend(fig[1, 2], sqrt)` | 2,039 characters | "an error (the tail cut off its first line) at line 116; in Legend()" | "MethodError for initialize_block!() at line 86; in Legend()" |
| `text!(ax, ...; text = 1.5)` | 10,608 characters | "an error (the tail cut off its first line) at line 116; in text!()" | "an error at line 86; in text!()" |

Makie's compute pipeline reports a deep failure as "Failed to resolve ...", which names
no Base exception type, so the second stays "an error"; it no longer claims a cut tail.

| Text above | Built | Why |
|---|---|---|
| `vspan!` with DateTime bounds breaks a following `lines!` (J1.1) | The prompt says spans, bands and vertical lines (`vspan!`, `hspan!`, `vlines!`, `band!`) fail on a time axis in any order, and the plot then puts time on the axis as numeric offsets with ticks from the data, as the catalogue's `line-timeseries` does | Measured in J1.1's image: `vspan!` after `lines!` fails too ("Cannot change dim conversion"), and `hspan!`, `vlines!` and `band!` fail the same way; `lines!`, `scatter!`, `barplot!`, `text!` and `hlines!` take a `Date` or `DateTime` axis |
| The runtime subtracts the loader's line count (J2a) | `error_summary(stderr_tail, *, run_form=None)` on the contract; the pipeline passes the run form | The summary sees only the stderr tail; the loader's span depends on the columns, and the run form is what ran. A keyword leaves Python's and R's summaries as they were |
| R's note in `RRuntime.loader_notes` | The fitting moved to `runtimes/notes.counted_note`, which R and Julia call | One copy of the 200-character fitting; R's output is unchanged |

#### Eligibility after J2b

`uv run --extra agents python -m agents.evals.eligibility` on 2026-10-30: the seven rows
of 3b unchanged, and Makie through its runtime:

| Library | Files | Eligible | Clean | Coupled | Blocked |
|---|---|---|---|---|---|
| makie | 325 | 308 (94.8 %) | 0 | 308 | 17 |

Makie's 17 blocked files are the 13 map specs, qrcode-basic (QRCoders and a URL) and the
three saves inside `with_theme(...) do`; `test_eligibility.py` pins the counts.

#### Next

- The owner's matrix run for Makie on Vertex (60 cases), the gate for the public release;
  `AGENT_LIBRARIES=...,ggplot2,makie` for a smoke or full run.
- A deployed sweep with the workload, which revises `render_p95_s` (25 s).
- Python's error line still counts the run form, a few lines past the working form's
  after its loader; the same keyword would let it name the working form's line, a change
  of Python's feedback the owner decides.
- The owner task for the `deploy-renderer` trigger's included files (`Project.toml`,
  `Manifest.toml`) stays open.

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
- `uv run --extra agents python -m agents.evals.eligibility` (the sweep prints
  eligible, coupled and blocked pairs for every Python library with a code profile,
  `eligibility.LIBRARIES`; it takes no library flag since 1b)
- `docker build -f agents/renderer/Dockerfile -t anyplot-renderer:dev .` then, for one
  catalogue file per language, `AGENT_RENDERER=local` through
  `tests/image/render_smoke.py` (new; the local backend with `--network none`)
- `cd app && yarn lint && yarn fm:check && yarn type-check && yarn test`
- `uv run python -m tools.changelog check --base origin/main`
- Owner, per library, on Vertex: `AGENT_LIBRARIES=matplotlib,seaborn,<library>
  uv run --extra agents python -m agents.evals.matrix --model claude-haiku-5-5
  --cases '*-<library>-*' --renderer remote --render-url <url>` (the library must be
  enabled in the harness's own process, or the readiness scan blocks every case as
  `library-disabled`; `--cases` takes `smoke`, `full`, `stress` or globs over case ids,
  `agents/evals/cases.py`); 80 %
  pass after at most one repair enables the library in `agents/cloudbuild.yaml`
  (`_LIBRARIES`).

## Measurements to take first (spikes, local Docker)

| Spike | Question | Where it decides |
|---|---|---|
| JS | Chromium under `--network none --read-only`: render time and peak RSS for chartjs, d3, echarts, highcharts, muix on `scatter-basic`; does a 1 GiB `RLIMIT_AS` kill it (expected yes) | step 3's limits |
| Python extras | plotnine, altair, pygal, lets-plot under `harness.py` plot mode: which writes, spawns or imports the guard refuses | steps 1b and 1c's allowlists |
| plotly, bokeh | whether a browser started from plot code (kaleido, Selenium) survives the plot guard; the answer below is no, hence step 4's screenshot through the JavaScript harness | step 4's design |
| R | image size with the setup-r package set; `Rscript` render time | step 2 |
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

**Julia through `julia --project=/opt/julia`** (Docker, `julia:1.13` with the repository's
`Project.toml` and `Manifest.toml` instantiated and precompiled into `/opt/julia-depot`
under the pinned `JULIA_CPU_TARGET`, `JULIA_PKG_PRECOMPILE_AUTO=0`; at run time
`JULIA_DEPOT_PATH=/tmp/depot:/opt/julia-depot`, `--network none --read-only --tmpfs /tmp`;
4 CPUs, no other load):

| Measurement | Result |
|---|---|
| Image, depot | 2.57 GB, of which the depot is 1.4 GB; instantiate 263 s, precompile 821 s (CairoMakie 0.15.16, Makie 0.24.16, CSV 0.10.17, DataFrames 1.8.2) |
| Cold render, container start included | `scatter-basic` 10.0 to 10.8 s, `bar-grouped` 16.9 to 17.4 s, `heatmap-basic` 19.3 to 19.6 s; no precompilation at run time (the depot's pkgimages load) |
| Peak RSS | 956 to 1,045 MiB |
| `ulimit -v 1048576` (1 GiB) | `LLVM ERROR: out of memory`, exit 134 |
| `ulimit -v 4194304` (4 GiB) and `ulimit -u 64` | renders as without a limit |
| `julia -t 1` | no measurable change |

Consequence: Julia ships synchronously (question 4: the cold render is well under 45 s on
4 CPUs; at 2 vCPU expect roughly twice, still under the 60 s timeout, to be confirmed on
the deployed renderer); `RLIMIT_AS` off for the Julia row, `RLIMIT_NPROC` 64 holds; the
1 GiB peak sits inside the 4 GiB instance with one slot, above the 512 MiB watchdog floor,
so no instance change for Julia alone.

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
| Image: pin the base image by digest; Highcharts in a public image is a redistribution question; bake `fc-cache`, `XDG_CACHE_HOME=/tmp`; Julia offline flags; `libcairo2` for cairosvg; the `ci-image.yml` change filter | Steps 1c, 2, 5 and questions 1 and 11 (the base image is private, so it redistributes nothing) |
| `render.mjs` takes the library from the file stem; MUI X imports are inlined by esbuild | `--library=` from the request against the closed set; a static-import allowlist for `.tsx` |
| Deny lists are hygiene, not a boundary: `globalThis["fe"+"tch"]`, `[].constructor.constructor`, R `get("system")`, Julia `getfield(Base, Symbol(...))` pass any identifier list | The threat model is stated: the sandbox protects the service, the list protects the person who runs the export from accidental I/O by the model; the lists grew by the review's names, and Julia's `using`/`import` is an allowlist |
| Order: R first as the smallest exec-mode pilot, then JavaScript, then plotly and bokeh on the proven Chromium path, then Julia | Adopted (question 3) |

Unverified by the review and still open: kaleido 1.x honouring `BROWSER_PATH` (moot
with step 4's design), gVisor's `RLIMIT_DATA` and `RLIMIT_NPROC` semantics, Chromium's
cold start under gVisor.

## Second opinion on steps 2 and 5 (Gemini 4 Argon and Fable, 2026-10-28)

Both: sound with changes. The revision of steps 2 and 5 above already carries what was
adopted; the claims about the code were checked, and the critical one was reproduced.

| Finding | From | Change |
|---|---|---|
| Under an `EPERM` exec filter R does not start: `utils` loads through `Sys.which("uname")`, and `stats` and ggplot2 follow it | Fable (measured; reproduced with R 4.3.3) | The preload filter answers `SECCOMP_RET_KILL_PROCESS`; gVisor's support is checked by the first deployed R smoke, with an `EPERM` plus interposer fallback |
| A missing preload object or a static binary runs the child unfiltered, with exit 0 | both | The harness refuses the result unless the pipe said `on`; the constructor closes the pipe and drops its variable |
| `LD_PRELOAD` in the sandbox's environment would load into the harness's Python | Fable | The harness builds the child's environment; `RuntimeCommand.exec_deny` replaces a check by language name |
| Linked libraries' constructors run before the preload's and may start threads | both | `SECCOMP_FILTER_FLAG_TSYNC` and the fork probe |
| R's direct binary needs `R_HOME`, `LD_LIBRARY_PATH` and a UTF-8 locale | both | In the R row (2b); `LANG=C.UTF-8` for Julia too |
| Installing `fontconfig` for `fc-cache` puts `fc-list` and `fc-match` on `SANDBOX_PATH`, which `delegates.py` refuses | Gemini | `fc-cache` in a builder stage |
| The `renderer-image` job has no `id-token` permission, and Dependabot runs without secrets | Gemini | `id-token: write`; build the toolchain when no login is possible |
| A literal `FROM image@sha256:` cannot take a toolchain CI built itself | both | `FROM ${TOOLCHAIN_IMAGE}:${TOOLCHAIN_TAG}`, the digest in the tag |
| The trigger and lock-bump flow races the deploy and costs a PR per toolchain change | Fable | Owner decision of 2026-10-28: the deploy builds the toolchain when its hash tag is missing, with a registry cache |
| `setup-r`'s snapshot note is parsed by `core/library_versions.py` | Gemini | The note stays; a test pins the toolchain's URL to it |
| `Base.compilecache` spawns a worker on any cache miss | both | `--compiled-modules=existing`; the spawn fails fast under the filter (measured) |

Still unverified: gVisor and `SECCOMP_RET_KILL_PROCESS`; the Posit `debian-13` package's
dependencies and library path; Cloud Run's image streaming under `sandbox do`; the
Cloud Build machine Julia's precompile needs. A later simplification to keep in mind
(Fable): embedding R through `libR` in the harness would put R under the in-process
filter with no preload at all.

## Second opinion on step 5 (Gemini 4 Argon and Fable, 2026-10-29)

Both: sound with changes. The owner approved the corrections and took the decisions
below on 2026-10-29; step 5 above carries them, and J1 built the first part. Each row
names who raised it; "verified" marks a claim reproduced in `julia:1.13.2` that day.

| Finding | From | Change |
|---|---|---|
| The root `.dockerignore` (an allowlist), `toolchain.py`'s `INPUTS` and `ci-image.yml`'s `RENDERER_CHANGES` lack `Project.toml` and `Manifest.toml`, so the Julia stage's `COPY` fails and a Manifest change skips the image job; the job's 25 minutes do not fit a cold toolchain build | Gemini | All four fixed in J1 (5b); the job has 60 minutes |
| The deploy builds the toolchain on the default machine within 1800 s and without a layer cache, so an R change reruns Julia's precompile | both (Fable proposed a nested toolchain build, Gemini a larger machine for the whole deploy) | Owner decision: the whole deploy on `E2_HIGHCPU_8` with 3600 s, not a nested toolchain build; a BuildKit registry cache on the fixed ref `anyplot-toolchain:buildcache` (5b) |
| `--compiled-modules=existing` (the 2026-10-28 text, and Gemini's proposal) loads a missed package from its source in process, with exit 0 and no message; the 2 s spawn kill under the filter belongs to the default `yes` | Fable (verified) | `--compiled-modules=strict`, which fails in about a second (5c); CI forces a miss and checks it |
| The row runs `julia` by name, which `SANDBOX_PATH` lacks, and carries neither the startup flags nor the thread and locale settings; under a 4 GiB cgroup Julia sizes its heap against the whole instance (verified) and its OpenBLAS starts a thread per core | Gemini, Fable | `JULIA_BINARY` by its path, the flags and environment of 5c; `--heap-size-hint=1536M` (Fable's value; Gemini proposed 2G) and `OPENBLAS_NUM_THREADS=1` |
| Nothing proves before traffic that the depot's package images load under gVisor | Gemini | A Makie render in the deploy's candidate smoke, with its wall time (5b) |
| `DateTime(s)` refuses microseconds, `+01:00`, `Z` and a space separator, and TimeZones.jl is only a transitive dependency | both (verified) | Owner decision: TimeZones as a direct dependency, offsets to UTC, microseconds truncated to milliseconds and announced with counts, the status the render's (5d) |
| Reading `big-integer` as `Float64` would lose digits Julia need not lose; `CSV.read` takes `NA` as missing by default | Gemini | Both integer kinds as `Int64`, exact to 2^63, so no integer note; `missingstring = ""`, explicit true and false strings, `strict = true`, `normalizenames = false`, `pool = false` (5d) |
| An identifier list misses string interpolation, broadcast calls, `Core.eval`, `Base.Libc`, `getproperty`, `import … as` and file writes | both | The validator refuses by shape, as R's does (5d) |
| RDatasets and PalmerPenguins (PalmerPenguins downloads at run time) | both | Kept in the project, one lockfile with the pipeline; refused as the adaptation finding `dataset-package` (5d) |
| The catalogue was written for Makie 0.21 and 0.22 and runs on 0.24 (`arrows!`, `NoShading`); four files save through `joinpath(@__DIR__, ...)`; `THEME` is `const` in some files; all 325 parse with tree-sitter-julia, none uses DataFrames, `qrcode-basic` needs a package outside the project and `map-tile-background` downloads | both (Fable parsed the 325 files) | J1 renders all 325 files ("What J1 built"); the normaliser takes both `THEME` forms and rewrites the four saves (5d) |
| A cold render at 2 vCPU may come close to the 60 s timeout | Gemini | Measured locally at 2 CPUs in J1; the measurement stage times it on Cloud Run, and a `PrecompileTools` workload joins only above about 25 s (5e) |
| The error grammar and the column access need a Julia form | Fable (verified) | The first `ERROR: LoadError:` line, the first plot frame and the last `in expression starting at` line; the adapter introduces `df[!, COL]` (5d) |

## Second opinion on steps 3 and 4 (Gemini 4 Argon and Fable, 2026-10-30)

Both: sound with changes. The owner was asleep; the corrections both reviewers agree on,
and those Fable verified, are adopted in steps 3 and 4 above, and two decisions are open
(questions 12 and 13). Each row names who raised it; "verified" marks a claim Fable
reproduced that night, and "measured" one that JS-1 measured.

| Finding | From | Change |
|---|---|---|
| esbuild bundles any file a `.tsx` snippet imports, image files included (`import x from "/etc/os-release"`) | both (Fable verified) | JS-2's `onResolve` plugin admits only allowlisted bare specifiers resolved under `ANYPLOT_NODE_MODULES`; the allowlist is derived at image build from the installed packages' `exports` maps (JS-1 built it: 219 specifiers) |
| `node` by name contradicts `delegates.py`, which refuses `node` on `SANDBOX_PATH` | both (Fable verified) | `NODE_BINARY` by its path (3c); the delegate list does not change |
| Chromium's packages bring `libpango-1.0-0` and with it `fc-list` and `fc-match` | Gemini (unverified); Fable: the headless shell links neither | The headless shell alone (273 against 403 MB, Fable verified); its libraries found with `ldd`, none brings the `fontconfig` package or Pango (measured), libgbm unpacked without Mesa (3a) |
| The plot-mode harness cannot start a program once its guard is armed, so a screenshot child after the plot is impossible | both | PB-1: a two-step exec mode that forks the plot's child before arming (step 4) |
| plotly and bokeh: the old text's HTML save needs Jinja's `exec` under the guard and puts model-written HTML in front of the unfiltered Chromium; the catalogue's bokeh canvas is past R2's cap | Gemini | The spike's JSON route as PB-2's default (`write_json`, `json_item`, the page built by the harness at the canonical canvas, `CustomJS` refused); PB-2 measures it first |
| The data: types in an environment variable break the wire contract and `theme_render.py`, and a downloaded file would run untyped | Gemini proposed the raw CSV in the page and a JavaScript parser baked into the source; Fable proposed typed JSON written by Python | They disagreed. Adopted: Fable's, because it keeps one reader of the canonical CSV; the job carries the JSON, which answers Gemini's wire and theme points (3d, JS-4) |
| `window.ANYPLOT_DATA` must escape `<`; `new Date("2026-03-01T00:00")` is local midnight | Fable (verified) | `<` escaped and `timezoneId: "UTC"` (3d); the row's `TZ=UTC` since JS-1 (measured) |
| Error lines: Gemini expected the inlined bundle to shift the snippet's line numbers and proposed `//# sourceURL`; MUI X's bundle is minified | Gemini; Fable measured an offset of exactly 1 (the snippet has its own `<script>`, its first line `try {`) | They disagreed. Adopted: Fable's offset of 1; MUI X errors name the class (3e) |
| Errors after the ready signal still reach `pageerror`; console errors print only on success and are unbounded (20,000 lines, 4.2 MB) | Fable (verified) | Caps on count and bytes, and the bounded tail on failure too (3d) |
| `page.route` misses WebSockets, and `window.open` popups bypass it; blob workers and `import("data:...")` run | Fable (verified) | `routeWebSocket` closes every socket and `--block-new-web-contents` nulls `window.open`; workers and data imports stay inside a page without network (3d) |
| A content security policy, Chromium flags (`--disable-dev-shm-usage`, `--disable-gpu`), V8 and Node heap caps | Gemini (unverified) | Measured against the sweep in JS-2 before any is adopted; Node runs only the harness, so no `NODE_OPTIONS` (3c) |
| The toolchain's hash, the `.dockerignore` and `RENDERER_CHANGES` lack `package.json`, `package-lock.json` and `automation/js-render/` | both (Fable verified) | All three added in JS-1, with tests (3b) |
| The catalogue's page font stack names Helvetica and Arial, and the image has only DejaVu and Noto | Fable (verified) | Liberation for the JavaScript row alone through its own fontconfig file, because system-wide it changes 3 of 40 sampled Python renders (measured, 3a) |
| `export.py` writes `#` headers, a syntax error in JavaScript and TSX | Gemini | `//` headers for JavaScript (3e); the run line follows question 12 |
| The edit applier's dialect: the token lines, the orientation directive, `//` comments, `#` inside CSS and SVG strings | Gemini | JS-3's JavaScript dialect (3e) |
| `adapter.md` hard-codes `df` outside its slots, and its prompt hash is pinned; `review_texts` | Gemini | `adapter_javascript.md` fills the slots and `adapter.md` stays; `review_texts` on (3f) |
| Data fidelity: integers past 2^53, booleans, dates, datetimes with offsets, `+null === 0` | Gemini | R's precedent: counted notes, UTC ISO strings, a prompt warning (3f) |
| The MUI X files written for 7.29 | Gemini: normalise the mechanical renames, regenerate the fixture specs, block the rest; Fable: serve them `coupled` with a hint derived from the exports allowlist | They disagreed: question 13. JS-1's sweep: 52 of the 196 fail, all on `ChartContainer` (3, "What JS-1 built") |
| The export cannot be `plot.js` alone | Fable | Question 12 |
| Renders take 0.5 to 0.7 s; all 1,617 files in about 20 minutes; the image grows by 0.6 to 0.7 GB | Fable | Measured in JS-1: wall p50 1.2 s with the container's start, under 10 minutes four at a time, +565 MB |
| Bake a fontconfig cache after the renderer's fonts | Gemini | Not measured; Chromium, R and Julia scan the fonts in every render today |

## Second opinion on JS-4a (Gemini 4 Argon and Fable, 2026-10-30)

The owner asked for JS-4 "mit Zweitmeinung"; both reviewed the JS-4a diff before its PR.
Both: sound with changes, nothing that widens the boundary, the data path correct in
every render path. Each finding was checked against the code before it was adopted.

| Finding | From | Change |
|---|---|---|
| A JavaScript loader note passes the 200-character change-note cap with 64-character column names (measured 201 to 208), which `PlotResult.changes` refuses | Gemini | `counted_note` cuts the first column's name with an ellipsis when even it does not fit, for every language; a test at the limits for R, Julia and JavaScript |
| A cell the typing cannot hold left the page without a table, and the repair blamed the plot code's first `data.map` | both | `data_json` raises, the pipeline drops the kinds, the loader refuses the run form with its reason |
| The shared palette paragraph tells the adapter to append to a list that catalogue JavaScript does not have, and to put `INK_MUTED` after it | both | `palette_literal` states the closed case (`t.palette` holds all eight, never a list of your own, `INK_MUTED` after the token lines); a shared palette slot is left for the next `adapter.md` revision |
| `new Date(null)` is 1970 and a string method throws on `null`; the date idioms map before filtering | Gemini | The `null` list names both, and the dates slot filters `d[DAY] != null` first |
| Text from the data into `innerHTML` or an HTML tooltip runs as markup in the exported page | Gemini | The safe-code slot sends data text to `textContent` or the library's plain text |
| The deploy gate is right, but a failed render answers 200, which curl's retries never see | both | A second try 30 s later; each failure prints the exit code, the reason, the attempts and the stderr tail |
| `fmt(-0.001, 2)` writes `-0,00`; `reduce` without a start throws on an empty table | Gemini; Fable | `fmt` rounds before the sign; the highlight's `reduce` starts at `null` |
| The root prompt names the R and Julia "converts" notes nowhere | Gemini | One line for "R converts", "Julia converts" and "JavaScript converts" |
| The pipeline leg (`_attempts` to the job, the version and the toggle) had no test | Fable | A service-flow test with a D3 session through the fake backend |
| Not adopted: `normalise` and `validate` ignore their `library` argument | Gemini | The runtime is bound to its library, as `JuliaRuntime` is |
| Not adopted: the image checks name one library file per language | Gemini | The Dockerfile copies `prompts/library/` whole; one file per language is the existing pattern |
| Open until JS-4b: the export header and the root prompt name `plot.html`, which JS-4a does not ship | Fable | Admin-only until then; JS-4b is next |

Cost: Gemini 4 Argon $1.45 (5 turns, 881,600 input tokens, 647,916 cached); Fable about
157,000 tokens.

## Second opinion on JS-4b's design (Gemini 4 Argon and Fable, 2026-10-31)

Both reviewed the draft of 3g before JS-4b-1 was built; the findings below are adopted in 3g.
"Measured" marks a claim Fable reproduced in Chromium.

| Finding | From | Change |
|---|---|---|
| A `srcdoc` frame inherits the wrapper's content security policy, so the draft's stricter wrapper policy (`default-src 'none'` without `script-src 'unsafe-inline'`) blanks the plot; `frame-src 'none'` does not block the `srcdoc` itself, but blocks the frame's navigation of itself to http(s) | both (Fable measured) | The wrapper's policy is exactly the harness's plus `frame-src 'none'`, pinned to the harness's constant by a test |
| Build the page on demand instead of storing it next to the PNGs: a page is the bundle plus the typed table, up to about 17 MB | both | `GET .../artifacts/plot.html` builds it per request through the renderer's `POST /page` |
| `PlotResult.artifacts` caps at four, and a JavaScript version with both themes and the page has five | Gemini | The cap is five (`schemas.MAX_ARTIFACTS`) |
| The agents service deploys before the renderer, and an older renderer has no `/page` | Gemini | A `404` raises `PageUnsupported`, answered `503 page_unavailable` |
| One page per shown theme: the page carries the theme's tokens, so the download follows the theme on the card | both | `?theme=`, defaulting to the version's theme; the card asks for the theme it shows |
| Split JS-4b into the download (JS-4b-1) and the in-chat preview (JS-4b-2), whose delivery needs a decision | both | JS-4b-1 is the download; JS-4b-2 waits for the owner's decision below |

**How the preview reaches the chat (JS-4b-2).** The reviewers disagreed. **Decided (owner,
2026-10-31): A**, built as "What JS-4b-2 built" describes.

- **(A) Gemini: a relay page.** A static, unauthenticated page on api.anyplot.ai, served with
  `Content-Security-Policy: sandbox allow-scripts; <the page's policy>; frame-ancestors <the
  site's origins>`, receives the page by `postMessage` from the chat (it checks the sender's
  origin) and writes it into a sandboxed `srcdoc` child. No token travels, and Cloudflare
  Access does not stand in the way.
- **(B) Fable: a capability URL.** A short-lived HMAC URL (its own key; the payload
  `user_id|sid|version|theme|exp`, about five minutes), served only when the request says
  `Sec-Fetch-Dest: iframe`, because Fable measured that the URL opened directly as a tab lets
  the plot code navigate the tab, and kept outside `/debug/*`.

## Second opinion on JS-4b-1's code (Gemini 4 Argon and Fable, 2026-10-31)

Both reviewed the JS-4b-1 commit before its PR: sound with changes.

| Finding | Decision |
|---|---|
| The page build holds the session's run entry on the server, but the card alone knew it was building, so a theme toggle, a message or a binding edit during the build got `409 run_active` | Adopted: `useAgentSession` tracks the build (`pageBusy`, part of `sessionBusy`), so the page holds the composer, the toggles and the edits back while `plot.html` builds, and starts no build while one of them runs |
| The page download counted as `downloaded_code` | Adopted: its own outcome, `downloaded_page`, in the closed set of the agents service, the BFF and the page (pinned equal by a test), counted as a keep by the API's usage card. The view files that enumerate the actions name it too (`agents/telemetry/views/02_event_views.sql` `keeps`, `06_score_outcomes.sql` `downloads`, the comment in `03_sessions.sql`); re-creating the views in BigQuery after the merge is the owner's step, and until then a page download is an outcome that keeps nothing there |
| The probe covered three of the four served libraries | Adopted: a Highcharts snippet, in the image test's `--hover --attempts` run; a comment says that `chrome-error://chromewebdata/` is what a blocked navigation looks like |
| "Byte for byte" for the `srcdoc` | Adopted: character for character, apart from the input stream's normalisation (CR LF and a lone CR become LF, NUL becomes U+FFFD), as on any load of the page |
| `/cancel` does not abort a page build | Not adopted: a build takes about 0.6 s, and the theme toggle, which renders far longer, does not stop on `/cancel` either |
| A cap of its own on the BFF's stream of `plot.html` | Not adopted: the agents service refuses a wrapper over 30 MiB before it answers, and Cloud Run caps a response that is not streamed at 32 MiB |
| Before the chat is public: the wrapper makes three or four transient copies of a page of up to 24 MiB (the decode, the two replaces, the encode), about 100 to 150 MiB at peak per build on the 2 GiB agents instance | Open: stream the wrapper, or do the replaces on bytes |
| Before the chat is public: a page too large to answer is `500 page_failed` | Open: answer it `413` with its own code |

## Second opinion on JS-4b-2's code (Gemini 4 Argon and Fable, 2026-10-31)

Both reviewed the JS-4b-2 commit before its PR: sound with changes, no hole in the isolation.

| Finding | Decision |
|---|---|
| Fable, measured: when something else answers `/preview/relay` (a Cloudflare 5xx or challenge page, a misconfigured Access, a future route that shadows the path), the one-shot `*` post on `load` hands it the user's page; Fable's own 404 page with a listener received the whole page | Adopted: a handshake. The relay posts the constant `"anyplot-relay-ready"` to its parent, its only message and one without content; the chat posts only on that signal from the relay frame's own window, once per mount, removes its listener on unmount, and shows `relay_unavailable` after 10 seconds without it. The probe frames a listening 404 page at the relay's URL (it receives nothing; a post on load, the control, hands it the page) and has the plot send the signal to the top (no post) |
| Gemini, medium: a collapse, by a click or when a newer version arrives, kept `pages` (up to two pages of 24 to 30 MiB per card), and a build still under way filled them and reported `opened_preview` after it | Adopted: one `dropPreview` (a new run number, the preview closed, the pages and the error dropped) for `.preview()`, the collapse and a newer version; a test each for the collapse with a build under way and for the newer version |
| Both, low: the frame's orientation came from the PNG's aspect, so a square plot whose PNG had not loaded or had failed was framed as a landscape one at 0.7 | Adopted, the preferred fix: the size comes from the page, the wrapper's first `.frame { width: Npx; height: Npx; }` rule, pinned to `render/page.py`'s output by a test (with a decoy rule inside the page); a page without the rule gets the landscape frame |
| Gemini: the one-shot guard had no failing negative control, and `self_navigation_blocked` passed whether or not the frame's navigation ran | Adopted: the parent posts a second page after the first (`second_page_ignored`, which fails without the flag), and the plot's frame must have left `about:srcdoc`, in the relay mode and the download's check |
| Fable, info: the relay frame follows `VITE_API_URL`, the chat `VITE_DEBUG_API_URL` | Adopted: the mock's header says so; with only `VITE_DEBUG_API_URL` on the mock, the browser runs the production relay instead of the checkout's |
| Gemini: drop `http://localhost:*` from `frame-ancestors` in production | Not adopted (Fable: acceptable as it is): the BFF's Origin check accepts the same origins, and the relay holds no data and has no network, so a local page framing it gains nothing |

**Checks after the deploy:**

- One live preview in the admin chat: `.interactive()` on a Chart.js plot shows the plot and
  answers a hover, in both themes, with a clean console.
- Whether a Cloudflare bot challenge ever hits `/preview/relay` inside the sandboxed frame. The
  frame has no `cf_clearance` cookie, so a challenge would loop; the card then shows
  `relay_unavailable` after 10 seconds, and the challenge page gets nothing.

## Open questions for the owner

Defaults apply until answered; each is marked where the plan uses it.

1. **Image layout.** (A) one `agents/renderer/Dockerfile` that builds every toolchain
   (fast only with a layer cache in CI and in Cloud Build, which builds the renderer
   without one today, and with the layers ordered by how often they change; a cold
   cache rebuilds every toolchain, and Julia's precompile alone took 18 minutes in the
   spike), or (B) a toolchain base image built on lock-file changes, with the renderer
   image `FROM` it by digest (fast CI and deploys).
   **Decided (owner, 2026-10-25): B, with the base image private in Artifact Registry**
   (the repository `anyplot` in `europe-west4`, where the renderer image already lives).
   A Cloud Build trigger builds and pushes it with Cloud Build's own service account, and
   the renderer's Cloud Build deploy pulls it the same way. The CI job `renderer-image` in
   `ci-image.yml` pulls it through the Workload Identity Federation login that
   `ci-tests.yml` already uses, which needs the Artifact Registry reader role on the
   repository: an owner task when step 2 adds the base image. Not public on GHCR: a
   public image is a redistribution (licence notices for everything in it, no
   Highcharts), and its only gain was pulls without a credential. **How it is built
   (owner, 2026-10-28, after the second opinion):** not by a trigger of its own; the
   renderer's deploy builds and pushes the toolchain when the tag of its inputs' hash is
   missing (step 2a).
2. **Base distribution.** Its premise no longer holds: on 2026-10-28 Posit serves
   R 4.6.1 for `debian-13`, `ubuntu-2404` and `ubuntu-2604`, and the Package Manager
   snapshot 2026-10-20 has the same compiled binaries (ggplot2 4.0.3, ragg 1.5.2) for
   trixie, noble and resolute, so every option installs the pipeline's package versions.
   What differs is the system's font stack, which ragg uses and Python's renders already
   live with:

   | | Debian 13 (`python:3.14-slim`, the renderer today) | Ubuntu 26.04 (the catalogue's CI runner) |
   |---|---|---|
   | freetype, harfbuzz, fontconfig, cairo | 2.13.3, 10.2.0, 2.15.0, 1.18.4 | 2.14.2, 12.3.2, 2.17.1, 1.18.4 |
   | Python stack | unchanged: the six libraries' image steps, the lets-plot bridge's fontconfig, the delegates check and the matrix results stay valid | moves to a uv-managed Python 3.14; every Python image step and each library's matrix run again |
   | R renders against the catalogue's | close, not identical (text shaping and hinting can move a label by a pixel) | the same system libraries as the runner that rendered the catalogue |
   | Julia, JavaScript | the same either way: Julia's JLLs and Chromium bring their own libraries | the same |
   | Recipes | Posit and Package Manager support Debian 13; rocker and most R Docker recipes are Ubuntu | rocker's layout and `setup-r` apply almost verbatim |

   **Decided (owner, 2026-10-28, after the second opinion): Debian 13.** The agent
   re-renders and the host gates judge the render, not its closeness to the catalogue's
   PNG; moving the Python stack would cost a full re-verification for a pixel-level gain
   in R alone. Gemini 4 Argon and Fable agreed.
3. **Order.** The design lists plotly and bokeh before JavaScript; this plan takes the
   seam first, then plotnine and altair, pygal and lets-plot, then R as the smallest
   exec-mode pilot, then JavaScript (five libraries, one runtime), then plotly and bokeh
   on that Chromium, then Julia. Default: this order.
4. **Julia.** Ship it in this round only if the cold render fits 45 s; otherwise defer
   it behind the submit-and-poll renderer change. The spike measured 10 to 20 s cold on
   4 CPUs with the precompiled depot, so the default is now: ship synchronously, and
   confirm the time at 2 vCPU on the deployed renderer before enabling.
   Measured on 2026-10-29 with J1's toolchain (local Docker, 2 CPUs, `strict`): see
   "What J1 built" under step 5; the deployed cold and warm numbers are the measurement
   stage's (5e). **Decided with the second opinion on step 5 (owner, 2026-10-29):**
   `--compiled-modules=strict`; datetimes through TimeZones.jl (offsets to UTC,
   microseconds truncated to milliseconds and announced, the status the render's); the
   whole renderer deploy on `E2_HIGHCPU_8` with a longer timeout rather than a nested
   toolchain build.
5. **Renderer memory.** If the spikes show Chromium or Julia near the 512 MiB
   `MemAvailable` floor on a 4 GiB instance, the renderer goes to 8 GiB (cost).
   Default: measure first.
6. **Highcharts licence** for user plots is an open decision in the design; admin-only
   use stays as today. Default: Highcharts ships behind the same `AGENT_LIBRARIES`
   switch and is not enabled until decided. **Decided (owner, 2026-10-30): Highcharts is
   served like the other libraries**, under Highcharts' non-commercial licence, as long as
   the site charges nothing; the decision is revisited before any revenue (advertising, a
   sponsorship, a paid tier). JS-4a enables it with Chart.js, D3 and ECharts.
7. **The 80 % matrix gate** per library needs the owner's Vertex run (Todoist task per
   library). Default: the gate stays.
8. **Non-Python validator** as a tree-sitter deny list (four grammar wheels in the
   `agents` extra), as the design names for JavaScript, with the threat model stated
   in "Second opinion". Default: yes, for R and Julia too.
9. **bokeh and plotly screenshots** through the JavaScript harness's Chromium as a
   second exec-mode child, after the plot code wrote the page; not Selenium with a
   shipped chromedriver (the design's note), and not Playwright for Python (it spawns
   a Node driver under the guard). Default: the harness child. **Revised by the second
   opinion on steps 3 and 4 (2026-10-30):** an armed harness cannot start that child, so
   PB-1 forks the plot's child before arming and screenshots from the unarmed parent,
   and the plot writes JSON, not a page (step 4).
10. **Exported code for bokeh and plotly** keeps the catalogue's own save block while
    the run form saves the figure for the sandbox (JSON since the revision of
    2026-10-30): the one place where the export is not byte for byte the run form
    (agent-network.md, "Fencing and exported code"). Default: accept the deviation for
    these two libraries and document it there. **Decided by the owner on 2026-10-31:**
    accepted; the export keeps the library's normal save, which runs unchanged on the
    user's machine with `data.csv`, and an interactive `plot.html` with `.interactive()`
    follows for both libraries (PB-2b). Built in PB-2a (`code/figure.py`, "What PB-2a
    built") and documented in agent-network.md.
11. **Highcharts in a public toolchain image**: the free licence covers non-commercial
    use, and a public GHCR image redistributes the bundle. **Settled by question 1
    (2026-10-25):** the base image is private in Artifact Registry, so it redistributes
    nothing, and Highcharts can live in it. Whether users' plots may use Highcharts stays
    question 6.
12. **The JavaScript export.** The catalogue's snippet does not run by itself: it needs the
    harness's page, its tokens and the library bundle, so a downloaded `plot.js` next to
    `data.csv` does not open anywhere (second opinion of 2026-10-30, Fable). (A) export a
    self-contained `plot.html` (the bundle, the tokens, the data and the snippet inlined,
    the page the harness already writes for the catalogue's interactive view), which opens
    in any browser; or (B) export `plot.js` (or `plot.tsx`) alone with a header that names
    the harness (`node render.mjs --library=<library> plot.js`), which runs only in a
    checkout of the repository. **Decided (owner, 2026-10-30): both, and the PNG.** A
    JavaScript plot offers the PNG, the self-contained interactive `plot.html` and the code
    file (`plot.js`, `plot.tsx` for MUI X), each viewable and downloadable. The code file's
    header is two `//` comments, and its run line names the page, not Node: `// run: open
    plot.html in a browser, which runs this code with the chart library, the light theme
    and your data` (JS-3, `code/export.py`); the page and its artifact are JS-4's.
13. **The 196 MUI X files written for 7.29.1.** The lock pins MUI X 9.16; JS-1's sweep
    rendered 144 of them unchanged and failed 52, all on `ChartContainer`, which 9.16 no
    longer exports. (A) serve them `coupled`, with a readiness hint derived from the
    image's import allowlist that names each import 9.16 does not export, and let the
    adapter rewrite it (Fable); (B) normalise the mechanical 7.29 to 9.16 renames and mark
    what remains `blocked` until regenerated (Gemini); or (C) wait for the running MUI X
    regeneration and serve MUI X only after it. **Decided (owner, 2026-10-30): A.** The
    7.29 files are served like the rest, `coupled` with a precise note, never blocked for
    their version alone; blocked stays for what the validator refuses. JS-3 built the note
    (`deprecated-api`: the 51 files that import `@mui/x-charts/ChartContainer`, which the
    allowlist does not hold, and `ChartContainer` imported by name from the package root);
    the other 144 render unchanged and get no version note. JS-4 still enables MUI X last,
    after Chart.js, D3 and ECharts.
