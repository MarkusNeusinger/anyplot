""" anyplot.ai
step-basic: Basic Step Plot
Library: altair 6.1.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-04-30
"""

import os
import sys


# Workaround: this file is named altair.py, which shadows the altair module
_cwd = os.getcwd()
if _cwd in sys.path:
    sys.path.remove(_cwd)
if "" in sys.path:
    sys.path.remove("")

import altair as alt  # noqa: E402, I001

sys.path.insert(0, _cwd)

import pandas as pd  # noqa: E402, I001

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Data — monthly cumulative software subscription revenue
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
cumulative_revenue = [12, 25, 31, 48, 52, 67, 89, 95, 108, 124, 145, 168]

df = pd.DataFrame({"Month": months, "Cumulative Revenue": cumulative_revenue})

# Step line
line = (
    alt.Chart(df)
    .mark_line(interpolate="step-after", strokeWidth=5, color=BRAND)
    .encode(
        x=alt.X("Month:N", title="Month", sort=months, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("Cumulative Revenue:Q", title="Cumulative Revenue (thousands $)"),
    )
)

# Markers at each data point
points = (
    alt.Chart(df)
    .mark_point(size=220, color=BRAND, filled=True, opacity=1.0)
    .encode(x=alt.X("Month:N", sort=months), y="Cumulative Revenue:Q")
)

# Compose and style
chart = (
    (line + points)
    .properties(
        width=1600,
        height=900,
        background=PAGE_BG,
        title=alt.Title("step-basic · altair · anyplot.ai", fontSize=28, color=INK),
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=18,
        titleFontSize=22,
    )
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
