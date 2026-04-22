""" pyplots.ai
histogram-stepwise: Step Histogram
Library: altair 6.0.0 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-30
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Generate sample data with interesting distribution
np.random.seed(42)
values = np.concatenate(
    [
        np.random.normal(25, 5, 300),  # First mode
        np.random.normal(45, 8, 200),  # Second mode
    ]
)

# Create histogram bins manually for step visualization
counts, bin_edges = np.histogram(values, bins=25)

# Build step data: for each bin, we need points at left and right edges
step_x = []
step_y = []
for i, count in enumerate(counts):
    step_x.extend([bin_edges[i], bin_edges[i + 1]])
    step_y.extend([count, count])

# Close the path at the ends (go to zero)
step_x = [bin_edges[0]] + step_x + [bin_edges[-1]]
step_y = [0] + step_y + [0]

df = pd.DataFrame({"Measurement Value": step_x, "Frequency": step_y, "order": range(len(step_x))})

# Create step histogram using line mark
chart = (
    alt.Chart(df)
    .mark_line(strokeWidth=3, color="#306998", interpolate="step-after")
    .encode(
        x=alt.X("Measurement Value:Q", title="Measurement Value"),
        y=alt.Y("Frequency:Q", title="Frequency"),
        order="order:O",
    )
    .properties(
        width=1600,
        height=900,
        title=alt.Title("histogram-stepwise · altair · pyplots.ai", fontSize=28, anchor="middle"),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, gridOpacity=0.3)
    .configure_view(strokeWidth=0)
)

# Save as PNG (4800 x 2700 with scale_factor=3)
chart.save("plot.png", scale_factor=3.0)

# Save as HTML for interactivity
chart.save("plot.html")
