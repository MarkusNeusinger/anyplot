""" pyplots.ai
indicator-macd: MACD Technical Indicator Chart
Library: plotly 6.5.0 | Python 3.13.11
Quality: 93/100 | Created: 2026-01-07
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Data - Generate realistic stock price data and calculate MACD
np.random.seed(42)

# Generate 150 trading days of synthetic price data
n_days = 150
dates = pd.date_range("2025-06-01", periods=n_days, freq="B")  # Business days

# Simulate price movement with trend and volatility
returns = np.random.normal(0.0005, 0.015, n_days)
price = pd.Series(100 * np.exp(np.cumsum(returns)))

# Calculate EMAs for MACD (12-day and 26-day EMAs)
ema_12 = price.ewm(span=12, adjust=False).mean()
ema_26 = price.ewm(span=26, adjust=False).mean()

# MACD components
macd_line = ema_12 - ema_26
signal_line = macd_line.ewm(span=9, adjust=False).mean()
histogram = macd_line - signal_line

# Use data from day 35 onwards (to have stable EMA values)
start_idx = 35
dates = dates[start_idx:]
macd_line = macd_line.values[start_idx:]
signal_line = signal_line.values[start_idx:]
histogram = histogram.values[start_idx:]

# Create histogram colors (green for positive, red for negative)
hist_colors = ["#2E8B57" if h >= 0 else "#DC143C" for h in histogram]

# Create figure
fig = make_subplots(rows=1, cols=1, vertical_spacing=0.1)

# Add MACD histogram bars
fig.add_trace(go.Bar(x=dates, y=histogram, name="Histogram", marker_color=hist_colors, opacity=0.7, showlegend=True))

# Add MACD line
fig.add_trace(go.Scatter(x=dates, y=macd_line, name="MACD (12, 26)", line=dict(color="#306998", width=3), mode="lines"))

# Add Signal line
fig.add_trace(go.Scatter(x=dates, y=signal_line, name="Signal (9)", line=dict(color="#FFD43B", width=3), mode="lines"))

# Add zero reference line
fig.add_hline(
    y=0,
    line=dict(color="#888888", width=2, dash="dash"),
    annotation_text="Zero Line",
    annotation_position="left",
    annotation_font_size=16,
)

# Update layout for high resolution
fig.update_layout(
    title=dict(text="indicator-macd · plotly · pyplots.ai", font=dict(size=32), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Date", font=dict(size=24)),
        tickfont=dict(size=18),
        gridcolor="rgba(128, 128, 128, 0.2)",
        showgrid=True,
    ),
    yaxis=dict(
        title=dict(text="MACD Value", font=dict(size=24)),
        tickfont=dict(size=18),
        gridcolor="rgba(128, 128, 128, 0.2)",
        showgrid=True,
        zeroline=False,
    ),
    legend=dict(
        font=dict(size=20),
        x=0.01,
        y=0.99,
        xanchor="left",
        yanchor="top",
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="rgba(0, 0, 0, 0.2)",
        borderwidth=1,
    ),
    template="plotly_white",
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(l=100, r=60, t=100, b=80),
    annotations=[
        dict(
            text="Parameters: EMA(12), EMA(26), Signal(9)",
            xref="paper",
            yref="paper",
            x=0.99,
            y=0.01,
            xanchor="right",
            yanchor="bottom",
            font=dict(size=16, color="#666666"),
            showarrow=False,
        )
    ],
)

# Save as PNG
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save as HTML for interactivity
fig.write_html("plot.html", include_plotlyjs="cdn")
