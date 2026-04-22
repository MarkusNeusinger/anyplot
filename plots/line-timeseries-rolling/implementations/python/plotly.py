""" pyplots.ai
line-timeseries-rolling: Time Series with Rolling Average Overlay
Library: plotly 6.5.0 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Data - Daily temperature readings with noise
np.random.seed(42)

# Generate 200 days of data
dates = pd.date_range("2024-01-01", periods=200, freq="D")

# Create realistic temperature pattern with seasonal trend + noise
days = np.arange(200)
seasonal = 15 * np.sin(2 * np.pi * days / 365 - np.pi / 2)  # Seasonal component
trend = 0.02 * days  # Slight warming trend
noise = np.random.randn(200) * 3  # Daily fluctuations
base_temp = 12  # Base temperature (Celsius)

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
    go.Scatter(
        x=df["date"], y=df["value"], mode="lines", name="Raw Data", line=dict(color="#306998", width=1.5), opacity=0.4
    )
)

# Rolling average - prominent smooth line
fig.add_trace(
    go.Scatter(
        x=df["date"],
        y=df["rolling_avg"],
        mode="lines",
        name=f"{window_size}-Day Rolling Average",
        line=dict(color="#FFD43B", width=4),
    )
)

# Layout for 4800x2700 canvas
fig.update_layout(
    title=dict(text="line-timeseries-rolling · plotly · pyplots.ai", font=dict(size=32), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Date", font=dict(size=24)),
        tickfont=dict(size=18),
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(0,0,0,0.1)",
    ),
    yaxis=dict(
        title=dict(text="Temperature (°C)", font=dict(size=24)),
        tickfont=dict(size=18),
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(0,0,0,0.1)",
    ),
    template="plotly_white",
    legend=dict(
        font=dict(size=20),
        x=0.02,
        y=0.98,
        xanchor="left",
        yanchor="top",
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor="rgba(0,0,0,0.2)",
        borderwidth=1,
    ),
    margin=dict(l=100, r=50, t=100, b=80),
    plot_bgcolor="white",
)

# Save as PNG (4800x2700)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save interactive HTML
fig.write_html("plot.html", include_plotlyjs="cdn")
