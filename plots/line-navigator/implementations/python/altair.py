""" pyplots.ai
line-navigator: Line Chart with Mini Navigator
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-20
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Daily sensor readings over 3 years (1095 data points)
np.random.seed(42)
dates = pd.date_range("2022-01-01", periods=1095, freq="D")

# Create realistic sensor data with trend, seasonality, and noise
trend = np.linspace(20, 35, 1095)  # Gradual increase
seasonal = 8 * np.sin(2 * np.pi * np.arange(1095) / 365)  # Yearly cycle
weekly = 2 * np.sin(2 * np.pi * np.arange(1095) / 7)  # Weekly pattern
noise = np.random.randn(1095) * 2

values = trend + seasonal + weekly + noise

df = pd.DataFrame({"date": dates, "value": values})

# Create interval selection for the navigator
brush = alt.selection_interval(encodings=["x"])

# Main chart (detail view) - shows selected range
main_chart = (
    alt.Chart(df)
    .mark_line(color="#306998", strokeWidth=2)
    .encode(
        x=alt.X("date:T", title="Date", scale=alt.Scale(domain=brush)),
        y=alt.Y("value:Q", title="Sensor Reading (°C)", scale=alt.Scale(zero=False)),
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%Y-%m-%d"),
            alt.Tooltip("value:Q", title="Value", format=".1f"),
        ],
    )
    .properties(width=1600, height=720, title=alt.Title("line-navigator · altair · pyplots.ai", fontSize=28))
)

# Navigator chart (overview) - shows full data with selection window
navigator = (
    alt.Chart(df)
    .mark_line(color="#306998", strokeWidth=1)
    .encode(x=alt.X("date:T", title=""), y=alt.Y("value:Q", title="", scale=alt.Scale(zero=False)))
    .properties(width=1600, height=135)
    .add_params(brush)
)

# Highlight selection area in navigator
selection_area = (
    alt.Chart(df)
    .mark_area(color="#FFD43B", opacity=0.3)
    .encode(x="date:T", y="value:Q", y2=alt.value(135))
    .transform_filter(brush)
)

# Combine navigator with selection highlight
navigator_with_selection = alt.layer(navigator, selection_area).properties(width=1600, height=135)

# Combine main chart and navigator vertically
# Configure styles on the final combined chart
combined = (
    alt.vconcat(main_chart, navigator_with_selection)
    .configure_view(strokeWidth=0)
    .configure_axis(labelFontSize=18, titleFontSize=22)
    .configure_title(fontSize=28)
)

# Save as PNG and HTML
combined.save("plot.png", scale_factor=3.0)
combined.save("plot.html")
