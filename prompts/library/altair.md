# altair

## Import

```python
import altair as alt
```

## Create Chart

```python
chart = alt.Chart(df).mark_point(size=150).encode(  # size ~3-4x default
    x='col_x:Q',
    y='col_y:Q'
).properties(
    width=1600,
    height=900,
    title=alt.Title(title, fontSize=28)
).configure_axis(
    labelFontSize=18,
    titleFontSize=22
)
```

## Encoding Types

```python
# Q = Quantitative (numeric)
x='value:Q'

# N = Nominal (categorical, no order)
color='category:N'

# O = Ordinal (categorical, with order)
x='month:O'

# T = Temporal (date/time)
x='date:T'
```

## Marks

```python
.mark_point()      # Scatter
.mark_line()       # Line
.mark_bar()        # Bar
.mark_boxplot()    # Boxplot
.mark_rect()       # Heatmap
.mark_area()       # Area
```

## Save (PNG)

```python
# Target: 4800 × 2700 px (see default-style-guide.md)
# 1600 × 3 = 4800, 900 × 3 = 2700
chart.save(f'plot-{THEME}.png', scale_factor=3.0)
```

**Note**: Requires `vl-convert-python` for PNG export.

## Interactivity

```python
# Enable zoom/pan
chart = chart.interactive()

# Tooltips
.encode(tooltip=['col_x', 'col_y'])
```

## Colors

Use the Okabe-Ito palette (see `prompts/default-style-guide.md` "Categorical Palette"). First series is **always** `#009E73`.

```python
OKABE_ITO = ['#009E73', '#D55E00', '#0072B2', '#CC79A7',
             '#E69F00', '#56B4E9', '#F0E442']

# Single-series
alt.Chart(df).mark_circle(color=OKABE_ITO[0]).encode(x='x', y='y')

# Multi-series
alt.Chart(df).mark_circle().encode(
    x='x', y='y',
    color=alt.Color('category:N', scale=alt.Scale(range=OKABE_ITO)),
)

# Continuous — NOT Okabe-Ito:
#   Sequential: scheme='viridis' or 'cividis'
#   Diverging:  scheme='brownbluegreen' (BrBG in altair naming)
alt.Color('value:Q', scale=alt.Scale(scheme='viridis'))
alt.Color('delta:Q', scale=alt.Scale(scheme='brownbluegreen'))
```

## Theme-adaptive Chrome (altair mapping)

```python
import os
THEME       = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG     = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK         = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT    = "#4A4A44" if THEME == "light" else "#B8B7B0"

chart = (
    base_chart
    .properties(background=PAGE_BG, width=1600, height=900)
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
    .configure_axis(
        domainColor=INK_SOFT, tickColor=INK_SOFT,
        gridColor=INK, gridOpacity=0.10,
        labelColor=INK_SOFT, titleColor=INK,
    )
    .configure_title(color=INK)
    .configure_legend(
        fillColor=ELEVATED_BG, strokeColor=INK_SOFT,
        labelColor=INK_SOFT, titleColor=INK,
    )
)

chart.save(f'plot-{THEME}.png')
chart.save(f'plot-{THEME}.html')
```

## Output Files

- Implementation: `plots/{spec-id}/implementations/altair.py` — executed twice with different `ANYPLOT_THEME`.
- Generated artifacts: `plot-light.png` + `plot-dark.png` + `plot-light.html` + `plot-dark.html`.

