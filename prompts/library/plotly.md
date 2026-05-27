# plotly

## Import

```python
import plotly.graph_objects as go
# or
import plotly.express as px
```

## Create Figure

```python
# Graph Objects
fig = go.Figure()
fig.add_trace(go.Scatter(x=x, y=y))

# Express (for quick plots)
fig = px.scatter(df, x='col_x', y='col_y')
```

## Canvas — hard rule, no deviation

The saved PNG must be **exactly** one of these two sizes (post-render gate in `impl-review.yml` rejects anything off by more than 16 px and re-triggers repair):

| Orientation | write_image kwargs                         | Final PNG     |
|-------------|--------------------------------------------|---------------|
| Landscape   | `width=800, height=450, scale=4`           | 3200 × 1800   |
| Square      | `width=600, height=600, scale=4`           | 2400 × 2400   |

`fig.update_layout(autosize=True)` is **forbidden** — it overrides `width`/`height` and produces variable output. Always pass `autosize=False` together with explicit `width`, `height`. Pin the layout margins explicitly so titles/legends don't push the inner plot off-center and the long mandated title never gets clipped:

```python
fig.update_layout(
    autosize=False,
    margin=dict(l=80, r=40, t=80, b=60),   # tweak ±20 if needed; never remove
)
```

Pick landscape or square based on the spec's content — same decision rule as every other library in the catalog.

## Layout & Sizing for 3200×1800 px (starting values — review-loop tunes)

```python
fig.update_layout(
    autosize=False,
    margin=dict(l=80, r=40, t=80, b=60),
    # Title kept compact — the long mandated "{spec-id} · python · plotly · anyplot.ai"
    # title would overflow at 22+px on this canvas.
    title=dict(text=title, font=dict(size=16)),
    xaxis=dict(title=dict(text=x_label, font=dict(size=12)), tickfont=dict(size=10)),
    yaxis=dict(title=dict(text=y_label, font=dict(size=12)), tickfont=dict(size=10)),
    template='plotly_white',
)

# Marker/line sizes (density-aware — see default-style-guide.md)
fig.update_traces(marker=dict(size=10))
fig.update_traces(line=dict(width=2.5))
```

See `prompts/default-style-guide.md` "Proportional Sizing" for review criteria.

## Save (PNG)

```python
# Hard target: 3200 × 1800 (landscape) or 2400 × 2400 (square). See "Canvas" above.
fig.write_image(f'plot-{THEME}.png', width=800, height=450, scale=4)         # landscape
# fig.write_image(f'plot-{THEME}.png', width=600, height=600, scale=4)       # square
```

**Note**: Requires `kaleido` for PNG export.

## Interactivity

Plotly is interactive by default (hover, zoom, pan).
For static outputs → `write_image()`.

## Colors

Use the anyplot palette (see `prompts/default-style-guide.md` "Categorical Palette"). First series is **always** `#009E73`.

```python
ANYPLOT_PALETTE = ['#009E73', '#C475FD', '#4467A3', '#BD8233',
                   '#AE3030', '#2ABCCD', '#954477', '#99B314']
ANYPLOT_AMBER = '#DDCC77'  # warning / caution (outside the categorical pool)

# Single-series
fig = go.Figure(go.Scatter(x=x, y=y, mode='markers',
                           marker=dict(color=ANYPLOT_PALETTE[0])))

# Multi-series via color_discrete_sequence (plotly express)
fig = px.scatter(df, x='x', y='y', color='category',
                 color_discrete_sequence=ANYPLOT_PALETTE)

# Continuous — only the two anyplot palette-derived cmaps are allowed:
imprint_seq = [[0.0, "#009E73"], [1.0, "#4467A3"]]                                            # sequential / single-polarity
midpoint = "#FAF8F1" if THEME == "light" else "#1A1A17"                                       # theme-adaptive
imprint_div = [[0.0, "#AE3030"], [0.5, midpoint], [1.0, "#4467A3"]]                           # diverging
# Sequential: color_continuous_scale=imprint_seq
# Diverging:  color_continuous_scale=imprint_div
# Forbidden: any other scale ('viridis'/'cividis'/'BrBG'/'Reds'/'Blues'/'Greens'/'jet'/'hsv'/'rainbow').
```

## Theme-adaptive Chrome (plotly mapping)

```python
import os
THEME       = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG     = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK         = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT    = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID        = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

fig.update_layout(
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    xaxis=dict(
        title=dict(font=dict(color=INK)),
        tickfont=dict(color=INK_SOFT),
        gridcolor=GRID, linecolor=INK_SOFT, zerolinecolor=INK_SOFT,
    ),
    yaxis=dict(
        title=dict(font=dict(color=INK)),
        tickfont=dict(color=INK_SOFT),
        gridcolor=GRID, linecolor=INK_SOFT, zerolinecolor=INK_SOFT,
    ),
    legend=dict(
        bgcolor=ELEVATED_BG, bordercolor=INK_SOFT, borderwidth=1,
        font=dict(color=INK_SOFT),
    ),
)

fig.write_image(f'plot-{THEME}.png', width=800, height=450, scale=4)
fig.write_html(f'plot-{THEME}.html', include_plotlyjs='cdn')
```

## Output Files

- Implementation: `plots/{spec-id}/implementations/plotly.py` — executed twice with different `ANYPLOT_THEME`.
- Generated artifacts: `plot-light.png` + `plot-dark.png` + `plot-light.html` + `plot-dark.html`.

