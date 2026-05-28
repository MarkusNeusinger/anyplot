"""anyplot.ai
area-basic: Basic Area Chart
Library: altair | Python 3.13
Quality: pending | Created: 2026-05-28
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


# Theme
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Data - daily website visitors over January 2024
np.random.seed(42)
dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
base = 5000
trend = np.linspace(0, 2000, 30)
weekly_pattern = np.array([1.2, 1.1, 1.0, 1.05, 1.15, 0.8, 0.7] * 5)[:30]
noise = np.random.randn(30) * 300
visitors = (base + trend) * weekly_pattern + noise
visitors[14] *= 1.4
visitors = np.maximum(visitors, 1000).astype(int)
df = pd.DataFrame({"date": dates, "visitors": visitors})

# Chart
title = "area-basic · python · altair · anyplot.ai"
chart = (
    alt.Chart(df)
    .mark_area(
        line={"color": BRAND, "strokeWidth": 2.5},
        color=alt.Gradient(
            gradient="linear",
            stops=[
                alt.GradientStop(color="rgba(0, 158, 115, 0.05)", offset=0),
                alt.GradientStop(color="rgba(0, 158, 115, 0.45)", offset=1),
            ],
            x1=1,
            x2=1,
            y1=1,
            y2=0,
        ),
    )
    .encode(
        x=alt.X("date:T", title="Date", axis=alt.Axis(format="%b %d", labelAngle=-30)),
        y=alt.Y(
            "visitors:Q", title="Daily Visitors (count)", scale=alt.Scale(domain=[0, int(df["visitors"].max() * 1.15)])
        ),
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%b %d, %Y"),
            alt.Tooltip("visitors:Q", title="Visitors", format=","),
        ],
    )
    .properties(width=620, height=320, background=PAGE_BG, title=alt.Title(title, fontSize=16))
    .configure_view(continuousWidth=620, continuousHeight=320, fill=PAGE_BG, strokeWidth=0)
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
    .configure_title(color=INK)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save PNG
chart.save(f"plot-{THEME}.png", scale_factor=4.0)

# Pad to exact 3200×1800
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

# Save HTML
chart.save(f"plot-{THEME}.html")
