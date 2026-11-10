""" anyplot.ai
line-basic: Basic Line Plot
Library: altair 6.3.0 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-10
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: single series uses position 1
BRAND = "#009E73"

# Columns: set these to your table's column names
MONTH = "Month"  # role: x
TEMPERATURE = "Temperature (°C)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("temperature.csv")
np.random.seed(42)
months = pd.date_range(start="2024-01-01", periods=12, freq="MS")
seasonal = 15 + 12 * np.sin((np.arange(12) - 3) * np.pi / 6)
df = pd.DataFrame({MONTH: months, TEMPERATURE: seasonal + np.random.randn(12) * 2})

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
x_field = MONTH.translate(ESCAPE)
y_field = TEMPERATURE.translate(ESCAPE)

base = alt.Chart(df).encode(
    x=alt.X(x_field, type="temporal", title=MONTH, axis=alt.Axis(format="%b", tickCount="month", grid=False)),
    y=alt.Y(y_field, type="quantitative", title=TEMPERATURE, scale=alt.Scale(zero=False, nice=True)),
)

line = base.mark_line(strokeWidth=2.5, color=BRAND)
points = base.mark_point(size=60, color=BRAND, filled=True).encode(
    tooltip=[
        alt.Tooltip(x_field, type="temporal", title=MONTH, format="%B %Y"),
        alt.Tooltip(y_field, type="quantitative", title=TEMPERATURE, format=".1f"),
    ]
)

chart = (
    (line + points)
    .properties(width=620, height=320, title=alt.Title("line-basic · python · altair · anyplot.ai"), background=PAGE_BG)
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.15,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=10,
        titleFontSize=12,
    )
    .configure_axisY(grid=True)
    .configure_title(color=INK, fontSize=16)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad (never crop) to the canonical landscape canvas
TARGET_W, TARGET_H = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TARGET_W or h > TARGET_H:
    raise SystemExit(f"altair produced {w}x{h}, exceeds target {TARGET_W}x{TARGET_H}")
if (w, h) != (TARGET_W, TARGET_H):
    canvas = Image.new("RGB", (TARGET_W, TARGET_H), PAGE_BG)
    canvas.paste(img, ((TARGET_W - w) // 2, (TARGET_H - h) // 2))
    canvas.save(f"plot-{THEME}.png")
