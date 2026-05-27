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
    element_text, element_rect, element_line,
    scale_color_manual, scale_fill_manual,
    scale_color_gradient, scale_fill_gradient,
    scale_color_gradient2, scale_fill_gradient2,
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

## Canvas — hard rule, no deviation

The saved PNG must be **exactly** one of these two sizes (post-render gate in `impl-review.yml` rejects anything off by more than 16 px and re-triggers repair):

| Orientation | `figure_size` | `ggsave` `width × height` (`units='in'`, `dpi=400`) | Final PNG     |
|-------------|---------------|------------------------------------------------------|---------------|
| Landscape   | `(8, 4.5)`    | `width=8, height=4.5`                                | 3200 × 1800   |
| Square      | `(6, 6)`      | `width=6, height=6`                                  | 2400 × 2400   |

Pick the orientation that suits the spec — same decision the other libraries make. plotnine's matplotlib backend respects `figure_size`/`width`/`height` directly, so no extra tricks are required as long as you don't pass `bbox_inches='tight'` to `ggsave` (`ggsave` doesn't expose it, but if you fall back to `plt.savefig`, do **not** add it — same trim risk as matplotlib/seaborn).

## Figure Size & Sizing for 3200×1800 px (starting values — review-loop tunes)

```python
plot = plot + theme(
    figure_size=(8, 4.5),
    text=element_text(size=7),            # Base text
    axis_title=element_text(size=10),     # Axis labels
    axis_text=element_text(size=8),       # Tick labels
    plot_title=element_text(size=12),     # Title — kept compact to fit the long mandated title
    legend_text=element_text(size=8)
)

# Element sizes in geoms (density-aware — see default-style-guide.md)
+ geom_point(size=2.5)   # ~2-3x library default
+ geom_line(size=1.0)    # line width (plotnine scale is finer than matplotlib's)
```

> `geom_text(size=N)` is in mm (× 2.845 ≈ pt), unlike `element_text(size=N)` which is pt. Annotation `size` should be ~2.5–4, never the same numeric scale as the theme.

See `prompts/default-style-guide.md` "Proportional Sizing" for review criteria.

## Save (PNG)

```python
plot.save(f'plot-{THEME}.png', dpi=400, width=8, height=4.5, units='in')
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

Use the anyplot palette (see `prompts/default-style-guide.md` "Categorical Palette"). First series is **always** `#009E73`.

```python
ANYPLOT_PALETTE = ['#009E73', '#C475FD', '#4467A3', '#BD8233',
                   '#AE3030', '#2ABCCD', '#954477', '#99B314']
ANYPLOT_AMBER = '#DDCC77'  # warning / caution (outside the categorical pool)

# Single-series
+ geom_point(color=ANYPLOT_PALETTE[0])

# Multi-series
+ scale_color_manual(values=ANYPLOT_PALETTE)
+ scale_fill_manual(values=ANYPLOT_PALETTE)

# Continuous — only the two anyplot palette-derived cmaps are allowed:
from plotnine import scale_color_gradient, scale_color_gradient2, scale_fill_gradient, scale_fill_gradient2
# Sequential (single-polarity)
+ scale_color_gradient(low='#009E73', high='#4467A3')
+ scale_fill_gradient(low='#009E73',  high='#4467A3')
# Diverging (around a meaningful midpoint, often 0)
+ scale_color_gradient2(low='#AE3030', mid='#FAF8F1', high='#4467A3', midpoint=0)
+ scale_fill_gradient2(low='#AE3030',  mid='#FAF8F1', high='#4467A3', midpoint=0)
# Forbidden: scale_color_cmap / scale_fill_cmap with viridis/cividis/BrBG/Reds/Blues/Greens — only anyplot stops.
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
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.15),
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

plot = (ggplot(df, aes('x', 'y')) + geom_point(color=ANYPLOT_PALETTE[0]) + anyplot_theme)
ggsave(plot, filename=f'plot-{THEME}.png', dpi=400, width=8, height=4.5)
```

## Output Files

- Implementation: `plots/{spec-id}/implementations/plotnine.py` — executed twice with different `ANYPLOT_THEME`.
- Generated artifacts: `plot-light.png` + `plot-dark.png` (plotnine is PNG-only via matplotlib backend).
