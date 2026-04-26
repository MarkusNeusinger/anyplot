# plotnine

## IMPORTANT: No Workarounds

**If plotnine cannot implement a plot type natively, DO NOT use matplotlib as a workaround.**

plotnine is a ggplot2-based grammar of graphics library. It does NOT support:
- 3D plots (no wireframes, surfaces, 3D scatter)
- Network/graph visualizations
- Geographic maps (without extensions)

If the specification requires features not available in plotnine's grammar of graphics, the implementation should FAIL rather than fall back to matplotlib or other libraries. Each library implementation should use only that library's native capabilities.

## Interactive Spec Handling

plotnine produces **static PNG only**. When implementing specs that mention interactive features:

- Specs with primary interactivity (hover, zoom, click, brush) → **NOT_FEASIBLE**
- Specs with animation → Use small multiples or faceted grid as static alternative
- Mixed specs (static + interactive) → Implement static features only, omit interactive silently
- **NEVER** simulate tooltips, hover states, or controls. See AR-08 in `prompts/quality-criteria.md`

---

## Import

```python
from plotnine import (
    ggplot, aes,
    geom_point, geom_line, geom_bar, geom_boxplot,
    labs, theme, theme_minimal,
    scale_fill_brewer, scale_color_brewer
)
```

## Create Plot

```python
plot = (
    ggplot(df, aes(x='col_x', y='col_y'))
    + geom_point()
    + labs(x=x_label, y=y_label, title=title)
    + theme_minimal()
)
```

## Figure Size & Sizing for 4800×2700 px

```python
plot = plot + theme(
    figure_size=(16, 9),
    text=element_text(size=14),           # Base text
    axis_title=element_text(size=20),     # Axis labels
    axis_text=element_text(size=16),      # Tick labels
    plot_title=element_text(size=24),     # Title
    legend_text=element_text(size=16)
)

# Element sizes in geoms
+ geom_point(size=4)    # ~3-4x default
+ geom_line(size=1.5)   # line width
```

## Save (PNG)

```python
plot.save(f'plot-{THEME}.png', dpi=300)
```

## Brewer Palettes

**IMPORTANT**: Palette type must match the palette name!

```python
# Qualitative (categorical)
+ scale_fill_brewer(type='qual', palette='Set2')
+ scale_fill_brewer(type='qual', palette='Paired')
+ scale_fill_brewer(type='qual', palette='Dark2')

# Sequential (numeric)
+ scale_fill_brewer(type='seq', palette='Blues')
+ scale_fill_brewer(type='seq', palette='Greens')

# Diverging (around zero)
+ scale_fill_brewer(type='div', palette='RdBu')
+ scale_fill_brewer(type='div', palette='PiYG')
```

```python
# WRONG: Set2 is NOT sequential!
+ scale_fill_brewer(type='seq', palette='Set2')

# RIGHT: Set2 is qualitative
+ scale_fill_brewer(type='qual', palette='Set2')
```

## Geoms

```python
geom_point()     # Scatter
geom_line()      # Line
geom_bar()       # Bar (stat='identity' for values)
geom_boxplot()   # Boxplot
geom_histogram() # Histogram
geom_tile()      # Heatmap
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

# Continuous — NOT Okabe-Ito:
from plotnine import scale_color_cmap, scale_fill_cmap
+ scale_color_cmap(cmap_name='viridis')          # sequential
+ scale_color_cmap(cmap_name='cividis')          # sequential CVD
+ scale_fill_cmap(cmap_name='BrBG')              # diverging
```

## Theme-adaptive Chrome (plotnine mapping)

plotnine wraps matplotlib under the hood, so theme tokens mirror the matplotlib pattern but are passed via `theme()`:

```python
import os
from plotnine import theme, element_rect, element_text, element_line, ggsave

THEME       = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG     = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK         = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT    = "#4A4A44" if THEME == "light" else "#B8B7B0"

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
    panel_border=element_rect(color=INK_SOFT, fill=None),
    axis_title=element_text(color=INK),
    axis_text=element_text(color=INK_SOFT),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT),
    legend_title=element_text(color=INK),
)

plot = (ggplot(df, aes('x', 'y')) + geom_point(color=OKABE_ITO[0]) + anyplot_theme)
ggsave(plot, filename=f'plot-{THEME}.png', dpi=300, width=16, height=9)
```

## Output Files

- Implementation: `plots/{spec-id}/implementations/plotnine.py` — executed twice with different `ANYPLOT_THEME`.
- Generated artifacts: `plot-light.png` + `plot-dark.png` (plotnine is PNG-only via matplotlib backend).
