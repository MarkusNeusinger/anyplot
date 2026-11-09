""" anyplot.ai
scatter-regression-lowess: Scatter Plot with LOWESS Regression
Library: altair 6.3.0 | Python 3.14.10
Quality: 77/100 | Updated: 2026-11-09
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
DISTANCE = "Independent Variable (meters)"  # role: x
MASS = "Dependent Variable (kg)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("measurements.csv")
np.random.seed(42)
n = 200
x = np.linspace(0, 10, n)
# Non-linear pattern: sine wave with trend and noise
y = 2 * np.sin(x * 0.8) + 0.5 * x + np.random.normal(0, 0.8, n)
df = pd.DataFrame({DISTANCE: x, MASS: y})

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
x_field = DISTANCE.translate(ESCAPE)
y_field = MASS.translate(ESCAPE)

smoothed = lowess(df[MASS], df[DISTANCE], frac=LOWESS_FRAC, return_sorted=True)
df_lowess = pd.DataFrame({DISTANCE: smoothed[:, 0], MASS: smoothed[:, 1]})

scatter = (
    alt.Chart(df)
    .mark_circle(size=55, opacity=0.6, color=IMPRINT_PALETTE[0])
    .encode(
        x=alt.X(x_field, type="quantitative", title=DISTANCE),
        y=alt.Y(y_field, type="quantitative", title=MASS),
        tooltip=[
            alt.Tooltip(x_field, type="quantitative", title=DISTANCE, format=".2f"),
            alt.Tooltip(y_field, type="quantitative", title=MASS, format=".2f"),
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
