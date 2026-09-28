# Repair Implementation

You are repairing the **{LANGUAGE}/{LIBRARY}** implementation for **{SPEC_ID}**.

This is **repair attempt {ATTEMPT}/4**. The previous implementation was rejected.

## Step 1: Read the AI review feedback

Read both sources to understand what needs to be fixed:

1. `/tmp/ai_feedback.md` - Full review from PR comments
2. `plots/{SPEC_ID}/metadata/{LANGUAGE}/{LIBRARY}.yaml` - Look at:
   - `review.strengths` (keep these aspects!)
   - `review.weaknesses` (fix the defect lines — `<ID> (<render>): …` — that are real per the spec's `## What a good version looks like` section and decide HOW yourself; never act on a `Suggestion:` line; see "Which weaknesses to fix" below)
   - `review.image_description` (understand what was generated visually)
   - `review.criteria_checklist` (context, not a list of orders: it shows where points were lost)
     - Items with `passed: false` tell you where to look; act on one when a defect line names it, or when it is a defect in the same sense and the characteristic section does not contradict it (then decline it, see below)
     - Focus on categories with low scores (e.g., visual_quality.score < visual_quality.max)
     - VQ-XX items for visual issues
     - SC-XX items for spec compliance
     - CQ-XX items for code quality

**Important:** If the review triggered AR-08 (FAKE_FUNCTIONALITY), this is NOT repairable via repair. The implementation must either be regenerated as a genuine static visualization or marked NOT_FEASIBLE. Do NOT fix by "improving" the fake elements.

### Which weaknesses to fix

Read the closing `## What a good version looks like` section of `plots/{SPEC_ID}/specification.md` (without one, use Description, Data and Notes) and decide per weakness:

- **Fix the defects that are real per the section.** A defect line names the criterion it violates, the render and the observed value (`VQ-02 (light): … → …. Likely cause: ….`). A weakness that asks for something an `Expected, not a defect:` bullet of the section names — e.g. "bubbles overlap in the dense cluster" on a bubble chart that already uses translucency and outlines — is obsolete: decline it as `W1 — obsolete (C2)` or, without W ids, with the bullet's text. The section never waives chrome rules (theme readability, canvas, palette, text legibility, auto-reject checks); those weaknesses are always real.
- **Never act on a `Suggestion:` line.** It names no violated rule and costs no points; decline it as "suggestion, not taken". A line in neither format comes from an older review: act on it only when it names something visibly wrong under the current criteria.
- **The checklist is context, not a list of orders.** A deducted item tells you where to look; the defect lines say what to fix.
- **Keep the data scenario and the variant.** Same domain, same story, same encodings unless a weakness names the scenario itself as the problem. On a `-basic` spec, add no new encodings or elements (derived color channels, trend or reference lines, highlights, callouts, annotation layers).
- **Don't add code for changes that don't show.** Every edit should be visible in the render or fix a named code-quality item.
- **Never move marks off their data values** to fix overlap — see the overlap line under "Visual-sizing fixes" below for the endorsed fixes and the SC-03 exemptions.
- **`Expected, not a defect:` bullets are permissions, not targets.** Never shape the data to produce them, and never treat making one disappear as a fix: a weakness that only asks for less of a permitted thing (less overlap, fewer crossings) is declined, as the first bullet says.

## Step 2: Read reference files

1. `prompts/library/{LIBRARY}.md` - Library-specific rules + theme-adaptive chrome mapping
2. `prompts/default-style-guide.md` - Canonical Imprint palette + theme tokens (re-read if VQ-07 or VQ-04 failed), plus "Visual Sizing Defaults" and "Proportional Sizing" sections (re-read if VQ-01 / VQ-02 / VQ-05 failed)
3. `plots/{SPEC_ID}/specification.md` - The specification

**Visual-sizing fixes (when VQ-01 / VQ-02 / VQ-05 failed):**
- Title too big / overflows → reduce fontsize or shorten title text
- Short axis label disproportionately big ("Date" dominates axis) → reduce that label's fontsize while keeping the other axis-label/tick fontsizes balanced
- Long descriptive label overflows axis → reduce fontsize OR rotate ticks/labels
- Text overlaps → adjust margins, rotate ticks, reduce label fontsize, or move legend
- Sparse data with tiny markers → increase `s=` / `size=` / `marker.size=` / `marker.radius`
- Dense data with oversized markers / overplotting → reduce marker size + add `alpha=0.5-0.7`
- Data marks overlapping each other → change the data generation, marker size or alpha. **Never move marks off their data values** (no force/collision simulation, nudge or declutter pass, or offsets on data marks) — the review deducts displaced marks under SC-03. Moving labels is fine. Exempt, as in SC-03: jitter in categorical strip/swarm plots, layout-positioned types (networks, treemaps, word clouds, packed circles), and any jitter, dodge or offset the spec's Data or Notes ask for. If the spec's `## What a good version looks like` section has an `Expected, not a defect:` bullet for the overlap and the marks are already distinguishable, decline the weakness (see "Which weaknesses to fix").
- Invisible legend glyphs (size circles, swatches, line samples) → give the legend the marks' fill, outline and alpha explicitly (e.g. ggplot2 `guides(size = guide_legend(override.aes = list(...)))`)

Adjust the canvas-controlling knobs of the relevant library family:
- DPI-based (matplotlib / seaborn / plotnine): `figsize`, `dpi`, `fontsize=`
- Scale-based (plotly / altair / lets-plot): `width`/`height`/`scale_factor`, theme font sizes
- Native-pixel (bokeh / highcharts / pygal): `width`/`height` directly, `text_font_size` / `style.fontSize` / `Style(... _font_size=...)` — for highcharts keep the three canvas-size spots in sync (Selenium `--window-size`, HTML `<div style="width:height:">`, `chart.options.chart = {'width':,'height':}`); for bokeh keep Selenium `W, H` matching `figure(width=, height=)`

**Do NOT re-read `prompts/quality-criteria.md`** — the review already distilled all criteria into `review.criteria_checklist` in the metadata YAML (Step 1) and the defect lines in `review.weaknesses`. The checklist is context: items with `passed: false` show where points were lost, and the defect lines say what to fix.

**Common VQ-07 failures and fixes:**
- Legacy `#306998` still in code → replace with `#009E73` (Imprint palette position 1).
- First series not brand green → rewrite so the primary category renders in `#009E73`.
- Any non-Imprint cmap (jet/hsv/rainbow/viridis/cividis/BrBG/Reds/Blues/Greens) → switch to `imprint_seq` (single-polarity) or `imprint_div` (diverging) — see `prompts/default-style-guide.md` "Continuous Data".
- Pure `#FFFFFF` / `#000000` background → use `#FAF8F1` / `#1A1A17` via the `ANYPLOT_THEME` token block.
- Chrome wrong-theme (dark text on dark bg) → wire up all title/axis/tick/grid/legend colors to the `INK`/`INK_SOFT` tokens.

## Step 3: Read current implementation

`plots/{SPEC_ID}/implementations/{LANGUAGE}/{LIBRARY}{EXT}` — `{EXT}` is `.py`
for python libraries, `.R` for ggplot2, `.jl` for makie, `.js` for the
framework-agnostic JavaScript libraries (chartjs, d3, echarts, highcharts), and
`.tsx` for muix (React / MUI X).

**Do NOT read sibling-library implementations under
`plots/{SPEC_ID}/implementations/`** (other libraries' source or `.yaml`).
Each library is an independent interpretation; copying data scenarios,
color choices, layout, or aspect ratio from a sibling defeats the point of
having multiple libraries in the catalog. See `prompts/plot-generator.md` →
"Library Independence" for the full rule.

## Step 4: Fix the issues

Based on the AI feedback, fix the defects you kept in "Which weaknesses to fix" (Step 1):
- Visual quality issues
- Code quality issues
- Spec compliance issues

Keep the data scenario and variant, add no code without a visible effect, and never move marks off their data values beyond the SC-03 exemptions.

## Step 5: Test the fix (BOTH themes)

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

**JavaScript (`LANGUAGE=javascript`)**: run the browser render harness (it writes
both the PNG and the interactive HTML); do not run the `.js`/`.tsx` file directly.
Run from the repo root so `node_modules` resolves (`{EXT}` is `.js` for
chartjs/d3/echarts/highcharts, `.tsx` for muix — the harness handles the React
bundling automatically):
```bash
cd plots/{SPEC_ID}/implementations/{LANGUAGE}
ANYPLOT_THEME=light node "$GITHUB_WORKSPACE/automation/js-render/render.mjs" {LIBRARY}{EXT}
ANYPLOT_THEME=dark  node "$GITHUB_WORKSPACE/automation/js-render/render.mjs" {LIBRARY}{EXT}
```

Both renders must succeed.

## Step 6: Visual self-check

View `plot-light.png` AND `plot-dark.png`. Verify the failed criteria are now fixed in both renders — and confirm the data colors are identical across themes (only chrome should flip).

## Step 7: Format the code

**Python (`LANGUAGE=python`)**:
```bash
source .venv/bin/activate
ruff format plots/{SPEC_ID}/implementations/{LANGUAGE}/{LIBRARY}.py
ruff check --fix plots/{SPEC_ID}/implementations/{LANGUAGE}/{LIBRARY}.py
```

**R (`LANGUAGE=r`)**: no formatter is required by CI. Keep idiomatic ggplot2
style (4-space indent, `<-` for assignment).

**Julia (`LANGUAGE=julia`)**: no formatter is required by CI. Keep idiomatic
Julia style (4-space indent, `lowercase_with_underscores` variables / functions,
`CamelCase` types/modules).

## Step 8: Commit and push

```bash
git config user.name "github-actions[bot]"
git config user.email "github-actions[bot]@users.noreply.github.com"
git add plots/{SPEC_ID}/implementations/{LANGUAGE}/{LIBRARY}{EXT}
git commit -m "fix({LIBRARY}): address review feedback for {SPEC_ID}

Attempt {ATTEMPT}/4 - fixes based on AI review"
git push origin {BRANCH}
```

If you declined any weakness in Step 1, add a `Declined:` list to the commit body, one line per weakness with its reason, for example:

```
Declined:
- "bubbles overlap in the dense cluster" — obsolete (C2): expected per the spec's characteristic section; alpha already keeps every bubble visible
- "Suggestion: a focal highlight on the leading bar" — suggestion, not taken
- "add a trend line" — asks for something the spec does not require
```

## Report result

Print: `REPAIR_SUCCESS` or `REPAIR_FAILED: <reason>`
