# lets-plot

ggplot2-style grammar of graphics by JetBrains.

**API level:** lets-plot 4. `uv.lock` pins this major; write against its API.

## Import

```python
from lets_plot import *
LetsPlot.setup_html()  # Required for notebook/export
```

## Create Plot

```python
plot = (
    ggplot(df, aes(x=STUDY_HOURS, y=EXAM_SCORE))
    + geom_point()
    + labs(title=title)
)
```

## Data block

The file follows the six zones of `prompts/adaptable-code.md`. lets-plot reads the tidy `df` directly with the column constants: `ggplot(df, aes(x=QUARTER, y=SALES, fill=PRODUCT_LINE))`. Column names with spaces, units and dots work as they are. lets-plot titles the axes and the legend from the column names, so `labs()` is needed only for the title or to change a label, and it keeps the data's order of a string column on the axis and in the color mapping. `LetsPlot.setup_html()` belongs in the head, above the column constants, never in the block.

```python
# Plot: reads only df and the constants above
plot = (
    ggplot(df, aes(x=QUARTER, y=SALES, fill=PRODUCT_LINE))
    + geom_bar(stat="identity", position=position_dodge(width=0.8), width=0.75)
    + scale_fill_manual(values=IMPRINT_PALETTE)
)
```

Continuous limits come from the data (`scale_y_continuous(limits=[0, df[SALES].max() * 1.15])`) or stay automatic, never typed numbers. The `0` there is the baseline of a bar or area chart, where the length of the mark is the value; a line or point axis takes both limits from the data, a little outside its smallest and largest value, or stays automatic.

## Canvas — hard rule, no deviation

The saved PNG must be **exactly** one of these two sizes (post-render gate in `impl-review.yml` rejects anything off by more than 16 px and re-triggers repair):

| Orientation | `ggsize` | `ggsave` `scale` | Final PNG     |
|-------------|----------|------------------|---------------|
| Landscape   | `(800, 450)` | `scale=4` | 3200 × 1800   |
| Square      | `(600, 600)` | `scale=4` | 2400 × 2400   |

Don't deviate from these pairs (e.g. `ggsize(900, 500)` lands at 3600×2000, well outside the ±16 px gate). Pick the orientation that suits the spec.

**Paint the whole canvas.** lets-plot paints `plot_background` only behind the plot box it draws, so two kinds of figure leave strips at the canvas edges:

- **A fixed aspect** (`coord_fixed`, `coord_polar`, `coord_map`) narrows the plot box to that aspect and leaves the rest of the canvas **transparent**: strips at the left and right (polar: also top and bottom), 15 to 230 px wide on the square canvas and over 700 px on the landscape one. Wrap the finished plot in a one-panel `gggrid` of the canvas size that carries the page color.
- **A composite** (`gggrid`, `ggbunch`) fills the space around its panels with opaque **white**, about 24 px at each edge in both themes. Give the composite itself the page color.

**Then let a fixed-aspect panel fill the canvas.** The wrap paints the strips but leaves them empty: a panel that keeps its aspect is only as large as the narrower side of the space left for it allows, and the rest of the canvas becomes blank bands. Three choices decide how large it gets:

- **The legend goes below the panel** (`theme(legend_position='bottom')`), or inside it where the figure leaves an empty corner. A legend beside the panel takes width that the panel needs, and the panel then shrinks on both axes and leaves bands above and below it. The title already sits above, so a legend below costs the panel least.
- **The canvas suits the figure with its title and legend below it**, not only its equal axes. A figure about as tall as wide (a chord, radar or polar chart, a tile grid, a map of a region about as tall as wide) fills the square canvas once its legend is below. A figure that stays clearly wider than tall with all of that (a world map, a hemicycle) suits Step 0's landscape pair.
- **A map fills the panel through its span.** Widen the shorter of the two coordinate ranges in `coord_fixed(xlim=..., ylim=...)` or `coord_map(xlim=..., ylim=...)` until the panel's shape matches the space the canvas leaves for it: the map shows more of its surroundings instead of empty bands. Both ranges come from the data, as above: the widened one is the data's range with a margin, never a typed number.

Step 4's canvas question checks the result: blank bands on two opposite sides of a fixed-aspect figure mean that one of these three choices is still open.

```python
# Fixed aspect: the legend below the panel, then the one-panel grid paints the canvas and the plot keeps its aspect.
# ggsize is the canvas Step 0 picks, never a third size:
plot = plot + theme(legend_position='bottom')
plot = gggrid([plot]) + ggsize(600, 600) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))  # square
plot = gggrid([plot]) + ggsize(800, 450) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))  # landscape

# Composite: the page color on the composite, besides each panel's own anyplot_theme;
# a ggtitle on the composite stays dark grey without its own plot_title color
plot = gggrid([p1, p2], ncol=2) + ggsize(800, 450) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG), plot_title=element_text(color=INK))
```

`ggbunch([...], [...]) + ggsize(800, 450)` takes the same `theme(...)`.

## Figure Size & Sizing for 3200×1800 px (starting values — review-loop tunes)

```python
# Base size (scaled 4x on export = 3200 × 1800 px) — see "Canvas" above
plot = plot + ggsize(800, 450)

# Text and element sizes
plot = plot + theme(
    axis_title=element_text(size=12),
    axis_text=element_text(size=10),
    plot_title=element_text(size=16),  # kept compact for the long mandated title
    legend_text=element_text(size=10)
)

# Element sizes in geoms (density-aware — see default-style-guide.md)
+ geom_point(size=2.5)   # ~2-3x default
+ geom_line(size=1.0)    # line width
```

> `geom_text(size=N)` is in mm (× 2.845 ≈ pt), unlike `element_text(size=N)` which is pt. Annotation `size` should be ~3–5, never the same numeric scale as the theme.

See `prompts/default-style-guide.md` "Proportional Sizing" for review criteria.

## Save (PNG + HTML)

```python
import os
from lets_plot import ggsave

THEME = os.getenv("ANYPLOT_THEME", "light")

# PNG: scale 4x to get 3200 × 1800 px
ggsave(plot, f'plot-{THEME}.png', scale=4)

# HTML (interactive)
ggsave(plot, f'plot-{THEME}.html')
```

## Aesthetics

```python
# Mappings: the column constants, never typed column names
aes(x=STUDY_HOURS, y=EXAM_SCORE, color=SCHOOL, size=CLASS_SIZE)

# Fixed aesthetics (outside aes)
geom_point(color=IMPRINT_PALETTE[0], size=5, alpha=0.7)
```

## Geoms

```python
geom_point()       # Scatter
geom_line()        # Line
geom_bar()         # Bar (stat='identity' for values)
geom_histogram()   # Histogram
geom_boxplot()     # Boxplot
geom_violin()      # Violin
geom_tile()        # Heatmap
geom_smooth()      # Trend line
geom_area()        # Area
geom_density()     # Density
```

## Scales

```python
# Categorical — use Imprint palette (see Colors section below)
+ scale_color_manual(values=IMPRINT_PALETTE)
+ scale_fill_manual(values=IMPRINT_PALETTE)

# Continuous — only the two Imprint ramps are allowed, as (position, hex) stops, low → high,
# with their own stops per theme (style guide, "Continuous Data"). FIELDS: colored cells that
# fill the plot (geom_tile, geom_raster, filled contours, map polygons). MARKS: colored points,
# lines, outlines or bars on the page. Keep only the ramps the plot uses.
import math
from itertools import pairwise
SEQ_FIELDS = (
    [(0.0, '#66E2B2'), (0.368, '#009E73'), (0.582, '#4467A3'), (1.0, '#002850')]
    if THEME == 'light'
    else [(0.0, '#00573D'), (0.467, '#009E73'), (1.0, '#CDD9FF')]
)
SEQ_MARKS = (
    [(0.0, '#009E73'), (0.338, '#4467A3'), (1.0, '#002850')]
    if THEME == 'light'
    else [(0.0, '#007755'), (0.32, '#009E73'), (1.0, '#CDD9FF')]
)

def ramp_color(stops, t):
    """The hex at t (0 to 1) along (position, hex) stops, blended linearly in sRGB."""
    if not math.isfinite(t):
        return 'none'  # a missing value draws nothing, never the low end
    t = min(max(t, 0.0), 1.0)
    (p0, c0), (p1, c1) = next((a, b) for a, b in pairwise(stops) if t <= b[0])
    share = (t - p0) / (p1 - p0)
    return '#' + ''.join(
        f'{round(int(c0[i:i + 2], 16) * (1 - share) + int(c1[i:i + 2], 16) * share):02X}' for i in (1, 3, 5)
    )

# Sequential: lets-plot's gradientn takes evenly spaced colors only (no stop positions),
# so sample the stops at 256 even steps
+ scale_fill_gradientn(colors=[ramp_color(SEQ_FIELDS, k / 255) for k in range(256)])
+ scale_color_gradientn(colors=[ramp_color(SEQ_MARKS, k / 255) for k in range(256)])
# Diverging: mid is the page for fields and a grey that keeps 3:1 for marks
DIV_MID_FIELDS = '#FAF8F1' if THEME == 'light' else '#1A1A17'
DIV_MID_MARKS = '#6B6A63' if THEME == 'light' else '#686762'
+ scale_fill_gradient2(low='#AE3030', mid=DIV_MID_FIELDS, high='#4467A3', midpoint=0)
+ scale_color_gradient2(low='#AE3030', mid=DIV_MID_MARKS, high='#4467A3', midpoint=0)
# Forbidden: scale_color_viridis / scale_fill_viridis or any non-anyplot stops.

# Axis scales
+ scale_x_continuous()
+ scale_y_log10()
```

## Themes

```python
+ theme_minimal()
+ theme_classic()
+ theme_bw()
+ theme_void()

# Custom theme
+ theme(
    axis_text=element_text(size=12),
    legend_position='right'
)
```

## Facets

```python
+ facet_wrap(REGION, ncol=3)
+ facet_grid(x=REGION, y=CHANNEL)
```

## Colors

Use the Imprint palette (see `prompts/default-style-guide.md` "Categorical Palette"). First series is **always** `#009E73`.

```python
IMPRINT_PALETTE = ['#009E73', '#C475FD', '#4467A3', '#BD8233',
                   '#AE3030', '#2ABCCD', '#954477', '#99B314']
ANYPLOT_AMBER = '#DDCC77'  # warning / caution (outside the categorical pool)

# Single-series
+ geom_point(color=IMPRINT_PALETTE[0])

# Multi-series
+ scale_color_manual(values=IMPRINT_PALETTE)
+ scale_fill_manual(values=IMPRINT_PALETTE)
```

## Theme-adaptive Chrome (lets-plot mapping)

```python
import os
from lets_plot import theme, element_rect, element_text, element_line, element_blank

THEME       = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG     = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK         = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT    = "#4A4A44" if THEME == "light" else "#B8B7B0"
# element_line has no alpha argument; lets-plot reads the alpha from an rgba() color
GRID        = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"   # INK at 15 %, the style guide's grid tone
GRID_MINOR  = "rgba(26,26,23,0.05)" if THEME == "light" else "rgba(240,239,232,0.05)"   # INK at 5 %, as plotnine's minor grid

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=GRID, size=0.3),
    panel_grid_minor=element_line(color=GRID_MINOR, size=0.2),
    axis_title=element_text(color=INK),
    axis_text=element_text(color=INK_SOFT),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT),
    legend_title=element_text(color=INK),
    strip_text=element_text(color=INK),  # facet labels; dark grey on the dark page without it
)

plot = (ggplot(df, aes(x=STUDY_HOURS, y=EXAM_SCORE)) + geom_point(color=IMPRINT_PALETTE[0]) + anyplot_theme)
```

## Output Files

- Implementation: `plots/{spec-id}/implementations/letsplot.py` — executed twice with different `ANYPLOT_THEME`.
- Generated artifacts: `plot-light.png` + `plot-dark.png` + `plot-light.html` + `plot-dark.html`.

## Key Differences from plotnine

- Uses `lets_plot` module (not `plotnine`)
- `ggsize()` instead of `theme(figure_size=...)`
- `ggsave()` with `scale` parameter for PNG export
- More interactive features built-in
