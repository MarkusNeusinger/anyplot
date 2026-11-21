"""anyplot.ai
line-confidence: Line Plot with Confidence Interval
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-09
"""

import os
import sys


if sys.path[0] == os.path.dirname(__file__):
    sys.path.pop(0)

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

# Imprint palette: single series uses the first position
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]

# Constants
LEVEL = 0.95  # coverage of the interval, shown in the legend
Z_SCORE = 1.96  # normal quantile for LEVEL

# Columns: set these to your table's column names
DAY = "Day"  # role: x
FORECAST = "Predicted value"  # role: y
LOWER = "Lower bound"  # role: y_lower
UPPER = "Upper bound"  # role: y_upper

# Data: replace this block with your own table, for example df = pd.read_csv("forecast.csv")
rng = np.random.default_rng(42)
days = np.arange(50)
trend = 100 + 0.5 * days + 0.02 * days**2 + np.sin(days / 5) * 5
mean = trend + rng.normal(0, 3, len(days))
half_width = Z_SCORE * (5 + 0.15 * days) / 2
df = pd.DataFrame({DAY: days, FORECAST: mean, LOWER: mean - half_width, UPPER: mean + half_width})

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
day, forecast, lower, upper = (c.translate(ESCAPE) for c in (DAY, FORECAST, LOWER, UPPER))
band_label = f"{LEVEL:.0%} confidence interval"
line_label = FORECAST

y_scale = alt.Scale(domain=[df[LOWER].min() * 0.97, df[UPPER].max() * 1.03], nice=False)
x_axis = alt.Axis(labelFontSize=14, titleFontSize=18, labelColor=INK_SOFT, titleColor=INK, tickCount=10)
y_axis = alt.Axis(labelFontSize=14, titleFontSize=18, labelColor=INK_SOFT, titleColor=INK)

band = (
    alt.Chart(df)
    .transform_calculate(series=f"'{band_label}'")
    .mark_area(opacity=0.25)
    .encode(
        x=alt.X(day, type="quantitative", title=DAY, axis=x_axis, scale=alt.Scale(domain=[0, df[DAY].max()])),
        y=alt.Y(lower, type="quantitative", title=FORECAST, scale=y_scale, axis=y_axis),
        y2=alt.Y2(upper),
        fill=alt.Fill(
            "series:N",
            scale=alt.Scale(domain=[band_label], range=[BRAND]),
            legend=alt.Legend(title=None, symbolOpacity=0.35, symbolType="square", orient="top-left", offset=8),
        ),
        tooltip=[
            alt.Tooltip(day, type="quantitative", title=DAY),
            alt.Tooltip(lower, type="quantitative", title=LOWER, format=".1f"),
            alt.Tooltip(upper, type="quantitative", title=UPPER, format=".1f"),
        ],
    )
)

line = (
    alt.Chart(df)
    .transform_calculate(series=f"'{line_label}'")
    .mark_line(strokeWidth=3.5)
    .encode(
        x=alt.X(day, type="quantitative"),
        y=alt.Y(forecast, type="quantitative", scale=y_scale),
        stroke=alt.Stroke(
            "series:N",
            scale=alt.Scale(domain=[line_label], range=[BRAND]),
            legend=alt.Legend(title=None, symbolType="stroke", symbolStrokeWidth=4, orient="top-left", offset=8),
        ),
        tooltip=[
            alt.Tooltip(day, type="quantitative", title=DAY),
            alt.Tooltip(forecast, type="quantitative", title=FORECAST, format=".1f"),
        ],
    )
)

chart = (
    alt.layer(band, line)
    .properties(
        width=620,
        height=320,
        background=PAGE_BG,
        title=alt.Title("line-confidence · python · altair · anyplot.ai", fontSize=22, color=INK, anchor="middle"),
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, strokeWidth=0.5)
    .configure_axis(domainColor=INK_SOFT, tickColor=INK_SOFT, gridColor=INK, gridOpacity=0.12)
    .configure_legend(
        fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, labelFontSize=14, padding=8, symbolSize=500
    )
)

chart.save(f"plot-{THEME}.png", scale_factor=4.0)

# Pad (never crop) to the canonical landscape canvas
TARGET_W, TARGET_H = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET_W or img.height > TARGET_H:
    raise SystemExit(f"altair produced {img.width}x{img.height}, exceeds {TARGET_W}x{TARGET_H}")
canvas = Image.new("RGB", (TARGET_W, TARGET_H), PAGE_BG)
canvas.paste(img, ((TARGET_W - img.width) // 2, (TARGET_H - img.height) // 2))
canvas.save(f"plot-{THEME}.png")

chart.interactive().save(f"plot-{THEME}.html")
