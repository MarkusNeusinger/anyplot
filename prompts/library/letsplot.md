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

Continuous limits come from the data (`scale_y_continuous(limits=[0, df[SALES].max() * 1.15])`) or stay automatic, never typed numbers.

## Canvas — hard rule, no deviation

The saved PNG must be **exactly** one of these two sizes (post-render gate in `impl-review.yml` rejects anything off by more than 16 px and re-triggers repair):

| Orientation | `ggsize` | `ggsave` `scale` | Final PNG     |
|-------------|----------|------------------|---------------|
| Landscape   | `(800, 450)` | `scale=4` | 3200 × 1800   |
| Square      | `(600, 600)` | `scale=4` | 2400 × 2400   |

Don't deviate from these pairs (e.g. `ggsize(900, 500)` lands at 3600×2000, well outside the ±16 px gate). Pick the orientation that suits the spec.

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

# Continuous — only the two Imprint palette-derived cmaps are allowed:
+ scale_color_gradient(low='#009E73', high='#4467A3')                              # sequential
+ scale_fill_gradient(low='#009E73',  high='#4467A3')
+ scale_color_gradient2(low='#AE3030', mid='#FAF8F1', high='#4467A3', midpoint=0)  # diverging
+ scale_fill_gradient2(low='#AE3030',  mid='#FAF8F1', high='#4467A3', midpoint=0)
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

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3),
    panel_grid_minor=element_line(color=INK, size=0.2),
    axis_title=element_text(color=INK),
    axis_text=element_text(color=INK_SOFT),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT),
    legend_title=element_text(color=INK),
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
