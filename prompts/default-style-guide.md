# AnyPlot.ai Default Style Guide

Style requirements for consistent, beautiful visualizations at a mid-sized canvas.

## Standard Canvas Size

anyplot renders at ~5.76 million pixels — a mid-sized canvas that balances Hi-Res sharpness for desktop monitors with mobile readability and reasonable file sizes.

**Common Mistake:** Using library defaults (e.g. matplotlib `fontsize=10`, plotly `marker.size=6`) still produces elements that are too small. Use the "Visual Sizing Defaults" table below as a starting point — the AI may adjust if the plot context demands it, and the review step checks proportions.

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

anyplot uses the **Imprint palette** — a bespoke, colorblind-safe categorical palette tuned for paper-ink rendering on both warm-cream and warm-black surfaces. It is the single consistency rule that spans every library and every plot. Always refer to it as **Imprint** (capitalised, no other names) in code comments, metadata, and review notes. Full design rationale: [`docs/reference/palette-variants-v3/decision-rationale.md`](../docs/reference/palette-variants-v3/decision-rationale.md).

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
- **First series is ALWAYS `#009E73`** — across every library, every plot type. A "Gentoo penguin" is the same green in matplotlib as it is in plotly.
- Use positions 1→N in order by default. Don't cherry-pick for aesthetic reasons.
- All 8 categorical positions stay identical across light and dark themes so a category keeps its identity.
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

Categorical palettes on continuous data produce misleading banding. anyplot ships exactly two Imprint-derived continuous colormaps; **no other cmap is allowed** — not viridis, not cividis, not BrBG, not Blues/Greens/Reds, and never jet/hsv/rainbow. Both Imprint cmaps are perceptually-uniform in CAM02-UCS:

- **`imprint_seq` (sequential):** brand green → blue. Use for single-polarity continuous data (intensity, magnitude, density, single-polarity heatmaps). Build with `LinearSegmentedColormap.from_list("imprint_seq", ["#009E73", "#4467A3"])` (matplotlib) or the library's equivalent two-stop gradient API.
- **`imprint_div` (diverging):** matte-red ↔ near-neutral ↔ blue. Use when the data has a meaningful midpoint (correlations, residuals, signed deviations, diverging heatmaps). The midpoint is theme-adaptive — use `#FAF8F1` on light bg, `#1A1A17` on dark bg. Build with `LinearSegmentedColormap.from_list("imprint_div", ["#AE3030", midpoint, "#4467A3"])`.

Pick `imprint_seq` vs `imprint_div` from the data's polarity. Never substitute a matplotlib/library-native cmap "because it looks nicer" — Imprint identity is part of the brand.

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

### Optional outline pattern (AI judgment)

5 of the 8 categorical hues + amber fall below WCAG 2.1 SC 1.4.11's 3:1 contrast on the cream bg (lavender, ochre, cyan, lime, and amber). On dark bg, only matte-red is marginally below. This is the known muted-palette / WCAG tension Okabe-Ito, Paul Tol "muted", and ColorBrewer Set2 all share.

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

The Imprint palette is selected via max-min ΔE optimisation across normal, deuteranopia, protanopia, and tritanopia simulations. Slot 5 (matte red `#AE3030`) is the deferred semantic-anchor — reached intentionally for bad/loss/error roles, not by ordinal position in every chart. This keeps red as a free semantic resource rather than spending it as a default categorical color. Never override the palette with custom categorical hexes unless you have a documented reason.

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

In addition to the background, every non-data element (title, axis labels, tick labels, spines, grid, legend text, annotations, callout-box fills, footnotes) must use theme-adaptive tokens. Only the Imprint palette data colors (positions 1–8) stay constant. The `neutral` and `muted` semantic anchors are theme-adaptive by design.

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
```

Output file names: `plot-light.png` / `plot-dark.png` (static libraries) plus `plot-light.html` / `plot-dark.html` (interactive libraries).

### Whitespace

- Generous margins around the plot area
- Padding between legend and plot, between title and axes
- Let the data breathe — don't cram elements together
- `tight_layout()` / `bbox_inches='tight'` to avoid wasted canvas, but don't compress

### Typography Hierarchy

- **Title**: Bold or medium weight, largest size — the first thing readers see
- **Axis labels**: Regular weight, clearly readable
- **Tick labels, legend text**: Regular weight, smaller but still legible
- **Tertiary text** (annotations, source notes): Lighter weight, smallest readable size

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

Three library families with different sizing controls:

| Element | DPI-based (matplotlib, seaborn, plotnine) | Scale-based (plotly, altair, lets-plot) | Native-pixel (bokeh, highcharts, pygal) |
|---------|--------------------------------------------|------------------------------------------|------------------------------------------|
| Canvas (16:9) | `figsize=(8, 4.5)` `dpi=400` | `width=800 height=450 scale=4` | `width=3200 height=1800` |
| Canvas (1:1) | `figsize=(6, 6)` `dpi=400` | `width=600 height=600 scale=4` | `width=2400 height=2400` |
| Title | 12pt | 16px | bokeh `'50pt'`; highcharts `'66px'`; pygal `66` |
| Axis labels | 10pt | 12px | bokeh `'42pt'`; highcharts `'56px'`; pygal `56` |
| Tick labels | 8pt | 10px | bokeh `'34pt'`; highcharts `'44px'`; pygal `44` |
| Legend | 8pt | 10px | bokeh `'34pt'`; highcharts `'44px'`; pygal `44` |

All three families produce the same 3200×1800 (or 2400×2400) output, so the source-pixel sizes of text are now comparable across libraries.

**Why the Native-pixel numbers look so much bigger** — and why bokeh's number differs from highcharts/pygal:

The three families use completely different unit conventions for the same visual size. Target source-pixel height for the title is ~67 (matches matplotlib 12pt @ dpi=400).

- **DPI-based** (matplotlib): `12pt × 400dpi/72 = 67 source-px`. The `pt` value is multiplied by dpi at render time.
- **Scale-based** (plotly): `16px × scale=4 = 64 source-px`. The `px` value is multiplied by scale at render time.
- **bokeh** (`'pt'` strings rendered through headless Chrome as CSS pt): `'50pt' × 1.333 = 67 source-px`. CSS pt is 1.333 source-px in the browser, no extra multiplier.
- **highcharts** (`'px'` CSS strings rendered through headless Chrome): `'66px' = 66 source-px`. CSS px maps 1:1 to source pixels at devicePixelRatio=1.
- **pygal** (unitless integer rendered into SVG): `66 = 66 source-px`. SVG unitless ≈ user-units ≈ pixels in the source-pixel grid.

So **the same target visual size requires a different nominal number per library** because each library's unit constant differs. bokeh '50pt' ≈ highcharts '66px' ≈ pygal 66 ≈ matplotlib 12pt @ dpi=400 ≈ plotly 16px @ scale=4. Don't try to make them all look the same number.

Bokeh also needs `min_border_*` reservations on the `figure(...)` constructor so the larger axis labels have room and aren't clipped from the PNG. See `prompts/library/bokeh.md` for the canonical numbers — keep that file as the single source of truth so the bottom/left/top/right values don't drift between here and the library prompt.

**Marker and line sizes** vary by library API and aren't directly comparable as a single number — matplotlib's `s=` is in points², plotly's `marker.size` is a pixel diameter, altair's `mark_point(size=...)` is an area, plotnine / lets-plot / ggplot2's `geom_point(size=...)` uses a smaller ggplot scale. See each library's own prompt (`prompts/library/<lib>.md` → "Sizing" section) for the canonical starting values, and adapt to data density per the heuristic below.

### Data-density Heuristic

Marker and line sizes should adapt to how dense the data is — no fixed values:

- **Few datapoints (< 50)** → larger, prominent markers; thicker lines.
- **Medium density (50–500)** → defaults from the table above.
- **High density (> 500)** → smaller markers + `alpha < 1` to combat overplotting; consider hex-bin / 2D-histogram alternatives.
- **Few series (1–3)** → thicker lines for prominence.
- **Many series (> 5)** → thinner lines so all stay visible.

### General Rules
- Elements should be **~2-3× larger** than the library's standard defaults.
- When in doubt, make it bigger.
- Test: Would this be readable on a typical 1920–2560 px desktop monitor, AND on a 400 px mobile width?

---

## Proportional Sizing

The review step checks these proportions visually from the source PNG. There are no hard pixel thresholds — violations cost points in the existing VQ-01 (Text Legibility), VQ-02 (No Overlap), VQ-05 (Layout & Canvas) categories rather than triggering a separate pass/fail. This keeps the contract holistic: a single visual problem (oversized short axis label, overlapping ticks) can reduce points in multiple categories.

- **Title proportion:** Title comfortably takes ~50–70% of the plot width. The mandated `{spec-id} · {lang} · {lib} · anyplot.ai` title is ~67 chars long and naturally fills 70–85% at the style-guide default fontsize — this is **expected**, not a violation. Only flag if title overflows past ~90% of width OR fontsize is too generous for the content. **When the optional `{Descriptive Title} · ` prefix is used, or when `{spec-id}` is long (e.g. `network-bipartite-weighted`), the total title runs past ~67 chars and the default fontsize will overflow** — the generator must shrink the title fontsize via the linear formula `fontsize = round(default × 67 / len(title))` (capped at the library-specific floor). See `prompts/plot-generator.md` "Title fontsize must scale with title length" for the per-library defaults and floors.
- **Axis label proportionality:** Short labels ("Date", "Year") should not dominate the axis with oversized fontsizes. Long descriptive labels ("Fläche von Häusern in Quadratmetern") are fine as long as they don't overflow — the "no overflow" rule covers that case.
- **Axis label balance:** X-axis label and Y-axis label are visually similar in size — one much larger than the other without semantic reason is a violation.
- **Tick label balance:** X-axis and Y-axis tick labels are visually similar in size (exception: rotated long categorical labels).
- **No overlap:** Text never overlaps with other text or with data elements.
- **No overflow:** No text extends beyond axis bounds, plot bounds, or frame.
- **Marker / line density appropriateness:** Element sizes match the data-density heuristic above (sparse → prominent; dense → smaller + alpha).

---

## AI Discretion

The AI makes the following design decisions for each visualization:

**Color & Palette:**
- Use Imprint palette positions 1→N in order for categorical data (see Color Philosophy). No custom hexes. May reassign positions when categories carry strong semantic color cues (grass→green, wood→ochre, blood→red, sky→blue, water→blue) — see Semantic Exception in Color Philosophy. Use the 3 semantic anchors (amber, neutral, muted) only when their role is the right fit, not as overflow slots.
- Colormap choice for continuous data: **`imprint_seq`** (single-polarity) or **`imprint_div`** (diverging-polarity). No other colormaps — see Continuous Data.
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

**Priority:** Clarity, beauty, and readability at full resolution (~5.76 million pixels) AND when scaled down to mobile width (~400 px).
