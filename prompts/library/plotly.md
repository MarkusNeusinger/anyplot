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

## Layout & Sizing for 4800×2700 px

```python
fig.update_layout(
    title=dict(text=title, font=dict(size=28)),
    xaxis=dict(title=dict(text=x_label, font=dict(size=22)), tickfont=dict(size=18)),
    yaxis=dict(title=dict(text=y_label, font=dict(size=22)), tickfont=dict(size=18)),
    template='plotly_white',
)

# Marker/line sizes
fig.update_traces(marker=dict(size=12))   # ~3-4x default
fig.update_traces(line=dict(width=3))
```

## Save (PNG)

```python
# Target: 4800 × 2700 px (see default-style-guide.md)
fig.write_image(f'plot-{THEME}.png', width=1600, height=900, scale=3)
```

**Note**: Requires `kaleido` for PNG export.

## Interactivity

Plotly is interactive by default (hover, zoom, pan).
For static outputs → `write_image()`.

## Colors

Use the Okabe-Ito palette (see `prompts/default-style-guide.md` "Categorical Palette"). First series is **always** `#009E73`.

```python
OKABE_ITO = ['#009E73', '#D55E00', '#0072B2', '#CC79A7',
             '#E69F00', '#56B4E9', '#F0E442']

# Single-series
fig = go.Figure(go.Scatter(x=x, y=y, mode='markers',
                           marker=dict(color=OKABE_ITO[0])))

# Multi-series via color_discrete_sequence (plotly express)
fig = px.scatter(df, x='x', y='y', color='category',
                 color_discrete_sequence=OKABE_ITO)

# Continuous — NOT Okabe-Ito:
#   Sequential: color_continuous_scale='viridis' or 'cividis'
#   Diverging:  color_continuous_scale='BrBG'
#   Forbidden:  'jet', 'hsv', 'rainbow'
```

## Theme-adaptive Chrome (plotly mapping)

```python
import os
THEME       = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG     = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK         = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT    = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID        = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

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

fig.write_image(f'plot-{THEME}.png', width=1600, height=900, scale=3)
fig.write_html(f'plot-{THEME}.html', include_plotlyjs='cdn')
```

## Output Files

- Implementation: `plots/{spec-id}/implementations/plotly.py` — executed twice with different `ANYPLOT_THEME`.
- Generated artifacts: `plot-light.png` + `plot-dark.png` + `plot-light.html` + `plot-dark.html`.

