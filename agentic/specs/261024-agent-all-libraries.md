# Feature: "Use with my data" for all 15 catalogue libraries

> **Status (2026-10-28):** plan, in progress. Steps 1a (the runtime seam) and 1b
> (plotnine and altair) merged with PR #12404; see "What 1b built" under step 1b. Step 1c
> (pygal and lets-plot) merged with PR #12405; see "What 1c built" under step 1c. The
> harness's kernel filter against program starts, which lets-plot's row requires, is
> implemented on its branch (step 1c, "Next"). With it the deploy serves all six Python
> libraries for the admin's live tests, because only the admin reaches the chat yet
> (owner decision of 2026-10-28); `AGENT_LIBRARIES` keeps its default
> `matplotlib,seaborn`, and each library's matrix run gates the public release. Every
> other library in this document is planned, not shipped.

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
task; a library is enabled in the deploy only after that run. For R, Julia and
JavaScript the ten fixture specs must first carry the Data block (owner task per step:
regenerate them through the pipeline's regen), because the readiness scan blocks a file
without the marker and the matrix would otherwise have a handful of cases.

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
  eligible.
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
   Highcharts), and its only gain was pulls without a credential.
2. **Base distribution.** R's binaries from Posit exist for Ubuntu, not Debian, so the
   toolchain image is Ubuntu 24.04 (rocker's R layout) with Python 3.14 managed by uv
   instead of `python:3.14-slim`. Default: yes.
3. **Order.** The design lists plotly and bokeh before JavaScript; this plan takes the
   seam first, then plotnine and altair, pygal and lets-plot, then R as the smallest
   exec-mode pilot, then JavaScript (five libraries, one runtime), then plotly and bokeh
   on that Chromium, then Julia. Default: this order.
4. **Julia.** Ship it in this round only if the cold render fits 45 s; otherwise defer
   it behind the submit-and-poll renderer change. The spike measured 10 to 20 s cold on
   4 CPUs with the precompiled depot, so the default is now: ship synchronously, and
   confirm the time at 2 vCPU on the deployed renderer before enabling.
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
    use, and a public GHCR image redistributes the bundle. **Settled by question 1
    (2026-10-25):** the base image is private in Artifact Registry, so it redistributes
    nothing, and Highcharts can live in it. Whether users' plots may use Highcharts stays
    question 6.
