""" pyplots.ai
indicator-ema: Exponential Moving Average (EMA) Indicator Chart
Library: plotly 6.5.1 | Python 3.13.11
Quality: 94/100 | Created: 2026-01-11
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Data - Generate realistic stock price data with trend and volatility
np.random.seed(42)
n_days = 120

# Create date range for trading days
dates = pd.date_range(start="2024-01-02", periods=n_days, freq="B")

# Generate price with uptrend, volatility, and some consolidation
base_price = 150
returns = np.random.normal(0.001, 0.015, n_days)
# Add trend phases: uptrend, consolidation, uptrend
trend = np.concatenate([np.linspace(0, 0.15, 40), np.linspace(0.15, 0.12, 30), np.linspace(0.12, 0.25, 50)])
close_prices = base_price * np.exp(np.cumsum(returns) + trend)

# Calculate EMAs
df = pd.DataFrame({"date": dates, "close": close_prices})
df["ema_12"] = df["close"].ewm(span=12, adjust=False).mean()
df["ema_26"] = df["close"].ewm(span=26, adjust=False).mean()

# Find crossover points (golden cross: short crosses above long)
crossover_up = (df["ema_12"] > df["ema_26"]) & (df["ema_12"].shift(1) <= df["ema_26"].shift(1))
crossover_down = (df["ema_12"] < df["ema_26"]) & (df["ema_12"].shift(1) >= df["ema_26"].shift(1))

# Create figure
fig = go.Figure()

# Add price line (most prominent)
fig.add_trace(
    go.Scatter(
        x=df["date"],
        y=df["close"],
        mode="lines",
        name="Price",
        line={"color": "#306998", "width": 3},
        hovertemplate="Date: %{x|%Y-%m-%d}<br>Price: $%{y:.2f}<extra></extra>",
    )
)

# Add EMA 12 (short-term)
fig.add_trace(
    go.Scatter(
        x=df["date"],
        y=df["ema_12"],
        mode="lines",
        name="EMA 12",
        line={"color": "#FFD43B", "width": 2},
        hovertemplate="Date: %{x|%Y-%m-%d}<br>EMA 12: $%{y:.2f}<extra></extra>",
    )
)

# Add EMA 26 (long-term)
fig.add_trace(
    go.Scatter(
        x=df["date"],
        y=df["ema_26"],
        mode="lines",
        name="EMA 26",
        line={"color": "#E74C3C", "width": 2},
        hovertemplate="Date: %{x|%Y-%m-%d}<br>EMA 26: $%{y:.2f}<extra></extra>",
    )
)

# Add crossover markers (golden cross - bullish)
golden_cross = df[crossover_up]
if len(golden_cross) > 0:
    fig.add_trace(
        go.Scatter(
            x=golden_cross["date"],
            y=golden_cross["ema_12"],
            mode="markers",
            name="Golden Cross",
            marker={"color": "#27AE60", "size": 16, "symbol": "triangle-up", "line": {"color": "white", "width": 2}},
            hovertemplate="Golden Cross<br>Date: %{x|%Y-%m-%d}<br>Price: $%{y:.2f}<extra></extra>",
        )
    )

# Add crossover markers (death cross - bearish)
death_cross = df[crossover_down]
if len(death_cross) > 0:
    fig.add_trace(
        go.Scatter(
            x=death_cross["date"],
            y=death_cross["ema_12"],
            mode="markers",
            name="Death Cross",
            marker={"color": "#C0392B", "size": 16, "symbol": "triangle-down", "line": {"color": "white", "width": 2}},
            hovertemplate="Death Cross<br>Date: %{x|%Y-%m-%d}<br>Price: $%{y:.2f}<extra></extra>",
        )
    )

# Update layout
fig.update_layout(
    title={"text": "indicator-ema · plotly · pyplots.ai", "font": {"size": 32}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "Date", "font": {"size": 24}},
        "tickfont": {"size": 18},
        "gridcolor": "rgba(128, 128, 128, 0.2)",
        "showgrid": True,
    },
    yaxis={
        "title": {"text": "Price (USD)", "font": {"size": 24}},
        "tickfont": {"size": 18},
        "tickformat": "$,.0f",
        "gridcolor": "rgba(128, 128, 128, 0.2)",
        "showgrid": True,
    },
    legend={
        "font": {"size": 18},
        "x": 0.02,
        "y": 0.98,
        "bgcolor": "rgba(255, 255, 255, 0.8)",
        "bordercolor": "rgba(128, 128, 128, 0.3)",
        "borderwidth": 1,
    },
    template="plotly_white",
    hovermode="x unified",
    margin={"l": 80, "r": 40, "t": 80, "b": 60},
)

# Save outputs
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
