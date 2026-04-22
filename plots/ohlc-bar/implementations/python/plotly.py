""" pyplots.ai
ohlc-bar: OHLC Bar Chart
Library: plotly 6.5.1 | Python 3.13.11
Quality: 98/100 | Created: 2026-01-08
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Data - Generate realistic stock price data for 45 trading days
np.random.seed(42)

dates = pd.date_range(start="2024-06-01", periods=45, freq="B")  # Business days

# Generate realistic price movement with trends
base_price = 150.0
returns = np.random.normal(0.001, 0.02, 45)  # Daily returns
cumulative = np.cumprod(1 + returns)
close_prices = base_price * cumulative

# Generate OHLC data with realistic relationships
data = []
for i, date in enumerate(dates):
    close = close_prices[i]
    # Open is close of previous day (or base for first day)
    open_price = close_prices[i - 1] if i > 0 else base_price

    # High and low based on intraday volatility
    intraday_range = close * np.random.uniform(0.01, 0.03)
    high = max(open_price, close) + np.random.uniform(0, intraday_range)
    low = min(open_price, close) - np.random.uniform(0, intraday_range)

    data.append({"date": date, "open": open_price, "high": high, "low": low, "close": close})

df = pd.DataFrame(data)

# Create OHLC chart using Plotly's native OHLC trace
fig = go.Figure(
    data=go.Ohlc(
        x=df["date"],
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        increasing={"line": {"color": "#306998", "width": 2}},  # Python Blue for up bars
        decreasing={"line": {"color": "#FFD43B", "width": 2}},  # Python Yellow for down bars
        name="Price",
    )
)

# Update layout for 4800x2700 canvas
fig.update_layout(
    title={"text": "ohlc-bar · plotly · pyplots.ai", "font": {"size": 32}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "Date", "font": {"size": 24}},
        "tickfont": {"size": 18},
        "gridcolor": "rgba(128, 128, 128, 0.3)",
        "gridwidth": 1,
        "rangeslider": {"visible": False},  # Disable range slider for cleaner look
        "tickformat": "%b %d",
    },
    yaxis={
        "title": {"text": "Price (USD)", "font": {"size": 24}},
        "tickfont": {"size": 18},
        "tickprefix": "$",
        "gridcolor": "rgba(128, 128, 128, 0.3)",
        "gridwidth": 1,
    },
    template="plotly_white",
    showlegend=False,
    margin={"l": 100, "r": 80, "t": 120, "b": 100},
    plot_bgcolor="white",
)

# Save as PNG (4800x2700 via scale=3)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save interactive HTML version
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
