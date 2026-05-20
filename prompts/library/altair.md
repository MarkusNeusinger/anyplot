# altair

## Import

```python
import altair as alt
```

## Canvas — hard rule, no deviation

The saved PNG must be **exactly** one of these two sizes (post-render gate in `impl-review.yml` rejects anything off by more than 16 px and re-triggers repair):

| Orientation | View dims      | scale_factor | Final PNG     |
|-------------|----------------|--------------|---------------|
| Landscape   | width=800, height=450 | 4.0 | 3200 × 1800 |
| Square      | width=600, height=600 | 4.0 | 2400 × 2400 |

Altair's **view dimensions are NOT the saved PNG dimensions.** `vl-convert` pads the view with title, axis-title, axis-tick-label, and legend extents *outside* `width`/`height`, so a chart with `width=800, height=450` and a long title easily saves at 3404×2120 or 4036×2052. This is the documented cause of every altair drift in the May 2026 fan-out.

**Two-part fix, both required:**

1. **Constrain the view** with `configure_view(continuousWidth=…, continuousHeight=…)` and **zero out chart padding** with `.properties(padding={"left":0, "right":0, "top":0, "bottom":0})`. This stops most of the inflation but does not guarantee exact dims when titles or legends are present.

2. **Normalize the saved PNG to exact target dims as the final step** of the implementation. Even with (1), vl-convert can over- or under-shoot by tens of pixels. After `chart.save(...)`, crop (centered) or pad (with `PAGE_BG`) so the saved file lands on the canonical target. Keep this as **inline code** — no helper function (CQ-01 KISS forbids functions/classes in plot impls):

```python
# Right after chart.save(f'plot-{THEME}.png', scale_factor=4.0):
from PIL import Image

TW, TH = 3200, 1800   # or (2400, 2400) for square
_img = Image.open(f'plot-{THEME}.png').convert('RGB')
_w, _h = _img.size
if _w > TW or _h > TH:                            # crop excess centred
    _l = max((_w - TW) // 2, 0)
    _t = max((_h - TH) // 2, 0)
    _img = _img.crop((_l, _t, _l + min(_w, TW), _t + min(_h, TH)))
    _w, _h = _img.size
if _w < TW or _h < TH:                            # pad shortfall with PAGE_BG
    _canvas = Image.new('RGB', (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _w) // 2, (TH - _h) // 2))
    _img = _canvas
_img.save(f'plot-{THEME}.png')
```

The HTML save is left untouched — only PNGs are gated.

```python
chart = alt.Chart(df).mark_point(size=60).encode(  # size ~2-3x default, density-aware
    x='col_x:Q',
    y='col_y:Q'
).properties(
    width=800,
    height=450,
    padding={"left": 0, "right": 0, "top": 0, "bottom": 0},
    title=alt.Title(title, fontSize=16)  # kept compact for the long mandated title
).configure_view(
    continuousWidth=800,
    continuousHeight=450,
).configure_axis(
    labelFontSize=10,
    titleFontSize=12
).configure_legend(
    labelFontSize=10,
    titleFontSize=10
)
```

See `prompts/default-style-guide.md` "Proportional Sizing" for review criteria.

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
# Hard target: 3200 × 1800 (landscape) or 2400 × 2400 (square). See "Canvas" above.
chart.save(f'plot-{THEME}.png', scale_factor=4.0)
# Follow with the inline crop/pad-to-target block from the "Canvas" section above
# (no helper function — KISS).
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
    .properties(background=PAGE_BG, width=800, height=450)
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

chart.save(f'plot-{THEME}.png', scale_factor=4.0)
# Apply the inline crop/pad-to-(3200,1800)-or-(2400,2400) block from the
# "Canvas" section above — MANDATORY, no helper function (KISS / CQ-01).
chart.save(f'plot-{THEME}.html')
```

## Output Files

- Implementation: `plots/{spec-id}/implementations/altair.py` — executed twice with different `ANYPLOT_THEME`.
- Generated artifacts: `plot-light.png` + `plot-dark.png` + `plot-light.html` + `plot-dark.html`.

