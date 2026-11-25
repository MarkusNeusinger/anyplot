# altair

**API level:** Altair 6. `uv.lock` pins this major; write against its API.

## Import

```python
import altair as alt
```

## Canvas — hard rule, no deviation

The saved PNG must be **exactly** one of these two sizes (post-render gate in `impl-review.yml` rejects anything off by more than 16 px and re-triggers repair):

| Orientation | Chart size              | scale_factor | Final PNG     |
|-------------|-------------------------|--------------|---------------|
| Landscape   | width=800, height=450   | 4.0          | 3200 × 1800   |
| Square      | width=600, height=600   | 4.0          | 2400 × 2400   |

Both with `autosize=alt.AutoSizeParams(type="fit", contains="padding")` and `padding=10` in the same `.properties(...)`. On a layered chart, `autosize`, `padding`, `background` and `configure_*` go on `alt.layer(...)` (or the `+` result), never on a member: Altair refuses a member that carries any of them with a `TypeError`.

**Without `autosize`, Altair's `width` / `height` size only the view, the plotting area.** `vl-convert` adds the title, axis titles, tick labels and legend *outside* it, so the saved file is **larger** than `(width * scale_factor, height * scale_factor)`: in the May 2026 fan-out, `width=800, height=450` saved at 3404×2120 or 4036×2052. A view sized smaller to make room (the old `620×320`) lands short of the canvas instead, and padding it up to the target leaves an empty frame around the chart.

**`type="fit"` makes `width` / `height` the size of the whole chart.** Vega-Lite grows or shrinks the view until view, axes, title and legend fill exactly 800×450 (600×600), and `contains="padding"` counts the `padding` inside that size. A single or layered chart then saves at exactly 3200×1800 (2400×2400) and fills the canvas; on other data, longer labels shrink the view, never grow the PNG. `padding=10` keeps the title and the outer labels 40 px off the canvas edge.

**Compound charts cannot fit.** `alt.hconcat`, `alt.vconcat`, `|`, `&`, `.facet(...)`, `.repeat(...)` and the `row=`, `column=` and `facet=` encoding channels ignore `type="fit"` (Vega-Lite warns and falls back to padding), so their PNG is the sum of their views plus the axes, titles and legends around them. There `width` / `height` size each view or facet cell, not the whole chart: the 800×450 of a single chart gives each of three facet columns 800×450 and saves at about 10000×2300. Give each view or cell a `width` / `height` that brings the whole chart close to the target and at or under it. The block below scales an overshoot down as a whole and pads a shortfall with `PAGE_BG`; a large shrink also shrinks the text, so size the views rather than rely on it.

**Always run this block after the PNG save.** It changes nothing on a chart that fits. **Do NOT crop.** Cropping silently destroys title/axis-label content at the edges (which the gate cannot detect — it only checks pixel count) and the AI review will flag the missing text as severe edge-clipping (AR-09 auto-reject):

```python
# Right after chart.save(f'plot-{THEME}.png', scale_factor=4.0):
from PIL import Image

TW, TH = 3200, 1800   # or (2400, 2400) for square
_img = Image.open(f'plot-{THEME}.png').convert('RGB')
if _img.size != (TW, TH):
    # Only a compound chart lands here: scale an overshoot down as a whole
    # (never crop), then centre the chart on the target canvas with PAGE_BG.
    _scale = min(1.0, TW / _img.width, TH / _img.height)
    _img = _img.resize((round(_img.width * _scale), round(_img.height * _scale)), Image.LANCZOS)
    _canvas = Image.new('RGB', (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _img.width) // 2, (TH - _img.height) // 2))
    _canvas.save(f'plot-{THEME}.png')
```

The HTML save is left untouched — only PNGs are gated.

```python
chart = alt.Chart(df).mark_point(size=60).encode(  # size ~2-3x default, density-aware
    x=alt.X(STUDY_HOURS.translate(ESCAPE), type="quantitative", title=STUDY_HOURS),  # see "Data block"
    y=alt.Y(EXAM_SCORE.translate(ESCAPE), type="quantitative", title=EXAM_SCORE),
).properties(
    width=800,       # see Canvas table: the whole chart, title and legend included
    height=450,
    autosize=alt.AutoSizeParams(type="fit", contains="padding"),
    padding=10,      # 40 px between the canvas edge and the title / outer labels
    title=alt.Title(title, fontSize=16)  # kept compact for the long mandated title
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

Pass the type as `type=` next to the escaped field (see "Data block"); the shorthand codes in a field string (`"Sales:Q"`) break on a column name that contains a colon.

```python
# Q = Quantitative (numeric)
alt.X(SALES.translate(ESCAPE), type="quantitative")

# N = Nominal (categorical, no order)
alt.Color(REGION.translate(ESCAPE), type="nominal")

# O = Ordinal (categorical, with order)
alt.X(MONTH.translate(ESCAPE), type="ordinal")

# T = Temporal (date/time)
alt.X(DATE.translate(ESCAPE), type="temporal")
```

## Data block

The file follows the six zones of `prompts/adaptable-code.md`. Altair reads the tidy `df` directly with `alt.Chart(df)` and the column constants as fields. Vega-Lite reads `.` and `[]` in a field name as nested access and `:` as a type suffix, so a column such as `"Sales (k USD.)"` breaks the chart, silently or with an error. Escape the constants once below the block, and give every encoding its `type=` and its `title=`, because an escaped field shows its backslashes in the automatic title:

```python
# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
chart = alt.Chart(df).mark_bar().encode(
    x=alt.X(QUARTER.translate(ESCAPE), type="nominal", title=QUARTER, sort=None),
    xOffset=alt.XOffset(PRODUCT_LINE.translate(ESCAPE), type="nominal", sort=None),
    y=alt.Y(SALES.translate(ESCAPE), type="quantitative", title=SALES),
    color=alt.Color(PRODUCT_LINE.translate(ESCAPE), type="nominal", title=PRODUCT_LINE, sort=None,
                    scale=alt.Scale(range=IMPRINT_PALETTE)),
)
```

`sort=None` keeps the data's order instead of sorting the labels. Scale domains come from the data (`alt.Scale(domain=[0, df[SALES].max() * 1.15])`) or stay automatic, never typed numbers.

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
# Then apply the inline fit-to-canvas block from the "Canvas" section above.
# Do NOT crop — cropping would clip title/axis labels and trigger AR-09.
```

**Note**: Requires `vl-convert-python` for PNG export.

## Interactivity

```python
# Enable zoom/pan
chart = chart.interactive()

# Tooltips (escaped fields, readable titles)
.encode(tooltip=[alt.Tooltip(QUARTER.translate(ESCAPE), title=QUARTER),
                 alt.Tooltip(SALES.translate(ESCAPE), title=SALES)])
```

## Colors

Use the Imprint palette (see `prompts/default-style-guide.md` "Categorical Palette"). First series is **always** `#009E73`.

```python
IMPRINT_PALETTE = ['#009E73', '#C475FD', '#4467A3', '#BD8233',
                   '#AE3030', '#2ABCCD', '#954477', '#99B314']
ANYPLOT_AMBER = '#DDCC77'  # warning / caution (outside the categorical pool)

# Single-series
alt.Chart(df).mark_circle(color=IMPRINT_PALETTE[0]).encode(x=..., y=...)

# Multi-series: the full list; Vega-Lite hands out the first n in order
alt.Chart(df).mark_circle().encode(
    x=..., y=...,
    color=alt.Color(SCHOOL.translate(ESCAPE), type="nominal", title=SCHOOL,
                    scale=alt.Scale(range=IMPRINT_PALETTE)),
)

# Continuous — only the two Imprint ramps are allowed, as (position, hex) stops, low → high,
# with their own stops per theme (style guide, "Continuous Data"). FIELDS: colored cells that
# fill the plot (rect heatmaps, maps, tiles). MARKS: colored points, lines, outlines or bars on
# the page. Keep only the ramps the plot uses.
SEQ_FIELDS = (
    [(0.0, "#66E2B2"), (0.368, "#009E73"), (0.582, "#4467A3"), (1.0, "#002850")]
    if THEME == "light"
    else [(0.0, "#00573D"), (0.467, "#009E73"), (1.0, "#CDD9FF")]
)
SEQ_MARKS = (
    [(0.0, "#009E73"), (0.338, "#4467A3"), (1.0, "#002850")]
    if THEME == "light"
    else [(0.0, "#007755"), (0.32, "#009E73"), (1.0, "#CDD9FF")]
)
# Sequential: a piecewise scale, one domain value per stop, placed by its position in the data's range.
# Vega-Lite blends a color range in HCL unless told otherwise; interpolate="rgb" blends in sRGB
# like the other libraries, so the colors between the stops are the style guide's.
lo, hi = df[DENSITY].min(), df[DENSITY].max()
alt.Color(DENSITY.translate(ESCAPE), type="quantitative", scale=alt.Scale(
    domain=[lo + p * (hi - lo) for p, _ in SEQ_FIELDS],  # SEQ_MARKS on marks
    range=[c for _, c in SEQ_FIELDS],
    interpolate="rgb",
))
# Diverging: three-stop range with domainMid at 0; the midpoint is the page for fields
# and a grey that keeps 3:1 for marks
DIV_FIELDS_RANGE = ['#AE3030', '#FAF8F1' if THEME == 'light' else '#1A1A17', '#4467A3']
DIV_MARKS_RANGE = ['#AE3030', '#6B6A63' if THEME == 'light' else '#686762', '#4467A3']
alt.Color(CHANGE.translate(ESCAPE), type="quantitative", scale=alt.Scale(
    range=DIV_FIELDS_RANGE,
    domainMid=0,
    interpolate="rgb",
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
    .properties(
        # A compound base_chart (concat, facet) takes no width/height here: leave them
        # out and size each view or cell instead ("Compound charts cannot fit" above).
        background=PAGE_BG, width=800, height=450, padding=10,
        autosize=alt.AutoSizeParams(type="fit", contains="padding"),
    )
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
# Apply the inline fit-to-(3200,1800)-or-(2400,2400) block from the
# "Canvas" section above — MANDATORY, no helper function (KISS / CQ-01).
chart.save(f'plot-{THEME}.html')
```

## Output Files

- Implementation: `plots/{spec-id}/implementations/altair.py` — executed twice with different `ANYPLOT_THEME`.
- Generated artifacts: `plot-light.png` + `plot-dark.png` + `plot-light.html` + `plot-dark.html`.

