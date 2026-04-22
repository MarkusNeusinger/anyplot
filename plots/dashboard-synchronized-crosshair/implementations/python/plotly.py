""" pyplots.ai
dashboard-synchronized-crosshair: Synchronized Multi-Chart Dashboard
Library: plotly 6.5.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-20
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Data - Stock-like data with price, volume, and RSI indicator
np.random.seed(42)
n_points = 200
dates = pd.date_range("2024-01-01", periods=n_points, freq="B")

# Price series (random walk)
price_returns = np.random.normal(0.0005, 0.015, n_points)
price = 100 * np.cumprod(1 + price_returns)

# Volume series (correlated with absolute returns)
base_volume = 1_000_000
volume = base_volume * (1 + 2 * np.abs(price_returns) + np.random.uniform(0, 0.5, n_points))
volume = volume.astype(int)

# RSI-like indicator (oscillating between 30-70 mostly)
rsi = 50 + 20 * np.sin(np.linspace(0, 8 * np.pi, n_points)) + np.random.normal(0, 5, n_points)
rsi = np.clip(rsi, 0, 100)

df = pd.DataFrame({"date": dates, "price": price, "volume": volume, "rsi": rsi})

# Create subplots with shared x-axis
fig = make_subplots(
    rows=3,
    cols=1,
    shared_xaxes=True,
    vertical_spacing=0.08,
    row_heights=[0.5, 0.25, 0.25],
    subplot_titles=("Price", "Volume", "RSI Indicator"),
)

# Price chart (top)
fig.add_trace(
    go.Scatter(
        x=df["date"],
        y=df["price"],
        mode="lines",
        name="Price",
        line=dict(color="#306998", width=2.5),
        hovertemplate="%{y:.2f}<extra></extra>",
    ),
    row=1,
    col=1,
)

# Volume chart (middle)
fig.add_trace(
    go.Bar(
        x=df["date"],
        y=df["volume"],
        name="Volume",
        marker=dict(color="#FFD43B", opacity=0.8),
        hovertemplate="%{y:,.0f}<extra></extra>",
    ),
    row=2,
    col=1,
)

# RSI chart (bottom)
fig.add_trace(
    go.Scatter(
        x=df["date"],
        y=df["rsi"],
        mode="lines",
        name="RSI",
        line=dict(color="#306998", width=2.5),
        hovertemplate="%{y:.1f}<extra></extra>",
    ),
    row=3,
    col=1,
)

# Add RSI reference lines (overbought/oversold)
fig.add_hline(y=70, line_dash="dash", line_color="#E74C3C", line_width=1.5, row=3, col=1)
fig.add_hline(y=30, line_dash="dash", line_color="#27AE60", line_width=1.5, row=3, col=1)

# Layout with synchronized crosshair
fig.update_layout(
    title=dict(
        text="dashboard-synchronized-crosshair · plotly · pyplots.ai", font=dict(size=32), x=0.5, xanchor="center"
    ),
    template="plotly_white",
    hovermode="x unified",
    hoverlabel=dict(font_size=16),
    showlegend=False,
    margin=dict(l=100, r=60, t=120, b=80),
)

# Subplot title styling
for annotation in fig["layout"]["annotations"]:
    annotation["font"] = dict(size=22)

# Y-axis styling for each subplot
fig.update_yaxes(
    title_text="Price ($)", title_font=dict(size=20), tickfont=dict(size=16), gridcolor="rgba(0,0,0,0.1)", row=1, col=1
)
fig.update_yaxes(
    title_text="Volume", title_font=dict(size=20), tickfont=dict(size=16), gridcolor="rgba(0,0,0,0.1)", row=2, col=1
)
fig.update_yaxes(
    title_text="RSI",
    title_font=dict(size=20),
    tickfont=dict(size=16),
    gridcolor="rgba(0,0,0,0.1)",
    range=[0, 100],
    row=3,
    col=1,
)

# X-axis styling (only visible on bottom chart)
fig.update_xaxes(
    title_text="Date", title_font=dict(size=20), tickfont=dict(size=16), gridcolor="rgba(0,0,0,0.1)", row=3, col=1
)

# Enable spike lines for synchronized crosshair effect
fig.update_xaxes(
    showspikes=True, spikemode="across", spikesnap="cursor", spikethickness=1.5, spikecolor="#666666", spikedash="solid"
)
fig.update_yaxes(showspikes=True, spikethickness=1, spikecolor="#999999", spikedash="dot")

# Save outputs
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
