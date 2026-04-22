""" pyplots.ai
line-filled: Filled Line Plot
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Website traffic over a month
np.random.seed(42)
days = np.arange(1, 31)
# Simulate daily visitors with weekly patterns and growth trend
base = 5000 + days * 100  # Growth trend
weekly_pattern = 800 * np.sin(2 * np.pi * days / 7)  # Weekly cycle
noise = np.random.normal(0, 300, len(days))
visitors = base + weekly_pattern + noise
visitors = np.maximum(visitors, 1000)  # Ensure positive values

df = pd.DataFrame({"Day": days, "Visitors": visitors})

# Create filled line chart (area chart)
chart = (
    alt.Chart(df)
    .mark_area(
        line={"color": "#306998", "strokeWidth": 3},
        color=alt.Gradient(
            gradient="linear",
            stops=[
                alt.GradientStop(color="rgba(48, 105, 152, 0.4)", offset=0),
                alt.GradientStop(color="rgba(48, 105, 152, 0.1)", offset=1),
            ],
            x1=1,
            x2=1,
            y1=1,
            y2=0,
        ),
    )
    .encode(
        x=alt.X("Day:Q", title="Day of Month", axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
        y=alt.Y("Visitors:Q", title="Daily Visitors", axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
        tooltip=["Day:Q", "Visitors:Q"],
    )
    .properties(
        width=1600, height=900, title=alt.Title("line-filled · altair · pyplots.ai", fontSize=28, anchor="middle")
    )
    .configure_axis(grid=True, gridOpacity=0.3, gridDash=[3, 3])
    .configure_view(strokeWidth=0)
)

# Save as PNG and HTML
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
