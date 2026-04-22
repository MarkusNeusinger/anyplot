""" pyplots.ai
histogram-2d: 2D Histogram Heatmap
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

import altair as alt
import numpy as np
import pandas as pd


# Data: Bivariate normal distribution with correlation
np.random.seed(42)
n_points = 2000
mean = [0, 0]
cov = [[1, 0.7], [0.7, 1]]  # Correlation of 0.7
data = np.random.multivariate_normal(mean, cov, n_points)
df = pd.DataFrame({"x": data[:, 0], "y": data[:, 1]})

# Create 2D histogram heatmap using mark_rect with binning
chart = (
    alt.Chart(df)
    .mark_rect()
    .encode(
        x=alt.X("x:Q", bin=alt.Bin(maxbins=40), title="X Value"),
        y=alt.Y("y:Q", bin=alt.Bin(maxbins=40), title="Y Value"),
        color=alt.Color(
            "count():Q",
            scale=alt.Scale(scheme="viridis"),
            title="Count",
            legend=alt.Legend(titleFontSize=18, labelFontSize=16, gradientLength=300, gradientThickness=20),
        ),
    )
    .properties(
        width=1400,
        height=800,
        title=alt.Title("histogram-2d \u00b7 altair \u00b7 pyplots.ai", fontSize=28, anchor="middle"),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, tickSize=8)
    .configure_view(strokeWidth=0)
)

# Save as PNG (scale_factor=3 for 4200x2400, close to target 4800x2700)
chart.save("plot.png", scale_factor=3.0)

# Save as HTML for interactivity
chart.save("plot.html")
