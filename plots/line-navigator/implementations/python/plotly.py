""" pyplots.ai
line-navigator: Line Chart with Mini Navigator
Library: plotly 6.5.2 | Python 3.13.11
Quality: 94/100 | Created: 2026-01-20
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Data - Daily sensor readings over 3 years (1095+ data points)
np.random.seed(42)
dates = pd.date_range("2022-01-01", periods=1100, freq="D")

# Simulate temperature sensor data with seasonal patterns and noise
days_of_year = np.arange(1100) % 365
seasonal = 15 * np.sin(2 * np.pi * days_of_year / 365)  # Seasonal cycle
trend = np.linspace(0, 3, 1100)  # Slight warming trend
noise = np.random.randn(1100) * 2
values = 20 + seasonal + trend + noise  # Base temp around 20C

df = pd.DataFrame({"date": dates, "value": values})

# Create figure with main line chart
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=df["date"],
        y=df["value"],
        mode="lines",
        name="Temperature",
        line={"color": "#306998", "width": 2},
        hovertemplate="%{x|%Y-%m-%d}<br>Temperature: %{y:.1f}°C<extra></extra>",
    )
)

# Layout with rangeslider (mini navigator)
fig.update_layout(
    title={
        "text": "Temperature Sensor Data · line-navigator · plotly · pyplots.ai",
        "font": {"size": 28},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Date", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "rangeslider": {
            "visible": True,
            "thickness": 0.15,  # 15% of chart height
            "bgcolor": "#f8f9fa",
            "bordercolor": "#dee2e6",
            "borderwidth": 1,
        },
        "rangeselector": {
            "buttons": [
                {"count": 1, "label": "1M", "step": "month", "stepmode": "backward"},
                {"count": 3, "label": "3M", "step": "month", "stepmode": "backward"},
                {"count": 6, "label": "6M", "step": "month", "stepmode": "backward"},
                {"count": 1, "label": "1Y", "step": "year", "stepmode": "backward"},
                {"step": "all", "label": "All"},
            ],
            "font": {"size": 14},
            "bgcolor": "#ffffff",
            "activecolor": "#306998",
            "bordercolor": "#dee2e6",
            "borderwidth": 1,
            "x": 0,
            "y": 1.08,
        },
        "type": "date",
    },
    yaxis={
        "title": {"text": "Temperature (°C)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "gridcolor": "rgba(0,0,0,0.1)",
        "gridwidth": 1,
    },
    template="plotly_white",
    hovermode="x unified",
    margin={"l": 80, "r": 40, "t": 100, "b": 40},
    showlegend=False,
)

# Save as PNG
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save as HTML for interactivity
fig.write_html("plot.html", include_plotlyjs="cdn")
