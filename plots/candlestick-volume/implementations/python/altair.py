""" pyplots.ai
candlestick-volume: Stock Candlestick Chart with Volume
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import altair as alt
import numpy as np
import pandas as pd


# Data: Generate 60 days of realistic stock OHLC data with volume
np.random.seed(42)
n_days = 60
dates = pd.date_range("2024-01-02", periods=n_days, freq="B")  # Business days

# Generate price data with realistic movements
price = 150.0  # Starting price
opens, highs, lows, closes, volumes = [], [], [], [], []

for _ in range(n_days):
    # Daily return with slight upward drift
    daily_return = np.random.normal(0.001, 0.02)
    volatility = np.random.uniform(0.01, 0.03)

    open_price = price
    close_price = price * (1 + daily_return)

    # High and low based on volatility
    intraday_high = max(open_price, close_price) * (1 + np.random.uniform(0, volatility))
    intraday_low = min(open_price, close_price) * (1 - np.random.uniform(0, volatility))

    opens.append(round(open_price, 2))
    highs.append(round(intraday_high, 2))
    lows.append(round(intraday_low, 2))
    closes.append(round(close_price, 2))

    # Volume with some variation (higher on volatile days)
    base_volume = 5000000
    vol_multiplier = 1 + abs(daily_return) * 20
    volumes.append(int(base_volume * vol_multiplier * np.random.uniform(0.7, 1.3)))

    price = close_price

df = pd.DataFrame({"date": dates, "open": opens, "high": highs, "low": lows, "close": closes, "volume": volumes})

# Determine if day is bullish (close >= open) or bearish
df["direction"] = np.where(df["close"] >= df["open"], "bullish", "bearish")

# Color scheme for candlesticks and volume
color_scale = alt.Scale(domain=["bullish", "bearish"], range=["#306998", "#FFD43B"])

# Base chart with shared x-axis selection
base = alt.Chart(df).encode(x=alt.X("date:T", axis=alt.Axis(title="Date", labelFontSize=16, titleFontSize=20)))

# Candlestick wicks (high-low lines)
wicks = base.mark_rule(strokeWidth=2).encode(
    y=alt.Y("low:Q", scale=alt.Scale(zero=False), axis=alt.Axis(title="Price ($)", labelFontSize=16, titleFontSize=20)),
    y2="high:Q",
    color=alt.Color("direction:N", scale=color_scale, legend=None),
)

# Candlestick bodies (open-close bars)
bodies = base.mark_bar(size=12).encode(
    y=alt.Y("open:Q", scale=alt.Scale(zero=False)),
    y2="close:Q",
    color=alt.Color("direction:N", scale=color_scale, legend=None),
    tooltip=[
        alt.Tooltip("date:T", title="Date"),
        alt.Tooltip("open:Q", title="Open", format="$.2f"),
        alt.Tooltip("high:Q", title="High", format="$.2f"),
        alt.Tooltip("low:Q", title="Low", format="$.2f"),
        alt.Tooltip("close:Q", title="Close", format="$.2f"),
        alt.Tooltip("volume:Q", title="Volume", format=","),
    ],
)

# Combine wicks and bodies for candlestick chart
candlestick = (wicks + bodies).properties(width=1600, height=600, title="")

# Volume chart
volume = (
    alt.Chart(df)
    .mark_bar(size=12)
    .encode(
        x=alt.X("date:T", axis=alt.Axis(title="Date", labelFontSize=16, titleFontSize=20)),
        y=alt.Y("volume:Q", axis=alt.Axis(title="Volume", labelFontSize=16, titleFontSize=20, format="~s")),
        color=alt.Color("direction:N", scale=color_scale, legend=None),
        tooltip=[alt.Tooltip("date:T", title="Date"), alt.Tooltip("volume:Q", title="Volume", format=",")],
    )
    .properties(width=1600, height=200)
)

# Add legend separately
legend_data = pd.DataFrame({"direction": ["bullish", "bearish"], "label": ["Bullish (Up)", "Bearish (Down)"]})
legend = (
    alt.Chart(legend_data)
    .mark_point(size=300)
    .encode(y=alt.Y("label:N", axis=None), color=alt.Color("direction:N", scale=color_scale, legend=None))
    .properties(width=50, title="")
)

# Combine candlestick and volume vertically
combined = alt.vconcat(candlestick, volume, spacing=10).properties(
    title=alt.Title("candlestick-volume · altair · pyplots.ai", fontSize=28, anchor="middle")
)

# Configure chart with appropriate styling
chart = combined.configure_axis(labelFontSize=16, titleFontSize=20).configure_view(strokeWidth=0)

# Save as PNG (scale_factor=3 for 4800x2700)
chart.save("plot.png", scale_factor=3.0)

# Save interactive HTML version
chart_interactive = combined.configure_axis(labelFontSize=16, titleFontSize=20).configure_view(strokeWidth=0)
chart_interactive.save("plot.html")
