# Repair Implementation

You are repairing the **{LANGUAGE}/{LIBRARY}** implementation for **{SPEC_ID}**.

This is **repair attempt {ATTEMPT}/3**. The previous implementation was rejected.

## Step 1: Read the AI review feedback

Read both sources to understand what needs to be fixed:

1. `/tmp/ai_feedback.md` - Full review from PR comments
2. `plots/{SPEC_ID}/metadata/{LANGUAGE}/{LIBRARY}.yaml` - Look at:
   - `review.strengths` (keep these aspects!)
   - `review.weaknesses` (fix these problems - decide HOW yourself)
   - `review.image_description` (understand what was generated visually)
   - `review.criteria_checklist` (see exactly which criteria failed)
     - Look for items with `passed: false` - these need fixing
     - Focus on categories with low scores (e.g., visual_quality.score < visual_quality.max)
     - VQ-XX items for visual issues
     - SC-XX items for spec compliance
     - CQ-XX items for code quality

**Important:** If the review triggered AR-08 (FAKE_FUNCTIONALITY), this is NOT repairable via repair. The implementation must either be regenerated as a genuine static visualization or marked NOT_FEASIBLE. Do NOT fix by "improving" the fake elements.

## Step 2: Read reference files

1. `prompts/library/{LIBRARY}.md` - Library-specific rules + theme-adaptive chrome mapping
2. `prompts/default-style-guide.md` - Canonical anyplot palette + theme tokens (re-read if VQ-07 or VQ-04 failed), plus "Visual Sizing Defaults" and "Proportional Sizing" sections (re-read if VQ-01 / VQ-02 / VQ-05 failed)
3. `plots/{SPEC_ID}/specification.md` - The specification

**Visual-sizing fixes (when VQ-01 / VQ-02 / VQ-05 failed):**
- Title too big / overflows → reduce fontsize or shorten title text
- Short axis label disproportionately big ("Date" dominates axis) → reduce that label's fontsize while keeping the other axis-label/tick fontsizes balanced
- Long descriptive label overflows axis → reduce fontsize OR rotate ticks/labels
- Text overlaps → adjust margins, rotate ticks, reduce label fontsize, or move legend
- Sparse data with tiny markers → increase `s=` / `size=` / `marker.size=` / `marker.radius`
- Dense data with oversized markers / overplotting → reduce marker size + add `alpha=0.5-0.7`

Adjust the canvas-controlling knobs of the relevant library family:
- DPI-based (matplotlib / seaborn / plotnine): `figsize`, `dpi`, `fontsize=`
- Scale-based (plotly / altair / lets-plot): `width`/`height`/`scale_factor`, theme font sizes
- Native-pixel (bokeh / highcharts / pygal): `width`/`height` directly, `text_font_size` / `style.fontSize` / `Style(... _font_size=...)` — for highcharts keep the three canvas-size spots in sync (Selenium `--window-size`, HTML `<div style="width:height:">`, `chart.options.chart = {'width':,'height':}`); for bokeh keep Selenium `W, H` matching `figure(width=, height=)`

**Do NOT re-read `prompts/quality-criteria.md`** — the review already distilled all criteria into `review.criteria_checklist` in the metadata YAML (Step 1). Use that checklist directly: items with `passed: false` are the ones to fix.

**Common VQ-07 failures and fixes:**
- Legacy `#306998` still in code → replace with `#009E73` (anyplot palette position 1).
- First series not brand green → rewrite so the primary category renders in `#009E73`.
- Any non-anyplot cmap (jet/hsv/rainbow/viridis/cividis/BrBG/Reds/Blues/Greens) → switch to `imprint_seq` (single-polarity) or `imprint_div` (diverging) — see `prompts/default-style-guide.md` "Continuous Data".
- Pure `#FFFFFF` / `#000000` background → use `#FAF8F1` / `#1A1A17` via the `ANYPLOT_THEME` token block.
- Chrome wrong-theme (dark text on dark bg) → wire up all title/axis/tick/grid/legend colors to the `INK`/`INK_SOFT` tokens.

## Step 3: Read current implementation

`plots/{SPEC_ID}/implementations/{LANGUAGE}/{LIBRARY}{EXT}` — `{EXT}` is `.py`
for python libraries, `.R` for ggplot2, and `.jl` for makie.

**Do NOT read sibling-library implementations under
`plots/{SPEC_ID}/implementations/`** (other libraries' source or `.yaml`).
Each library is an independent interpretation; copying data scenarios,
color choices, layout, or aspect ratio from a sibling defeats the point of
having multiple libraries in the catalog. See `prompts/plot-generator.md` →
"Library Independence" for the full rule.

## Step 4: Fix the issues

Based on the AI feedback, fix:
- Visual quality issues
- Code quality issues
- Spec compliance issues

## Step 5: Test the fix (BOTH themes)

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

**Julia (`LANGUAGE=julia`)**:
```bash
cd plots/{SPEC_ID}/implementations/{LANGUAGE}
ANYPLOT_THEME=light julia --project=. {LIBRARY}.jl
ANYPLOT_THEME=dark  julia --project=. {LIBRARY}.jl
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

Attempt {ATTEMPT}/3 - fixes based on AI review"
git push origin {BRANCH}
```

## Report result

Print: `REPAIR_SUCCESS` or `REPAIR_FAILED: <reason>`
