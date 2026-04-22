""" pyplots.ai
candlestick-volume: Stock Candlestick Chart with Volume
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-31
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Data - Generate 60 trading days of realistic OHLC + volume data
np.random.seed(42)
n_days = 60
dates = pd.date_range("2024-01-02", periods=n_days, freq="B")  # Business days

# Start price and generate random walk
start_price = 150.0
returns = np.random.normal(0.0005, 0.02, n_days)
prices = start_price * np.cumprod(1 + returns)

# Generate OHLC from close prices
close = prices
open_prices = np.roll(close, 1)
open_prices[0] = start_price

# Generate high/low with realistic intraday range
daily_range = np.abs(np.random.normal(0.015, 0.008, n_days)) * close
high = np.maximum(open_prices, close) + daily_range * np.random.uniform(0.3, 0.7, n_days)
low = np.minimum(open_prices, close) - daily_range * np.random.uniform(0.3, 0.7, n_days)

# Volume with correlation to price movement (higher volume on bigger moves)
base_volume = 5_000_000
price_change = np.abs(close - open_prices) / open_prices
volume = base_volume * (1 + 3 * price_change) * np.random.uniform(0.7, 1.3, n_days)
volume = volume.astype(int)

# Determine up/down days for coloring
is_up = close >= open_prices
colors = ["#306998" if up else "#FFD43B" for up in is_up]

# Create subplot with shared x-axis
# Price pane: 75% height, Volume pane: 25% height
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.75, 0.25])

# Add candlestick chart
fig.add_trace(
    go.Candlestick(
        x=dates,
        open=open_prices,
        high=high,
        low=low,
        close=close,
        increasing={"line": {"color": "#306998", "width": 2}, "fillcolor": "#306998"},
        decreasing={"line": {"color": "#FFD43B", "width": 2}, "fillcolor": "#FFD43B"},
        name="Price",
        showlegend=False,
    ),
    row=1,
    col=1,
)

# Add volume bars
fig.add_trace(
    go.Bar(x=dates, y=volume, marker={"color": colors, "line": {"width": 0}}, name="Volume", showlegend=False),
    row=2,
    col=1,
)

# Update layout for professional appearance
fig.update_layout(
    title={"text": "candlestick-volume · plotly · pyplots.ai", "font": {"size": 32}, "x": 0.5, "xanchor": "center"},
    template="plotly_white",
    hovermode="x unified",
    # Add crosshair cursor
    xaxis={
        "showspikes": True,
        "spikemode": "across",
        "spikesnap": "cursor",
        "spikecolor": "#888888",
        "spikethickness": 1,
        "spikedash": "solid",
    },
    xaxis2={
        "showspikes": True,
        "spikemode": "across",
        "spikesnap": "cursor",
        "spikecolor": "#888888",
        "spikethickness": 1,
        "spikedash": "solid",
    },
    yaxis={
        "showspikes": True,
        "spikemode": "across",
        "spikesnap": "cursor",
        "spikecolor": "#888888",
        "spikethickness": 1,
        "spikedash": "solid",
    },
    yaxis2={
        "showspikes": True,
        "spikemode": "across",
        "spikesnap": "cursor",
        "spikecolor": "#888888",
        "spikethickness": 1,
        "spikedash": "solid",
    },
    # Disable range slider
    xaxis_rangeslider_visible=False,
    # Margins for proper spacing
    margin={"l": 80, "r": 40, "t": 100, "b": 60},
)

# Update axes styling
fig.update_xaxes(
    title={"text": "Date", "font": {"size": 22}},
    tickfont={"size": 18},
    gridcolor="rgba(128,128,128,0.2)",
    gridwidth=1,
    row=2,
    col=1,
)

fig.update_yaxes(
    title={"text": "Price ($)", "font": {"size": 22}},
    tickfont={"size": 18},
    tickformat="$.0f",
    gridcolor="rgba(128,128,128,0.2)",
    gridwidth=1,
    row=1,
    col=1,
)

fig.update_yaxes(
    title={"text": "Volume", "font": {"size": 22}},
    tickfont={"size": 18},
    tickformat=".2s",
    gridcolor="rgba(128,128,128,0.2)",
    gridwidth=1,
    row=2,
    col=1,
)

# Hide x-axis title on price pane
fig.update_xaxes(title=None, row=1, col=1)

# Save as PNG (4800 x 2700 pixels)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save as HTML for interactivity
fig.write_html("plot.html", include_plotlyjs="cdn")
