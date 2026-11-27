""" anyplot.ai
box-basic: Basic Box Plot
Library: altair 6.3.0 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-27
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

# Imprint palette: all eight positions, one per department in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
DEPARTMENT = "Department"  # role: category
SALARY = "Salary (USD)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("salaries.csv")
np.random.seed(42)
params = {
    "Engineering": (95000, 15000, 80),
    "Marketing": (72000, 12000, 65),
    "Sales": (68000, 18000, 90),
    "HR": (63000, 9000, 55),
    "Finance": (85000, 13000, 70),
}
records = []
for dept, (mean, std, n) in params.items():
    salaries = np.clip(np.random.normal(mean, std, n), 25000, None)
    records.extend({DEPARTMENT: dept, SALARY: round(s, -2)} for s in salaries)
df = pd.DataFrame(records)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
departments = df[DEPARTMENT].unique().tolist()
title = "box-basic · python · altair · anyplot.ai"

chart = (
    alt.Chart(df)
    .mark_boxplot(
        size=100,
        median={"stroke": "white", "strokeWidth": 3},
        rule={"color": INK_SOFT, "strokeWidth": 2},
        outliers={"size": 100, "strokeWidth": 1.5, "opacity": 0.75},
    )
    .encode(
        x=alt.X(
            DEPARTMENT.translate(ESCAPE),
            type="nominal",
            title=DEPARTMENT,
            sort=departments,
            axis=alt.Axis(labelAngle=0, titlePadding=10),
        ),
        y=alt.Y(
            SALARY.translate(ESCAPE),
            type="quantitative",
            title=SALARY,
            scale=alt.Scale(zero=False),
            axis=alt.Axis(format="$,.0f", titlePadding=10),
        ),
        color=alt.Color(
            DEPARTMENT.translate(ESCAPE),
            type="nominal",
            title=DEPARTMENT,
            sort=departments,
            scale=alt.Scale(range=IMPRINT_PALETTE),
            legend=None,
        ),
        tooltip=[
            alt.Tooltip(DEPARTMENT.translate(ESCAPE), type="nominal", title=DEPARTMENT),
            alt.Tooltip(f"median({SALARY.translate(ESCAPE)}):Q", title="Median", format="$,.0f"),
            alt.Tooltip(f"q1({SALARY.translate(ESCAPE)}):Q", title="Q1", format="$,.0f"),
            alt.Tooltip(f"q3({SALARY.translate(ESCAPE)}):Q", title="Q3", format="$,.0f"),
        ],
    )
    .properties(
        width=800,
        height=450,
        autosize=alt.AutoSizeParams(type="fit", contains="padding"),
        padding=10,
        background=PAGE_BG,
        title=alt.Title(title, fontSize=16, anchor="start", offset=10),
    )
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
    .configure_title(color=INK)
)

# Save PNG
chart.save(f"plot-{THEME}.png", scale_factor=4.0)

# Fit-to-canvas safety net (3200 × 1800): a no-op when the chart already fits
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
