# Generate Implementation

**YOUR PRIMARY TASK: Create a working plot implementation file.**

You MUST create: `plots/{SPEC_ID}/implementations/{LANGUAGE}/{LIBRARY}{EXT}`

This is NOT optional. The workflow will FAIL if this file does not exist after you finish.

The `{EXT}` value depends on `{LANGUAGE}`:

| LANGUAGE     | EXT   | Runner                                                       |
|--------------|-------|--------------------------------------------------------------|
| `python`     | `.py`  | `python` (in `.venv`)                                       |
| `r`          | `.R`   | `Rscript`                                                   |
| `julia`      | `.jl`  | `julia --project=.`                                         |
| `javascript` | `.js`  | `node automation/js-render/render.mjs` (browser harness)    |
| `javascript` | `.tsx` | `node automation/js-render/render.mjs` (MUI X — React, esbuild-bundled by the same harness) |

> **JavaScript renders in a browser, not a CLI.** Unlike R/Julia (which write a
> PNG directly), a JS charting snippet draws into a DOM node. You do **not** run
> the `.js`/`.tsx` file directly — you run the shared render harness, which wraps
> your idiomatic snippet (`new Chart(...)`, `d3.select(...)`, `echarts.init(...)`)
> in an HTML page, loads the pinned library bundle, renders it under headless
> Chromium (Playwright), and screenshots the mount node `#container` at the exact
> canvas size. It emits both `plot-{THEME}.png` (gallery) **and**
> `plot-{THEME}.html` (interactive detail view). See `prompts/library/{LIBRARY}.md`.
>
> **MUI X (`muix`) is the React exception.** Its snippet is a `.tsx` file that
> **default-exports a React component** (e.g. `export default function Chart() { return <BarChart … /> }`)
> — there is no imperative `new Chart(...)`. The same harness esbuild-bundles it
> with react + `@mui/x-charts`, wraps it in a theme-aware MUI `ThemeProvider`, and
> mounts it via `createRoot`. Run it exactly the same way (`render.mjs muix.tsx`).
> **Community `@mui/x-charts` only — never `@mui/x-charts-pro` / Premium.** See
> `prompts/library/muix.md`.

---

**Variables:**
- LANGUAGE: {LANGUAGE}
- LIBRARY: {LIBRARY}
- SPEC_ID: {SPEC_ID}
- Regeneration: {IS_REGENERATION}

## Step 0: Canvas dimensions (HARD CONTRACT — applies before anything else)

The saved `plot-light.png` / `plot-dark.png` **must** end up at exactly one of these two pixel sizes:

| Orientation | Pixels      | Use case |
|-------------|-------------|----------|
| Landscape   | 3200 × 1800 | Default — most plots (16:9) |
| Square      | 2400 × 2400 | Symmetric plots: pie, radar, heatmaps, maze, crossword, anything with no preferred horizontal axis (1:1) |

Pick the orientation that suits the spec's content; do **not** average between them, do **not** invent a third aspect ratio. The exact knobs to set for your library are in `prompts/library/{LIBRARY}.md` ("Canvas — hard rule, no deviation"). Use those numbers verbatim.

**If regenerating: the previous implementation's `figsize` / `dpi` / `width` / `height` / `scale_factor` values are HISTORICAL. Do NOT carry them forward, even if every other line in the previous code is fine.** Your very first edit to the previous file is to overwrite those values to the canonical pair from the library prompt. Everything else (fonts, colours, layout, data scenario) comes after that one edit is in place.

A post-render gate in `impl-review.yml` measures the saved PNG dimensions and rejects anything off-target by more than 16 px on either axis, then routes the PR into `impl-repair.yml`. Repair attempts are capped — drift past 4 attempts deletes the implementation from `main`. The cheapest path is to land on target on the first render. Step 3 below includes a PIL self-check you must run before committing.

## Step 1: Read the rules (quickly)

Read these files to understand the requirements:

1. `prompts/plot-generator.md` - Base generation rules
2. `prompts/adaptable-code.md` - The Data block convention: six zones, one `# Data` block that ends in `df`, columns named once as constants, plot code that derives everything from `df`. Every new implementation follows it, in every language.
3. `prompts/default-style-guide.md` - **CRITICAL**: Imprint palette, continuous-data rules, theme-adaptive chrome tokens. Every new implementation must comply. Always refer to the palette as **Imprint** in code comments and metadata — never "anyplot palette".
4. `prompts/library/{LIBRARY}.md` - Library-specific rules + theme-adaptive chrome mapping for this library, including its "Data block" idiom
5. `plots/{SPEC_ID}/specification.md` - What to visualize. Its closing `## What a good version looks like` section (when present) names what a good render of this plot type shows, and the review scores against it. Build toward its `A good version shows:` bullets (the review deducts when one is missing). Its `Expected, not a defect:` bullets are permissions, not targets: never shape the data to produce them (no clustering points to show overlap). Without the section, derive the same from Description, Data and Notes.

### If regenerating (`IS_REGENERATION=true`) — MANDATORY

When regenerating an existing implementation, you MUST read these BEFORE writing any code:

1. `/tmp/anyplot-prev-review.md` — structured review from the previous attempt: image description, the strengths it credited, its weaknesses `W1`..`Wn` (each tagged `(defect)`, `(suggestion)` or `(older review)`), the criteria checklist, and the spec's characteristic bullets `C1`..`Cn`. The workflow extracts this automatically from the previous `metadata/{LANGUAGE}/{LIBRARY}.yaml`.
2. `plots/{SPEC_ID}/implementations/{LANGUAGE}/{LIBRARY}{EXT}` — the previous implementation (`.py` for python, `.R` for r, `.jl` for julia, `.js` for javascript).

**Default regen mindset: incremental improvement, not rewrite.**

- Keep the strengths the current criteria still credit; a strength praising an unrequested addition does not bind — on a `-basic` spec, removing it is a fix.
- **Act on the defects, decline the rest.** Judge each weakness by its tag and by the spec's `## What a good version looks like` section (without one, by Description, Data and Notes), and name every declined one with a one-line reason in the commit body:
  - `(defect)` — a violated rule: fix it and decide HOW yourself.
  - `(suggestion)` — an idea the previous review did not require. Never act on a `Suggestion:` line; decline it as `Declined: W2 — suggestion, not taken`.
  - `(older review)` — a note written before the current rubric, a hint only: act on it when it names something visibly wrong under the current criteria, otherwise decline it.
  - Whatever its tag, a weakness that asks for less of something an `Expected, not a defect:` bullet names is obsolete — e.g. "bubbles overlap in the dense cluster" on a bubble chart that already uses translucency and outlines: decline it as `W1 — obsolete (C2)`.
  - The checklist is context, not a list of orders: a ❌ item tells you where to look, and you act on it only when it is a defect in the same sense.
- **Answer overlap weaknesses through data generation, marker size or alpha — never by moving marks off their data values.** No force/collision simulations, nudge or declutter passes, or offsets on data marks; moving labels is fine. The review deducts displaced marks (SC-03). Exempt, as in SC-03: jitter in categorical strip/swarm plots, layout-positioned types (networks, treemaps, word clouds, packed circles), and any jitter, dodge or offset the spec's Data or Notes ask for.
- **Keep the data scenario and the variant.** Same domain, same story, same encodings unless a weakness names the scenario itself as the problem or a change request (below) asks for a different one. On a `-basic` spec, add no new encodings or elements (derived color channels, trend or reference lines, highlights, callouts, annotation layers) — the review scores them as the wrong variant. For Python (`LANGUAGE=python`): re-expressing the same values as one `df` with column constants (the Data block of `prompts/adaptable-code.md`) keeps the scenario; it is not a new one.
- **Don't add code for changes that don't show.** Every edit should be visible in the render or fix a named code-quality item; a longer file with an unchanged picture is not an improvement. A `CQ-04` weakness names its replacement: apply exactly that replacement, keep the data and the render the same, and change nothing else for it. Without a CQ-04 weakness, leave computations as they are on a regeneration. For Python (`LANGUAGE=python`): a `CQ-01 (code)` line or a failed perturbation from the Step 3c self-check is a named code-quality item, like a CQ-04 weakness. Converting the file to the Data block convention is the one change you make although the picture stays the same, and it may move computations below the block (widths, limits and positions derived from `df`); see "Converting a Python file" below.
- **Canvas size: the Step 0 contract is non-negotiable on regen.** The previous file's `figsize` / `dpi` / `width` / `height` / `scale_factor` values are **historical**, never current — overwrite them to the canonical pair from `prompts/library/{LIBRARY}.md` as your *first* edit, before touching anything else. The post-render gate checks this and re-triggers repair on drift; do not let that fire.
- **Base style wins on everything else.** If anything in `prompts/default-style-guide.md` or `prompts/library/{LIBRARY}.md` differs from the previous implementation, update the previous code to match. This includes **font sizes** (title, axis labels, tick labels, legend), **marker and line sizes**, **palette** (Imprint palette positions), **theme tokens** (background, INK, INK_SOFT, ELEVATED_BG, GRID), and **chrome** (spines, gridlines, legend frame). The previous review may not have flagged the old values because they were valid at the time — that does NOT make them current. Always re-read the library prompt's "Sizing" section and the style guide's "Visual Sizing Defaults" table on every regen and align. Also normalise any stale "anyplot palette" wording in the previous code's comments to "Imprint palette".
- Do NOT discard working structure / data generation / layout choices that the previous review did not flag. For Python (`LANGUAGE=python`): the data generation keeps its values, not its form — the same numbers, names and order move into the one `# Data` block and end in `df`.
- No defect listed and nothing in Step 0 or the base style to align → a small edit, and a kept regeneration, is the expected outcome. Do not invent changes to have something to show. For Python (`LANGUAGE=python`): a previous file that fails the adaptability check has a listed defect, so convert it even when nothing else needs to change.
- Your deliverable is a refined version of the previous file, not a fresh rewrite from the spec.
- **Converting a Python file (`LANGUAGE=python`).** Before you edit, run the static check on the previous file to see what it lacks: `python -m core.adaptability check plots/{SPEC_ID}/implementations/python/{LIBRARY}.py`, from the repository root with `.venv` activated. It prints the record and the `CQ-01 (code)` lines and, unlike Step 3c, writes no log entry. Convert toward an identical picture: keep every value, label, order, color assignment and size, and replace each literal tied to the sample with an expression over `df` that reproduces it for the sample as closely as you can — `0.75 / len(table.columns)` for a bar width of 0.25 with three groups, a factor on the data's maximum for a typed axis limit (`df[SALES].max() * 1.13` where the old file typed 480 over a maximum of 425). A pure conversion merges when the new render differs from the previous one in at most 0.5 % of its pixels per theme at the same canvas size; a conversion that moves things is an ordinary regeneration and merges only with a visible improvement. When you also fix a defect, that fix is the only visible change. The optional `pair` command in Step 3c measures the difference.
- **R, Julia and JavaScript (`LANGUAGE` other than `python`):** the Data block convention applies to new files. On a regeneration it is no reason to rewrite working data code; the mindset above applies unchanged.

### Library Independence — DO NOT read sibling implementations

This implementation is for **one library only**. Never read another library's
source file or `.yaml` under `plots/{SPEC_ID}/implementations/` or
`plots/{SPEC_ID}/metadata/` — not even "for reference" or "to stay consistent
with the catalog". Each library is an independent interpretation of the spec;
identical charts rendered by different engines defeat the catalog's purpose.

Pick your own example data scenario (the spec lists multiple applications),
your own valid visual variant, your own aspect ratio within the spec's range,
and your own idiomatic API. The shared anchors are only the spec, the library
prompt, and the base style guide. See `prompts/plot-generator.md` →
"Library Independence" for the full rule.

### Change Request — cross-library divergence hint

If the file `/tmp/anyplot-change-request.txt` exists, read it. Its content is a
**hard requirement** of this regen: the cross-library similarity audit (in
`daily-regen` pre-flight) flagged this library as too close to a sibling on a
dimension the spec didn't dictate, and produced a one-sentence direction hint
to break the convergence.

When a change_request is present:

- **Apply it.** This is the only cross-library context permitted in this run;
  treat it as binding.
- **Do NOT open sibling-library files** even to "verify" the request. The hint
  contains everything you need; the Library Independence rule above still
  binds.
- The "no changes for the sake of changes" exception (default regen mindset
  prefers incremental improvement) does **NOT** apply when a change_request is
  present — you must implement the requested change.
- **Preserve `review.strengths`** while applying the new direction. Override
  "Respect the spec variant" (`prompts/plot-generator.md` → "Data storytelling")
  and the "Keep the data scenario and the variant" regen rule above only insofar as the change_request
  explicitly permits — the spec-variant rule still binds the rest of the
  implementation.
- The hint is short by design (~1 sentence). It will name the sibling and the
  shared signal, then suggest 2–3 alternative directions along that dimension.
  Pick one of the suggested alternatives, or another that fits the same
  dimension; do not invent a tangential change.

If `/tmp/anyplot-change-request.txt` does not exist, ignore this section
entirely — there is nothing to apply.

### Feasibility Check (Static Libraries Only)

If LIBRARY is **matplotlib**, **seaborn**, **plotnine**, **ggplot2**, or **makie**, AND the specification mentions interactive features (hover, zoom, click, brush, animation, streaming):

1. Is the spec's PRIMARY value its interactivity?
2. If YES → Do NOT generate. Report: `NOT_FEASIBLE: {LIBRARY} cannot provide {required_feature} as static PNG.`
3. If NO (static chart is still valuable) → Generate only the static-achievable features. Do NOT simulate interactive features.

## Step 2: CREATE THE FILE (MANDATORY)

**You MUST use the Write tool to create:**

```
plots/{SPEC_ID}/implementations/{LANGUAGE}/{LIBRARY}{EXT}
```

where `{EXT}` is `.py` for `python`, `.R` for `r`, `.jl` for `julia`, and `.js` for `javascript`.

The script MUST:
- Follow the six zones of `prompts/adaptable-code.md`: head (imports, theme tokens, palette, setup) → optional `# Constants` → column constants with `# role:` comments → one `# Data` block that ends in `df` (`const data` in JavaScript) → plot code below `# Plot` → save
- Read `ANYPLOT_THEME` (`"light"` or `"dark"`, default `"light"`) and render accordingly. The same single script file handles both themes.
  - Python: `os.getenv("ANYPLOT_THEME", "light")`
  - R: `Sys.getenv("ANYPLOT_THEME", "light")`
  - Julia: `get(ENV, "ANYPLOT_THEME", "light")`
  - JavaScript: the browser has no env — the harness exposes `window.ANYPLOT_THEME` (`"light"`/`"dark"`) and `window.ANYPLOT_TOKENS` (page bg, ink, grid, Imprint palette). Read those.
- Save output as `plot-{THEME}.png` (theme-suffixed). Python/R/Julia save it themselves; **JavaScript snippets do NOT save** — the render harness screenshots `#container` and writes the PNG (and HTML) for you.
- For interactive libraries (plotly, bokeh, altair, highcharts, pygal, letsplot): also save `plot-{THEME}.html`. ggplot2 and makie are PNG-only, no HTML variant. **JavaScript** (chartjs, d3, echarts, muix) is interactive, but the harness emits the HTML — the snippet must not.
- Use `#009E73` (Imprint palette position 1) as the **first categorical series**, always. Multi-series follows the canonical order: `#C475FD`, `#4467A3`, `#BD8233`, `#AE3030`, `#2ABCCD`, `#954477`, `#99B314`. May reassign positions when categories carry strong semantic color cues (grass→green, wood→ochre, blood→red, sky→blue) — see `prompts/default-style-guide.md` "Semantic exception". Three semantic anchors outside the categorical pool: `#DDCC77` (amber, warning), theme-adaptive `palette.neutral` (totals/baseline), theme-adaptive `palette.muted` (other/rest).
- For continuous data: build `imprint_seq` (single-polarity, `["#009E73", "#4467A3"]`) or `imprint_div` (diverging, `["#AE3030", midpoint, "#4467A3"]` where midpoint is `#FAF8F1` on light / `#1A1A17` on dark) from the Imprint palette. No other cmaps — never viridis/cividis/BrBG/Reds/Blues/Greens or jet/hsv/rainbow.
- Plot backgrounds: `#FAF8F1` (light) / `#1A1A17` (dark). Never pure `#FFFFFF` or `#000000`.
- Theme-adaptive chrome (title, axis labels, tick labels, grid, spines, legend frames, annotation boxes) — see `prompts/default-style-guide.md` "Theme-adaptive Chrome" and the library-specific mapping in `prompts/library/{LIBRARY}.md`.

**DO NOT SKIP THIS STEP. The file MUST be created.**

## Step 3: Test and fix (up to 3 attempts)

Run the implementation **twice**, once per theme.

**Python (`LANGUAGE=python`)**:
```bash
source .venv/bin/activate
cd plots/{SPEC_ID}/implementations/{LANGUAGE}
MPLBACKEND=Agg ANYPLOT_THEME=light python -P {LIBRARY}.py
MPLBACKEND=Agg ANYPLOT_THEME=dark  python -P {LIBRARY}.py
```

> **Why `-P`:** this directory contains one file per library (`matplotlib.py`, `seaborn.py`, `plotly.py`, …). Without `-P` (Python 3.11+ "safe path" flag), Python prepends the script's own directory to `sys.path`, so `import matplotlib.pyplot` inside e.g. `seaborn.py` resolves to the sibling `matplotlib.py` file instead of the real installed package — a `ModuleNotFoundError: 'matplotlib' is not a package` that has nothing to do with your code. `-P` skips that prepend so the real site-packages import wins.

**R (`LANGUAGE=r`)**:
```bash
cd plots/{SPEC_ID}/implementations/{LANGUAGE}
ANYPLOT_THEME=light Rscript {LIBRARY}.R
ANYPLOT_THEME=dark  Rscript {LIBRARY}.R
```

**Julia (`LANGUAGE=julia`)**:
```bash
cd plots/{SPEC_ID}/implementations/{LANGUAGE}
ANYPLOT_THEME=light julia --project=. {LIBRARY}.jl
ANYPLOT_THEME=dark  julia --project=. {LIBRARY}.jl
```

**JavaScript (`LANGUAGE=javascript`)**: run the render harness, not the file. It
wraps your snippet in HTML, renders under headless Chromium, screenshots
`#container`, and writes both the PNG and the interactive HTML. For `muix` (`.tsx`)
it additionally esbuild-bundles your default-exported React component with
react + `@mui/x-charts` and mounts it — same command either way. Run from the repo
root so `node_modules` resolves:
```bash
cd plots/{SPEC_ID}/implementations/{LANGUAGE}
ANYPLOT_THEME=light node "$GITHUB_WORKSPACE/automation/js-render/render.mjs" {LIBRARY}{EXT}
ANYPLOT_THEME=dark  node "$GITHUB_WORKSPACE/automation/js-render/render.mjs" {LIBRARY}{EXT}
```
The harness derives the library + bundle from the filename (`{LIBRARY}{EXT}`,
i.e. `chartjs.js` … `muix.tsx`) and the orientation from a
`//# anyplot-orientation: square` directive in the file (default landscape). It
exits non-zero if your snippet throws or leaves `#container` empty.

Both runs must succeed and produce `plot-light.png` / `plot-dark.png` (plus `plot-light.html` / `plot-dark.html` for interactive libs — ggplot2 and makie are PNG-only; the JS harness writes the HTML itself). If either fails, fix and try again (max 3 attempts).

### Step 3b: Canvas dimension self-check (Step 0 contract verification)

After both renders succeed, run this check against the light PNG. It catches Step 0 violations *before* the PR goes to review:

```bash
source .venv/bin/activate
python -c "
from PIL import Image
import sys
p = 'plots/{SPEC_ID}/implementations/{LANGUAGE}/plot-light.png'
w, h = Image.open(p).size
targets = [(3200, 1800), (2400, 2400)]
ok = any(abs(w-tw) <= 16 and abs(h-th) <= 16 for tw, th in targets)
print(f'canvas {w}x{h} ' + ('OK' if ok else 'DRIFTED — adjust library-specific canvas knobs and re-render'))
sys.exit(0 if ok else 1)
"
```

If this exits non-zero, you have **not** satisfied the Step 0 contract. Re-read `prompts/library/{LIBRARY}.md` "Canvas — hard rule" and apply the exact code there; common causes are listed in that file (e.g. matplotlib/seaborn `bbox_inches="tight"` shaves ~40 px; bokeh's default toolbar leaves ~140 px; altair's vl-convert pads outside `width`/`height`). Re-render and re-check until OK. Do not skip this and rely on the post-render gate to catch it — repair cycles cost compute.

### Step 3c: Adaptability self-check (Python only)

**Python (`LANGUAGE=python`) only; R, Julia and JavaScript skip this step.** After Step 3b passes, check that the file follows the Data block convention (`prompts/adaptable-code.md`) and still renders on other data. One command runs both checks: the static check of the six zones, and a smoke run that executes the file on perturbed copies of its own `df` (renamed columns, one with spaces, a unit and a dot; one more and one fewer category; a single group where the spec allows one; fewer and more rows; scaled values; a missing value). Run it from the repository root, and give the Bash call a 10-minute timeout, because bokeh and plotly start Chrome for every render:

```bash
cd "$GITHUB_WORKSPACE"
source .venv/bin/activate
python -m core.smoke_run selfcheck plots/{SPEC_ID}/implementations/python/{LIBRARY}.py --log /tmp/anyplot-selfcheck.jsonl
```

It prints one `CQ-01 (code): line N … → …. Likely cause: ….` line per failing rule class, then one line per perturbation, and exits 0 when both checks are clean. A map spec, and a generated spec with nothing to perturb, count as clean.

- **Fix every line and every failed perturbation that is not tagged `(advisory)`,** then re-render both themes (Step 3), re-run Step 3b, and run this step again. A `CQ-01 (code)` line names the line of your file, what it found, the target and the likely cause; a failed perturbation names the error and the line where it was raised. Typical fixes: a literal tied to the sample becomes an expression over `df`, a palette sized to the sample becomes the full eight-entry list, a typed label becomes a column constant, a zero fill becomes a NaN-aware reduction.
- **Lines and perturbations tagged `(advisory)` never fail the check.** Fix one when the fix is small and leaves the render unchanged; otherwise leave it.
- **At most three attempts in total,** the first run included. Adaptability never blocks the implementation: if the check still fails after the third attempt, keep the best version that renders correctly in both themes and passes Step 3b, and go on to Step 4. Never trade a defect in the render for a clean check.
- **Each run appends one line to `/tmp/anyplot-selfcheck.jsonl`,** which the workflow stages; never delete or edit it. If the command itself cannot run (exit 2, or a runner error you cannot fix in your file), say so in the commit body and go on to Step 4.

Regeneration only, optional: to see whether your file still renders the same picture as the previous version, render both in one environment and compare them:

```bash
mkdir -p /tmp/anyplot-prev-src
git show origin/main:plots/{SPEC_ID}/implementations/python/{LIBRARY}.py > /tmp/anyplot-prev-src/{LIBRARY}.py
python -m core.smoke_run pair --new plots/{SPEC_ID}/implementations/python/{LIBRARY}.py \
    --prev /tmp/anyplot-prev-src/{LIBRARY}.py --out-dir /tmp/anyplot-pair
```

It exits 0 when both themes stay within 0.5 % of differing pixels at the same canvas size (`identical`), 1 when they differ (it names the theme and the fraction), and 2 when a render fails. It is a measurement for you, never a gate here: a regeneration that fixes a visible defect differs by design.

## Step 4: Visual self-check (BOTH renders)

Look at `plot-light.png` AND `plot-dark.png`:
- Does each match the specification?
- Are axes labeled correctly in both?
- Is the visualization clear on the light surface (`#FAF8F1`) AND the dark surface (`#1A1A17`)?
- Are the data colors **identical** between light and dark (only chrome flipped)?
- Is the first categorical series `#009E73`?

## Step 5: Format the code

**Python (`LANGUAGE=python`)**:
```bash
source .venv/bin/activate
ruff format plots/{SPEC_ID}/implementations/{LANGUAGE}/{LIBRARY}.py
ruff check --fix plots/{SPEC_ID}/implementations/{LANGUAGE}/{LIBRARY}.py
```

**R (`LANGUAGE=r`)**: no formatter is required by CI. Keep the code idiomatic
ggplot2 style (4-space indent, `<-` for assignment, `=` only in arguments). If
`styler` is available, you may run
`Rscript -e 'styler::style_file("plots/{SPEC_ID}/implementations/r/{LIBRARY}.R")'`
— but a missing styler is not a failure.

**Julia (`LANGUAGE=julia`)**: no formatter is required by CI. Follow idiomatic
Julia style (4-space indent, no trailing whitespace, `lowercase_with_underscores`
for variables and functions, `CamelCase` for types/modules). If `JuliaFormatter`
is available, you may run
`julia --project=. -e 'using JuliaFormatter; format_file("plots/{SPEC_ID}/implementations/julia/{LIBRARY}.jl")'`
— but a missing formatter is not a failure.

## Step 6: Verify file exists (CRITICAL)

Before committing, verify the implementation file exists:

```bash
ls -la plots/{SPEC_ID}/implementations/{LANGUAGE}/{LIBRARY}{EXT}
```

`{EXT}` is `.py` for python, `.R` for r, `.jl` for julia, `.js` for javascript.

**If the file does NOT exist, you MUST go back to Step 2 and create it!**

## Step 7: Commit

```bash
git config user.name "github-actions[bot]"
git config user.email "github-actions[bot]@users.noreply.github.com"
git add plots/{SPEC_ID}/implementations/{LANGUAGE}/{LIBRARY}{EXT}
git commit -m "feat({LIBRARY}): implement {SPEC_ID}"
git push -u origin implementation/{SPEC_ID}/{LIBRARY}
```

Commit only the implementation file, and use only the packages the runner already has: never run `Pkg.add`, `uv add`, `pip install` or `npm install`. The workflow fails the run when your commit changes `Manifest.toml`, `Project.toml`, `uv.lock`, `pyproject.toml`, `package.json`, `package-lock.json` or `.python-version`, because a re-resolved lock file moves the library version for every implementation of the language.

For Python (`LANGUAGE=python`), the commit body always carries the result of the last Step 3c run, first generations included: `pass`, or `fail` with the rule classes of the remaining non-advisory lines and the names of the remaining failed perturbations, and the attempt number:

```bash
git commit -m "feat({LIBRARY}): implement {SPEC_ID}" -m "Adaptability self-check: pass, attempt 1"
# or, after three attempts:  -m "Adaptability self-check: fail (palette, more_categories), attempt 3"
```

If `IS_REGENERATION=true`, use an expanded commit body that names the weaknesses you addressed and the ones you declined, by W id with the tag the previous review gave them, each declined one with its reason. Example:

```
feat(matplotlib): implement scatter-basic

Regen from quality 78. Addressed:
- W3 (defect, VQ-01): tick labels on the dark background now use INK_SOFT
- W4 (older review): grid contrast lowered to the style guide's opacity
Declined:
- W1 — obsolete (C2): "points overlap in the dense center" asks for less
  of what the spec's Expected, not a defect bullet permits; alpha already
  keeps every point visible
- W2 — suggestion, not taken: "a focal highlight on the densest cluster"
- W5 — asks for something the spec does not require: "add a trend line"
- W6 — names a call the runtime does not provide: "StatsBase.autocor"

Adaptability self-check: pass, attempt 2
```

Pass the multi-line message via `-F -` or a heredoc so git preserves the body.

## Final Check

Before finishing, confirm:
1. ✅ `plots/{SPEC_ID}/implementations/{LANGUAGE}/{LIBRARY}{EXT}` exists (`.py` for python, `.R` for r, `.jl` for julia, `.js` for javascript)
2. ✅ `plot-light.png` AND `plot-dark.png` were generated successfully (plus `plot-light.html` / `plot-dark.html` for interactive libs — ggplot2 and makie are PNG-only)
3. ✅ First categorical series renders in `#009E73` in both themes
4. ✅ Changes were committed and pushed
5. ✅ If regenerating: `/tmp/anyplot-prev-review.md` and the previous source file were read; every defect was fixed, every `Suggestion:` line was declined as "suggestion, not taken", every obsolete weakness was declined with its C id, and each older note was acted on only when it names something visibly wrong under the current criteria (declined ones named with a reason in the commit body)
6. ✅ Every data mark sits at its data value — overlap was handled through data generation, marker size or alpha, not by moving marks (SC-03 exemptions only: categorical strip/swarm jitter, layout-positioned types, jitter/dodge/offset the spec asks for)
7. ✅ If regenerating: same data scenario and variant as before (unless a weakness or change request asked otherwise), no new encodings on a `-basic` spec, and no added code whose effect does not show in the render. For Python (`LANGUAGE=python`), converting the file to the Data block convention is the exception: it may add code while the render stays identical
8. ✅ For Python (`LANGUAGE=python`): Step 3c ran (at most three attempts) and the commit body carries its `Adaptability self-check:` line; for every language, the file follows the zones of `prompts/adaptable-code.md`

If any of these failed, DO NOT report success.
