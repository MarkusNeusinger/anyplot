"""anyplot.ai
range-interval: Range Interval Chart
Library: altair 6.1.0 | Python 3.13.13
Quality: 99/100 | Updated: 2026-05-18
"""

import os

import altair as alt
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
MONTH = "Month"  # role: category
MIN_TEMP = "Minimum temperature (°C)"  # role: min_value
MAX_TEMP = "Maximum temperature (°C)"  # role: max_value

# Data: replace this block with your own table, for example df = pd.read_csv("ranges.csv")
df = pd.DataFrame(
    {
        MONTH: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        MIN_TEMP: [-2, -1, 3, 7, 12, 16, 18, 17, 13, 8, 3, 0],
        MAX_TEMP: [5, 7, 12, 18, 23, 27, 30, 29, 24, 17, 10, 6],
    }
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
MID_TEMP = "Midpoint (°C)"
df[MID_TEMP] = (df[MIN_TEMP] + df[MAX_TEMP]) / 2

month_y = alt.Y(
    MONTH.translate(ESCAPE), type="nominal", title=MONTH, sort=None, axis=alt.Axis(labelFontSize=11, titleFontSize=13)
)
base = alt.Chart(df).encode(y=month_y)

# Range bars floating from minimum to maximum
bars = base.mark_bar(height=13, cornerRadius=2, opacity=0.8, color=IMPRINT_PALETTE[0]).encode(
    x=alt.X(
        MIN_TEMP.translate(ESCAPE),
        type="quantitative",
        title="Temperature (°C)",
        scale=alt.Scale(domain=[df[MIN_TEMP].min() - 2, df[MAX_TEMP].max() + 2], nice=False),
        axis=alt.Axis(labelFontSize=11, titleFontSize=13),
    ),
    x2=alt.X2(MAX_TEMP.translate(ESCAPE)),
    tooltip=[
        alt.Tooltip(MONTH.translate(ESCAPE), type="nominal", title=MONTH),
        alt.Tooltip(MIN_TEMP.translate(ESCAPE), type="quantitative", title=MIN_TEMP),
        alt.Tooltip(MAX_TEMP.translate(ESCAPE), type="quantitative", title=MAX_TEMP),
        alt.Tooltip(MID_TEMP.translate(ESCAPE), type="quantitative", title=MID_TEMP, format=".1f"),
    ],
)

# Endpoint markers sit exactly on the two bounds
min_points = base.mark_point(size=45, filled=True, shape="circle", color=IMPRINT_PALETTE[1]).encode(
    x=alt.X(MIN_TEMP.translate(ESCAPE), type="quantitative")
)
max_points = base.mark_point(size=45, filled=True, shape="circle", color=IMPRINT_PALETTE[2]).encode(
    x=alt.X(MAX_TEMP.translate(ESCAPE), type="quantitative")
)

# Midpoint markers stay small so the ranges remain the mark
mid_points = base.mark_point(size=22, filled=True, shape="diamond", color=INK, stroke=INK_SOFT, strokeWidth=1).encode(
    x=alt.X(MID_TEMP.translate(ESCAPE), type="quantitative")
)

chart = (
    alt.layer(bars, min_points, max_points, mid_points)
    .properties(
        width=620,
        height=320,
        background=PAGE_BG,
        title=alt.Title("range-interval · python · altair · anyplot.ai", fontSize=16, anchor="middle", color=INK),
    )
    .configure_axis(
        labelFontSize=11,
        titleFontSize=13,
        labelColor=INK_SOFT,
        titleColor=INK,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridOpacity=0.10,
        gridColor=INK,
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, strokeWidth=1)
    .configure_title(color=INK, fontSize=16)
)

chart.save(f"plot-{THEME}.png", scale_factor=4.0)

# Pad (never crop) to the canonical landscape canvas
TW, TH = 3200, 1800
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
_w, _h = _img.size
if _w > TW or _h > TH:
    raise SystemExit(f"altair vl-convert produced {_w}×{_h}, exceeds target {TW}×{TH}. Shrink width/height.")
if _w < TW or _h < TH:
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _w) // 2, (TH - _h) // 2))
    _canvas.save(f"plot-{THEME}.png")

chart.save(f"plot-{THEME}.html")
