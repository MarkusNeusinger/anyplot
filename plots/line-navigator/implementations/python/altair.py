"""anyplot.ai
line-navigator: Line Chart with Mini Navigator
Library: altair | Python 3.13
Quality: pending | Created: 2026-05-27
"""

import os
import sys


# Prevent this file (altair.py) from shadowing the installed altair package.
# Python adds the script's directory as sys.path[0] when running a .py file;
# removing it (by absolute path match) lets site-packages take precedence.
_this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != _this_dir]

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
BRAND = "#009E73"  # anyplot palette position 1 — ALWAYS first series
HIGHLIGHT = "#DDCC77"  # amber — selection window indicator

# Data — daily sensor readings over 3 years (1095 data points)
np.random.seed(42)
dates = pd.date_range("2022-01-01", periods=1095, freq="D")
trend = np.linspace(20, 35, 1095)
seasonal = 8 * np.sin(2 * np.pi * np.arange(1095) / 365)
weekly = 2 * np.sin(2 * np.pi * np.arange(1095) / 7)
noise = np.random.randn(1095) * 2
values = trend + seasonal + weekly + noise
df = pd.DataFrame({"date": dates, "value": values})

title = "line-navigator · python · altair · anyplot.ai"
title_fontsize = 16  # len=45 < 67 baseline, no shrink needed

# Initial selection covers first half of 2023 to demonstrate navigation
start_ms = int(pd.Timestamp("2023-01-01").timestamp() * 1000)
end_ms = int(pd.Timestamp("2023-07-01").timestamp() * 1000)
brush = alt.selection_interval(encodings=["x"], value={"x": [start_ms, end_ms]})

NAV_H = 50  # navigator chart height in pixels

# Main chart — detail view linked to brush selection
main_chart = (
    alt.Chart(df)
    .mark_line(color=BRAND, strokeWidth=2)
    .encode(
        x=alt.X("date:T", title="Date", scale=alt.Scale(domain=brush)),
        y=alt.Y("value:Q", title="Sensor Reading (°C)", scale=alt.Scale(zero=False)),
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%Y-%m-%d"),
            alt.Tooltip("value:Q", title="Value", format=".1f"),
        ],
    )
    .properties(width=620, height=220, title=alt.Title(title, fontSize=title_fontsize))
    .interactive()
)

# Navigator chart — full data overview with draggable selection window
navigator_line = (
    alt.Chart(df)
    .mark_line(color=BRAND, strokeWidth=1)
    .encode(
        x=alt.X("date:T", title=""),
        y=alt.Y("value:Q", title="", axis=alt.Axis(labels=False, ticks=False), scale=alt.Scale(zero=False)),
    )
    .properties(width=620, height=NAV_H)
    .add_params(brush)
)

# Amber highlight fills from data line down to chart bottom for selected range
selection_highlight = (
    alt.Chart(df)
    .mark_area(color=HIGHLIGHT, opacity=0.35)
    .encode(x=alt.X("date:T"), y=alt.Y("value:Q", scale=alt.Scale(zero=False)), y2=alt.value(NAV_H))
    .transform_filter(brush)
)

navigator = alt.layer(navigator_line, selection_highlight).properties(width=620, height=NAV_H)

# Combine main chart and navigator vertically
combined = (
    alt.vconcat(main_chart, navigator, spacing=10)
    .properties(background=PAGE_BG)
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_axis(
        labelFontSize=10,
        titleFontSize=12,
        gridColor=INK,
        gridOpacity=0.12,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
    )
    .configure_title(color=INK)
)

# Save PNG then pad to exact 3200×1800 target
combined.save(f"plot-{THEME}.png", scale_factor=4.0)

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

# Save HTML (interactive version)
combined.save(f"plot-{THEME}.html")
