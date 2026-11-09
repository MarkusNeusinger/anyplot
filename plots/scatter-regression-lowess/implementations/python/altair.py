""" anyplot.ai
scatter-regression-lowess: Scatter Plot with LOWESS Regression
Library: altair 6.3.0 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-09
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image
from statsmodels.nonparametric.smoothers_lowess import lowess


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: points take position 1, the LOWESS curve position 2 for contrast
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
LOWESS_FRAC = 0.3

# Columns
TEMPERATURE = "Daily Mean Temperature (°C)"  # role: x
DEMAND = "Electricity Demand (GW)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("daily_demand.csv")
np.random.seed(42)
n = 200
temperature = np.sort(np.random.uniform(-5, 35, n))
# Heating load on cold days, a flat comfort zone, and a steeper air-conditioning load on hot days
demand = (
    38 + 0.035 * (temperature - 17) ** 2 + 0.004 * np.clip(temperature - 22, 0, None) ** 3 + np.random.normal(0, 2.2, n)
)
df = pd.DataFrame({TEMPERATURE: temperature, DEMAND: demand})

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
x_field = TEMPERATURE.translate(ESCAPE)
y_field = DEMAND.translate(ESCAPE)

smoothed = lowess(df[DEMAND], df[TEMPERATURE], frac=LOWESS_FRAC, return_sorted=True)
df_lowess = pd.DataFrame({TEMPERATURE: smoothed[:, 0], DEMAND: smoothed[:, 1]})

scatter = (
    alt.Chart(df)
    .mark_circle(size=55, opacity=0.6, color=IMPRINT_PALETTE[0])
    .encode(
        x=alt.X(x_field, type="quantitative", title=TEMPERATURE),
        y=alt.Y(y_field, type="quantitative", title=DEMAND, scale=alt.Scale(zero=False)),
        tooltip=[
            alt.Tooltip(x_field, type="quantitative", title=TEMPERATURE, format=".1f"),
            alt.Tooltip(y_field, type="quantitative", title=DEMAND, format=".1f"),
        ],
    )
)

lowess_line = (
    alt.Chart(df_lowess)
    .mark_line(strokeWidth=3, color=IMPRINT_PALETTE[1])
    .encode(x=alt.X(x_field, type="quantitative"), y=alt.Y(y_field, type="quantitative"))
)

title = "LOWESS Smoothing · scatter-regression-lowess · python · altair · anyplot.ai"
title_fontsize = max(11, round(16 * (67 / len(title) if len(title) > 67 else 1.0)))

chart = (
    (scatter + lowess_line)
    .properties(width=640, height=340, background=PAGE_BG, title=alt.Title(title, fontSize=title_fontsize))
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=10,
        titleFontSize=12,
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_title(color=INK)
    .interactive()
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
