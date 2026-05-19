# lets-plot

ggplot2-style grammar of graphics by JetBrains.

## Import

```python
from lets_plot import *
LetsPlot.setup_html()  # Required for notebook/export
```

## Create Plot

```python
plot = (
    ggplot(df, aes(x='col_x', y='col_y'))
    + geom_point()
    + labs(x=x_label, y=y_label, title=title)
)
```

## Figure Size & Sizing for 3200×1800 px (starting values — review-loop tunes)

```python
# Base size (scaled 4x on export = 3200 × 1800 px)
plot = plot + ggsize(800, 450)

# Text and element sizes
plot = plot + theme(
    axis_title=element_text(size=16),
    axis_text=element_text(size=14),
    plot_title=element_text(size=22),
    legend_text=element_text(size=14)
)

# Element sizes in geoms (density-aware — see default-style-guide.md)
+ geom_point(size=2.5)   # ~2-3x default
+ geom_line(size=1.0)    # line width
```

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
# Mappings
aes(x='col_x', y='col_y', color='category', size='value')

# Fixed aesthetics (outside aes)
geom_point(color='blue', size=5, alpha=0.7)
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
# Categorical — use Okabe-Ito (see Colors section below)
+ scale_color_manual(values=OKABE_ITO)
+ scale_fill_manual(values=OKABE_ITO)

# Continuous — NOT Okabe-Ito:
+ scale_color_viridis()                        # sequential
+ scale_fill_gradient2(low='#A6611A', mid='#F5F5F5', high='#018571')  # BrBG-style diverging

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
+ facet_wrap('category', ncol=3)
+ facet_grid(x='row_var', y='col_var')
```

## Colors

Use the Okabe-Ito palette (see `prompts/default-style-guide.md` "Categorical Palette"). First series is **always** `#009E73`.

```python
OKABE_ITO = ['#009E73', '#D55E00', '#0072B2', '#CC79A7',
             '#E69F00', '#56B4E9', '#F0E442']

# Single-series
+ geom_point(color=OKABE_ITO[0])

# Multi-series
+ scale_color_manual(values=OKABE_ITO)
+ scale_fill_manual(values=OKABE_ITO)
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

plot = (ggplot(df, aes('x', 'y')) + geom_point(color=OKABE_ITO[0]) + anyplot_theme)
```

## Output Files

- Implementation: `plots/{spec-id}/implementations/letsplot.py` — executed twice with different `ANYPLOT_THEME`.
- Generated artifacts: `plot-light.png` + `plot-dark.png` + `plot-light.html` + `plot-dark.html`.

## Key Differences from plotnine

- Uses `lets_plot` module (not `plotnine`)
- `ggsize()` instead of `theme(figure_size=...)`
- `ggsave()` with `scale` parameter for PNG export
- More interactive features built-in
