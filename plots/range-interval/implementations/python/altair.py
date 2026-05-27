""" anyplot.ai
range-interval: Range Interval Chart
Library: altair 6.1.0 | Python 3.13.13
Quality: 99/100 | Updated: 2026-05-18
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

# Okabe-Ito palette
BRAND = "#009E73"  # First series - always
SECONDARY = "#C475FD"
ACCENT = "#4467A3"

# Data: Monthly temperature ranges (°C) for a temperate city
data = pd.DataFrame(
    {
        "month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "min_temp": [-2, -1, 3, 7, 12, 16, 18, 17, 13, 8, 3, 0],
        "max_temp": [5, 7, 12, 18, 23, 27, 30, 29, 24, 17, 10, 6],
    }
)

# Calculate midpoint for reference
data["mid_temp"] = (data["min_temp"] + data["max_temp"]) / 2

# Month order for proper sorting
month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Create base chart
base = alt.Chart(data).encode(
    y=alt.Y("month:N", sort=month_order, title="Month", axis=alt.Axis(labelFontSize=18, titleFontSize=22))
)

# Range bars (horizontal bars from min to max)
bars = base.mark_bar(height=25, cornerRadius=4).encode(
    x=alt.X("min_temp:Q", title="Temperature (°C)", axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
    x2="max_temp:Q",
    color=alt.value(BRAND),
    opacity=alt.value(0.8),
    tooltip=[
        alt.Tooltip("month:N", title="Month"),
        alt.Tooltip("min_temp:Q", title="Min Temp (°C)"),
        alt.Tooltip("max_temp:Q", title="Max Temp (°C)"),
        alt.Tooltip("mid_temp:Q", title="Midpoint (°C)", format=".1f"),
    ],
)

# Min endpoint markers
min_points = base.mark_point(size=200, filled=True, shape="circle").encode(x="min_temp:Q", color=alt.value(SECONDARY))

# Max endpoint markers
max_points = base.mark_point(size=200, filled=True, shape="circle").encode(x="max_temp:Q", color=alt.value(ACCENT))

# Midpoint markers
mid_points = base.mark_point(size=80, filled=True, shape="diamond").encode(
    x="mid_temp:Q", color=alt.value(INK), stroke=alt.value(INK_SOFT), strokeWidth=alt.value(2)
)

# Layer all elements
chart = (
    alt.layer(bars, min_points, max_points, mid_points)
    .properties(
        width=1600,
        height=900,
        background=PAGE_BG,
        title=alt.Title("range-interval · python · altair · anyplot.ai", fontSize=28, anchor="middle", color=INK),
    )
    .configure_axis(
        labelFontSize=18,
        titleFontSize=22,
        labelColor=INK_SOFT,
        titleColor=INK,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridOpacity=0.10,
        gridColor=INK,
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, strokeWidth=1)
    .configure_title(color=INK, fontSize=28)
)

# Save as PNG (scale_factor=3 for 4800x2700)
chart.save(f"plot-{THEME}.png", scale_factor=3.0)

# Save as HTML for interactivity
chart.save(f"plot-{THEME}.html")
