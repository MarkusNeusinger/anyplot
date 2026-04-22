""" pyplots.ai
line-basic: Basic Line Plot
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Monthly temperature readings over a year
np.random.seed(42)
months = pd.date_range(start="2024-01-01", periods=12, freq="MS")
# Simulate temperature pattern (cold in winter, warm in summer)
base_temp = 15 + 12 * np.sin((np.arange(12) - 3) * np.pi / 6)
temperature = base_temp + np.random.randn(12) * 2

df = pd.DataFrame({"Month": months, "Temperature": temperature})

# Plot
chart = (
    alt.Chart(df)
    .mark_line(strokeWidth=4, color="#306998")
    .encode(
        x=alt.X("Month:T", title="Month", axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
        y=alt.Y("Temperature:Q", title="Temperature (°C)", axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
    )
    .properties(width=1600, height=900, title=alt.Title("line-basic · altair · pyplots.ai", fontSize=28))
)

# Add points to enhance visibility
points = alt.Chart(df).mark_point(size=200, color="#306998", filled=True).encode(x="Month:T", y="Temperature:Q")

# Combine line and points with subtle grid
final_chart = (chart + points).configure_axis(gridColor="#E0E0E0", gridOpacity=0.3).configure_view(strokeWidth=0)

# Save
final_chart.save("plot.png", scale_factor=3.0)
final_chart.save("plot.html")
