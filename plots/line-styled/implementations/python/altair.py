""" anyplot.ai
line-styled: Styled Line Plot
Library: altair 6.3.0 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-09
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: color comes on top of the line style, one hue per series in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants: the standard styles first (solid, dashed, dotted, dash-dot), then long dash and dash-dot-dot
LINE_WIDTH = 2.5  # one width for every style; a dash as long as the line is wide draws a square dot
LINE_STYLES = [[1, 0], [10, 4], [2.5, 4], [10, 4, 2.5, 4], [18, 4], [10, 4, 2.5, 4, 2.5, 4]]

# Columns: set these to your table's column names
MONTH = "Month"  # role: x
STATIONS = ["Coastal", "Mountain", "Valley", "Highland"]  # role: y_
TEMPERATURE = "Temperature (°C)"  # the measure the series share, for the value axis
STATION = "Weather Station"  # what tells the series apart, for the legend

# Data: replace this block with your own table, for example df = pd.read_csv("station_temperatures.csv")
np.random.seed(42)
base_temp = np.array([5, 7, 12, 16, 21, 25, 28, 27, 23, 17, 11, 6])
df = pd.DataFrame(
    {
        MONTH: pd.date_range("2025-01-01", periods=12, freq="MS"),
        **{
            station: base_temp + offset + np.random.randn(12) * 1.5
            for station, offset in zip(STATIONS, [0, -3, 5, -6], strict=True)
        },
    }
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})

long = df.melt(id_vars=MONTH, value_vars=STATIONS, var_name=STATION, value_name=TEMPERATURE)

lines = (
    alt.Chart(long)
    .mark_line(strokeWidth=LINE_WIDTH, strokeJoin="round")
    .encode(
        x=alt.X(
            MONTH.translate(ESCAPE),
            type="temporal",
            title=MONTH,
            axis=alt.Axis(format="%b", tickCount="month", grid=False, labelPadding=6),
        ),
        y=alt.Y(TEMPERATURE.translate(ESCAPE), type="quantitative", title=TEMPERATURE, scale=alt.Scale(zero=False)),
        color=alt.Color(
            STATION.translate(ESCAPE),
            type="nominal",
            title=STATION,
            sort=STATIONS,
            scale=alt.Scale(domain=STATIONS, range=IMPRINT_PALETTE),
        ),
        strokeDash=alt.StrokeDash(
            STATION.translate(ESCAPE),
            type="nominal",
            title=STATION,
            sort=STATIONS,
            scale=alt.Scale(domain=STATIONS, range=LINE_STYLES),
        ),
        tooltip=[
            alt.Tooltip(STATION.translate(ESCAPE), title=STATION),
            alt.Tooltip(MONTH.translate(ESCAPE), type="temporal", title=MONTH, format="%B"),
            alt.Tooltip(TEMPERATURE.translate(ESCAPE), type="quantitative", title=TEMPERATURE, format=".1f"),
        ],
    )
)

chart = (
    lines.properties(
        width=520,
        height=340,
        background=PAGE_BG,
        padding={"left": 12, "right": 16, "top": 10, "bottom": 10},
        title=alt.Title("line-styled · python · altair · anyplot.ai", fontSize=16, color=INK, offset=12),
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=11,
        titleFontSize=12,
        titleFontWeight="normal",
        titlePadding=10,
        gridColor=INK,
        gridOpacity=0.15,
    )
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=RULE,
        padding=12,
        offset=18,
        titleColor=INK,
        labelColor=INK_SOFT,
        titleFontSize=11,
        labelFontSize=11,
        titlePadding=8,
        symbolType="stroke",
        symbolSize=1600,
        symbolStrokeWidth=LINE_WIDTH,
        rowPadding=2,
        labelOffset=8,
    )
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)

TW, TH = 3200, 1800
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
_w, _h = _img.size
if _w > TW or _h > TH:
    raise SystemExit(
        f"altair vl-convert produced {_w}×{_h}, exceeds target {TW}×{TH}. "
        f"Shrink chart .properties(width=, height=) values and re-render."
    )
if _w < TW or _h < TH:
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _w) // 2, (TH - _h) // 2))
    _canvas.save(f"plot-{THEME}.png")

chart.save(f"plot-{THEME}.html")
