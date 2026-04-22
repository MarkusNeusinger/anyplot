""" pyplots.ai
ridgeline-basic: Basic Ridgeline Plot
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Monthly temperature distributions for ridgeline visualization
np.random.seed(42)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

data = []
# Create realistic temperature patterns (Northern Hemisphere)
base_temps = [2, 4, 8, 14, 18, 22, 25, 24, 20, 14, 8, 4]  # Mean temp per month
temp_stds = [4, 5, 5, 4, 4, 3, 3, 3, 4, 5, 5, 4]  # Variability per month

for i, month in enumerate(months):
    temps = np.random.normal(base_temps[i], temp_stds[i], 200)
    for t in temps:
        data.append({"month": month, "temperature": t, "month_order": i})

df = pd.DataFrame(data)

# Create ridgeline using row faceting with overlap
# The overlap creates the characteristic ridge appearance
chart = (
    alt.Chart(df)
    .transform_density(
        density="temperature",
        as_=["temperature", "density"],
        groupby=["month", "month_order"],
        extent=[-15, 40],
        bandwidth=2,
    )
    .mark_area(fillOpacity=0.8, stroke="#306998", strokeWidth=2, interpolate="monotone")
    .encode(
        x=alt.X(
            "temperature:Q",
            title="Temperature (°C)",
            axis=alt.Axis(labelFontSize=18, titleFontSize=22, grid=True, gridOpacity=0.3),
            scale=alt.Scale(domain=[-15, 40]),
        ),
        y=alt.Y("density:Q", title=None, axis=None, scale=alt.Scale(domain=[0, 0.15])),
        fill=alt.Fill(
            "month_order:O", scale=alt.Scale(scheme="blues", domain=list(range(12)), reverse=True), legend=None
        ),
        row=alt.Row(
            "month:N",
            sort=months,
            header=alt.Header(labelFontSize=18, labelAngle=0, labelAlign="right", labelPadding=10, title=None),
        ),
    )
    .properties(
        width=1400,
        height=55,
        title=alt.Title(
            text="Monthly Temperature Distribution · ridgeline-basic · altair · pyplots.ai",
            fontSize=28,
            anchor="middle",
        ),
    )
    .configure_facet(spacing=-25)  # Negative spacing for overlap effect
    .configure_view(stroke=None)
    .configure_axis(labelFontSize=16, titleFontSize=20)
)

# Save as PNG (scale adjusted for ~4800x2700 target)
chart.save("plot.png", scale_factor=3.0)

# Save as interactive HTML
chart.save("plot.html")
