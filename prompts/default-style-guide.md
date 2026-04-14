# AnyPlot.ai Default Style Guide

Style requirements for consistent, beautiful visualizations at large canvas sizes.

## Important: Large Canvas Size

anyplot renders at high resolution (~13 million pixels). All element sizes must be scaled for visibility!

**Common Mistake:** Using default/standard sizes results in tiny, hard-to-see elements.

---

## Dimensions

Two formats are allowed (similar pixel count for consistent font sizing):

| Format | Size | Aspect Ratio | Use Case |
|--------|------|--------------|----------|
| **Landscape** | 4800 × 2700 px | 16:9 | Default, most plots |
| **Square** | 3600 × 3600 px | 1:1 | Symmetric plots (pie, radar, heatmaps, grid-based) |

**AI decides freely** which format is best for each specific plot.

**Why these sizes?**
- Landscape: 4800 × 2700 = 12.96 million pixels
- Square: 3600 × 3600 = 12.96 million pixels
- Same pixel area → same font sizes work for both

---

## Color Philosophy

### Primary Color

**Python Blue `#306998`** is the only recommended color for single-series plots. It is the brand anchor for every anyplot visualization.

### Multi-Series Palettes

For plots with multiple series, the AI chooses a cohesive, colorblind-safe palette **starting with Python Blue**:
- The first series is always Python Blue `#306998`
- Additional colors are chosen by the AI to complement Python Blue while maintaining colorblind safety
- No hardcoded second, third, or fourth color — the AI picks what works best for the specific data and context

### Color Restraint

- **2-3 colors** is ideal for most plots
- **4-5 colors** is the practical maximum for categorical data
- **6+ colors** is rare and should only be used when the data demands it (e.g., many categories)
- When many categories exist, consider grouping or using a sequential colormap instead

### Sequential & Diverging Data

For continuous data, use perceptually-uniform colormaps:
- **Sequential**: `viridis`, `plasma`, `inferno`, `cividis`, `Blues`, `Greens`
- **Diverging**: `RdBu`, `PiYG`, `coolwarm` (centered on meaningful midpoint)
- Avoid rainbow colormaps (`jet`, `hsv`) — they are not perceptually uniform

### Colorblind Safety

All color choices must be distinguishable by people with deuteranopia and protanopia:
- Avoid red-green as the only distinguishing feature
- Use luminance differences (light vs dark), not just hue
- When in doubt, test with a colorblind simulator

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

- Clean white (`#FFFFFF`) is the default
- Very faint warm gray (`#FAFAFA`) is acceptable as an alternative
- Never use colored or dark backgrounds

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

## Visual Sizing Principles

Since we render at ~13 million pixels, elements must be **visually prominent**:

### Text

Two font size groups exist due to how libraries render (DPI-based vs. pixel-based):

| Element | DPI-based (matplotlib, seaborn, plotnine, letsplot) | Pixel-based (plotly, bokeh, altair, highcharts, pygal) |
|---------|------------------------------------------------------|--------------------------------------------------------|
| Title | 24pt | 28px |
| Axis labels | 20pt | 22px |
| Tick labels | 16pt | 18px |
| Legend | 16pt | 16px |

DPI-based libraries use `figsize=(16, 9)` + `dpi=300` = 4800x2700px. Pixel-based libraries set dimensions directly.

### Data Elements
- **Points/Markers**: Clearly visible, not tiny dots
- **Lines**: Thick enough to see clearly
- **Bars**: With subtle edges for definition

### General Rules
- Elements should be **~3-4x larger** than standard defaults
- When in doubt, make it bigger
- Test: Would this be readable on a 4K monitor?

---

## AI Discretion

The AI makes the following design decisions for each visualization:

**Color & Palette:**
- Specific colors beyond Python Blue (for multi-series)
- Colormap choice for sequential/diverging data
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
- Grid opacity (within 15-25% range)
- Background shade (white or faint gray)

**Data Presentation:**
- Emphasis techniques (bold color, size variation, focal points)
- Data label placement
- Annotations and callouts (only when specification explicitly requests them)

**Priority:** Clarity, beauty, and readability at full resolution (~13 million pixels).
