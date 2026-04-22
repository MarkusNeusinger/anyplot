""" pyplots.ai
lollipop-grouped: Grouped Lollipop Chart
Library: altair 6.0.0 | Python 3.13.11
Quality: 94/100 | Created: 2026-01-09
"""

import altair as alt
import numpy as np
import pandas as pd


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

# Colors
colors = ["#306998", "#FFD43B", "#4CAF50"]
color_scale = alt.Scale(domain=series, range=colors)

# Base chart for stems (lines from 0 to value)
base = alt.Chart(df).encode(
    x=alt.X("category:N", title="Region", axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
    xOffset="x_offset:Q",
    color=alt.Color(
        "series:N",
        scale=color_scale,
        title="Quarter",
        legend=alt.Legend(titleFontSize=18, labelFontSize=16, symbolSize=200),
    ),
)

# Stems
stems = base.mark_rule(strokeWidth=4).encode(
    y=alt.Y(
        "value:Q",
        title="Performance Score",
        axis=alt.Axis(labelFontSize=18, titleFontSize=22),
        scale=alt.Scale(domain=[0, 110]),
    ),
    y2=alt.datum(0),
)

# Markers
markers = base.mark_circle(size=400, opacity=1).encode(y=alt.Y("value:Q"))

# Combine stems and markers
chart = (
    (stems + markers)
    .properties(
        width=1600, height=900, title=alt.Title("lollipop-grouped · altair · pyplots.ai", fontSize=28, anchor="middle")
    )
    .configure_axis(grid=True, gridOpacity=0.3)
    .configure_view(strokeWidth=0)
)

# Save outputs
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
