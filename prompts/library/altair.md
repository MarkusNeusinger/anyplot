# altair

## Import

```python
import altair as alt
```

## Canvas — hard rule, no deviation

The saved PNG must be **exactly** one of these two sizes (post-render gate in `impl-review.yml` rejects anything off by more than 16 px and re-triggers repair):

| Orientation | Inner view dims        | scale_factor | Final PNG     |
|-------------|------------------------|--------------|---------------|
| Landscape   | width=620, height=320  | 4.0          | → fits in 3200 × 1800 with title+legend padding |
| Square      | width=500, height=460  | 4.0          | → fits in 2400 × 2400 with title+legend padding |

**Altair's view dimensions are NOT the saved PNG dimensions.** `vl-convert` pads the view with title, axis title, axis tick labels, and legend extents *outside* the chart's `width` / `height`, so the SAVED file is always **larger** than `(width * scale_factor, height * scale_factor)`. In the May 2026 fan-out, `width=800, height=450` (which naively maps to 3200×1800) actually saved at 3404×2120 or 4036×2052 because the title and legend added 100–200 px of padding on each side.

**The fix is to size the inner view smaller** so vl-convert's extra padding still leaves the final PNG within the target. The values above (`620×320` for landscape, `500×460` for square) leave roughly 360–500 px of width and 400–500 px of height available for the title bar, axis labels, and right-side legend. Tune within ±20 px if your chart genuinely needs more room, but **stay under 800×450 / 600×600** — the old defaults are guaranteed to overshoot.

**Then PAD the saved PNG up to exact target dims.** Even with the smaller view, vl-convert can land slightly short. After `chart.save(...)`, pad the canvas with `PAGE_BG` to land exactly on the canonical target. **Do NOT crop.** Cropping silently destroys title/axis-label content at the edges (which the gate cannot detect — it only checks pixel count) and the AI review will flag the missing text as severe edge-clipping (AR-09 auto-reject):

```python
# Right after chart.save(f'plot-{THEME}.png', scale_factor=4.0):
from PIL import Image

TW, TH = 3200, 1800   # or (2400, 2400) for square
_img = Image.open(f'plot-{THEME}.png').convert('RGB')
_w, _h = _img.size
if _w > TW or _h > TH:
    # vl-convert overshot the inner-view target. This is a real bug in the
    # chart definition (probably oversized title fontSize, oversized legend,
    # or width/height too large). Fail loudly so impl-repair triggers — do
    # NOT crop, because cropping clips title/axis labels and the AR-09 edge-
    # clipping auto-reject will catch it anyway.
    raise SystemExit(
        f"altair vl-convert produced {_w}×{_h}, exceeds target {TW}×{TH}. "
        f"Shrink chart .properties(width=, height=) values and re-render."
    )
if _w < TW or _h < TH:
    # PAD-only: centre the chart on the target canvas with PAGE_BG fill.
    _canvas = Image.new('RGB', (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _w) // 2, (TH - _h) // 2))
    _canvas.save(f'plot-{THEME}.png')
```

The HTML save is left untouched — only PNGs are gated.

```python
chart = alt.Chart(df).mark_point(size=60).encode(  # size ~2-3x default, density-aware
    x='col_x:Q',
    y='col_y:Q'
).properties(
    width=620,       # see Canvas table — landscape inner-view
    height=320,
    padding={"left": 0, "right": 0, "top": 0, "bottom": 0},
    title=alt.Title(title, fontSize=16)  # kept compact for the long mandated title
).configure_view(
    continuousWidth=620,
    continuousHeight=320,
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
# Then apply the inline PAD-only-to-target block from the "Canvas" section above.
# Do NOT crop — cropping would clip title/axis labels and trigger AR-09.
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

Use the Imprint palette (see `prompts/default-style-guide.md` "Categorical Palette"). First series is **always** `#009E73`.

```python
ANYPLOT_PALETTE = ['#009E73', '#C475FD', '#4467A3', '#BD8233',
                   '#AE3030', '#2ABCCD', '#954477', '#99B314']
ANYPLOT_AMBER = '#DDCC77'  # warning / caution (outside the categorical pool)

# Single-series
alt.Chart(df).mark_circle(color=ANYPLOT_PALETTE[0]).encode(x='x', y='y')

# Multi-series
alt.Chart(df).mark_circle().encode(
    x='x', y='y',
    color=alt.Color('category:N', scale=alt.Scale(range=ANYPLOT_PALETTE)),
)

# Continuous — only the two Imprint palette-derived cmaps are allowed:
# Sequential: two-stop range
alt.Color('value:Q', scale=alt.Scale(range=['#009E73', '#4467A3']))
# Diverging: three-stop range with domainMid at 0
alt.Color('delta:Q', scale=alt.Scale(
    range=['#AE3030', '#FAF8F1', '#4467A3'],
    domainMid=0,
))
# Forbidden: scheme='viridis'/'cividis'/'brownbluegreen' and any other named scheme for continuous data.
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
        gridColor=INK, gridOpacity=0.15,
        labelColor=INK_SOFT, titleColor=INK,
    )
    .configure_title(color=INK)
    .configure_legend(
        fillColor=ELEVATED_BG, strokeColor=INK_SOFT,
        labelColor=INK_SOFT, titleColor=INK,
    )
)

chart.save(f'plot-{THEME}.png', scale_factor=4.0)
# Apply the inline PAD-only-to-(3200,1800)-or-(2400,2400) block from the
# "Canvas" section above — MANDATORY, no helper function (KISS / CQ-01).
chart.save(f'plot-{THEME}.html')
```

## Output Files

- Implementation: `plots/{spec-id}/implementations/altair.py` — executed twice with different `ANYPLOT_THEME`.
- Generated artifacts: `plot-light.png` + `plot-dark.png` + `plot-light.html` + `plot-dark.html`.

