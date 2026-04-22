""" pyplots.ai
timeseries-decomposition: Time Series Decomposition Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from statsmodels.tsa.seasonal import seasonal_decompose


# Data: Monthly airline passengers (classic time series with trend and seasonality)
np.random.seed(42)

# Create 10 years of monthly data (120 points)
dates = pd.date_range(start="2014-01-01", periods=120, freq="MS")

# Generate realistic airline passenger data with trend, seasonality, and noise
trend = np.linspace(100, 250, 120)  # Growing trend
seasonal = 30 * np.sin(2 * np.pi * np.arange(120) / 12)  # Annual cycle (peak in summer)
noise = np.random.normal(0, 10, 120)
passengers = trend + seasonal + noise

# Create time series and decompose
ts = pd.Series(passengers, index=dates)
decomposition = seasonal_decompose(ts, model="additive", period=12)

# Create subplots (4 rows, shared x-axis)
fig = make_subplots(
    rows=4,
    cols=1,
    shared_xaxes=True,
    vertical_spacing=0.08,
    subplot_titles=("Original", "Trend", "Seasonal", "Residual"),
)

# Color scheme
primary_color = "#306998"  # Python Blue
secondary_color = "#FFD43B"  # Python Yellow

# Original series
fig.add_trace(
    go.Scatter(x=dates, y=ts.values, mode="lines", line=dict(color=primary_color, width=2.5), name="Original"),
    row=1,
    col=1,
)

# Trend component
fig.add_trace(
    go.Scatter(
        x=dates,
        y=decomposition.trend,
        mode="lines",
        line=dict(color="#2E8B57", width=3),  # Sea green for trend
        name="Trend",
    ),
    row=2,
    col=1,
)

# Seasonal component
fig.add_trace(
    go.Scatter(
        x=dates,
        y=decomposition.seasonal,
        mode="lines",
        line=dict(color="#E07020", width=2.5),  # Orange for seasonal
        name="Seasonal",
    ),
    row=3,
    col=1,
)

# Residual component
fig.add_trace(
    go.Scatter(
        x=dates,
        y=decomposition.resid,
        mode="lines",
        line=dict(color="#8B4789", width=2),  # Purple for residual
        name="Residual",
    ),
    row=4,
    col=1,
)

# Update layout for large canvas
fig.update_layout(
    title=dict(text="timeseries-decomposition · plotly · pyplots.ai", font=dict(size=32), x=0.5, xanchor="center"),
    template="plotly_white",
    showlegend=False,
    height=900,
    width=1600,
    margin=dict(l=100, r=60, t=100, b=80),
)

# Update all y-axes
y_axis_titles = ["Passengers (thousands)", "Trend", "Seasonal Component", "Residual"]
for i, title in enumerate(y_axis_titles, 1):
    fig.update_yaxes(
        title=dict(text=title, font=dict(size=20)),
        tickfont=dict(size=16),
        gridcolor="rgba(128, 128, 128, 0.2)",
        gridwidth=1,
        row=i,
        col=1,
    )

# Update x-axes
for i in range(1, 5):
    fig.update_xaxes(tickfont=dict(size=16), gridcolor="rgba(128, 128, 128, 0.2)", gridwidth=1, row=i, col=1)

# Bottom x-axis label
fig.update_xaxes(title=dict(text="Date", font=dict(size=20)), row=4, col=1)

# Update subplot titles font size
for annotation in fig.layout.annotations:
    annotation.font.size = 22

# Save as PNG (4800 x 2700 px)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save interactive HTML version
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
