""" pyplots.ai
scatter-color-mapped: Color-Mapped Scatter Plot
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - simulate temperature readings at geographic locations
np.random.seed(42)
n_points = 150

# Create spatial coordinates with clustered patterns
x = np.concatenate([np.random.normal(20, 8, 50), np.random.normal(60, 10, 50), np.random.normal(40, 12, 50)])
y = np.concatenate([np.random.normal(30, 8, 50), np.random.normal(70, 10, 50), np.random.normal(50, 15, 50)])

# Third variable: intensity/temperature that correlates with position
intensity = 0.3 * x + 0.5 * y + np.random.normal(0, 8, n_points)
intensity = (intensity - intensity.min()) / (intensity.max() - intensity.min()) * 100  # Scale 0-100

df = pd.DataFrame({"X Position": x, "Y Position": y, "Intensity": intensity})

# Create color-mapped scatter plot
chart = (
    alt.Chart(df)
    .mark_circle(size=180, opacity=0.75, strokeWidth=0.5, stroke="#333333")
    .encode(
        x=alt.X("X Position:Q", title="X Position (units)", scale=alt.Scale(nice=True)),
        y=alt.Y("Y Position:Q", title="Y Position (units)", scale=alt.Scale(nice=True)),
        color=alt.Color(
            "Intensity:Q",
            title="Intensity",
            scale=alt.Scale(scheme="viridis"),
            legend=alt.Legend(
                titleFontSize=18, labelFontSize=16, symbolSize=200, gradientLength=300, gradientThickness=20
            ),
        ),
        tooltip=["X Position:Q", "Y Position:Q", "Intensity:Q"],
    )
    .properties(
        width=1600,
        height=900,
        title=alt.Title("scatter-color-mapped · altair · pyplots.ai", fontSize=28, anchor="middle"),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, gridOpacity=0.3, gridDash=[3, 3])
    .configure_view(strokeWidth=0)
)

# Save as PNG (4800 x 2700 px with scale_factor=3)
chart.save("plot.png", scale_factor=3.0)

# Save as HTML for interactivity
chart.save("plot.html")
