""" anyplot.ai
dumbbell-basic: Basic Dumbbell Chart
Library: altair 6.1.0 | Python 3.14.4
Quality: 89/100 | Updated: 2026-04-26
"""

import os

import altair as alt
import pandas as pd


# Theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette positions 1 and 2
COLOR_BEFORE = "#009E73"
COLOR_AFTER = "#D55E00"

# Data — Employee satisfaction scores before and after policy changes
data = pd.DataFrame(
    {
        "category": [
            "Customer Support",
            "Engineering",
            "Sales",
            "Marketing",
            "HR",
            "Finance",
            "Operations",
            "Legal",
            "R&D",
            "IT",
        ],
        "Before": [52, 61, 58, 65, 72, 68, 55, 74, 63, 59],
        "After": [78, 82, 76, 81, 85, 79, 64, 81, 69, 64],
    }
)
data["difference"] = data["After"] - data["Before"]
data = data.sort_values("difference", ascending=True)

# Long-form data for the two dot series
dots_data = pd.melt(
    data, id_vars=["category", "difference"], value_vars=["Before", "After"], var_name="period", value_name="score"
)

x_scale = alt.Scale(domain=[45, 90])
y_sort = alt.EncodingSortField(field="difference", order="ascending")

# Connecting lines (theme-adaptive subtle ink)
lines = (
    alt.Chart(data)
    .mark_rule(strokeWidth=3, color=INK_SOFT, opacity=0.55)
    .encode(y=alt.Y("category:N", sort=y_sort, title=None), x=alt.X("Before:Q", scale=x_scale), x2=alt.X2("After:Q"))
)

# Dots for Before / After values
dots = (
    alt.Chart(dots_data)
    .mark_circle(size=420, opacity=1.0, stroke=PAGE_BG, strokeWidth=2)
    .encode(
        y=alt.Y("category:N", sort=y_sort, title=None),
        x=alt.X("score:Q", scale=x_scale, title="Employee Satisfaction Score (%)"),
        color=alt.Color(
            "period:N",
            scale=alt.Scale(domain=["Before", "After"], range=[COLOR_BEFORE, COLOR_AFTER]),
            legend=alt.Legend(title="Policy Change", labelFontSize=16, titleFontSize=18),
        ),
        tooltip=["category:N", "period:N", "score:Q"],
    )
)

chart = (
    (lines + dots)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "Employee Satisfaction · dumbbell-basic · altair · anyplot.ai",
            fontSize=28,
            color=INK,
            anchor="start",
            offset=20,
        ),
        background=PAGE_BG,
    )
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_axis(
        labelFontSize=18,
        titleFontSize=22,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
    )
    .configure_title(color=INK)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK, padding=12)
)

chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
