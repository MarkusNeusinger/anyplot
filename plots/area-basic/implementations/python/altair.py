"""anyplot.ai
area-basic: Basic Area Chart
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-28
"""

import os
import sys


# Prevent self-import: this file is named altair.py, so remove its directory
# from sys.path before importing the altair package.
_this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if p and os.path.abspath(p) != _this_dir]

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: a single series uses position 1
BRAND = "#009E73"

# Columns: set these to your table's column names
DATE = "Date"  # role: x
VISITORS = "Daily visitors (count)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("visitors.csv")
np.random.seed(42)
dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
base = 5000
trend = np.linspace(0, 2000, 30)
weekly_pattern = np.array([1.2, 1.1, 1.0, 1.05, 1.15, 0.8, 0.7] * 5)[:30]
noise = np.random.randn(30) * 300
visitors = (base + trend) * weekly_pattern + noise
visitors[14] *= 1.4
visitors = np.maximum(visitors, 1000).astype(int)
df = pd.DataFrame({DATE: dates, VISITORS: visitors})

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})

chart = (
    alt.Chart(df)
    .mark_area(
        line={"color": BRAND, "strokeWidth": 2.5},
        color=alt.Gradient(
            gradient="linear",
            stops=[
                alt.GradientStop(color="rgba(0, 158, 115, 0.05)", offset=0),
                alt.GradientStop(color="rgba(0, 158, 115, 0.60)", offset=1),
            ],
            x1=1,
            x2=1,
            y1=1,
            y2=0,
        ),
    )
    .encode(
        x=alt.X(DATE.translate(ESCAPE), type="temporal", title=DATE, axis=alt.Axis(format="%b %d", labelAngle=-30)),
        y=alt.Y(
            VISITORS.translate(ESCAPE),
            type="quantitative",
            title=VISITORS,
            scale=alt.Scale(domain=[0, float(df[VISITORS].max() * 1.15)]),
        ),
        tooltip=[
            alt.Tooltip(DATE.translate(ESCAPE), type="temporal", title=DATE, format="%b %d, %Y"),
            alt.Tooltip(VISITORS.translate(ESCAPE), type="quantitative", title=VISITORS, format=","),
        ],
    )
    .properties(
        width=800,
        height=450,
        autosize=alt.AutoSizeParams(type="fit", contains="padding"),
        padding=10,
        background=PAGE_BG,
        title=alt.Title("area-basic · python · altair · anyplot.ai", fontSize=16),
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
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
    .configure_axisX(grid=False)
    .configure_title(color=INK)
)

# Save PNG
chart.save(f"plot-{THEME}.png", scale_factor=4.0)

# Fit to the exact 3200×1800 canvas (centre on the page colour, never crop)
TW, TH = 3200, 1800
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (TW, TH):
    _scale = min(1.0, TW / _img.width, TH / _img.height)
    _img = _img.resize((round(_img.width * _scale), round(_img.height * _scale)), Image.LANCZOS)
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _img.width) // 2, (TH - _img.height) // 2))
    _canvas.save(f"plot-{THEME}.png")

# Save HTML
chart.save(f"plot-{THEME}.html")
