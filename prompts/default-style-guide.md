# AnyPlot.ai Default Style Guide

Style requirements for consistent, beautiful visualizations at a mid-sized canvas.

## Standard Canvas Size

anyplot renders at ~5.76 million pixels — a mid-sized canvas that balances Hi-Res sharpness for desktop monitors with mobile readability and reasonable file sizes.

**Common Mistake:** Using library defaults (e.g. plotly `marker.size=6`) still produces elements that are too small. Use the "Visual Sizing Defaults" table below as a starting point — the AI may adjust if the plot context demands it, and the review step checks proportions.

---

## Dimensions

Two formats are allowed (same pixel count for consistent font sizing across both):

| Format | Size | Aspect Ratio | Use Case |
|--------|------|--------------|----------|
| **Landscape** | 3200 × 1800 px | 16:9 | Default, most plots |
| **Square** | 2400 × 2400 px | 1:1 | Symmetric plots (pie, radar, heatmaps, grid-based) |

**AI decides freely** which format is best for each specific plot.

**Why these sizes?**
- Landscape: 3200 × 1800 = 5.76 million pixels
- Square: 2400 × 2400 = 5.76 million pixels
- Same pixel area → the same font sizes work for both formats
- Big enough to stay sharp at typical 1920–2560 px desktop widths
- Small enough that mobile loads (and the `400w` / `800w` srcset variants) stay snappy

---

## Color Philosophy

anyplot uses the **Imprint palette** — a bespoke, colorblind-safe categorical palette tuned for paper-ink rendering on both warm-cream and warm-black surfaces. It is the single consistency rule that spans every library and every plot. Always refer to it as **Imprint** (capitalised, no other names) in code comments, metadata, and review notes. Full design rationale: [`docs/reference/palette-variants/v3/decision-rationale.md`](../docs/reference/palette-variants/v3/decision-rationale.md).

### Categorical Palette (Imprint, canonical order)

8 hues in hybrid-v3 sort order. First 4 slots span 4 distinct perceptual hue families (green / purple / blue / yellow), then greedy max-min CVD distance for the tail. Slot 5 is the deferred semantic-red anchor (matte red `#AE3030`) — reached intentionally for bad/loss/error roles, not by ordinal position in every chart.

| # | Hex | Name | Hue family | Role |
|---|-----|------|------------|------|
| 1 | `#009E73` | brand green | green | ★ **brand — ALWAYS first series** |
| 2 | `#C475FD` | lavender | purple | |
| 3 | `#4467A3` | blue | blue | |
| 4 | `#BD8233` | ochre | yellow | earth / commodity |
| 5 | `#AE3030` | matte red | red | semantic anchor for bad / loss / error |
| 6 | `#2ABCCD` | cyan | cyan | sky / tech-cool |
| 7 | `#954477` | rose | purple | wellness / health |
| 8 | `#99B314` | lime | green | growth / nature |

**Hard rules:**
- **First series is ALWAYS `#009E73`** — across every library, every plot type. A "Gentoo penguin" is the same green in matplotlib as it is in plotly. Ordered categories are the one exception: their ramp sets the colors, so a Likert chart may start on its red pole.
- Use positions 1→N in order by default. Don't cherry-pick for aesthetic reasons. Ordered categories take a ramp instead (see "Ordered Categories" below).
- The 8 categorical colors stay identical across light and dark themes so a category keeps its identity. The continuous ramps are not categorical colors: each has its own stops per theme (see "Continuous Data" below).
- Never introduce custom hex values when the Imprint palette already covers the need.

**Semantic exception:**
The default rule is "use positions 1→N in canonical order." But whenever a category has a strong, widely-shared color association that a reader would expect, pick the closest palette member instead of the next ordinal position. This isn't a niche carve-out — there are many such cases. Some illustrative examples (not an exhaustive list):

- **Real-world objects:** grass→green, wood→ochre, blood→red, sky→blue, water→blue, ice→cyan.
- **Status / quality:** bad/error/fail→red, good/ok/pass→green, warning→**amber (see anchors below)**, neutral/disabled→**muted (see anchors below)**.
- **Finance:** profit/up/gain→green, loss/down→red (stock-chart bullish/bearish bars, P&L deltas).
- **Sentiment / polarity:** positive→green, negative→red, neutral→**muted**.
- **Domain conventions:** temperature hot→red / cold→blue, traffic-light states (red/**amber**/green), etc.

The test isn't "does it appear in the list above" — it's "would a typical reader of this chart expect this category to look like this color?" If yes, and a palette member matches that expectation, use it.

### Semantic anchors (outside the categorical pool)

Three additional anchors that are **never** returned by the canonical `palette[:n]` order. Use them only when the semantic role calls for them — never as fallback slots when the pool runs out.

| Anchor | Hex | Role |
|--------|-----|------|
| `amber` | `#DDCC77` | warning / caution. Single fixed hex (Paul Tol "muted" yellow). Min ΔE under CVD to the 8 categorical hexes = 14.52 — confidently distinct from every member. |
| `neutral` | adaptive: `#1A1A17` light / `#F0EFE8` dark | totals / baseline / outline / reference line. Same hex as text + gridlines, so the series reads as part of the chart's structural layer. |
| `muted` | adaptive: `#6B6A63` light / `#A8A79F` dark | other / rest / disabled / confidence-band fill. Soft-contrast neutral for elements that should sit behind the data without competing. |

Practical: in matplotlib `plt.plot(x, y, color="#DDCC77")` for a "warning" annotation; for theme-adaptive neutrals, branch on `ANYPLOT_THEME` (see Reference Python snippet below).

**Constraints (always):**
- Colors must come **from the Imprint palette or the 3 anchors** (no custom hexes).
- The semantic mapping must be obvious from the data labels — the legend or category names should literally say "Pass / Fail", "Profit / Loss", "Up / Down", "Hot / Cold", "OK / Warning / Error", etc.
- Default to canonical order whenever the categories are abstract (groups A/B/C, regions, models, anonymous bins, k-means clusters) — no expectation to break ordinal there.

### Continuous Data — the categorical palette is NOT used

Categorical palettes on continuous data produce misleading banding. anyplot ships exactly two Imprint-derived continuous colormaps, `imprint_seq` and `imprint_div`; **no other cmap is allowed** — not viridis, not cividis, not BrBG, not Blues/Greens/Reds, and never jet/hsv/rainbow.

Each ramp is a list of `(position, hex)` stops from the lowest value (position 0) to the highest (position 1). Colors between two stops blend linearly in sRGB, as `LinearSegmentedColormap.from_list` does; a library that blends in another space by default (Vega-Lite in HCL, ggplot2 in CIELAB) moves the colors between the stops a little, never the stops. The ramps are not perceptually uniform; the sequential stops sit at positions proportional to CIELAB lightness, so lightness changes about evenly along the ramp. Each ramp has its own stops per theme and per use:

- **Fields:** colored areas whose cells touch and fill the plot — heatmaps, spectrograms, filled contours, maps, tiles, hexbins.
- **Marks:** colored marks that sit on the page themselves — points, lines, outlines, and bars colored by a value.

**`imprint_seq` (sequential):** for single-polarity continuous data (intensity, magnitude, density, single-polarity heatmaps). The ramp passes through brand green `#009E73`. In both themes the high values stand out from the page and the low values recede into it, so the ramp runs light → dark on the light page and dark → bright on the dark page. A spec that asks for "light to dark" means low to high: in the dark render the ramp runs dark to bright, and that fulfils the spec.

| Use | Light theme, low → high | Dark theme, low → high |
|-----|-------------------------|------------------------|
| Fields | `(0, "#66E2B2")`, `(0.368, "#009E73")`, `(0.582, "#4467A3")`, `(1, "#002850")`: pale mint → brand green → blue → navy | `(0, "#00573D")`, `(0.467, "#009E73")`, `(1, "#CDD9FF")`: deep green → brand green → pale blue |
| Marks | `(0, "#009E73")`, `(0.338, "#4467A3")`, `(1, "#002850")`: brand green → blue → navy | `(0, "#007755")`, `(0.32, "#009E73")`, `(1, "#CDD9FF")`: dark green → brand green → pale blue |

The fields ramps span the wider lightness range, and their low end sits close to the page: right for a field, whose cells are read against each other, wrong for a mark, which is read against the page. Every color of the sequential marks ramps keeps WCAG 3:1 against its page (WCAG 2.1 SC 1.4.11), so no mark fades into the page.

**`imprint_div` (diverging):** matte red ↔ midpoint ↔ blue, `(0, "#AE3030")`, `(0.5, midpoint)`, `(1, "#4467A3")`, for data with a meaningful midpoint (correlations, residuals, signed deviations, diverging heatmaps); the midpoint sits at the data's meaningful value, often 0.

- **Fields:** the midpoint is the page color, `#FAF8F1` on light and `#1A1A17` on dark, so a cell at the midpoint reads as part of the page.
- **Marks:** the midpoint is the `muted` anchor, `#6B6A63` on light and `#A8A79F` on dark (a SHAP beeswarm, scatter points colored by a signed value). A page-colored midpoint would make the marks near the midpoint vanish against the page; ordered categories follow the same rule.

Which name holds which ramp, per use; each name already holds the stops of the render's theme:

| Language | Fields | Marks | Theme |
|----------|--------|-------|-------|
| Python | `SEQ_FIELDS`, `DIV_FIELDS` | `SEQ_MARKS`, `DIV_MARKS` | picked from `THEME` where the lists are defined (Reference Python snippet below, library prompts) |
| R (ggplot2) | `SEQ_FIELDS`, `DIV_MID_FIELDS` | `SEQ_MARKS`, `DIV_MID_MARKS` | picked from `THEME` (`prompts/library/ggplot2.md`) |
| Julia (Makie) | `ANYPLOT_SEQ_FIELDS`, `ANYPLOT_DIV_FIELDS` | `ANYPLOT_SEQ_MARKS`, `ANYPLOT_DIV_MARKS` | picked from `THEME` (`prompts/library/makie.md`) |
| JavaScript | `t.seqFields`, `t.divFields` | `t.seqMarks`, `t.divMarks` | the render harness fills the tokens for the theme it renders |

Build in matplotlib with `LinearSegmentedColormap.from_list("imprint_seq", SEQ_FIELDS)` or `LinearSegmentedColormap.from_list("imprint_div", DIV_MARKS)`, or with the library's equivalent gradient API that takes stop positions. A library whose gradient API takes evenly spaced colors only (bokeh's `LinearColorMapper`, pygal, lets-plot's `scale_*_gradientn`, ECharts' `visualMap`, Chart.js) samples the stops at 256 even steps with the one helper its library prompt gives, `ramp_color` in Python and `rampAt` in JavaScript. The tokens `t.seq` and `t.div` are the first release's two-stop ramps, kept only so existing files render as before; new code never uses them.

Pick `imprint_seq` vs `imprint_div` from the data's polarity, and fields vs marks from what carries the color. Never substitute a matplotlib/library-native cmap "because it looks nicer" — Imprint identity is part of the brand.

### Ordered Categories

Categories with a natural order — Likert levels ("strongly disagree" … "strongly agree"), grades, small / medium / large, age bands — are not unrelated groups: the categorical palette would present them as such and hide their order. Color them with discrete steps of one Imprint ramp in their natural order, and keep that order in the legend:

- **One direction** (low → high, small → large): steps of the marks ramp of `imprint_seq`.
- **A neutral midpoint** (disagree ↔ agree, worse ↔ better): steps of the marks ramp of `imprint_div`, whose middle level is the `muted` anchor, because the page-colored midpoint of the fields ramp would vanish against the background. When the poles mean bad and good, the semantic exception may anchor them in red and green: matte red `#AE3030` on the bad side (disagree, poor), brand green `#009E73` on the good side (agree, good) — never the other way round.

The steps take the stops of the theme they render in. Every step stays distinguishable from its neighbours and from the background in both themes.

### Color Restraint & series-count guidance

Categorical-color distinguishability falls with n. The hybrid-v3 sort holds ΔE ≥ 13.7 through n=6 under CVD; above that, the eye starts losing pairs. Concrete guidance:

| n series | Color alone is enough? | Add redundant encoding? |
|----------|------------------------|--------------------------|
| 1–2 | Yes | No |
| 3–4 | Yes | No (optional: marker shape on scatter) |
| 5–6 | Borderline (ΔE_CVD ≈ 13.7–10.7) | Recommended: distinct marker shapes OR linestyles |
| 7 | No (ΔE_CVD = 10.7 — at discrimination floor) | Required: marker shape + linestyle, OR small multiples |
| 8 | No (ΔE_CVD = 8.81 — below floor) | Required: small multiples, OR direct labels per series |
| 9+ | Out of palette | Use small multiples; never recycle colors |

**Default to fewer series.** Before adding the Nth color, ask: "could this be small multiples / faceting?" Usually the answer is yes and the chart improves.

**In code, list all eight hues and use the first n.** The palette constant always holds the eight categorical hues in canonical order, and each group takes its color by position (`IMPRINT_PALETTE[i]`, or the library's color cycle fed the full list), with `n` counted from the data, never a literal slice sized to the sample (`[:3]`). The same code then colors one more group correctly on other data. Where the code picks colors by position or by group (`IMPRINT_PALETTE[i]`, `colors[group]`), a ninth group fails loudly instead of recycling a color; a library's color cycle repeats colors instead, so prefer the explicit lookup where the code assigns colors itself.

### Optional outline pattern (AI judgment)

Measured on the two plot surfaces by WCAG relative luminance, three of the 8 categorical hues and amber fall below WCAG 2.1 SC 1.4.11's 3:1 contrast on the light page `#FAF8F1`: lavender (2.70), cyan (2.15), lime (2.24), and amber (1.52), with ochre just above the line (3.09). On the dark page `#1A1A17`, matte red (2.71) and rose (2.80) stay below 3:1, with blue just above the line (3.09). This is the known muted-palette / WCAG tension Okabe-Ito, Paul Tol "muted", and ColorBrewer Set2 all share.

The industry-standard fix is a thin ink-color stroke. **This is a renderer judgment call, not a hard rule.** Add a stroke when:

- The affected series carries critical information (status, threshold, alert)
- The chart is at small physical size (thumbnail, dashboard tile)
- The audience includes screen-readers / accessibility-strict contexts

Skip the stroke when:

- The series is decorative / secondary
- The chart already uses redundant encoding (marker shapes, labels)
- The stroke would add visual noise (overlapping scatter, dense lines)

Recommended stroke: 1px solid in the chart's ink color (`palette.neutral(theme)`), applied to line edges, scatter markers, bar/pie fills. Stroke contrast against bg always passes since ink is full-contrast.

### Colorblind Safety

The Imprint palette is selected via max-min ΔE optimisation across normal, deuteranopia, protanopia, and tritanopia simulations. Slot 5 (matte red `#AE3030`) is the deferred semantic-anchor — reached intentionally for bad/loss/error roles, not by ordinal position in every chart. This keeps red as a free semantic resource rather than spending it as a default categorical color. Never override the palette with custom categorical hexes unless you have a documented reason. The sequential ramps carry their order in lightness, so their low and high ends stay apart under all three simulated deficiencies.

---

## Aesthetic Principles

### Minimalism

Every visual element must earn its place. If removing an element doesn't reduce understanding, remove it.

- No chartjunk: decorative borders, unnecessary 3D effects, gradient fills for style
- No embellishments that don't encode data
- Favor clean, simple compositions over busy ones

### Spines

- **Default**: Remove top and right spines. Keep only left and bottom (L-shaped frame)
- **Alternative**: Remove all spines for very clean looks (heatmaps, minimal scatter)
- **Exception**: Keep all four spines only when the plot type requires it (e.g., enclosed heatmap grid)

### Background

anyplot plots live inside page surfaces that are warm off-white / near-black, **never pure white or pure black** (pure values make the saturated palette look harsh).

| Theme | Plot background (`bg-surface`) | Elevated (callout boxes, legend frames) |
|-------|--------------------------------|----------------------------------------|
| Light | `#FAF8F1` | `#FFFDF6` |
| Dark  | `#1A1A17` | `#242420` |

- The background is theme-dependent and must match the surface where the plot will be embedded on the website.
- Implementations read `os.environ["ANYPLOT_THEME"]` (`"light"` or `"dark"`, default `"light"`) and render accordingly. The pipeline runs each implementation twice to produce `plot-light.png` and `plot-dark.png`.
- Never use pure `#FFFFFF`, pure `#000000`, or unrelated colored backgrounds.

### Theme-adaptive Chrome

In addition to the background, every non-data element (title, axis labels, tick labels, spines, grid, legend text, annotations, callout-box fills, footnotes) must use theme-adaptive tokens. Only the 8 categorical Imprint colors stay constant. The `neutral` and `muted` semantic anchors are theme-adaptive by design, and the continuous ramps take the stops of the theme.

| Role | Light theme | Dark theme |
|------|-------------|------------|
| Primary text (title, axis labels) | `#1A1A17` | `#F0EFE8` |
| Secondary text (tick labels, legend, subtitles) | `#4A4A44` | `#B8B7B0` |
| Tertiary text (footnotes, meta annotations) | `#6B6A63` | `#A8A79F` |
| Grid lines, rule dividers, thin borders | `rgba(26,26,23,0.15)` | `rgba(240,239,232,0.15)` |
| Callout / legend box fill | `#FFFDF6` | `#242420` |

**Reference Python snippet** (generators must emit logic equivalent to this — exact syntax is library-specific):

```python
import os
THEME = os.getenv("ANYPLOT_THEME", "light")

# theme-adaptive chrome
PAGE_BG     = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK         = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT    = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED   = "#6B6A63" if THEME == "light" else "#A8A79F"
RULE        = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint categorical palette — 8 hues, theme-independent, hybrid-v3 sort
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233",
                   "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]  # "#009E73" — ALWAYS first series

# semantic anchors — outside the categorical pool
ANYPLOT_AMBER   = "#DDCC77"     # warning / caution
ANYPLOT_NEUTRAL = INK           # totals / baseline / outline (theme-adaptive)
ANYPLOT_MUTED   = INK_MUTED     # other / rest / disabled    (theme-adaptive)

# continuous ramps — (position, hex) stops, low → high, per theme (see "Continuous Data")
if THEME == "light":
    SEQ_FIELDS = [(0.0, "#66E2B2"), (0.368, "#009E73"), (0.582, "#4467A3"), (1.0, "#002850")]
    SEQ_MARKS  = [(0.0, "#009E73"), (0.338, "#4467A3"), (1.0, "#002850")]
else:
    SEQ_FIELDS = [(0.0, "#00573D"), (0.467, "#009E73"), (1.0, "#CDD9FF")]
    SEQ_MARKS  = [(0.0, "#007755"), (0.32, "#009E73"), (1.0, "#CDD9FF")]
DIV_FIELDS = [(0.0, "#AE3030"), (0.5, PAGE_BG), (1.0, "#4467A3")]    # midpoint: the page
DIV_MARKS  = [(0.0, "#AE3030"), (0.5, INK_MUTED), (1.0, "#4467A3")]  # midpoint: the muted anchor
```

Output file names: `plot-light.png` / `plot-dark.png` (static libraries) plus `plot-light.html` / `plot-dark.html` (interactive libraries).

### Whitespace

- Generous margins around the plot area
- Padding between legend and plot, between title and axes
- Let the data breathe — don't cram elements together
- `tight_layout()` or the library's margin settings to avoid wasted canvas, but don't compress. Never `bbox_inches='tight'`: it trims the saved PNG below the fixed canvas size

### Typography Hierarchy

- **Title**: Bold or medium weight, largest size — the first thing readers see
- **Axis labels**: Regular weight, clearly readable
- **Tick labels, legend text**: Regular weight, smaller but still legible
- **Tertiary text** (annotations, source notes): Lighter weight, smallest readable size

### Axis and Legend Titles

Axis titles and legend titles are text for a reader, not identifiers: words separated by spaces and a unit in parentheses — "Reaktionszeit (ms)", never the column name `Reaktionszeit_ms` — in the data's language. A legend whose series came from reshaping wide columns names the level that tells them apart ("Q1", "Q2"), not each full original header ("Umsatz Q1 (CHF)"); what the series share, such as the measure and the unit, belongs in the legend title or the axis title.

### Grid Guidelines

- **Prefer no grid** for simple plots with few data points
- **When used**: Y-axis grid only for bar/line charts, both axes for scatter plots
- **Style**: Solid thin lines (not dashed), opacity 15-25%, very subtle
- **Never**: Bold grid lines, high-contrast grid, grid that competes with data

### Decoration Removal Checklist

Before finalizing any plot, consider removing:
- Top and right spines (remove by default)
- Tick marks (keep tick labels, remove the small marks themselves where possible)
- Unnecessary grid lines (especially for simple plots)
- Single-series legends (if only one series, the legend is redundant)
- Redundant axis labels (if the title already explains the axis)
- Box frames around legends

### Data Element Styling

- **Scatter markers**: White edge (`edgecolors='white'`) for definition, especially with overlapping points
- **Line thickness**: Moderate (2.5-3.5 for primary lines, thinner for secondary)
- **Bar edges**: Subtle white or slightly darker edge for definition
- **Alpha/opacity**: Use density-appropriate alpha — more points need more transparency

---

## Visual Sizing Defaults

**These are starting values — the AI may adjust if the plot context demands it.** The review step then checks proportions (see "Proportional Sizing" below) and the repair loop tunes any element that's off.

### Text Sizes

Three library families with different sizing controls:

| Element | DPI-based (matplotlib, seaborn, plotnine) | Scale-based (plotly, altair, lets-plot) | Native-pixel (bokeh, pygal) |
|---------|--------------------------------------------|------------------------------------------|------------------------------------------|
| Canvas (16:9) | `figsize=(8, 4.5)` `dpi=400` | `width=800 height=450 scale=4` | `width=3200 height=1800` |
| Canvas (1:1) | `figsize=(6, 6)` `dpi=400` | `width=600 height=600 scale=4` | `width=2400 height=2400` |
| Title | 12pt | 16px | bokeh `'50pt'`; pygal `66` |
| Axis labels | 10pt | 12px | bokeh `'42pt'`; pygal `56` |
| Tick labels | 8pt | 10px | bokeh `'34pt'`; pygal `44` |
| Legend | 8pt | 10px | bokeh `'34pt'`; pygal `44` |

The JavaScript libraries (chartjs, d3, echarts, highcharts, muix) are a fourth family: they render through the browser harness at `deviceScaleFactor=2` over a 1600×900 (or 1200×1200) CSS mount, so they size text in **CSS px within that mount space** (title `~22px`, axis titles `~16px`, tick labels `~14px`, legend text `14–16px`) — not the native 3200-px numbers. Their per-library prompts are the source of truth; see e.g. `prompts/library/highcharts.md`.

The two libraries outside Python and JavaScript follow the same pattern. ggplot2 sizes its theme text in pt and saves with `ggsave(..., dpi = 400)`, so it takes the DPI-based column: title 12, axis titles 10, tick labels and legend text 8. Makie draws on a 1600×900 (or 1200×1200) figure saved with `px_per_unit = 2`, so like the JavaScript family it sizes text in the figure's own px: `titlesize = 20`, axis labels 14, tick labels 12. `prompts/library/ggplot2.md` and `prompts/library/makie.md` are the source of truth.

All families produce the same 3200×1800 (or 2400×2400) output, so the source-pixel sizes of text are comparable across libraries.

These sizes are also the review's reference for text legibility (VQ-01), judged in the full-size render: text at or above them is never too small. Each library is measured against its own sizes. They do not all land on the same source-pixel height: JavaScript and Makie tick labels come out near 24 to 28 px, the other families near 40 to 44 px.

**Why the Native-pixel numbers look so much bigger** — and why bokeh's number differs from pygal:

The three families use completely different unit conventions for the same visual size. Target source-pixel height for the title is ~67 (matches matplotlib 12pt @ dpi=400).

- **DPI-based** (matplotlib): `12pt × 400dpi/72 = 67 source-px`. The `pt` value is multiplied by dpi at render time.
- **Scale-based** (plotly): `16px × scale=4 = 64 source-px`. The `px` value is multiplied by scale at render time.
- **bokeh** (`'pt'` strings rendered through headless Chrome as CSS pt): `'50pt' × 1.333 = 67 source-px`. CSS pt is 1.333 source-px in the browser, no extra multiplier.
- **pygal** (unitless integer rendered into SVG): `66 = 66 source-px`. SVG unitless ≈ user-units ≈ pixels in the source-pixel grid.

So **the same target visual size requires a different nominal number per library** because each library's unit constant differs. bokeh '50pt' ≈ pygal 66 ≈ matplotlib 12pt @ dpi=400 ≈ plotly 16px @ scale=4. Don't try to make them all look the same number. (The JS libraries differ again — they render at dpr=2 over a 1600-px mount, so their CSS px are ~half the native number; their own prompts give the values.)

Bokeh also needs `min_border_*` reservations on the `figure(...)` constructor so the larger axis labels have room and aren't clipped from the PNG. See `prompts/library/bokeh.md` for the canonical numbers — keep that file as the single source of truth so the bottom/left/top/right values don't drift between here and the library prompt.

### Marker and Line Sizes

**Marker and line sizes** vary by library API and aren't directly comparable as a single number — matplotlib's `s=` is in points², plotly's `marker.size` is a pixel diameter, altair's `mark_point(size=...)` is an area, plotnine / lets-plot / ggplot2's `geom_point(size=...)` uses a smaller ggplot scale. See each library's own prompt (`prompts/library/<lib>.md` → "Sizing" section) for the canonical starting values, and adapt to data density per the heuristic below.

### Data-density Heuristic

Marker and line sizes should adapt to how dense the data is — no fixed values:

- **Few datapoints (< 50)** → larger, prominent markers; thicker lines.
- **Medium density (50–500)** → defaults from the table above.
- **High density (> 500)** → smaller markers + `alpha < 1` to combat overplotting; consider hex-bin / 2D-histogram alternatives.
- **Few series (1–3)** → thicker lines for prominence.
- **Many series (> 5)** → thinner lines so all stay visible.

### Per-mark Labels and Decorations

Some elements are drawn once per bar or point: value labels, dots on bar ends, shadows, a text next to each point. Unlike a title, a legend or a single callout, their count grows with the data, so a choice that suits 8 bars can bury 50. Keep them only while each label fits the space of its mark (a bar label no wider than its bar's slot) and the plot stays legible, which rarely holds past about 25 marks. With more marks, drop them, or label only the extremes (the largest and the smallest value) when the plot needs numbers. Text that is the encoding itself (heatmap cell values, a word cloud, a table) follows its spec instead.

A label that tells the reader nothing is clutter at any mark count: a value that is the same by construction on every mark (each bar of a 100 % stacked chart labelled "100 %") or a text that repeats exactly what an axis already states. Leave it out.

### General Rules
- Marks and lines should be **~2-3× larger** than the library's standard defaults. Text follows "Text Sizes" above, not this rule.
- When in doubt about a mark or a line, make it bigger.
- Test: Is this comfortably readable in the full-size render, on a typical 1920–2560 px desktop monitor? A thumbnail about 400 px wide only has to keep the plot recognisable; its small text is not meant to be read there.

---

## Proportional Sizing

The review step checks these proportions visually from the source PNG. There are no hard pixel thresholds — violations cost points in the existing VQ-01 (Text Legibility), VQ-02 (No Overlap), VQ-03 (Element Visibility), VQ-05 (Layout & Canvas) categories rather than triggering a separate pass/fail. This keeps the contract holistic: a single visual problem (oversized short axis label, overlapping ticks) can reduce points in multiple categories.

- **Title proportion:** Title comfortably takes ~50–70% of the plot width. The mandated `{spec-id} · {lang} · {lib} · anyplot.ai` title is ~67 chars long and naturally fills 70–85% at the style-guide default fontsize — this is **expected**, not a violation. Only flag if title overflows past ~90% of width OR fontsize is too generous for the content. **When the optional `{Descriptive Title} · ` prefix is used, or when `{spec-id}` is long (e.g. `network-bipartite-weighted`), the total title runs past ~67 chars and the default fontsize will overflow** — the generator must shrink the title fontsize via the linear formula `fontsize = round(default × 67 / len(title))` (capped at the library-specific floor). See `prompts/plot-generator.md` "Title fontsize must scale with title length" for the per-library defaults and floors.
- **Axis label proportionality:** Short labels ("Date", "Year") should not dominate the axis with oversized fontsizes. Long descriptive labels ("Fläche von Häusern in Quadratmetern") are fine as long as they don't overflow — the "no overflow" rule covers that case.
- **Axis label balance:** X-axis label and Y-axis label are visually similar in size — one much larger than the other without semantic reason is a violation.
- **Tick label balance:** X-axis and Y-axis tick labels are visually similar in size (exception: rotated long categorical labels).
- **No overlap:** Text never overlaps with other text or with data elements.
- **No overflow:** No text extends beyond axis bounds, plot bounds, or frame.
- **Marker / line density appropriateness:** Element sizes match the data-density heuristic above (sparse → prominent; dense → smaller + alpha).
- **Per-mark label density:** Value labels, dots on bar ends and shadows follow "Per-mark Labels and Decorations" above; labels that crowd their marks cost VQ-03, labels that overlap cost VQ-02.

---

## AI Discretion

The AI makes the following design decisions for each visualization:

**Color & Palette:**
- Use Imprint palette positions 1→N in order for categorical data (see Color Philosophy). No custom hexes. May reassign positions when categories carry strong semantic color cues (grass→green, wood→ochre, blood→red, sky→blue, water→blue) — see Semantic Exception in Color Philosophy. Use the 3 semantic anchors (amber, neutral, muted) only when their role is the right fit, not as overflow slots.
- Colormap choice for continuous data: **`imprint_seq`** (single-polarity) or **`imprint_div`** (diverging-polarity), each with the theme's stops for fields or for marks. No other colormaps — see Continuous Data.
- Alpha/opacity values based on data density

**Layout & Structure:**
- Landscape vs. square format
- Legend placement (or omission for single-series)
- Spine visibility (L-shaped, none, or all)
- Margin and padding adjustments

**Typography:**
- Font family
- Weight variations within the hierarchy
- Exact font sizes (within the guidelines)

**Grid & Background:**
- Grid on/off, and which axes
- Grid opacity (within 10-15% range — subtle, never competes with data)
- Plot background follows the theme (`#FAF8F1` light / `#1A1A17` dark) — not chosen freely

**Data Presentation:**
- Emphasis techniques (bold color, size variation, focal points)
- Data label placement
- Annotations and callouts (only when specification explicitly requests them)

**Priority:** Clarity, beauty, and readability at full resolution (~5.76 million pixels). Scaled down to a thumbnail (~400 px), the plot stays recognisable.
