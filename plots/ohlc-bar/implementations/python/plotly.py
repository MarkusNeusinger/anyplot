""" anyplot.ai
ohlc-bar: OHLC Bar Chart
Library: plotly 6.7.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-17
"""

import os
import sys


# Remove current directory from path to avoid naming conflicts
sys.path = [p for p in sys.path if p not in ("", ".", os.path.dirname(__file__))]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import plotly.graph_objects as go  # noqa: E402


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette for up/down coloring
BRAND = "#009E73"  # Position 1 - bluish green, first series
UP_COLOR = BRAND  # Use brand green for up days
DOWN_COLOR = "#AE3030"  # imprint red — down days

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
        increasing={"line": {"color": UP_COLOR, "width": 2}},
        decreasing={"line": {"color": DOWN_COLOR, "width": 2}},
        name="Price",
    )
)

# Update layout for 4800x2700 canvas with theme-adaptive chrome
fig.update_layout(
    title={"text": "ohlc-bar · plotly · anyplot.ai", "font": {"size": 28, "color": INK}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "Date", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "gridcolor": GRID,
        "gridwidth": 1,
        "linecolor": INK_SOFT,
        "rangeslider": {"visible": False},
        "tickformat": "%b %d",
    },
    yaxis={
        "title": {"text": "Price (USD)", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "tickprefix": "$",
        "gridcolor": GRID,
        "gridwidth": 1,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    showlegend=False,
    margin={"l": 100, "r": 80, "t": 120, "b": 100},
)

# Save outputs
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
