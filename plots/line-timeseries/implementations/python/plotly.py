""" pyplots.ai
line-timeseries: Time Series Line Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Data - Daily temperature readings over one year
np.random.seed(42)
dates = pd.date_range(start="2024-01-01", end="2024-12-31", freq="D")

# Create realistic temperature pattern with seasonal variation
day_of_year = np.arange(len(dates))
seasonal = 15 * np.sin(2 * np.pi * (day_of_year - 80) / 365)  # Peak around late July
baseline = 12  # Average temperature
noise = np.random.randn(len(dates)) * 3
temperatures = baseline + seasonal + noise

df = pd.DataFrame({"date": dates, "temperature": temperatures})

# Create plot
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=df["date"],
        y=df["temperature"],
        mode="lines",
        line={"color": "#306998", "width": 2.5},
        name="Temperature",
        hovertemplate="Date: %{x|%b %d, %Y}<br>Temperature: %{y:.1f}°C<extra></extra>",
    )
)

# Layout for 4800x2700 px
fig.update_layout(
    title={
        "text": "Daily Temperature 2024 · line-timeseries · plotly · pyplots.ai",
        "font": {"size": 32},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Date", "font": {"size": 24}},
        "tickfont": {"size": 18},
        "tickformat": "%b %Y",
        "dtick": "M1",
        "gridcolor": "rgba(128, 128, 128, 0.3)",
        "gridwidth": 1,
        "showgrid": True,
    },
    yaxis={
        "title": {"text": "Temperature (°C)", "font": {"size": 24}},
        "tickfont": {"size": 18},
        "gridcolor": "rgba(128, 128, 128, 0.3)",
        "gridwidth": 1,
        "showgrid": True,
    },
    template="plotly_white",
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin={"l": 100, "r": 80, "t": 120, "b": 100},
    showlegend=False,
)

# Save as PNG (4800x2700 px) and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
