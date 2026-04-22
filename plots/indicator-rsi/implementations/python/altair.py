""" pyplots.ai
indicator-rsi: RSI Technical Indicator Chart
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-07
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Generate realistic RSI data from simulated price movements
np.random.seed(42)
n_periods = 120
dates = pd.date_range(start="2024-01-01", periods=n_periods, freq="D")

# Simulate price changes to calculate RSI
price_changes = np.random.randn(n_periods) * 2

# Calculate RSI using standard 14-period lookback
lookback = 14
gains = np.zeros(n_periods)
losses = np.zeros(n_periods)

for i in range(1, n_periods):
    change = price_changes[i]
    if change > 0:
        gains[i] = change
    else:
        losses[i] = abs(change)

# Smoothed averages using exponential moving average style
avg_gain = np.zeros(n_periods)
avg_loss = np.zeros(n_periods)
avg_gain[lookback] = np.mean(gains[1 : lookback + 1])
avg_loss[lookback] = np.mean(losses[1 : lookback + 1])

for i in range(lookback + 1, n_periods):
    avg_gain[i] = (avg_gain[i - 1] * (lookback - 1) + gains[i]) / lookback
    avg_loss[i] = (avg_loss[i - 1] * (lookback - 1) + losses[i]) / lookback

# Calculate RSI
with np.errstate(divide="ignore", invalid="ignore"):
    rs = np.where(avg_loss != 0, avg_gain / avg_loss, 0)
    rsi = np.where(avg_loss != 0, 100 - (100 / (1 + rs)), 100)
rsi[:lookback] = 50  # Fill initial values with neutral

df = pd.DataFrame({"date": dates, "rsi": rsi})

# Overbought zone (70-100)
overbought_df = pd.DataFrame({"y": [70], "y2": [100]})

# Oversold zone (0-30)
oversold_df = pd.DataFrame({"y": [0], "y2": [30]})

# Overbought zone shading (red/orange tint)
overbought_zone = (
    alt.Chart(overbought_df).mark_rect(opacity=0.15, color="#E74C3C").encode(y=alt.Y("y:Q"), y2=alt.Y2("y2:Q"))
)

# Oversold zone shading (green tint)
oversold_zone = (
    alt.Chart(oversold_df).mark_rect(opacity=0.15, color="#27AE60").encode(y=alt.Y("y:Q"), y2=alt.Y2("y2:Q"))
)

# Horizontal threshold lines
threshold_df = pd.DataFrame({"y": [30, 50, 70], "label": ["Oversold (30)", "Neutral (50)", "Overbought (70)"]})

threshold_lines = (
    alt.Chart(threshold_df)
    .mark_rule(strokeDash=[8, 4], strokeWidth=2)
    .encode(
        y=alt.Y("y:Q"),
        color=alt.Color(
            "label:N",
            scale=alt.Scale(
                domain=["Oversold (30)", "Neutral (50)", "Overbought (70)"], range=["#27AE60", "#95A5A6", "#E74C3C"]
            ),
            legend=alt.Legend(title="Threshold Lines", orient="top-right", titleFontSize=16, labelFontSize=14),
        ),
    )
)

# RSI line chart
rsi_line = (
    alt.Chart(df)
    .mark_line(strokeWidth=3, color="#306998")
    .encode(
        x=alt.X("date:T", title="Date", axis=alt.Axis(format="%b %Y")),
        y=alt.Y("rsi:Q", title="RSI Value", scale=alt.Scale(domain=[0, 100])),
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%Y-%m-%d"),
            alt.Tooltip("rsi:Q", title="RSI", format=".1f"),
        ],
    )
)

# Combine all layers
chart = (
    alt.layer(overbought_zone, oversold_zone, threshold_lines, rsi_line)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "indicator-rsi · altair · pyplots.ai",
            fontSize=28,
            anchor="middle",
            subtitle="14-Period RSI with Overbought/Oversold Zones",
            subtitleFontSize=18,
        ),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, gridOpacity=0.3)
    .configure_view(strokeWidth=0)
)

# Save outputs
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
