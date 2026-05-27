""" anyplot.ai
lollipop-grouped: Grouped Lollipop Chart
Library: altair 6.1.0 | Python 3.13.13
Quality: 99/100 | Updated: 2026-05-17
"""

import os
import sys


# Remove current directory from path to avoid shadowing the altair package
sys.path = [p for p in sys.path if os.path.abspath(p) != os.getcwd()]

import altair as alt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

# Data: Quarterly performance metrics across regions
np.random.seed(42)

categories = ["North", "South", "East", "West"]
series = ["Q1 2024", "Q2 2024", "Q3 2024"]

data = []
base_values = {"North": 85, "South": 72, "East": 78, "West": 90}
quarter_adjustments = {"Q1 2024": 0, "Q2 2024": 5, "Q3 2024": 10}

for cat in categories:
    for ser in series:
        value = base_values[cat] + quarter_adjustments[ser] + np.random.randint(-8, 12)
        data.append({"category": cat, "series": ser, "value": value})

df = pd.DataFrame(data)

# Create offset positions for grouped lollipops
df["series_order"] = df["series"].map({s: i for i, s in enumerate(series)})
df["x_offset"] = (df["series_order"] - (len(series) - 1) / 2) * 0.25

# Color scale using Okabe-Ito palette
color_scale = alt.Scale(domain=series, range=IMPRINT[: len(series)])

# Base chart
base = alt.Chart(df).encode(
    x=alt.X("category:N", title="Region", axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
    xOffset="x_offset:Q",
    color=alt.Color(
        "series:N",
        scale=color_scale,
        title="Quarter",
        legend=alt.Legend(titleFontSize=18, labelFontSize=16, symbolSize=200),
    ),
    tooltip=["category:N", "series:N", alt.Tooltip("value:Q", format=".0f")],
)

# Stems (lines from 0 to value)
stems = base.mark_rule(strokeWidth=4).encode(
    y=alt.Y(
        "value:Q",
        title="Performance Score",
        axis=alt.Axis(labelFontSize=18, titleFontSize=22),
        scale=alt.Scale(domain=[0, 110]),
    ),
    y2=alt.datum(0),
)

# Markers (circular dots)
markers = base.mark_circle(size=400, opacity=1).encode(y=alt.Y("value:Q"))

# Combine stems and markers
chart = (
    (stems + markers)
    .properties(
        width=1600,
        height=900,
        background=PAGE_BG,
        title=alt.Title("lollipop-grouped · altair · pyplots.ai", fontSize=28, anchor="middle"),
    )
    .configure_axis(
        grid=True,
        gridOpacity=0.10,
        gridColor=INK_SOFT,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_title(color=INK)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save outputs
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
