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

anyplot uses the **Okabe-Ito palette** — a peer-reviewed, colorblind-safe categorical palette designed for scientific publication. It is the single consistency rule that spans every library and every plot.

### Categorical Palette (Okabe-Ito, canonical order)

| # | Hex | Name | Role |
|---|-----|------|------|
| 1 | `#009E73` | bluish green | ★ **brand — ALWAYS first series** |
| 2 | `#D55E00` | vermillion | |
| 3 | `#0072B2` | blue | |
| 4 | `#CC79A7` | reddish purple | |
| 5 | `#E69F00` | orange | |
| 6 | `#56B4E9` | sky blue | |
| 7 | `#F0E442` | yellow | Position ≥7 only — never thin lines or small markers (low luminance on light surfaces) |
| 8 | *adaptive neutral* | — | `#1A1A1A` on light theme, `#E8E8E0` on dark theme. Reserved for aggregates, residuals, reference lines. |

**Hard rules:**
- **First series is ALWAYS `#009E73`** — across every library, every plot type. A "Gentoo penguin" is the same green in matplotlib as it is in plotly.
- Use positions 1→N in order. Don't cherry-pick.
- Only position 8 changes between light and dark themes; positions 1–7 stay identical so a category keeps its identity.
- Never introduce custom hex values when the Okabe-Ito palette already covers the need.

### Continuous Data — Okabe-Ito is NOT used

Categorical palettes on continuous data produce misleading banding. For continuous data, use perceptually-uniform colormaps:

- **Sequential:** `viridis` or `cividis` (default). `Blues` / `Greens` for single-polarity data that should visually tie to the brand.
- **Diverging:** `BrBG` from ColorBrewer (centered on a meaningful midpoint).
- **Heatmaps:** `viridis` for neutral, or single-polarity `Reds` / `Blues` when polarity is semantic.
- **Forbidden:** `jet`, `hsv`, rainbow colormaps — not perceptually uniform.

### Color Restraint

- **2-3 colors** is ideal for most categorical plots.
- **4-5 colors** is the practical maximum.
- **6+ colors** is rare — prefer grouping or a sequential colormap instead.

### Colorblind Safety

The Okabe-Ito palette is already safe for deuteranopia and protanopia. Never override it with custom categorical hexes unless you have a documented reason.

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

In addition to the background, every non-data element (title, axis labels, tick labels, spines, grid, legend text, annotations, callout-box fills, footnotes) must use theme-adaptive tokens. Only the Okabe-Ito data colors (positions 1–7) stay constant.

| Role | Light theme | Dark theme |
|------|-------------|------------|
| Primary text (title, axis labels) | `#1A1A17` | `#F0EFE8` |
| Secondary text (tick labels, legend, subtitles) | `#4A4A44` | `#B8B7B0` |
| Tertiary text (footnotes, meta annotations) | `#6B6A63` | `#A8A79F` |
| Grid lines, rule dividers, thin borders | `rgba(26,26,23,0.10)` | `rgba(240,239,232,0.10)` |
| Callout / legend box fill | `#FFFDF6` | `#242420` |

**Reference Python snippet** (generators must emit logic equivalent to this — exact syntax is library-specific):

```python
import os
THEME = os.getenv("ANYPLOT_THEME", "light")

PAGE_BG     = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK         = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT    = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED   = "#6B6A63" if THEME == "light" else "#A8A79F"
RULE        = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

BRAND       = "#009E73"  # Okabe-Ito position 1, theme-independent
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
| Title | 14pt | 18px | '18pt' |
| Axis labels | 12pt | 14px | '14pt' |
| Tick labels | 10pt | 12px | '12pt' |
| Legend | 10pt | 12px | '12pt' |

All three families produce the same 3200×1800 (or 2400×2400) output, so text pixel sizes are comparable across libraries.

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

- **Title proportion:** Title takes ~50–70% of the plot width. Too narrow → fontsize probably too small. Too wide / overflowing → fontsize probably too big or title too verbose.
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
- Use Okabe-Ito positions 1→N in order for categorical data (see Color Philosophy). No custom hexes.
- Colormap choice for continuous data: `viridis`/`cividis` sequential, `BrBG` diverging, `viridis` or single-polarity `Reds`/`Blues` for heatmaps
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

**Priority:** Clarity, beauty, and readability at full resolution (~13 million pixels).
