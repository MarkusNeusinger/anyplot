""" pyplots.ai
candlestick-basic: Basic Candlestick Chart
Library: altair 6.0.0 | Python 3.14.3
Quality: 89/100 | Updated: 2026-02-24
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Simulated 30 days of stock price data
np.random.seed(42)
n_days = 30
dates = pd.date_range(start="2024-01-01", periods=n_days, freq="B")

# Generate realistic OHLC data with random walk
prices = [100.0]
for _ in range(n_days - 1):
    change = np.random.randn() * 2
    prices.append(prices[-1] + change)

data = []
for i, date in enumerate(dates):
    base = prices[i]
    volatility = np.random.uniform(1, 3)

    open_price = base + np.random.uniform(-volatility, volatility)
    close_price = base + np.random.uniform(-volatility, volatility)
    high_price = max(open_price, close_price) + np.random.uniform(0.5, volatility)
    low_price = min(open_price, close_price) - np.random.uniform(0.5, volatility)

    data.append(
        {
            "date": date,
            "open": round(open_price, 2),
            "high": round(high_price, 2),
            "low": round(low_price, 2),
            "close": round(close_price, 2),
        }
    )

df = pd.DataFrame(data)
df["direction"] = np.where(df["close"] >= df["open"], "Bullish", "Bearish")

# Colors - colorblind-safe: teal for bullish, warm orange for bearish
color_scale = alt.Scale(domain=["Bullish", "Bearish"], range=["#26A69A", "#FF8F00"])

# Candlestick wicks (high-low lines)
wicks = (
    alt.Chart(df)
    .mark_rule(strokeWidth=1.5)
    .encode(
        x=alt.X("date:T", title="Date", axis=alt.Axis(format="%b %d")),
        y=alt.Y("low:Q", title="Price ($)", scale=alt.Scale(zero=False)),
        y2="high:Q",
        color=alt.Color("direction:N", scale=color_scale, legend=None),
    )
)

# Candlestick bodies (open-close bars)
bodies = (
    alt.Chart(df)
    .mark_bar(size=20)
    .encode(
        x="date:T",
        y="open:Q",
        y2="close:Q",
        color=alt.Color(
            "direction:N", scale=color_scale, legend=alt.Legend(title="Direction", labelFontSize=16, titleFontSize=18)
        ),
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%b %d, %Y"),
            alt.Tooltip("open:Q", title="Open", format="$.2f"),
            alt.Tooltip("high:Q", title="High", format="$.2f"),
            alt.Tooltip("low:Q", title="Low", format="$.2f"),
            alt.Tooltip("close:Q", title="Close", format="$.2f"),
        ],
    )
)

# Layer wicks and bodies with interactive zoom/pan
chart = (
    alt.layer(wicks, bodies)
    .resolve_scale(color="independent")
    .properties(
        width=1600,
        height=900,
        title=alt.Title("candlestick-basic \u00b7 altair \u00b7 pyplots.ai", fontSize=28, anchor="middle"),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, gridOpacity=0.15)
    .configure_legend(labelFontSize=16, titleFontSize=18)
    .configure_view(strokeWidth=0)
    .interactive()
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
