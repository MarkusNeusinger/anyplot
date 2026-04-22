""" pyplots.ai
indicator-sma: Simple Moving Average (SMA) Indicator Chart
Library: plotly 6.5.1 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-11
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Data: Generate realistic stock price data with trend and volatility
np.random.seed(42)

n_days = 300
dates = pd.date_range(start="2025-01-01", periods=n_days, freq="B")  # Business days

# Generate price with trend and random walk
initial_price = 150.0
returns = np.random.normal(0.0005, 0.018, n_days)  # Daily returns with slight upward bias
price = initial_price * np.cumprod(1 + returns)

# Add some realistic trend patterns
trend = np.sin(np.linspace(0, 3 * np.pi, n_days)) * 15
price = price + trend

# Create DataFrame
df = pd.DataFrame({"date": dates, "close": price})

# Calculate SMAs
df["sma_20"] = df["close"].rolling(window=20).mean()
df["sma_50"] = df["close"].rolling(window=50).mean()
df["sma_200"] = df["close"].rolling(window=200).mean()

# Create figure
fig = go.Figure()

# Add price line (prominent)
fig.add_trace(
    go.Scatter(
        x=df["date"],
        y=df["close"],
        mode="lines",
        name="Close Price",
        line=dict(color="#306998", width=2.5),
        hovertemplate="Date: %{x|%Y-%m-%d}<br>Price: $%{y:.2f}<extra></extra>",
    )
)

# Add SMA lines with distinct colors
fig.add_trace(
    go.Scatter(
        x=df["date"],
        y=df["sma_20"],
        mode="lines",
        name="SMA 20",
        line=dict(color="#FFD43B", width=2),
        hovertemplate="Date: %{x|%Y-%m-%d}<br>SMA 20: $%{y:.2f}<extra></extra>",
    )
)

fig.add_trace(
    go.Scatter(
        x=df["date"],
        y=df["sma_50"],
        mode="lines",
        name="SMA 50",
        line=dict(color="#E74C3C", width=2),
        hovertemplate="Date: %{x|%Y-%m-%d}<br>SMA 50: $%{y:.2f}<extra></extra>",
    )
)

fig.add_trace(
    go.Scatter(
        x=df["date"],
        y=df["sma_200"],
        mode="lines",
        name="SMA 200",
        line=dict(color="#2ECC71", width=2),
        hovertemplate="Date: %{x|%Y-%m-%d}<br>SMA 200: $%{y:.2f}<extra></extra>",
    )
)

# Update layout for 4800x2700 px output
fig.update_layout(
    title=dict(text="indicator-sma · plotly · pyplots.ai", font=dict(size=32), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Date", font=dict(size=24)),
        tickfont=dict(size=18),
        showgrid=True,
        gridcolor="rgba(128, 128, 128, 0.2)",
        gridwidth=1,
    ),
    yaxis=dict(
        title=dict(text="Price ($)", font=dict(size=24)),
        tickfont=dict(size=18),
        showgrid=True,
        gridcolor="rgba(128, 128, 128, 0.3)",
        gridwidth=1,
        tickformat="$.0f",
    ),
    legend=dict(
        font=dict(size=20),
        x=0.02,
        y=0.98,
        xanchor="left",
        yanchor="top",
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="rgba(128, 128, 128, 0.3)",
        borderwidth=1,
    ),
    template="plotly_white",
    margin=dict(l=100, r=60, t=100, b=80),
    hovermode="x unified",
)

# Save as PNG (4800 x 2700 px)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save as HTML for interactivity
fig.write_html("plot.html", include_plotlyjs="cdn")
