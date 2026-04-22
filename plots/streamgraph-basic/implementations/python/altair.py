""" pyplots.ai
streamgraph-basic: Basic Stream Graph
Library: altair 6.0.0 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-23
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Monthly streaming hours by music genre over two years
np.random.seed(42)

months = pd.date_range(start="2022-01-01", periods=24, freq="MS")
genres = ["Pop", "Rock", "Hip-Hop", "Electronic", "Jazz", "Classical"]

# Generate smooth, realistic streaming data for each genre
data = []
for genre in genres:
    # Base value varies by genre popularity
    base = {"Pop": 150, "Rock": 100, "Hip-Hop": 120, "Electronic": 80, "Jazz": 40, "Classical": 30}[genre]
    # Generate smooth curve with seasonal variation and organic growth
    trend = np.linspace(0, 20, 24)  # Slight growth over time
    seasonal = 30 * np.sin(np.linspace(0, 4 * np.pi, 24))
    noise = np.random.randn(24).cumsum() * 5
    values = base + trend + seasonal + noise
    values = np.maximum(values, 10)  # Ensure positive values
    for i, month in enumerate(months):
        data.append({"time": month, "category": genre, "value": values[i]})

df = pd.DataFrame(data)

# Color palette - Python Blue/Yellow first, then colorblind-safe additions
colors = ["#306998", "#FFD43B", "#E377C2", "#2CA02C", "#9467BD", "#FF7F0E"]

# Create streamgraph using area mark with center baseline (stack='center')
chart = (
    alt.Chart(df)
    .mark_area(
        interpolate="basis",  # Basis spline for smooth flowing curves
        opacity=0.85,
    )
    .encode(
        x=alt.X(
            "time:T", title="Time", axis=alt.Axis(format="%b %Y", labelFontSize=18, titleFontSize=22, labelAngle=-45)
        ),
        y=alt.Y(
            "value:Q",
            title="Streaming Hours (millions)",
            stack="center",  # Center baseline for streamgraph aesthetic
            axis=alt.Axis(
                labelFontSize=18,
                titleFontSize=22,
                labels=False,  # Hide y-axis labels for streamgraph aesthetic
                ticks=False,
            ),
        ),
        color=alt.Color(
            "category:N",
            title="Genre",
            scale=alt.Scale(domain=genres, range=colors),
            legend=alt.Legend(titleFontSize=20, labelFontSize=18, orient="right"),
        ),
        order=alt.Order("category:N"),
        tooltip=["time:T", "category:N", alt.Tooltip("value:Q", format=".1f")],
    )
    .properties(
        width=1600, height=900, title=alt.Title("streamgraph-basic · altair · pyplots.ai", fontSize=28, anchor="middle")
    )
    .configure_axis(grid=False)  # Remove grid for cleaner streamgraph
    .configure_view(strokeWidth=0)
)

# Save as PNG (4800 x 2700 px: 1600 * 3 = 4800, 900 * 3 = 2700)
chart.save("plot.png", scale_factor=3.0)

# Save interactive HTML version
chart.interactive().save("plot.html")
