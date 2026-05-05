"""anyplot.ai
waffle-basic: Basic Waffle Chart
Library: altair | Python 3.13
Quality: pending | Created: 2025-05-05
"""

import os

import altair as alt
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first series is #009E73)
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00"]

# Data - Budget allocation with 5 categories including a small one
categories = ["Engineering", "Marketing", "Operations", "Design", "Legal"]
values = [40, 28, 18, 10, 4]  # Percentages (sum to 100)

# Build 10x10 grid (100 squares, each = 1%)
squares = []
square_idx = 0
for cat, val, color in zip(categories, values, OKABE_ITO, strict=True):
    for _ in range(val):
        row = square_idx // 10
        col = square_idx % 10
        squares.append({"category": cat, "row": row, "col": col, "color": color})
        square_idx += 1

df = pd.DataFrame(squares)

# Create waffle chart
chart = (
    alt.Chart(df)
    .mark_rect(stroke="white", strokeWidth=2, cornerRadius=4)
    .encode(
        x=alt.X("col:O", axis=None),
        y=alt.Y("row:O", axis=None, sort="descending"),
        color=alt.Color(
            "category:N",
            scale=alt.Scale(domain=categories, range=OKABE_ITO),
            legend=alt.Legend(
                title="Category",
                titleFontSize=22,
                labelFontSize=18,
                symbolSize=300,
                orient="right",
                labelExpr="datum.label + ' (' + {"
                + ", ".join([f"'{cat}': '{val}%'" for cat, val in zip(categories, values, strict=True)])
                + "}[datum.label] + ')'",
            ),
        ),
        tooltip=["category:N"],
    )
    .properties(
        width=1600,
        height=900,
        background=PAGE_BG,
        title=alt.Title(
            "Budget Allocation · waffle-basic · altair · anyplot.ai", fontSize=28, anchor="middle", color=INK
        ),
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
    .configure_axis(
        domainColor=INK_SOFT, tickColor=INK_SOFT, gridColor=INK, gridOpacity=0.10, labelColor=INK_SOFT, titleColor=INK
    )
    .configure_title(color=INK)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save outputs
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
