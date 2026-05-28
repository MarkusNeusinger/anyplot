"""anyplot.ai
box-basic: Basic Box Plot
Library: altair | Python 3.13
Quality: pending | Updated: 2026-05-28
"""

import os

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

ANYPLOT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"]

# Data — salary distributions across five departments
np.random.seed(42)
departments = ["Engineering", "Marketing", "Sales", "HR", "Finance"]
params = {
    "Engineering": (95000, 15000, 80),
    "Marketing": (72000, 12000, 65),
    "Sales": (68000, 18000, 90),
    "HR": (63000, 9000, 55),
    "Finance": (85000, 13000, 70),
}

records = []
for dept, (mean, std, n) in params.items():
    salaries = np.random.normal(mean, std, n)
    salaries = np.clip(salaries, 25000, None)
    for s in salaries:
        records.append({"Department": dept, "Salary": round(s, -2)})

df = pd.DataFrame(records)

# Plot
title = "box-basic · python · altair · anyplot.ai"

chart = (
    alt.Chart(df)
    .mark_boxplot(
        size=90,
        median={"stroke": "white", "strokeWidth": 3},
        outliers={"size": 100, "strokeWidth": 1.5, "opacity": 0.75},
    )
    .encode(
        x=alt.X("Department:N", title="Department", sort=departments, axis=alt.Axis(labelAngle=0, titlePadding=10)),
        y=alt.Y(
            "Salary:Q",
            title="Salary (USD)",
            scale=alt.Scale(domain=[22000, 142000]),
            axis=alt.Axis(format="$,.0f", tickCount=7, titlePadding=10),
        ),
        color=alt.Color("Department:N", scale=alt.Scale(domain=departments, range=ANYPLOT_PALETTE), legend=None),
        tooltip=[
            alt.Tooltip("Department:N"),
            alt.Tooltip("median(Salary):Q", title="Median", format="$,.0f"),
            alt.Tooltip("q1(Salary):Q", title="Q1", format="$,.0f"),
            alt.Tooltip("q3(Salary):Q", title="Q3", format="$,.0f"),
        ],
    )
    .properties(
        width=620,
        height=320,
        background=PAGE_BG,
        padding={"left": 0, "right": 0, "top": 0, "bottom": 0},
        title=alt.Title(title, fontSize=16, anchor="start", offset=10),
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
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
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=10,
        titleFontSize=10,
    )
)

# Save PNG
chart.save(f"plot-{THEME}.png", scale_factor=4.0)

# Pad to exact canvas target (3200 × 1800)
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
