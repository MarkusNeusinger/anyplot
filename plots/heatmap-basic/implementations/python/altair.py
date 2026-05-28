""" anyplot.ai
heatmap-basic: Basic Heatmap
Library: altair 6.1.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-28
"""

import os
import sys


# Remove current script directory to prevent self-import (file is named altair.py)
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if p not in ("", ".") and os.path.abspath(p) != _here]

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
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint diverging colormap midpoint — theme-adaptive
DIV_MID = "#FAF8F1" if THEME == "light" else "#1A1A17"

# Data — correlation matrix for 8 weather variables
np.random.seed(42)
variables = [
    "Temperature",
    "Humidity",
    "Wind Speed",
    "Pressure",
    "Visibility",
    "Cloud Cover",
    "Precipitation",
    "UV Index",
]

n_samples = 200
raw = np.random.randn(n_samples, len(variables))

# Inject realistic correlations; multiplier 1.2 on Visibility pushes it below -0.8
raw[:, 1] += raw[:, 0] * 0.6  # Humidity ~ Temperature
raw[:, 5] += raw[:, 1] * 0.7  # Cloud Cover ~ Humidity
raw[:, 6] += raw[:, 5] * 0.65  # Precipitation ~ Cloud Cover
raw[:, 4] -= raw[:, 5] * 1.2  # Visibility strongly inversely ~ Cloud Cover (< -0.8)
raw[:, 7] -= raw[:, 5] * 0.7  # UV Index inversely ~ Cloud Cover
raw[:, 7] += raw[:, 0] * 0.5  # UV Index ~ Temperature
raw[:, 3] -= raw[:, 0] * 0.4  # Pressure inversely ~ Temperature
raw[:, 2] += raw[:, 3] * 0.3  # Wind Speed ~ Pressure

corr = np.corrcoef(raw.T)

axis_order = list(variables)

df = pd.DataFrame(
    [
        {"Row": row_var, "Column": col_var, "value": round(corr[i, j], 2)}
        for i, row_var in enumerate(variables)
        for j, col_var in enumerate(variables)
    ]
)

# Title — 44 chars < 67 baseline → ratio = 1.0 → default fontSize 16
title_str = "heatmap-basic · python · altair · anyplot.ai"

# Text annotation color: all light on dark theme; adaptive on light theme
if THEME == "dark":
    text_color_enc = alt.value("#F0EFE8")
else:
    text_color_enc = (
        alt.when((alt.datum.value > 0.55) | (alt.datum.value < -0.55))
        .then(alt.value("#ffffff"))
        .otherwise(alt.value(INK))
    )

# Heatmap layer — Imprint diverging colormap (#AE3030 → midpoint → #4467A3)
heatmap = (
    alt.Chart(df)
    .mark_rect(stroke="#ffffff", strokeWidth=1.5, cornerRadius=2)
    .encode(
        x=alt.X(
            "Column:N",
            title=None,
            sort=axis_order,
            axis=alt.Axis(labelFontSize=10, labelAngle=-45, orient="top", labelPadding=4),
        ),
        y=alt.Y(
            "Row:N",
            title="Weather Variable",
            sort=axis_order,
            axis=alt.Axis(labelFontSize=10, titleFontSize=11, labelPadding=4, titlePadding=6),
        ),
        color=alt.Color(
            "value:Q",
            scale=alt.Scale(range=["#AE3030", DIV_MID, "#4467A3"], domain=[-1, 1], domainMid=0),
            legend=alt.Legend(
                title="Correlation",
                titleFontSize=11,
                labelFontSize=10,
                gradientLength=220,
                gradientThickness=12,
                titlePadding=5,
                offset=8,
                direction="vertical",
            ),
        ),
        tooltip=[
            alt.Tooltip("Column:N", title="Column"),
            alt.Tooltip("Row:N", title="Row"),
            alt.Tooltip("value:Q", title="Correlation", format=".2f"),
        ],
    )
)

# Bold borders for strong correlations (|r| ≥ 0.7) — theme-adaptive stroke
highlight = (
    alt.Chart(df)
    .transform_filter((alt.datum.value >= 0.7) | (alt.datum.value <= -0.7))
    .mark_rect(stroke=INK, strokeWidth=2.5, filled=False, cornerRadius=2)
    .encode(x=alt.X("Column:N", sort=axis_order), y=alt.Y("Row:N", sort=axis_order))
)

# Cell value annotations
text = (
    alt.Chart(df)
    .mark_text(fontSize=10, fontWeight="bold")
    .encode(
        x=alt.X("Column:N", sort=axis_order),
        y=alt.Y("Row:N", sort=axis_order),
        text=alt.Text("value:Q", format=".2f"),
        color=text_color_enc,
    )
)

chart = (
    (heatmap + highlight + text)
    .properties(
        width=350,
        height=380,
        background=PAGE_BG,
        title=alt.Title(
            title_str,
            subtitle=[
                "Pairwise Pearson correlations for 8 weather metrics.",
                "Bold borders mark strong relationships (|r| ≥ 0.7).",
            ],
            fontSize=14,
            subtitleFontSize=11,
            subtitleColor=INK_MUTED,
            color=INK,
            anchor="start",
            offset=10,
        ),
        padding={"left": 10, "right": 10, "top": 10, "bottom": 10},
    )
    .configure_axis(grid=False, domainColor=INK_SOFT, tickColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save PNG — target: 2400 × 2400 (square, 1:1 for symmetric heatmap)
TW, TH = 2400, 2400
chart.save(f"plot-{THEME}.png", scale_factor=4.0)

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
