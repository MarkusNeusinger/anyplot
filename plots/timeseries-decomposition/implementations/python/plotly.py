""" anyplot.ai
timeseries-decomposition: Time Series Decomposition Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-14
"""

import os
import sys

sys.path.pop(0)

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from statsmodels.tsa.seasonal import seasonal_decompose

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data: Monthly airline passengers (classic time series)
np.random.seed(42)
dates = pd.date_range(start="2014-01-01", periods=120, freq="MS")
trend = np.linspace(100, 250, 120)
seasonal = 30 * np.sin(2 * np.pi * np.arange(120) / 12)
noise = np.random.normal(0, 10, 120)
passengers = trend + seasonal + noise

# Time series and decomposition
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

# Add traces for each component
fig.add_trace(
    go.Scatter(
        x=dates,
        y=ts.values,
        mode="lines",
        line=dict(color=IMPRINT[0], width=2.5),
        name="Original",
        hovertemplate="<b>Original</b><br>Date: %{x|%Y-%m}<br>Value: %{y:.1f}<extra></extra>",
    ),
    row=1,
    col=1,
)

fig.add_trace(
    go.Scatter(
        x=dates,
        y=decomposition.trend,
        mode="lines",
        line=dict(color=IMPRINT[1], width=3),
        name="Trend",
        hovertemplate="<b>Trend</b><br>Date: %{x|%Y-%m}<br>Value: %{y:.1f}<extra></extra>",
    ),
    row=2,
    col=1,
)

fig.add_trace(
    go.Scatter(
        x=dates,
        y=decomposition.seasonal,
        mode="lines",
        line=dict(color=IMPRINT[2], width=2.5),
        name="Seasonal",
        hovertemplate="<b>Seasonal</b><br>Date: %{x|%Y-%m}<br>Value: %{y:.1f}<extra></extra>",
    ),
    row=3,
    col=1,
)

fig.add_trace(
    go.Scatter(
        x=dates,
        y=decomposition.resid,
        mode="lines",
        line=dict(color=IMPRINT[3], width=2),
        name="Residual",
        hovertemplate="<b>Residual</b><br>Date: %{x|%Y-%m}<br>Value: %{y:.1f}<extra></extra>",
    ),
    row=4,
    col=1,
)

# Update layout
fig.update_layout(
    title=dict(text="timeseries-decomposition · plotly · anyplot.ai", font=dict(size=28, color=INK), x=0.5, xanchor="center"),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    showlegend=False,
    height=900,
    width=1600,
    margin=dict(l=100, r=60, t=100, b=80),
)

# Update all y-axes with theme-adaptive colors
y_axis_titles = ["Passengers", "Trend", "Seasonal", "Residual"]
for i, title in enumerate(y_axis_titles, 1):
    fig.update_yaxes(
        title=dict(text=title, font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        gridcolor=GRID,
        gridwidth=1,
        linecolor=INK_SOFT,
        row=i,
        col=1,
    )

# Update x-axes
for i in range(1, 5):
    fig.update_xaxes(
        tickfont=dict(size=18, color=INK_SOFT),
        gridcolor=GRID,
        gridwidth=1,
        linecolor=INK_SOFT,
        row=i,
        col=1,
    )

# Bottom x-axis label
fig.update_xaxes(title=dict(text="Date", font=dict(size=22, color=INK)), row=4, col=1)

# Update subplot titles font size and color
for annotation in fig.layout.annotations:
    annotation.font.size = 22
    annotation.font.color = INK

# Save as PNG and HTML
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
