# Quality Criteria

Two-stage evaluation: Auto-Reject + Quality Scoring.

## Overview

```text
Implementation
     │
     ▼
┌─────────────────────┐
│  Stage 1: Auto-Reject  │  ──► FAIL → Score = 0
│  (9 checks)            │       AR-01..AR-05, AR-07: regenerate (workflow)
│                        │       AR-06, AR-08, AR-09: repair via review cascade (AI)
└─────────────────────┘
     │ PASS
     ▼
┌─────────────────────┐
│  Stage 2: Quality      │  ──► Review 1: ≥ 90 → ai-approved, merge
│  (0-100 points)        │  ──► Review 2: ≥ 80 → ai-approved, merge
│                        │  ──► Review 3: ≥ 70 → ai-approved, merge
│                        │  ──► Review 4: ≥ 60 → ai-approved, merge
│                        │  ──► Review 5: ≥ 50 → ai-approved, merge
└─────────────────────┘
     │ After Review 5
     ▼
┌─────────────────────┐
│  Final Decision        │  ──► < 50 → not in repo, regenerate
└─────────────────────┘
```

---

## Stage 1: Auto-Reject

Checks that gate quality scoring. On fail: Score=0. Workflow-handled checks (AR-01..AR-05, AR-07) reject without retry — regenerate the whole impl. AI-handled checks (AR-06, AR-08, AR-09) set score=0 inside the review and enter the existing 5-review / 4-repair cascade.

| ID | Check | Description | Verification |
|----|-------|-------------|--------------|
| AR-01 | SYNTAX_ERROR | Code cannot be parsed | Language parser (`python -m py_compile`, `Rscript -e parse`, `node --check`, …) |
| AR-02 | RUNTIME_ERROR | Code throws exception | Execution with timeout |
| AR-03 | NO_OUTPUT | No `plot.png` created | File exists? |
| AR-04 | EMPTY_PLOT | Image empty | < 10KB or > 95% white |
| AR-05 | NO_LIBRARY | Library not used | 0 plot functions from library |
| AR-06 | NOT_FEASIBLE | Library cannot implement spec | AI decision |
| AR-07 | WRONG_FORMAT | Wrong output type | Not .png for static libraries |
| AR-08 | FAKE_FUNCTIONALITY | Static library simulates interactive features | AI decision |
| AR-09 | EDGE_CLIPPING | Title / axis label / legend clipped at canvas border | AI decision (visual) |

**Check order:** AR-01 → AR-02 → AR-03 → AR-04 → AR-05 → AR-06 → AR-07 → AR-08 → AR-09

### AR-05: Library Usage

Implementation must use **plot functions** from the library, not just styling.

| Library | Must use | NOT sufficient |
|---------|----------|----------------|
| seaborn | `sns.scatterplot`, `sns.barplot`, `sns.heatmap`, etc. | Only `sns.set_style()` or `sns.load_dataset()` |
| plotly | `px.*` or `go.*` plot functions | Only `update_layout()` |
| bokeh | `figure.scatter()`, `figure.line()`, etc. | Only styling |
| altair | `alt.Chart().mark_*()` | Only `configure_*()` |
| plotnine | `ggplot() + geom_*()` | Only `theme()` |
| pygal | Chart classes with data | Only config |
| highcharts | `Highcharts.chart()` with series | Only options objects |
| letsplot | `ggplot() + geom_*()` | Only `ggsize()` |
| chartjs | `new Chart(...)` with datasets | Only options/plugin config |
| d3 | Data joins + scales rendering marks (`selection.data(...).join(...)`) | Only selections/styling |
| echarts | `chart.setOption(...)` with series | Only `echarts.init()`/theme config |
| muix | MUI X chart components (`<LineChart>`, `<ScatterChart>`, …) with series | Only `ThemeProvider`/styling |

**Note:** Using data loading utilities (e.g., `sns.load_dataset()`, `sklearn.datasets`) from other libraries is allowed and does not count as library usage. This check only evaluates whether the implementation uses the library's **plotting functions**.

### AR-06: Not Feasible

When a library cannot technically implement a spec (e.g., pygal cannot do 3D), this is an Auto-Reject. No retry, no file in repo.

### AR-08: Fake Functionality

A static library (matplotlib, seaborn, plotnine, ggplot2, makie) simulates interactive features that cannot work in a PNG image.

**Triggers (auto-reject):**
- Simulated tooltips (annotation boxes styled to look like hover tooltips)
- Simulated selection/hover state (one element highlighted as if "clicked" or "hovered")
- Simulated UI controls (drawn buttons, sliders, dropdown menus)
- Code comments containing "simulating hover", "simulating click", "simulating interactivity", or similar

**NOT auto-reject (legitimate techniques):**
- Small multiples / faceted grids as static alternative to animation
- Cell annotations in heatmaps (these are native text, not fake tooltips)
- Color encoding of time direction (arrows, gradients showing progression)
- Honest notes like "See Plotly version for interactive features"

### AR-09: Edge Clipping

Any text element — title, axis title, axis tick labels, legend, annotations — is **clipped at the canvas border**, meaning visible pixels of the element are missing because they were rendered outside the saved PNG's bounding box and chopped off.

This is distinct from VQ-05's soft "no overflow" check (deducts when text leaves its *axis* but stays on the canvas). AR-09 rejects outright when pixels are missing at the *canvas* edge. The post-render canvas-size gate enforces dimensions but cannot see what is at those edges — that's the reviewer's job.

**Triggers (auto-reject, Score = 0):**
- Title cropped at top edge (top of letters cut, descenders missing, title not fully visible above the plot area)
- Y-axis tick labels missing leftmost digit because they touch the left canvas edge ("500" rendered as "00")
- X-axis label cut at bottom edge (axis title only half-visible at the canvas bottom)
- Legend entries hidden behind / merged into the canvas edge
- Any annotation, label, or category text whose bounding box is partially outside the saved PNG

**NOT auto-reject (legitimate / handled by VQ-05 instead):**
- Tooltips or hover affordances drawn intentionally near the edge
- Decorative gridlines or borders aligned with the canvas edge
- Text that overflows its *axis bounds* but stays fully within the canvas — that's a VQ-05 deduction at most, not AR-09
- Tight-but-readable margins: every pixel of the text is visible, just close to the edge
- Touching the border without missing pixels (proximity ≠ clipping)

The bar is strict: AR-09 requires evidence that pixels were *removed*, not merely that an element sits near the boundary.

---

## Allowed Image Formats

| Format | Size | Aspect Ratio |
|--------|------|--------------|
| **Landscape** | 3200 × 1800 px | 16:9 |
| **Square** | 2400 × 2400 px | 1:1 |

**Both have ~5.76M pixels** → same font sizes work for both.

**AI decides freely** which format is best for the specific plot.

---

## Stage 2: Quality Scoring (100 Points)

**Only if Stage 1 passed.** Focus purely on quality.

### Scoring Philosophy: Cascading Thresholds

| Review Stage | Requirement | Outcome |
|--------------|-------------|---------|
| Review 1 (Initial) | ≥ 90 | **Approved** - Publication quality |
| Review 2 (Repair 1) | ≥ 80 | **Approved** - High quality |
| Review 3 (Repair 2) | ≥ 70 | **Approved** - Good quality |
| Review 4 (Repair 3) | ≥ 60 | **Approved** - Acceptable quality |
| Review 5 (Repair 4) | ≥ 50 | **Approved** - Minimum quality |
| Final Status | < 50 | **Rejected** - Not in repo |

**Workflow:**
- **Meet Stage Threshold**: ai-approved, merged immediately
- **Below Stage Threshold**: ai-rejected, repair loop (up to 4 repair attempts)
- **After 4 repairs (Review 5)**: < 50 → close PR and regenerate

**Principles:**
- Full points only for **perfect** implementation
- Small flaws = immediate deduction
- Cascading thresholds allow good plots to merge faster while preventing infinite loops
- 90%+ = could appear in Nature/Science

### Point Distribution

| Category | Points | Focus |
|----------|--------|-------|
| Visual Quality | 30 | Readability, clarity, no defects |
| Design Excellence | 20 | Aesthetic sophistication, storytelling, polish |
| Spec Compliance | 15 | Matches the spec? |
| Data Quality | 15 | Good example data? |
| Code Quality | 10 | Clean code? |
| Library Mastery | 10 | Uses library strengths creatively? |
| **Total** | **100** | |

---

## Visual Quality (30 Points)

| ID | Criterion | Max | Scoring |
|----|-----------|-----|---------|
| VQ-01 | Text Legibility | 8 | 8=perfect (sizes explicitly set), 5=good, 3=ok, 0=poor |
| VQ-02 | No Overlap | 6 | 6=no overlap, 3=minimal, 0=overlap |
| VQ-03 | Element Visibility | 6 | 6=optimal sizing, 3=visible, 0=barely visible |
| VQ-04 | Color Accessibility | 2 | 2=colorblind-safe contrast, 1=ok, 0=red-green only |
| VQ-05 | Layout & Canvas | 4 | 4=perfect, 2=ok, 0=cut-off |
| VQ-06 | Axis Labels & Title | 2 | 2=with units, 1=descriptive, 0=x/y |
| VQ-07 | Palette Compliance | 2 | 2=correct Imprint palette / `imprint_seq` or `imprint_div` cmap + theme-correct chrome, 1=partial, 0=non-compliant |

### VQ-01: Text Legibility (8 Points)

All text must be clearly readable at 3200×1800 / 2400×2400 px and remain legible when the PNG is scaled down to ~400 px (mobile viewport). See `prompts/default-style-guide.md` → "Visual Sizing Defaults" for per-library-family starting values and "Proportional Sizing" for the proportional checks.

**Source-of-values is irrelevant** for VQ-01: defaults, AI-tuned, or repair-loop-tuned all score equally — what matters is the visual result. If the AI deviates from the style-guide defaults because the plot looks better that way (e.g. shrinking the title to fit a long mandated string, or growing tick labels for a sparse plot), that is **not** a deduction.

| Points | Criterion |
|--------|-----------|
| 8 | All font sizes explicitly set and the result looks well-proportioned: no overflow, balanced X/Y axis labels + ticks, readable at both desktop and mobile widths. Title fits without clipping — for the long mandated `{spec-id} · {lang} · {lib} · anyplot.ai` format ~70–85% of width is expected and fine; shorter custom titles aim for ~50–70%. Deviations from style-guide defaults are fine if they improve the result. |
| 5 | All readable but relying on library defaults rather than explicit sizing |
| 3 | Partially too small OR proportions clearly off (e.g. short axis label "Date" disproportionately oversized, title overflowing >90% of width or clipping the canvas edges) |
| 0 | Text hard to read at the canvas size, or text element unreadable in one of the two themes |

**Key distinction:** Score of 8 requires **explicitly setting** font sizes, not just lucky defaults.

### VQ-02: No Overlap (6 Points)

No overlapping text elements.

| Points | Criterion |
|--------|-----------|
| 6 | No overlap - all text fully readable |
| 3 | Minimal overlap, main content readable |
| 0 | Significant overlap, text unreadable |

**Common problems:**
- X-axis labels overlap with many categories
- Tick labels overlap each other
- Legend overlaps data

**Overlap of data marks** (bubbles, points, violins, network nodes) is a weakness only when it **hides information** — a cluster so opaque that the extent or the presence of distinct marks can no longer be read. For overlap-native types (bubble charts, dense scatters, strip plots, networks) overlap in dense regions is expected: when translucency, a thin outline (page- or ink-colored) or a smaller marker keeps every mark distinguishable, it is **not a deduction**. Never suggest moving marks off their data values to reduce overlap — the fixes are data generation, marker size and alpha (see SC-03).

### VQ-03: Element Visibility (6 Points)

Data elements must be visible and adapted to data density.

| Points | Criterion |
|--------|-----------|
| 6 | Markers/lines perfectly adapted to data density |
| 3 | Visible, but not optimal (too big/small) |
| 0 | Elements barely visible or completely overlapping |

**Guidelines for Scatter:**

| Data points | Marker Size (s=) | Alpha |
|-------------|------------------|-------|
| < 30 | 200-400 | 0.9-1.0 |
| 30-100 | 100-200 | 0.7-0.9 |
| 100-300 | 50-100 | 0.5-0.7 |
| 300+ | 20-50 | 0.3-0.5 |

**Legend glyphs count as elements.** Size-legend circles, color swatches and line samples must be visible in **both** themes and must match the marks they explain (same fill, outline, alpha and shape). A glyph drawn in the page color, at near-zero alpha, or without the marks' fill is an invisible element: deduct VQ-03 in proportion, and also SC-04 when the encoding it explains becomes unreadable. Look at the legend in each render — do not assume it inherited the marks' styling. The weakness should name the likely fix (e.g. ggplot2 `guides(size = guide_legend(override.aes = list(fill = ..., alpha = ...)))`, or setting the legend marker color explicitly from the palette).

### VQ-04: Color Accessibility (2 Points)

This check covers **contrast and CVD safety beyond palette choice** — e.g., adequate luminance difference between overlapping series, sufficient alpha for overlapping markers, no red-green as the sole distinguishing signal when overriding the palette.

| Points | Criterion |
|--------|-----------|
| 2 | Good contrast, CVD-safe — elements distinguishable without relying on hue alone |
| 1 | Acceptable but not optimal |
| 0 | Red-green as only distinguishing feature, or critical contrast failures |

**Note:** Palette choice itself (correct Imprint palette, correct continuous cmap) is scored separately in **VQ-07**. VQ-04 is about how the palette is *applied* — spacing, alpha, luminance — not which palette was picked.

### VQ-05: Layout Balance & Canvas Utilization (4 Points)

| Points | Criterion |
|--------|-----------|
| 4 | Perfect layout: plot fills 50-80% of canvas, balanced margins |
| 2 | Minor issues: plot fills 30-50% of canvas, some wasted space |
| 0 | **Severe**: plot fills <30% of canvas, OR content cut-off, OR legend isolated |

**Canvas Utilization Rules:**
- Plot elements (chart, axes, labels) should use **at least 40%** of the canvas area
- Whitespace should be **balanced** around the plot (not all on one side)
- Legend should be **near** the plot, not floating isolated in empty space
- Tiny plot in center of huge canvas = **automatic 0 points**

### VQ-06: Axis Labels & Title (2 Points)

| Points | Criterion |
|--------|-----------|
| 2 | Descriptive with units: "Temperature (°C)" |
| 1 | Descriptive without units: "Temperature" |
| 0 | Generic: "x", "y", or empty |

### VQ-07: Palette Compliance (2 Points)

The implementation must use the **Imprint categorical palette** (defined in `prompts/default-style-guide.md` "Categorical Palette") for categorical data and one of the **Imprint continuous colormaps** (`imprint_seq` or `imprint_div`) for continuous data — no other cmaps. Both light and dark renders are inspected — the data colors (positions 1–8) must be identical across themes; only the theme-adaptive chrome (background, text, grid, legend box) may flip. Three semantic anchors (`#DDCC77` amber, theme-adaptive `neutral` and `muted`) sit outside the categorical pool and are only used intentionally for their semantic role. Always refer to the palette as **Imprint** (capitalised) in your review notes — never "anyplot palette".

| Points | Criterion |
|--------|-----------|
| 2 | Perfect palette + perfect theme chrome: first categorical series is `#009E73`; if multi-series, colors come from the Imprint palette — canonical order (`#C475FD`, `#4467A3`, `#BD8233`, `#AE3030`, `#2ABCCD`, `#954477`, `#99B314`) by default, or reassigned to palette members that match strong semantic cues (grass→green, wood→ochre, blood→red, sky→blue); continuous data uses `imprint_seq` (single-polarity) or `imprint_div` (diverging) — no other cmaps; plot background is `#FAF8F1` (light) or `#1A1A17` (dark) — never pure white/black; text, grid, and legend-box colors are theme-correct in both renders |
| 1 | Partial compliance: palette is the Imprint palette but first series is not `#009E73`; OR continuous data uses an Imprint cmap but the wrong polarity (e.g. `imprint_seq` on diverging-polarity data); OR chrome is mostly theme-correct with one or two off elements (e.g., dark render has one black label) |
| 0 | Non-compliant: legacy `#306998` (Python Blue) or legacy variant-D hexes (`#9418DB`, `#B71D27`, `#16B8F3`, `#D359A7`, `#BA843E`) still present; categorical palette is arbitrary custom hexes, `Set2`, `tab10`, or `colorblind`; continuous data uses `jet`/`hsv`/`rainbow`; categorical palette applied to continuous data (banding); plot background is pure `#FFFFFF`/`#000000`; or chrome is wrong-theme (e.g., dark page with dark text) |

**Evaluation steps for VQ-07:**
1. Look at `plot-light.png`: does the primary data series render in `#009E73`? Does the background look like `#FAF8F1`?
2. Look at `plot-dark.png`: is the data series still `#009E73` (identical to light)? Is the background `#1A1A17`? Is all text light-colored?
3. If multi-series, confirm the next colors in order match Imprint palette positions 2–N (or the semantic-exception assignment when category labels imply real-world colors).
4. If continuous: check the source code for `cmap=` / `scheme=` / `color_continuous_scale=`. Reject anything other than `imprint_seq` (single-polarity) or `imprint_div` (diverging). Common rejections: `jet`/`hsv`/`rainbow`/`viridis`/`cividis`/`BrBG`/`Reds`/`Blues`/`Greens` — all forbidden.
5. If either render fails theme-chrome (unreadable text, wrong background), score drops accordingly.

---

## Design Excellence (20 Points)

This category evaluates aesthetic sophistication beyond mere correctness. A plot can be technically correct but visually generic — Design Excellence separates "works" from "beautiful."

| ID | Criterion | Max | Description |
|----|-----------|-----|-------------|
| DE-01 | Aesthetic Sophistication | 8 | Color harmony, typography, professional polish |
| DE-02 | Visual Refinement | 6 | Grid styling, whitespace, attention to detail |
| DE-03 | Data Storytelling | 6 | Visual hierarchy, data choice, emphasis on insight |

### DE-01: Aesthetic Sophistication (8 Points)

| Points | Criterion |
|--------|-----------|
| 8 | Publication-ready: custom palette, intentional hierarchy, FiveThirtyEight-level design |
| 6 | Strong design: thoughtful colors, good typography, clearly above defaults |
| 4 | Looks like a well-configured library default |
| 2 | Generic/boring: default colors, no design thought |
| 0 | Ugly: clashing colors, poor typography, looks broken |

**Calibration:** DE-01 > 6 is rare on first attempt. Most implementations will score 2-4.

### DE-02: Visual Refinement (6 Points)

| Points | Criterion |
|--------|-----------|
| 6 | Perfect: subtle grid (or none), spines removed, generous whitespace, every detail polished |
| 4 | Good: some refinement visible (grid adjusted, spines partially removed) |
| 2 | Default: library defaults with minimal customization |
| 0 | Sloppy: bold grid, all spines, cramped layout |

### DE-03: Data Storytelling (6 Points)

| Points | Criterion |
|--------|-----------|
| 6 | Excellent: plot tells a clear story through data choice, visual hierarchy, and emphasis — viewer immediately sees the insight |
| 4 | Good: visual hierarchy guides the reader — color contrast, size variation, or focal points create emphasis |
| 2 | Default: data is displayed but not interpreted — viewer must find their own story |
| 0 | None: raw data dump with no context |

**Calibration:** DE-03 = 2 is the default. Most implementations just display data without storytelling. Score of 4+ does NOT require annotations — visual hierarchy (color contrast, size variation, focal points) is sufficient. Annotations are only expected when the spec explicitly requests them (e.g., spec-id contains "annotated").

---

## Spec Compliance (15 Points)

| ID | Criterion | Max | Description |
|----|-----------|-----|-------------|
| SC-01 | Plot Type | 5 | Correct chart type |
| SC-02 | Required Features | 4 | All spec features present |
| SC-03 | Data Mapping | 3 | X/Y correctly assigned |
| SC-04 | Title & Legend | 3 | Title format correct, legend labels match data |

### SC-01: Plot Type (5 Points)

| Points | Criterion |
|--------|-----------|
| 5 | Correct chart type, all subtypes present |
| 3 | Correct base type but missing variant (e.g., grouped bar instead of stacked) |
| 0 | Wrong chart type entirely |

**Related but different form.** A related chart type that is not the one the spec names — a donut for a pie, split-violin halves that do not meet — scores SC-01 partially (typically 3) on any spec, not only on `-basic` ones.

**Variant creep on `-basic` specs.** When the spec id ends in `-basic`, encodings or elements the spec neither requires nor offers as optional (a Data column or a Notes bullet that allows color by category is asked for; a channel driven by a derived fourth variable is not) — a color channel driven by a derived fourth variable, per-group fits or trend lines, reference or mean lines, highlighted marks or bands, callouts or other annotation layers; one such addition is enough — make it the wrong variant: score SC-01 partially (typically 3) and give that addition **no** DE-03 or LM-02 credit. When the spec's characteristic section lists what its variant excludes, the list names the likeliest additions, not all of them: anything the spec neither requires nor offers as optional is still creep. A basic chart earns storytelling through its data and design, not through extra channels (see `prompts/plot-generator.md` → "Respect the spec variant").

### SC-02: Required Features (4 Points)

| Points | Criterion |
|--------|-----------|
| 4 | All features from spec present and working |
| 2 | Most features present, minor omissions |
| 0 | Key features missing |

### SC-03: Data Mapping (3 Points)

| Points | Criterion |
|--------|-----------|
| 3 | X/Y correctly assigned, axes show all data |
| 1 | Minor mapping issues |
| 0 | X/Y swapped or data not visible |

**Data-value integrity: marks sit at their data values.** Changing the generated data (a different seed, a spread-out scenario, rejection sampling) is allowed — the spec does not pin the data. Displacing marks **after** the data exists is not: force or collision layouts applied to data marks, nudge or declutter passes that rewrite plotted x/y values, or offsets that move a mark away from the value its tooltip or axis reports. Deduct SC-03 in proportion to how far marks move relative to the axis range (a few marks shifted by a hair is a small deduction; a cloud rearranged by a simulation loses most of SC-03), and never list such displacement as a strength. A smoothed curve that swings past the values it connects (spline overshoot) also shows values the data does not have; deduct SC-03 in proportion to the overshoot. **Exempt:** jitter in categorical strip and swarm plots (the categorical axis carries no value), and layout-positioned types where position is not data — networks, treemaps, word clouds, packed circles — and any jitter, dodge or offset the spec's Data or Notes ask for (then it is a required feature, not displacement). Moving **labels** to avoid collisions is fine; moving the **marks** is not.

### SC-04: Title & Legend (3 Points)

| Points | Criterion |
|--------|-----------|
| 3 | Title is `{spec-id} · {language} · {library} · anyplot.ai`, optionally prefixed with `{Descriptive Title} · ` (language ∈ {python, r, julia, javascript}). Legend labels correct |
| 2 | Title format correct but legend issues, or vice versa |
| 1 | Partially correct |
| 0 | Missing or wrong |

---

## Data Quality (15 Points)

| ID | Criterion | Max | Scoring |
|----|-----------|-----|---------|
| DQ-01 | Feature Coverage | 6 | 6=shows ALL aspects, 3=most, 0=one-sided |
| DQ-02 | Realistic Context | 5 | 5=real scenario, 3=plausible, 1=abstract labels, 0=nonsense |
| DQ-03 | Appropriate Scale & Factual Correctness | 4 | 4=factually correct proportions, 2=plausible, 0=nonsense/impossible |

### DQ-01: Feature Coverage (6 Points)

Example data must show ALL features of the plot type.

**A permission is not an aspect to exhibit.** An `Expected, not a defect:` bullet in the spec's characteristic section (see "Plot-Type Characteristics") names something the data may produce, not something it has to show: data with little or no overlap loses nothing. A point count inside the spec's Data range is not a DQ-01 lever either — never deduct "only N points" for a count in range, and never credit dense clusters or overlap as coverage.

**An optional feature is not an aspect to exhibit either.** A feature the Notes only allow, such as percentage labels or asymmetric error bars, is a display choice: a version without it loses nothing on DQ-01.

| Points | Criterion |
|--------|-----------|
| 6 | Shows all aspects (e.g., boxplot with outliers AND different distributions) |
| 3 | Shows main features, but not all edge cases |
| 0 | All groups look the same, no variation |

**Examples:**
- Candlestick: Bullish AND bearish candles
- Boxplot: Outliers AND different spreads
- Histogram: Multimodal distribution when appropriate

### DQ-02: Realistic Context (5 Points)

| Points | Criterion |
|--------|-----------|
| 5 | Real, comprehensible, **neutral** scenario (science, business, nature) |
| 3 | Plausible, but generic |
| 1 | Abstract labels only ("Category A", "Group 1", "Series X") |
| 0 | Nonsensical data OR controversial/sensitive topic (real politics, race, religion, gender stereotypes) |

**Content Policy:** Data must avoid controversial, divisive, or sensitive topics:
- ❌ Real politics (real parties, politicians, elections, a real legislature — national, regional, or supranational — partisan messaging)
- ❌ Religion, race/ethnicity comparisons
- ❌ Gender/sexuality stereotypes
- ❌ Violence, war, weapons
- ✅ Science, business, nature, technology, food, education (generic)

A clearly fictional parliament (invented party names that carry no real-world ideology, invented seat counts, no real country, election, or politician) is not political content: it never scores 0 or triggers the cap. When the spec asks for invented data, being fictional is not a deduction: it scores on comprehensibility like any other scenario, and the fix for flat invented names is better invented names, never real ones.

### DQ-03: Appropriate Scale & Factual Correctness (4 Points)

| Points | Criterion |
|--------|-----------|
| 4 | All values, proportions, and relational scales align perfectly with established real-world facts and logical constraints for the chosen domain. |
| 2 | Values are plausible but relationships or proportions may be slightly inaccurate. |
| 0 | Violation of fundamental physical, geographical, or logical realities; data is factually impossible or nonsensical for the context. |

---

## Code Quality (10 Points)

| ID | Criterion | Max | Description |
|----|-----------|-----|-------------|
| CQ-01 | KISS Structure | 3 | Imports → Data → Plot → Save (no functions/classes) |
| CQ-02 | Reproducibility | 2 | `np.random.seed(42)` or deterministic data |
| CQ-03 | Clean Imports | 2 | Only used imports (including data utilities like `sns.load_dataset()`) |
| CQ-04 | Code Elegance | 2 | Appropriate complexity, no algorithm written out that an available call computes, no over-engineering, no fake functionality |
| CQ-05 | Output & API | 1 | Saves as `plot.png`, no deprecated functions |

### CQ-04: Code Elegance (2 Points)

| Points | Criterion |
|--------|-----------|
| 2 | Clean, appropriate complexity for the visualization, and no algorithm written out that an available call computes |
| 1 | A named block could be much leaner with the same output and equal readability: an algorithm written out that an available call computes the same way (a KDE, binning, quantiles, ACF/PACF, a fit, a linkage), or a block that a named, clearly shorter form replaces (duplicated logic, dead code, a pass without a visible effect) |
| 0 | Over-engineered, draws fake UI elements, or contains fake-functionality code/comments |

**CQ-04 = 0 if code draws fake interactive elements** (buttons, sliders, tooltip boxes) or contains comments like "simulating hover/click."

#### Available to compute with

What CI installs for the library under review. These four blocks are the same, word for word, as in `prompts/plot-generator.md` → "Available Standard Packages", which the generator reads.

**Python — compute with:**
- Every Python library gets numpy, pandas, SciPy, scikit-learn and statsmodels. Examples:
  - density and fits: `scipy.stats.gaussian_kde`, `np.histogram`, `np.percentile`, `np.polyfit`, `scipy.stats.linregress`, `statsmodels.api.OLS`;
  - time series and signals: `np.fft.rfft`, `scipy.signal.welch`, `scipy.signal.spectrogram`, `statsmodels.tsa.stattools.acf` / `pacf`, `statsmodels.nonparametric.smoothers_lowess.lowess`;
  - clustering and geometry: `scipy.cluster.hierarchy.linkage` / `dendrogram`, `sklearn.cluster.KMeans`, `scipy.spatial.ConvexHull` / `Voronoi`, `scipy.interpolate`, `scipy.integrate.solve_ivp`;
  - model evaluation: `sklearn.metrics.roc_curve` / `confusion_matrix`;
  - data wrangling: pandas `rolling` / `ewm` / `groupby` / `pivot_table` / `cut`;
  - the plotting library's own stat functions (`sns.kdeplot`, `transform_density`, `stat_density`, …).
- matplotlib is installed everywhere, but its plotting calls belong only in matplotlib and seaborn implementations; elsewhere use only its non-plotting utilities, such as `matplotlib.colors`.
- Not available: networkx, squarify, cartopy, and any package outside these.

**R — compute with:**
- ggplot2, dplyr, tidyr, scales, tibble, ragg, viridis, patchwork, systemfonts, textshaping, palmerpenguins and gapminder, their imports, base R and R's recommended packages (survival, MASS, class, cluster). Examples:
  - base `stats`: `acf`, `pacf`, `density`, `loess`, `lm`, `hclust` / `dist` / `cutree`, `kmeans`, `prcomp`, `fft` / `spectrum`, `ecdf`, `quantile`, `smooth.spline`;
  - ggplot2 stat layers: `stat_density`, `geom_smooth`, `stat_ecdf`, `stat_qq`, `geom_density_2d`, `stat_summary`;
  - `survival::survfit`.

**Julia — compute with:**
- CairoMakie, Makie, DataFrames, CSV, Colors, ColorSchemes, RDatasets, PalmerPenguins, PNGFiles, QRCoders, Random and Statistics, plus the standard libraries LinearAlgebra, Dates and Printf. Examples:
  - Makie recipes that compute for you: `density!`, `hist!`, `stephist!`, `boxplot!`, `violin!`, `qqplot!`, `ecdfplot!`, `rainclouds!`, `contour!`;
  - Statistics: `mean`, `median`, `quantile`, `std`, `cor`;
  - least squares with `X \ y`.
- Not loadable: StatsBase, KernelDensity, FFTW, Clustering, GLM and Loess. A short written-out ACF, FFT or linkage is therefore fine.

**JavaScript — compute with:**
- Only the snippet's own library is loaded: chartjs, d3, echarts, highcharts or muix. No JavaScript runtime here has a 1-D KDE, an FFT, a regression or clustering, so short written-out versions are fine. What each library computes for you is in `prompts/library/{library}.md` → **Computation**.

Library-specific facts: `prompts/library/{library}.md` → Computation.

How to score it:

- What nothing available provides may be written out, and it is not a deduction.
- A leanness deduction is a defect line only when it names the replacement and the lines: ``CQ-04 (code): lines A–B <what is written out, with the saving in lines> → `<call>` (<package>). Likely cause: ….``, or `→ remove` for dead or duplicated code. The call names the arguments that reproduce the output (a bandwidth, `ddof`, a `method`, a window): a library default that gives different numbers is not the same computation. Without a concrete replacement it is a `Suggestion:` line.
- "Clearly shorter" is proportional: a block that shrinks to a fraction of its length is a defect, and a few lines of taste is a suggestion. A block of a handful of lines (a closed-form slope and intercept, a four-line loop) is a suggestion whatever the ratio. There is no line threshold.
- Not deducted: the mandated header, theme and palette token blocks, the `sys.path` self-shadowing guard, and a hand-roll whose output no available call reproduces.
- A replacement is a call or a removal, never a new helper function (CQ-01), and never code golf: a shorter version that reads worse is not leaner.
- Installed packages are not dependencies to avoid: never credit a hand-roll for avoiding one.
- Leanness costs 1 point at most, however many blocks it names, and never takes CQ-04 to 0. CQ-04 = 0 stays reserved for fake functionality and gross over-engineering.

---

## Library Mastery (10 Points)

| ID | Criterion | Max | Description |
|----|-----------|-----|-------------|
| LM-01 | Idiomatic Usage | 5 | Uses library's recommended patterns and high-level API |
| LM-02 | Distinctive Features | 5 | Leverages features unique to this library |

### LM-01: Idiomatic Usage (5 Points)

| Points | Criterion |
|--------|-----------|
| 5 | Expertly uses the library's high-level API and recommended patterns |
| 3 | Correct usage but doesn't leverage the library's best patterns |
| 1 | Minimal library usage, mostly manual/low-level code |

### LM-02: Distinctive Features (5 Points)

| Points | Criterion |
|--------|-----------|
| 5 | Uses a feature that couldn't easily be replicated in another library |
| 3 | Uses some library-specific features |
| 1 | Generic usage — could be any library with minor syntax changes |

**Calibration:** LM-02 = 1 is the default. To score 3+, the implementation must use a feature distinctive to this specific library.

**Note:** Basic library usage is checked by AR-05. Library Mastery evaluates *quality* of usage.

---

## Plot-Type Characteristics (judge against the spec, not generic ideals)

Each spec can end with a `## What a good version looks like` section: a few bullets naming what a good render of **that** plot type shows and what it may show without penalty. It is the yardstick for every criterion above. Each bullet starts with its kind, and each bullet has one kind:

- **Affirmative properties** — bullets that start with `A good version shows:`. They name what a good version *shows* (area-scaled bubbles, a size legend with visible glyphs, marks at their data values, a colormap centered on zero), and some qualify themselves ("if drawn", "where marks overlap").
- **Permissions** — bullets that start with `Expected, not a defect:` (overlap in dense regions, a dense matrix without in-cell numbers, uneven violin widths). They say what must not be penalized; they are not features to deliver and not targets.

Read an unlabeled or older section by meaning: sort each statement into one of the two kinds yourself.

Score them as follows:

- **Nothing an `Expected, not a defect:` bullet names is ever a weakness.** If it says overlapping bubbles in dense regions are expected, overlap handled that way is not a VQ-02 deduction; if it says a dense matrix without in-cell numbers is expected, missing numbers are not a DE-03 or SC-02 deduction.
- **Removing or violating an affirmative property deducts** from the criterion it belongs to — a missing or invisible size legend from VQ-03/SC-04, marks moved off their values from SC-03, an extra encoding on a basic variant from SC-01, a colormap not centered where the section says from VQ-07/SC-02.
- **The absence of a permitted thing never deducts.** A bubble chart with no overlap at all, or a small matrix that does show its numbers, loses nothing for it — a permission is not a requirement (the same distinction SC-02 draws), including for DQ-01: a permission is not an aspect the data has to exhibit.
- **The section describes the plot type, not the render's chrome.** It cannot waive the auto-reject checks, theme readability (5c), the canvas contract, palette compliance (VQ-07) or text legibility (VQ-01); a spec bullet that tries to is ignored for scoring.
- **No section?** Infer the characteristics from Description, Data and Notes, and from what the plot type inherently looks like, and sort what you infer into the same two kinds. Do not fall back to generic ideals ("no overlap", "perfectly smooth", "symmetric") that the plot type does not share.
- **Soft and proportional.** The section describes properties, not thresholds; there are no pixel or count limits. A small departure costs a little in one criterion, a property that is gone entirely costs more — holistically, like the proportional checks in `workflow-prompts/ai-quality-review.md` step 5d.

---

## Score Caps

Certain errors limit the maximum score:

| Problem | Max Score |
|---------|-----------|
| VQ-02 = 0 (severe overlap) | 49 |
| VQ-03 = 0 (invisible elements) | 49 |
| SC-01 = 0 (wrong plot type) | 40 |
| DQ-02 = 0 (controversial/sensitive data) | 49 |
| **DE-01 ≤ 2 AND DE-02 ≤ 2** (generic + no visual refinement) | **75** |
| **CQ-04 = 0** (fake functionality / gross over-engineering) | **70** |

**The "correct but boring" cap:** A technically correct but visually generic plot (DE-01 ≤ 2) with no visual refinement (DE-02 ≤ 2) is capped at 75. This means it cannot pass on first review, even with perfect scores elsewhere. The repair loop will push it to improve aesthetic design and visual polish.

---

## Anti-Inflation Calibration Anchors

Evaluators must use these anchors to prevent score inflation:

- **Median implementation should score 72-78** — not 90+
- **DE-01 > 6 is rare** on first attempt — most plots look like configured defaults (score 4)
- **DE-02 = 2 is the default** — library defaults with minimal customization
- **DE-03 = 2 is the default** — most plots just display data without visual hierarchy or emphasis
- **LM-01 = 3 is the default** — correct usage but doesn't leverage the library's best patterns
- **LM-02 = 1 is the default** — most implementations use the library generically
- **When in doubt, deduct** — the repair loop exists to improve quality
- A plot scoring 90+ should genuinely impress a data visualization professional

**Expected distribution:**
- ~25-30% score 85+ on first attempt (vs. current ~95% scoring 90+)
- ~50-60% score 72-84 (good but need design/storytelling improvements)
- ~10-15% score below 72 (significant issues)

---

## Example Evaluation

A "good" plot (~76%):

```text
VISUAL QUALITY (23/30)
  VQ-01: 5/8   (readable, but relying on defaults not explicit sizes)
  VQ-02: 6/6   (no overlap)
  VQ-03: 5/6   (visible, markers could be better)
  VQ-04: 2/2   (good contrast, CVD-safe)
  VQ-05: 2/4   (ok layout, some wasted space)
  VQ-06: 2/2   (labels with units)
  VQ-07: 1/2   (palette is anyplot but first series used #AE3030 instead of #009E73)

DESIGN EXCELLENCE (8/20)
  DE-01: 4/8   (well-configured default, not exceptional)
  DE-02: 2/6   (library defaults, minimal refinement)
  DE-03: 2/6   (data displayed but no storytelling)

SPEC COMPLIANCE (13/15)
  SC-01: 5/5   (correct type)
  SC-02: 3/4   (one minor feature missing)
  SC-03: 3/3   (mapping ok)
  SC-04: 2/3   (title ok, legend not perfect)

DATA QUALITY (13/15)
  DQ-01: 5/6   (shows most features)
  DQ-02: 4/5   (plausible scenario, not abstract)
  DQ-03: 4/4   (good values)

CODE QUALITY (9/10)
  CQ-01: 3/3   (KISS)
  CQ-02: 2/2   (seed set)
  CQ-03: 2/2   (clean imports)
  CQ-04: 1/2   (lines 39–60 write out ACF/PACF → `statsmodels.tsa.stattools.acf`/`pacf`)
  CQ-05: 1/1   (correct output)

LIBRARY MASTERY (9/10)
  LM-01: 5/5   (idiomatic usage)
  LM-02: 4/5   (uses some distinctive features)

TOTAL: 75/100 = "Good" Tier → Repair loop
```

Note: This plot scored well on technical criteria but only 8/20 on Design Excellence. To reach 90+, it needs better aesthetic sophistication (DE-01), visual refinement (DE-02), and data storytelling through visual emphasis and hierarchy (DE-03).
