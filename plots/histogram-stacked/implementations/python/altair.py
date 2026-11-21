"""anyplot.ai
histogram-stacked: Stacked Histogram
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-12
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette, canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

SCORE = "Test Score (points)"  # role: values
METHOD = "Study Method"  # role: group
STUDENTS = "Number of Students"

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
rng = np.random.default_rng(42)
method_a = rng.normal(loc=72, scale=10, size=150)
method_b = rng.normal(loc=78, scale=8, size=120)
method_c = rng.normal(loc=68, scale=12, size=100)

df = pd.DataFrame(
    {
        SCORE: np.clip(np.concatenate([method_a, method_b, method_c]), 0, 100),
        METHOD: (
            ["Traditional Study"] * len(method_a)
            + ["Active Recall"] * len(method_b)
            + ["Passive Reading"] * len(method_c)
        ),
    }
)

# Plot
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
score_field = SCORE.translate(ESCAPE)
method_field = METHOD.translate(ESCAPE)

chart = (
    alt.Chart(df)
    .mark_bar(opacity=0.85, stroke=PAGE_BG, strokeWidth=0.5)
    .encode(
        x=alt.X(score_field, type="quantitative", bin=alt.Bin(maxbins=20), title=SCORE),
        y=alt.Y("count()", type="quantitative", title=STUDENTS, stack="zero"),
        color=alt.Color(
            method_field,
            type="nominal",
            title=METHOD,
            scale=alt.Scale(domain=list(df[METHOD].dropna().unique()), range=IMPRINT_PALETTE),
            legend=alt.Legend(orient="right"),
        ),
        order=alt.Order(method_field, type="nominal", sort="ascending"),
    )
    .properties(
        width=540,
        height=320,
        background=PAGE_BG,
        title=alt.Title("histogram-stacked · python · altair · anyplot.ai", fontSize=16, anchor="middle"),
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, strokeWidth=0.5)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=11,
        titleFontSize=13,
    )
    .configure_title(color=INK)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=11,
        titleFontSize=12,
        padding=8,
    )
)

chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad to the canonical 3200x1800 canvas
TW, TH = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TW or h > TH:
    raise SystemExit(f"altair produced {w}x{h}, exceeds target {TW}x{TH}")
canvas = Image.new("RGB", (TW, TH), PAGE_BG)
canvas.paste(img, ((TW - w) // 2, (TH - h) // 2))
canvas.save(f"plot-{THEME}.png")
