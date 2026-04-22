""" pyplots.ai
stem-basic: Basic Stem Plot
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Discrete signal samples (simulating a damped oscillation)
np.random.seed(42)
x = np.arange(0, 30)
y = np.exp(-x / 10) * np.cos(x * 0.8) + np.random.randn(30) * 0.05

df = pd.DataFrame({"x": x, "y": y, "y0": 0})

# Create stems (vertical lines from baseline y=0 to each data point)
stems = (
    alt.Chart(df)
    .mark_rule(color="#306998", strokeWidth=2.5, opacity=0.8)
    .encode(
        x=alt.X("x:Q", title="Sample Index", axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
        y=alt.Y("y0:Q"),
        y2=alt.Y2("y:Q"),
    )
)

# Create markers at the top of each stem
markers = (
    alt.Chart(df)
    .mark_circle(color="#306998", size=300, stroke="white", strokeWidth=2)
    .encode(
        x=alt.X("x:Q"),
        y=alt.Y("y:Q", title="Amplitude", axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
        tooltip=[alt.Tooltip("x:Q", title="Sample"), alt.Tooltip("y:Q", title="Amplitude", format=".3f")],
    )
)

# Create baseline at y=0
baseline = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(color="#333333", strokeWidth=2).encode(y=alt.Y("y:Q"))

# Combine stems, markers, and baseline
chart = (
    (baseline + stems + markers)
    .properties(
        width=1600, height=900, title=alt.Title("stem-basic · altair · pyplots.ai", fontSize=28, anchor="middle")
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, grid=True, gridOpacity=0.3, gridDash=[4, 4])
    .configure_view(strokeWidth=0)
)

# Save as PNG (scale_factor=3 to get 4800x2700)
chart.save("plot.png", scale_factor=3.0)

# Save as HTML for interactive version
chart.save("plot.html")
