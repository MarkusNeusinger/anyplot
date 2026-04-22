""" pyplots.ai
stock-event-flags: Stock Chart with Event Flags
Library: plotly 6.5.2 | Python 3.13.11
Quality: 93/100 | Created: 2026-01-21
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Data - Generate realistic stock price data
np.random.seed(42)
n_days = 180

dates = pd.date_range(start="2024-01-02", periods=n_days, freq="B")  # Business days

# Generate OHLC data with realistic price movements
initial_price = 150.0
returns = np.random.randn(n_days) * 0.02  # 2% daily volatility
close_prices = initial_price * np.exp(np.cumsum(returns))

# Generate OHLC from close prices
high_prices = close_prices * (1 + np.abs(np.random.randn(n_days)) * 0.015)
low_prices = close_prices * (1 - np.abs(np.random.randn(n_days)) * 0.015)
open_prices = np.roll(close_prices, 1)
open_prices[0] = initial_price

# Ensure OHLC constraints
high_prices = np.maximum(high_prices, np.maximum(open_prices, close_prices))
low_prices = np.minimum(low_prices, np.minimum(open_prices, close_prices))

df = pd.DataFrame({"date": dates, "open": open_prices, "high": high_prices, "low": low_prices, "close": close_prices})

# Define events at specific dates
events = pd.DataFrame(
    {
        "event_date": pd.to_datetime(
            ["2024-01-25", "2024-03-15", "2024-04-18", "2024-05-10", "2024-06-07", "2024-07-18", "2024-08-22"]
        ),
        "event_type": ["Earnings", "Dividend", "News", "Earnings", "Split", "Dividend", "Earnings"],
        "event_label": ["Q4 Beat", "Div $0.50", "Product Launch", "Q1 Miss", "4:1 Split", "Div $0.55", "Q2 Beat"],
    }
)

# Map event types to colors and symbols
event_colors = {
    "Earnings": "#306998",  # Python Blue
    "Dividend": "#2E8B57",  # Sea Green
    "News": "#FF6B35",  # Orange
    "Split": "#9B59B6",  # Purple
}

event_symbols = {"Earnings": "star", "Dividend": "diamond", "News": "triangle-up", "Split": "square"}

# Create figure
fig = go.Figure()

# Add candlestick chart
fig.add_trace(
    go.Candlestick(
        x=df["date"],
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        name="Price",
        increasing_line_color="#2E8B57",
        decreasing_line_color="#DC3545",
        increasing_fillcolor="#2E8B57",
        decreasing_fillcolor="#DC3545",
        line_width=1.5,
    )
)

# Add event flags with vertical lines and markers
for _, event in events.iterrows():
    event_date = event["event_date"]
    # Find closest trading day
    date_idx = (df["date"] - event_date).abs().argmin()
    actual_date = df["date"].iloc[date_idx]
    price_at_event = df["high"].iloc[date_idx]

    # Calculate flag position above the price
    price_range = df["high"].max() - df["low"].min()
    flag_y = price_at_event + price_range * 0.08

    color = event_colors.get(event["event_type"], "#306998")
    symbol = event_symbols.get(event["event_type"], "circle")

    # Add vertical dashed line from flag to price
    fig.add_trace(
        go.Scatter(
            x=[actual_date, actual_date],
            y=[price_at_event, flag_y],
            mode="lines",
            line=dict(color=color, width=2, dash="dash"),
            showlegend=False,
            hoverinfo="skip",
        )
    )

    # Add flag marker with label
    fig.add_trace(
        go.Scatter(
            x=[actual_date],
            y=[flag_y],
            mode="markers+text",
            marker=dict(size=20, color=color, symbol=symbol, line=dict(color="white", width=2)),
            text=[event["event_label"]],
            textposition="top center",
            textfont=dict(size=14, color=color, family="Arial Black"),
            name=event["event_type"],
            showlegend=False,
            hovertemplate=(
                f"<b>{event['event_type']}</b><br>{event['event_label']}<br>Date: %{{x|%Y-%m-%d}}<extra></extra>"
            ),
        )
    )

# Add legend entries for event types
for event_type in event_colors.keys():
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker=dict(size=16, color=event_colors[event_type], symbol=event_symbols[event_type]),
            name=event_type,
        )
    )

# Update layout
fig.update_layout(
    title=dict(
        text="stock-event-flags · plotly · pyplots.ai",
        font=dict(size=32, family="Arial Black"),
        x=0.5,
        xanchor="center",
    ),
    xaxis=dict(
        title=dict(text="Date", font=dict(size=22)),
        tickfont=dict(size=16),
        rangeslider=dict(visible=False),
        gridcolor="rgba(128, 128, 128, 0.2)",
        showgrid=True,
    ),
    yaxis=dict(
        title=dict(text="Price ($)", font=dict(size=22)),
        tickfont=dict(size=16),
        tickformat="$.0f",
        gridcolor="rgba(128, 128, 128, 0.2)",
        showgrid=True,
    ),
    template="plotly_white",
    legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=0.01,
        bgcolor="rgba(255, 255, 255, 0.9)",
        bordercolor="rgba(128, 128, 128, 0.3)",
        borderwidth=1,
        font=dict(size=14),
    ),
    margin=dict(l=80, r=40, t=100, b=80),
    hovermode="x unified",
)

# Save outputs
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
