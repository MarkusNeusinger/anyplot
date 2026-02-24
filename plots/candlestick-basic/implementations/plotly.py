""" pyplots.ai
candlestick-basic: Basic Candlestick Chart
Library: plotly 6.5.2 | Python 3.14.3
Quality: /100 | Updated: 2026-02-24
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Data - 30 trading days of simulated stock prices
np.random.seed(42)
dates = pd.date_range(start="2024-01-02", periods=30, freq="B")

# Generate realistic price movement starting at $150 (rally, pullback, recovery)
price = 150.0
drift = [0.4] * 8 + [-0.5] * 12 + [0.35] * 10
opens, highs, lows, closes = [], [], [], []

for i in range(30):
    open_price = price
    change = np.random.randn() * 2.5 + drift[i]
    close_price = open_price + change

    high_price = max(open_price, close_price) + abs(np.random.randn()) * 1.8
    low_price = min(open_price, close_price) - abs(np.random.randn()) * 1.8

    opens.append(open_price)
    highs.append(high_price)
    lows.append(low_price)
    closes.append(close_price)

    price = close_price

df = pd.DataFrame({"date": dates, "open": opens, "high": highs, "low": lows, "close": closes})

# Create candlestick chart
fig = go.Figure(
    data=[
        go.Candlestick(
            x=df["date"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            increasing={"line": {"color": "#26A69A", "width": 2}, "fillcolor": "#26A69A"},
            decreasing={"line": {"color": "#EF5350", "width": 2}, "fillcolor": "#EF5350"},
            hovertemplate=(
                "<b>%{x|%b %d, %Y}</b><br>"
                "Open: $%{open:.2f}<br>"
                "High: $%{high:.2f}<br>"
                "Low: $%{low:.2f}<br>"
                "Close: $%{close:.2f}<br>"
                "<extra></extra>"
            ),
        )
    ]
)

# Layout
fig.update_layout(
    title={
        "text": (
            "ACME Corp Daily Prices"
            "<br><sup style='color:#888;font-size:16px'>"
            "candlestick-basic · plotly · pyplots.ai</sup>"
        ),
        "font": {"size": 28},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Date", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "tickformat": "%b %d",
        "rangeslider": {"visible": False},
        "rangebreaks": [{"bounds": ["sat", "mon"]}],
        "gridcolor": "rgba(128, 128, 128, 0.15)",
        "showgrid": False,
    },
    yaxis={
        "title": {"text": "Price (USD)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "tickprefix": "$",
        "gridcolor": "rgba(128, 128, 128, 0.15)",
        "gridwidth": 1,
        "zeroline": False,
    },
    template="plotly_white",
    plot_bgcolor="white",
    margin={"l": 90, "r": 40, "t": 100, "b": 80},
    hoverlabel={"bgcolor": "white", "font_size": 14, "bordercolor": "#ccc"},
)

# Save as PNG (4800x2700)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save interactive HTML
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
