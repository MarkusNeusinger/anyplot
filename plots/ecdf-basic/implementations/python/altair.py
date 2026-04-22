""" pyplots.ai
ecdf-basic: Basic ECDF Plot
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import altair as alt
import numpy as np
import pandas as pd


# Data
np.random.seed(42)
values = np.random.normal(loc=50, scale=15, size=200)

# Sort values and compute ECDF
sorted_values = np.sort(values)
ecdf_y = np.arange(1, len(sorted_values) + 1) / len(sorted_values)

df = pd.DataFrame({"value": sorted_values, "ecdf": ecdf_y})

# Chart
chart = (
    alt.Chart(df)
    .mark_line(interpolate="step-after", strokeWidth=3, color="#306998")
    .encode(
        x=alt.X("value:Q", title="Value", scale=alt.Scale(nice=True)),
        y=alt.Y("ecdf:Q", title="Cumulative Proportion", scale=alt.Scale(domain=[0, 1])),
        tooltip=["value:Q", "ecdf:Q"],
    )
    .properties(width=1600, height=900, title=alt.Title("ecdf-basic · altair · pyplots.ai", fontSize=28))
    .configure_axis(labelFontSize=18, titleFontSize=22, gridOpacity=0.3, gridDash=[4, 4])
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
