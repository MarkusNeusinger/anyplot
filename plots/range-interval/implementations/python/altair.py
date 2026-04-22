""" pyplots.ai
range-interval: Range Interval Chart
Library: altair 6.0.0 | Python 3.13.11
Quality: 93/100 | Created: 2026-01-09
"""

import altair as alt
import pandas as pd


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
    color=alt.value("#306998"),
    opacity=alt.value(0.7),
    tooltip=[
        alt.Tooltip("month:N", title="Month"),
        alt.Tooltip("min_temp:Q", title="Min Temp (°C)"),
        alt.Tooltip("max_temp:Q", title="Max Temp (°C)"),
        alt.Tooltip("mid_temp:Q", title="Midpoint (°C)", format=".1f"),
    ],
)

# Min endpoint markers
min_points = base.mark_point(size=200, filled=True, shape="circle").encode(x="min_temp:Q", color=alt.value("#1a4971"))

# Max endpoint markers
max_points = base.mark_point(size=200, filled=True, shape="circle").encode(x="max_temp:Q", color=alt.value("#FFD43B"))

# Midpoint markers
mid_points = base.mark_point(size=80, filled=True, shape="diamond").encode(
    x="mid_temp:Q", color=alt.value("#ffffff"), stroke=alt.value("#306998"), strokeWidth=alt.value(2)
)

# Layer all elements
chart = (
    alt.layer(bars, min_points, max_points, mid_points)
    .properties(
        width=1600, height=900, title=alt.Title("range-interval · altair · pyplots.ai", fontSize=28, anchor="middle")
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, gridOpacity=0.3)
    .configure_view(strokeWidth=0)
)

# Save as PNG (scale_factor=3 for 4800x2700)
chart.save("plot.png", scale_factor=3.0)

# Save as HTML for interactivity
chart.save("plot.html")
