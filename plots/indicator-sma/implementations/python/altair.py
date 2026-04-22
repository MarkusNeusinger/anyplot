""" pyplots.ai
indicator-sma: Simple Moving Average (SMA) Indicator Chart
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-11
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Generate realistic stock price data with trend
np.random.seed(42)
n_days = 300
dates = pd.date_range("2025-01-01", periods=n_days, freq="D")

# Generate price with trend and volatility
returns = np.random.normal(0.0003, 0.015, n_days)
price = 100 * np.cumprod(1 + returns)

# Add some trend structure
trend = np.linspace(0, 20, n_days)
price = price + trend

df = pd.DataFrame({"date": dates, "close": price})

# Calculate SMAs
df["sma_20"] = df["close"].rolling(window=20).mean()
df["sma_50"] = df["close"].rolling(window=50).mean()
df["sma_200"] = df["close"].rolling(window=200).mean()

# Reshape data for Altair layered chart
price_df = df[["date", "close"]].copy()
price_df["series"] = "Close Price"
price_df = price_df.rename(columns={"close": "value"})

sma20_df = df[["date", "sma_20"]].copy()
sma20_df["series"] = "SMA 20"
sma20_df = sma20_df.rename(columns={"sma_20": "value"})

sma50_df = df[["date", "sma_50"]].copy()
sma50_df["series"] = "SMA 50"
sma50_df = sma50_df.rename(columns={"sma_50": "value"})

sma200_df = df[["date", "sma_200"]].copy()
sma200_df["series"] = "SMA 200"
sma200_df = sma200_df.rename(columns={"sma_200": "value"})

# Combine all series
combined_df = pd.concat([price_df, sma20_df, sma50_df, sma200_df], ignore_index=True)

# Define color scheme - Python Blue for price, distinct colors for SMAs
color_scale = alt.Scale(
    domain=["Close Price", "SMA 20", "SMA 50", "SMA 200"], range=["#306998", "#FFD43B", "#E74C3C", "#2ECC71"]
)

# Define stroke dash patterns for different series
stroke_dash_scale = alt.Scale(
    domain=["Close Price", "SMA 20", "SMA 50", "SMA 200"], range=[[0], [8, 4], [4, 4], [2, 2]]
)

# Define stroke width - price line thicker
stroke_width_scale = alt.Scale(domain=["Close Price", "SMA 20", "SMA 50", "SMA 200"], range=[3, 2.5, 2.5, 2.5])

# Create chart
chart = (
    alt.Chart(combined_df)
    .mark_line()
    .encode(
        x=alt.X("date:T", title="Date", axis=alt.Axis(format="%b %Y", labelAngle=-45)),
        y=alt.Y("value:Q", title="Price ($)", scale=alt.Scale(zero=False)),
        color=alt.Color(
            "series:N",
            scale=color_scale,
            legend=alt.Legend(
                title="Series",
                orient="top-right",
                titleFontSize=18,
                labelFontSize=16,
                symbolSize=200,
                symbolStrokeWidth=3,
            ),
        ),
        strokeDash=alt.StrokeDash("series:N", scale=stroke_dash_scale, legend=None),
        strokeWidth=alt.StrokeWidth("series:N", scale=stroke_width_scale, legend=None),
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%Y-%m-%d"),
            alt.Tooltip("series:N", title="Series"),
            alt.Tooltip("value:Q", title="Price", format="$.2f"),
        ],
    )
    .properties(width=1600, height=900, title="indicator-sma · altair · pyplots.ai")
    .configure_title(fontSize=28, anchor="middle")
    .configure_axis(labelFontSize=18, titleFontSize=22, gridOpacity=0.3)
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
