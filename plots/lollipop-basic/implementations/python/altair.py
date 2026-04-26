"""anyplot.ai
lollipop-basic: Basic Lollipop Chart
Library: altair | Python 3.13
Quality: pending | Updated: 2026-04-26
"""

import os

import altair as alt
import pandas as pd


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = INK
GRID_OPACITY = 0.10

BRAND = "#009E73"  # Okabe-Ito position 1 — ALWAYS first series

# Data — Product sales by category, sorted by value
categories = [
    "Electronics",
    "Clothing",
    "Home & Garden",
    "Sports",
    "Books",
    "Toys",
    "Beauty",
    "Automotive",
    "Food & Grocery",
    "Pet Supplies",
]
values = [425000, 312000, 287000, 234000, 198000, 176000, 152000, 134000, 118000, 95000]

df = pd.DataFrame({"category": categories, "value": values})
df = df.sort_values("value", ascending=False).reset_index(drop=True)

# Stems (vertical lines from baseline to value)
stems = (
    alt.Chart(df)
    .mark_rule(color=BRAND, strokeWidth=4)
    .encode(
        x=alt.X("category:N", sort="-y", title="Category", axis=alt.Axis(labelAngle=-35)),
        y=alt.Y("value:Q", title="Sales (USD)", axis=alt.Axis(format="$,.0f")),
    )
)

# Dots at the top of each stem
dots = (
    alt.Chart(df)
    .mark_circle(color=BRAND, size=550, opacity=1, stroke=PAGE_BG, strokeWidth=2)
    .encode(
        x=alt.X("category:N", sort="-y"),
        y=alt.Y("value:Q"),
        tooltip=[alt.Tooltip("category:N", title="Category"), alt.Tooltip("value:Q", title="Sales", format="$,.0f")],
    )
)

chart = (
    (stems + dots)
    .properties(
        width=1600,
        height=900,
        background=PAGE_BG,
        title=alt.Title(
            "Product Sales by Category · lollipop-basic · altair · anyplot.ai",
            fontSize=28,
            anchor="start",
            color=INK,
            offset=20,
        ),
    )
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_axis(
        domainColor=INK_SOFT,
        domainWidth=1,
        tickColor=INK_SOFT,
        gridColor=GRID,
        gridOpacity=GRID_OPACITY,
        gridWidth=1,
        labelColor=INK_SOFT,
        labelFontSize=18,
        titleColor=INK,
        titleFontSize=22,
        titlePadding=18,
    )
    .configure_axisX(grid=False, labelPadding=8)
    .configure_axisY(grid=True, labelPadding=8)
    .configure_title(color=INK, fontWeight="bold")
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
