""" pyplots.ai
indicator-bollinger: Bollinger Bands Indicator Chart
Library: plotly 6.5.1 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-07
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Data - Generate realistic stock price data with Bollinger Bands
np.random.seed(42)
n_periods = 120

# Generate synthetic stock price data with trends and volatility
dates = pd.date_range("2024-01-01", periods=n_periods, freq="B")  # Business days
returns = np.random.normal(0.0005, 0.018, n_periods)
# Add some trending behavior
trend = np.sin(np.linspace(0, 3 * np.pi, n_periods)) * 0.003
returns = returns + trend
price = 100 * np.cumprod(1 + returns)

# Calculate Bollinger Bands (20-period SMA, 2 standard deviations)
window = 20
df = pd.DataFrame({"date": dates, "close": price})
df["sma"] = df["close"].rolling(window=window).mean()
df["std"] = df["close"].rolling(window=window).std()
df["upper_band"] = df["sma"] + 2 * df["std"]
df["lower_band"] = df["sma"] - 2 * df["std"]

# Remove NaN values from rolling calculation
df = df.dropna().reset_index(drop=True)

# Create figure
fig = go.Figure()

# Add the filled area between bands (volatility envelope)
fig.add_trace(
    go.Scatter(x=df["date"], y=df["upper_band"], mode="lines", line={"width": 0}, showlegend=False, hoverinfo="skip")
)

fig.add_trace(
    go.Scatter(
        x=df["date"],
        y=df["lower_band"],
        mode="lines",
        line={"width": 0},
        fill="tonexty",
        fillcolor="rgba(48, 105, 152, 0.2)",
        name="Bollinger Bands (2σ)",
        hoverinfo="skip",
    )
)

# Add upper band line
fig.add_trace(
    go.Scatter(
        x=df["date"],
        y=df["upper_band"],
        mode="lines",
        line={"color": "#306998", "width": 2, "dash": "solid"},
        name="Upper Band (+2σ)",
        hovertemplate="Upper: $%{y:.2f}<extra></extra>",
    )
)

# Add lower band line
fig.add_trace(
    go.Scatter(
        x=df["date"],
        y=df["lower_band"],
        mode="lines",
        line={"color": "#306998", "width": 2, "dash": "solid"},
        name="Lower Band (-2σ)",
        hovertemplate="Lower: $%{y:.2f}<extra></extra>",
    )
)

# Add middle band (SMA) - dashed line
fig.add_trace(
    go.Scatter(
        x=df["date"],
        y=df["sma"],
        mode="lines",
        line={"color": "#FFD43B", "width": 3, "dash": "dash"},
        name="20-day SMA",
        hovertemplate="SMA: $%{y:.2f}<extra></extra>",
    )
)

# Add price line (close) - most prominent
fig.add_trace(
    go.Scatter(
        x=df["date"],
        y=df["close"],
        mode="lines",
        line={"color": "#1a1a2e", "width": 3},
        name="Close Price",
        hovertemplate="Date: %{x|%Y-%m-%d}<br>Close: $%{y:.2f}<extra></extra>",
    )
)

# Update layout for 4800x2700 px output
fig.update_layout(
    title={
        "text": "indicator-bollinger · plotly · pyplots.ai",
        "font": {"size": 32, "color": "#1a1a2e"},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Date", "font": {"size": 24}},
        "tickfont": {"size": 18},
        "showgrid": True,
        "gridcolor": "rgba(0,0,0,0.1)",
        "gridwidth": 1,
    },
    yaxis={
        "title": {"text": "Price ($)", "font": {"size": 24}},
        "tickfont": {"size": 18},
        "tickformat": "$.0f",
        "showgrid": True,
        "gridcolor": "rgba(0,0,0,0.1)",
        "gridwidth": 1,
    },
    template="plotly_white",
    legend={
        "font": {"size": 18},
        "orientation": "h",
        "yanchor": "bottom",
        "y": 1.02,
        "xanchor": "center",
        "x": 0.5,
        "bgcolor": "rgba(255,255,255,0.8)",
    },
    margin={"l": 100, "r": 60, "t": 120, "b": 80},
    hovermode="x unified",
)

# Save as PNG (4800 x 2700 px)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save interactive HTML version
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
