""" anyplot.ai
scatter-basic: Basic Scatter Plot
Library: altair 6.2.2 | Python 3.13.14
Quality: 87/100 | Updated: 2026-06-25
"""

import os
import sys


# Remove script directory from sys.path so the altair package resolves, not this file
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens — Imprint palette
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"  # Imprint palette position 1

# Data — study hours vs. exam scores (r ~ 0.70, moderate positive correlation)
np.random.seed(42)
n = 180
study_hours = np.random.uniform(1, 12, n)
exam_scores = np.clip(40 + study_hours * 4.2 + np.random.normal(0, 12.0, n), 30, 100)
df = pd.DataFrame({"hours": study_hours, "score": exam_scores})

pearson_r = float(np.corrcoef(df["hours"], df["score"])[0, 1])

# Scatter layer
points = (
    alt.Chart(df)
    .mark_circle(size=140, opacity=0.7, color=BRAND, stroke=PAGE_BG, strokeWidth=0.8)
    .encode(
        x=alt.X(
            "hours:Q",
            title="Study Hours per Week",
            scale=alt.Scale(domain=[0, 13], nice=False),
            axis=alt.Axis(tickCount=6, ticks=False, labelPadding=10, titlePadding=14, domain=False),
        ),
        y=alt.Y(
            "score:Q",
            title="Exam Score (%)",
            scale=alt.Scale(domain=[25, 105], nice=False),
            axis=alt.Axis(tickCount=8, ticks=False, labelPadding=10, titlePadding=14, domain=False),
        ),
        tooltip=[
            alt.Tooltip("hours:Q", title="Study hrs / wk", format=".1f"),
            alt.Tooltip("score:Q", title="Exam %", format=".1f"),
        ],
    )
)

# Regression line — Altair's transform_regression showcases its declarative layering grammar
regression = (
    alt.Chart(df)
    .mark_line(color=INK_SOFT, strokeWidth=2.0, strokeDash=[6, 4], opacity=0.75)
    .transform_regression("hours", "score")
    .encode(x=alt.X("hours:Q"), y=alt.Y("score:Q"))
)

chart = (
    alt.layer(points, regression)
    .properties(
        width=620,
        height=320,
        background=PAGE_BG,
        title=alt.Title(
            "scatter-basic · altair · anyplot.ai",
            subtitle=f"n = {n}  ·  Pearson r = {pearson_r:.2f}",
            fontSize=16,
            fontWeight="normal",
            color=INK,
            subtitleFontSize=10,
            subtitleColor=INK_MUTED,
            subtitlePadding=4,
            anchor="start",
            offset=16,
        ),
    )
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_axis(
        labelFontSize=10,
        titleFontSize=12,
        titleFontWeight="normal",
        gridColor=INK,
        gridOpacity=0.10,
        gridWidth=0.8,
        labelColor=INK_SOFT,
        titleColor=INK,
    )
)

# Save PNG
chart.save(f"plot-{THEME}.png", scale_factor=4.0)

# Pad to exact target 3200 × 1800 (vl-convert pads outside width/height)
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
