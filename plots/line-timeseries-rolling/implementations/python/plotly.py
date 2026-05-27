""" anyplot.ai
line-timeseries-rolling: Time Series with Rolling Average Overlay
Library: plotly 6.7.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-13
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.25)" if THEME == "light" else "rgba(240,239,232,0.25)"

# Okabe-Ito palette
BRAND = "#009E73"  # Raw data (first series)
ACCENT = "#C475FD"  # Rolling average

# Data - Daily temperature readings with noise
np.random.seed(42)

# Generate 200 days of data
dates = pd.date_range("2024-01-01", periods=200, freq="D")

# Create realistic temperature pattern with seasonal trend + noise
days = np.arange(200)
seasonal = 15 * np.sin(2 * np.pi * days / 365 - np.pi / 2)
trend = 0.02 * days
noise = np.random.randn(200) * 3
base_temp = 12

raw_values = base_temp + seasonal + trend + noise

# Create DataFrame
df = pd.DataFrame({"date": dates, "value": raw_values})

# Calculate 14-day rolling average
window_size = 14
df["rolling_avg"] = df["value"].rolling(window=window_size, center=False).mean()

# Create figure
fig = go.Figure()

# Raw data - lighter, semi-transparent line
fig.add_trace(
    go.Scatter(x=df["date"], y=df["value"], mode="lines", name="Raw Data", line=dict(color=BRAND, width=2), opacity=0.4)
)

# Rolling average - prominent smooth line
fig.add_trace(
    go.Scatter(
        x=df["date"],
        y=df["rolling_avg"],
        mode="lines",
        name=f"{window_size}-Day Rolling Average",
        line=dict(color=ACCENT, width=4),
    )
)

# Layout for 4800x2700 canvas
fig.update_layout(
    title=dict(
        text="line-timeseries-rolling · plotly · anyplot.ai", font=dict(size=28, color=INK), x=0.5, xanchor="center"
    ),
    xaxis=dict(
        title=dict(text="Date", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        showgrid=True,
        gridwidth=1,
        gridcolor=GRID,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
    ),
    yaxis=dict(
        title=dict(text="Temperature (°C)", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        showgrid=True,
        gridwidth=1,
        gridcolor=GRID,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    legend=dict(
        font=dict(size=20, color=INK_SOFT),
        x=0.02,
        y=0.98,
        xanchor="left",
        yanchor="top",
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
    ),
    margin=dict(l=120, r=60, t=100, b=100),
)

# Save as PNG (4800x2700) and HTML
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
