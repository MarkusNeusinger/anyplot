# Generate Implementation

**YOUR PRIMARY TASK: Create a working plot implementation file.**

You MUST create: `plots/{SPEC_ID}/implementations/{LANGUAGE}/{LIBRARY}{EXT}`

This is NOT optional. The workflow will FAIL if this file does not exist after you finish.

The `{EXT}` value depends on `{LANGUAGE}`:

| LANGUAGE | EXT  | Runner                |
|----------|------|-----------------------|
| `python` | `.py` | `python` (in `.venv`) |
| `r`      | `.R`  | `Rscript`             |

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
2. `prompts/default-style-guide.md` - **CRITICAL**: Okabe-Ito palette, continuous-data rules, theme-adaptive chrome tokens. Every new implementation must comply.
3. `prompts/library/{LIBRARY}.md` - Library-specific rules + theme-adaptive chrome mapping for this library
4. `plots/{SPEC_ID}/specification.md` - What to visualize

### If regenerating (`IS_REGENERATION=true`) — MANDATORY

When regenerating an existing implementation, you MUST read these BEFORE writing any code:

1. `/tmp/anyplot-prev-review.md` — structured review from the previous attempt (image description, strengths, weaknesses, failed criteria checklist). The workflow extracts this automatically from the previous `metadata/{LANGUAGE}/{LIBRARY}.yaml`.
2. `plots/{SPEC_ID}/implementations/{LANGUAGE}/{LIBRARY}{EXT}` — the previous implementation (`.py` for python, `.R` for r).

**Default regen mindset: incremental improvement, not rewrite.**

- Preserve the bits listed under "Strengths" unchanged.
- Address every bullet under "Weaknesses" and each ❌ item in the criteria checklist.
- **Canvas size: the Step 0 contract is non-negotiable on regen.** The previous file's `figsize` / `dpi` / `width` / `height` / `scale_factor` values are **historical**, never current — overwrite them to the canonical pair from `prompts/library/{LIBRARY}.md` as your *first* edit, before touching anything else. The post-render gate checks this and re-triggers repair on drift; do not let that fire.
- **Base style wins on everything else.** If anything in `prompts/default-style-guide.md` or `prompts/library/{LIBRARY}.md` differs from the previous implementation, update the previous code to match. This includes **font sizes** (title, axis labels, tick labels, legend), **marker and line sizes**, **palette** (Okabe-Ito positions), **theme tokens** (background, INK, INK_SOFT, ELEVATED_BG, GRID), and **chrome** (spines, gridlines, legend frame). The previous review may not have flagged the old values because they were valid at the time — that does NOT make them current. Always re-read the library prompt's "Sizing" section and the style guide's "Visual Sizing Defaults" table on every regen and align.
- Do NOT discard working structure / data generation / layout choices that the previous review did not flag.
- Your deliverable is a refined version of the previous file, not a fresh rewrite from the spec.

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
  "Respect the spec variant" (below) only insofar as the change_request
  explicitly permits — the spec-variant rule still binds the rest of the
  implementation.
- The hint is short by design (~1 sentence). It will name the sibling and the
  shared signal, then suggest 2–3 alternative directions along that dimension.
  Pick one of the suggested alternatives, or another that fits the same
  dimension; do not invent a tangential change.

If `/tmp/anyplot-change-request.txt` does not exist, ignore this section
entirely — there is nothing to apply.

### Feasibility Check (Static Libraries Only)

If LIBRARY is **matplotlib**, **seaborn**, **plotnine**, or **ggplot2**, AND the specification mentions interactive features (hover, zoom, click, brush, animation, streaming):

1. Is the spec's PRIMARY value its interactivity?
2. If YES → Do NOT generate. Report: `NOT_FEASIBLE: {LIBRARY} cannot provide {required_feature} as static PNG.`
3. If NO (static chart is still valuable) → Generate only the static-achievable features. Do NOT simulate interactive features.

## Step 2: CREATE THE FILE (MANDATORY)

**You MUST use the Write tool to create:**

```
plots/{SPEC_ID}/implementations/{LANGUAGE}/{LIBRARY}{EXT}
```

where `{EXT}` is `.py` for `python` and `.R` for `r`.

The script MUST:
- Follow the KISS structure: imports → data → plot → save
- Read `ANYPLOT_THEME` from the environment (`"light"` or `"dark"`, default `"light"`) and render accordingly. The same single script file handles both themes.
  - Python: `os.getenv("ANYPLOT_THEME", "light")`
  - R: `Sys.getenv("ANYPLOT_THEME", "light")`
- Save output as `plot-{THEME}.png` (theme-suffixed, based on the env var).
- For interactive libraries (plotly, bokeh, altair, highcharts, pygal, letsplot): also save `plot-{THEME}.html`. ggplot2 is PNG-only, no HTML variant.
- Use `#009E73` (Okabe-Ito position 1) as the **first categorical series**, always. Multi-series follows the canonical order: `#D55E00`, `#0072B2`, `#CC79A7`, `#E69F00`, `#56B4E9`, `#F0E442`.
- For continuous data: `viridis`/`cividis` (sequential) or `BrBG` (diverging). Never `jet`/`hsv`/`rainbow`.
- Plot backgrounds: `#FAF8F1` (light) / `#1A1A17` (dark). Never pure `#FFFFFF` or `#000000`.
- Theme-adaptive chrome (title, axis labels, tick labels, grid, spines, legend frames, annotation boxes) — see `prompts/default-style-guide.md` "Theme-adaptive Chrome" and the library-specific mapping in `prompts/library/{LIBRARY}.md`.

**DO NOT SKIP THIS STEP. The file MUST be created.**

## Step 3: Test and fix (up to 3 attempts)

Run the implementation **twice**, once per theme.

**Python (`LANGUAGE=python`)**:
```bash
source .venv/bin/activate
cd plots/{SPEC_ID}/implementations/{LANGUAGE}
MPLBACKEND=Agg ANYPLOT_THEME=light python {LIBRARY}.py
MPLBACKEND=Agg ANYPLOT_THEME=dark  python {LIBRARY}.py
```

**R (`LANGUAGE=r`)**:
```bash
cd plots/{SPEC_ID}/implementations/{LANGUAGE}
ANYPLOT_THEME=light Rscript {LIBRARY}.R
ANYPLOT_THEME=dark  Rscript {LIBRARY}.R
```

Both runs must succeed and produce `plot-light.png` / `plot-dark.png` (plus `plot-light.html` / `plot-dark.html` for interactive libs). If either fails, fix and try again (max 3 attempts).

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

## Step 6: Verify file exists (CRITICAL)

Before committing, verify the implementation file exists:

```bash
ls -la plots/{SPEC_ID}/implementations/{LANGUAGE}/{LIBRARY}{EXT}
```

`{EXT}` is `.py` for python, `.R` for r.

**If the file does NOT exist, you MUST go back to Step 2 and create it!**

## Step 7: Commit

```bash
git config user.name "github-actions[bot]"
git config user.email "github-actions[bot]@users.noreply.github.com"
git add plots/{SPEC_ID}/implementations/{LANGUAGE}/{LIBRARY}{EXT}
git commit -m "feat({LIBRARY}): implement {SPEC_ID}"
git push -u origin implementation/{SPEC_ID}/{LIBRARY}
```

If `IS_REGENERATION=true`, use an expanded commit body that names what you addressed. Example:

```
feat(matplotlib): implement scatter-basic

Regen from quality 78. Addressed:
- text legibility on dark background
- grid contrast (VQ-03 failed → fixed)
```

Pass the multi-line message via `-F -` or a heredoc so git preserves the body.

## Final Check

Before finishing, confirm:
1. ✅ `plots/{SPEC_ID}/implementations/{LANGUAGE}/{LIBRARY}{EXT}` exists (`.py` for python, `.R` for r)
2. ✅ `plot-light.png` AND `plot-dark.png` were generated successfully (plus `plot-light.html` / `plot-dark.html` for interactive libs — ggplot2 is PNG-only)
3. ✅ First categorical series renders in `#009E73` in both themes
4. ✅ Changes were committed and pushed
5. ✅ If regenerating: `/tmp/anyplot-prev-review.md` and the previous source file were read, and each weakness / failed criterion was either addressed or consciously kept (explained in the commit body)

If any of these failed, DO NOT report success.
