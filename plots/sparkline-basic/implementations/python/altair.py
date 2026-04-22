""" pyplots.ai
sparkline-basic: Basic Sparkline
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Simulated daily sales over 60 days with trend and fluctuations
np.random.seed(42)
n_points = 60
base_trend = np.linspace(100, 150, n_points)
noise = np.random.randn(n_points) * 10
values = base_trend + noise

# Add realistic business patterns (weekly dips on weekends)
for i in range(n_points):
    if i % 7 in [5, 6]:
        values[i] *= 0.85

df = pd.DataFrame({"x": range(n_points), "value": values})

# Find min/max points for highlights
min_idx = df["value"].idxmin()
max_idx = df["value"].idxmax()
highlights = df.iloc[[min_idx, max_idx]].copy()
highlights["type"] = ["min", "max"]

# First and last point markers
endpoints = df.iloc[[0, -1]].copy()

# Sparkline - minimal line chart without axes or labels
line = (
    alt.Chart(df)
    .mark_line(strokeWidth=3, color="#306998")
    .encode(x=alt.X("x:Q", axis=None), y=alt.Y("value:Q", axis=None, scale=alt.Scale(zero=False)))
)

# Endpoint markers (subtle gray)
endpoint_markers = (
    alt.Chart(endpoints)
    .mark_circle(size=200, color="#888888")
    .encode(x=alt.X("x:Q", axis=None), y=alt.Y("value:Q", axis=None, scale=alt.Scale(zero=False)))
)

# Highlight min (Python Yellow) and max (Python Blue) points
points = (
    alt.Chart(highlights)
    .mark_circle(size=400)
    .encode(
        x=alt.X("x:Q", axis=None),
        y=alt.Y("value:Q", axis=None, scale=alt.Scale(zero=False)),
        color=alt.Color("type:N", scale=alt.Scale(domain=["min", "max"], range=["#FFD43B", "#306998"]), legend=None),
    )
)

# Combine layers
chart = (
    (line + endpoint_markers + points)
    .properties(
        width=1600,
        height=300,  # Compact aspect ratio ~5:1
        title=alt.Title("sparkline-basic · altair · pyplots.ai", fontSize=28),
    )
    .configure_view(strokeWidth=0)  # Remove chart border
)

# Save as PNG and HTML
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
