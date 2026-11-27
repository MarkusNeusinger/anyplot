"""anyplot.ai
violin-basic: Basic Violin Plot
Library: altair 6.1.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-29
"""

import importlib
import os
import sys

import numpy as np
import pandas as pd
from PIL import Image


# Drop script directory from sys.path so `altair` resolves the package, not this file
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
alt = importlib.import_module("altair")

# Theme tokens — Imprint palette + theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
DEPARTMENT = "Department"  # role: category
SALARY = "Salary ($)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("salaries.csv")
np.random.seed(42)
dept_records = []
for dept, mu, sigma, n in [
    ("Support", 55000, 10000, 150),
    ("Marketing", 70000, 13000, 150),
    ("Engineering", 92000, 16000, 150),
]:
    for v in np.random.normal(mu, sigma, n):
        dept_records.append({DEPARTMENT: dept, SALARY: v})

# Sales: bimodal — base salary + commission earners (highlights violin over box plot)
for v in np.concatenate([np.random.normal(50000, 8000, 75), np.random.normal(92000, 11000, 75)]):
    dept_records.append({DEPARTMENT: "Sales", SALARY: v})

df = pd.DataFrame(dept_records)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
DEPT_F, SALARY_F = DEPARTMENT.translate(ESCAPE), SALARY.translate(ESCAPE)
dept_order = [str(d) for d in df[DEPARTMENT].dropna().unique()]
color_scale = alt.Scale(domain=dept_order, range=IMPRINT_PALETTE)

base = alt.Chart(df)

# Violin shape — KDE, mirrored via stack="center"
violin = (
    base.transform_density(
        density=SALARY_F,
        as_=[SALARY_F, "density"],
        groupby=[DEPT_F],
        extent=[int(df[SALARY].min()) - 8000, int(df[SALARY].max()) + 8000],
    )
    .mark_area(orient="horizontal", opacity=0.75)
    .encode(
        y=alt.Y(SALARY_F, type="quantitative", title=SALARY),
        x=alt.X(
            "density:Q",
            stack="center",
            impute=None,
            title=None,
            axis=alt.Axis(labels=False, values=[0], grid=False, ticks=False),
        ),
        color=alt.Color(DEPT_F, type="nominal", scale=color_scale, legend=None),
        tooltip=[
            alt.Tooltip(DEPT_F, type="nominal", title=DEPARTMENT),
            alt.Tooltip(SALARY_F, type="quantitative", title=SALARY, format="$,.0f"),
        ],
    )
)

# IQR marker — thick vertical rule from Q1 to Q3
quartile_rule = (
    base.transform_aggregate(q1=f"q1({SALARY_F})", q3=f"q3({SALARY_F})", groupby=[DEPT_F])
    .mark_rule(color=INK, strokeWidth=4)
    .encode(y="q1:Q", y2="q3:Q")
)

# Median line — horizontal rule at the median, contrasts against the IQR bar
median_line = (
    base.transform_aggregate(med=f"median({SALARY_F})", groupby=[DEPT_F])
    .mark_rule(color=PAGE_BG, strokeWidth=3)
    .encode(
        y=alt.Y("med:Q"),
        tooltip=[
            alt.Tooltip(DEPT_F, type="nominal", title=DEPARTMENT),
            alt.Tooltip("med:Q", title="Median Salary", format="$,.0f"),
        ],
    )
)

# Title — 43 chars, below 67-char threshold so fontSize=16 is fine
title_str = "violin-basic · python · altair · anyplot.ai"
n_chars = len(title_str)
ratio = 67 / n_chars if n_chars > 67 else 1.0
title_fontsize = max(11, round(16 * ratio))

# Chart — four violin panels faceted side-by-side; dept ordering tells salary story
chart = (
    alt.layer(violin, quartile_rule, median_line)
    .facet(
        column=alt.Column(
            DEPT_F,
            type="nominal",
            header=alt.Header(labelFontSize=16, labelOrient="bottom", title=None, labelPadding=12, labelColor=INK_SOFT),
            sort=dept_order,
        )
    )
    .resolve_scale(x="independent")
    .properties(background=PAGE_BG, title=alt.Title(title_str, fontSize=title_fontsize, anchor="middle", color=INK))
    .configure_facet(spacing=15)
    .configure_view(stroke=None, fill=PAGE_BG, continuousWidth=160, continuousHeight=340)
    .configure_axis(
        labelFontSize=10,
        titleFontSize=12,
        labelColor=INK_SOFT,
        titleColor=INK,
        gridColor=INK,
        gridOpacity=0.12,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
    )
    .configure_title(color=INK)
)

# Save PNG + pad to exact 3200 × 1800 target (vl-convert pads title/axis outside view dims)
TW, TH = 3200, 1800
chart.save(f"plot-{THEME}.png", scale_factor=4.0)

_img = Image.open(f"plot-{THEME}.png").convert("RGB")
_w, _h = _img.size
if (_w, _h) != (TW, TH):
    # Scale an overshoot down as a whole (never crop), then centre on the target canvas
    _scale = min(1.0, TW / _w, TH / _h)
    _img = _img.resize((round(_w * _scale), round(_h * _scale)), Image.LANCZOS)
    _w, _h = _img.size
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _w) // 2, (TH - _h) // 2))
    _canvas.save(f"plot-{THEME}.png")

# Save HTML
chart.save(f"plot-{THEME}.html")
