""" pyplots.ai
line-timeseries-rolling: Time Series with Rolling Average Overlay
Library: altair 6.0.0 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-30
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Daily temperature readings over 6 months with 7-day rolling average
np.random.seed(42)
dates = pd.date_range("2024-01-01", periods=180, freq="D")

# Simulate temperature with seasonal trend + noise (winter to early summer)
day_of_year = np.arange(180)
# Temperature rises from winter (Jan) toward summer (Jun)
seasonal_trend = 10 + 12 * np.sin(2 * np.pi * (day_of_year - 90) / 365)
noise = np.random.normal(0, 3, 180)
raw_values = seasonal_trend + noise

df = pd.DataFrame({"date": dates, "value": raw_values})

# Calculate 7-day rolling average
df["rolling_avg"] = df["value"].rolling(window=7, center=True).mean()

# Prepare data for layered chart with proper legend
df_long = pd.melt(
    df, id_vars=["date"], value_vars=["value", "rolling_avg"], var_name="series", value_name="temperature"
)

# Rename series for cleaner legend
df_long["series"] = df_long["series"].map({"value": "Raw Data", "rolling_avg": "7-Day Rolling Average"})

# Remove NaN values from rolling average
df_long = df_long.dropna()

# Create chart with both lines
chart = (
    alt.Chart(df_long)
    .mark_line()
    .encode(
        x=alt.X("date:T", title="Date", axis=alt.Axis(labelFontSize=18, titleFontSize=22, format="%b %d")),
        y=alt.Y(
            "temperature:Q",
            title="Temperature (°C)",
            axis=alt.Axis(labelFontSize=18, titleFontSize=22),
            scale=alt.Scale(zero=False),
        ),
        color=alt.Color(
            "series:N",
            scale=alt.Scale(domain=["Raw Data", "7-Day Rolling Average"], range=["#306998", "#FFD43B"]),
            legend=alt.Legend(title="Series", labelFontSize=16, titleFontSize=18, orient="top-right", offset=10),
        ),
        strokeWidth=alt.condition(alt.datum.series == "7-Day Rolling Average", alt.value(4), alt.value(1.5)),
        opacity=alt.condition(alt.datum.series == "7-Day Rolling Average", alt.value(1.0), alt.value(0.5)),
    )
    .properties(
        width=1600,
        height=900,
        title=alt.Title("line-timeseries-rolling · altair · pyplots.ai", fontSize=28, anchor="middle"),
    )
    .configure_axis(gridOpacity=0.3, gridDash=[4, 4])
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
