""" pyplots.ai
polar-basic: Basic Polar Chart
Library: plotly 6.5.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import numpy as np
import plotly.graph_objects as go


# Data - Hourly temperature readings over 24 hours (cyclical pattern)
np.random.seed(42)
hours = np.arange(0, 24)
theta = hours * 15  # Convert hours to degrees (360/24 = 15 degrees per hour)

# Temperature pattern: cooler at night, warmer during day
base_temp = 15 + 10 * np.sin(np.radians(theta - 90))  # Peak at noon (hour 12 = 180 degrees)
noise = np.random.randn(24) * 1.5
radius = base_temp + noise

# Create polar chart
fig = go.Figure()

# Add baseline reference circle at r=0 for clarity
baseline_theta = np.linspace(0, 360, 100)
fig.add_trace(
    go.Scatterpolar(
        r=[0] * 100,
        theta=baseline_theta,
        mode="lines",
        line={"width": 2, "color": "rgba(0, 0, 0, 0.5)"},
        showlegend=False,
        hoverinfo="skip",
    )
)

# Main temperature trace
fig.add_trace(
    go.Scatterpolar(
        r=radius,
        theta=theta,
        mode="markers+lines",
        marker={"size": 16, "color": "#306998"},
        line={"width": 3, "color": "#306998"},
        fill="toself",
        fillcolor="rgba(48, 105, 152, 0.2)",
        name="Temperature",
    )
)

# Layout with appropriate sizing for 4800x2700 px
fig.update_layout(
    title={"text": "polar-basic · plotly · pyplots.ai", "font": {"size": 28}, "x": 0.5, "xanchor": "center"},
    polar={
        "radialaxis": {
            "visible": True,
            "range": [0, max(radius) * 1.1],
            "tickfont": {"size": 18},
            "title": {"text": "Temperature (°C)", "font": {"size": 22}},
            "gridcolor": "rgba(0, 0, 0, 0.35)",
            "gridwidth": 1,
            "linecolor": "rgba(0, 0, 0, 0.5)",
            "linewidth": 2,
        },
        "angularaxis": {
            "tickmode": "array",
            "tickvals": list(range(0, 360, 30)),
            "ticktext": ["0h", "2h", "4h", "6h", "8h", "10h", "12h", "14h", "16h", "18h", "20h", "22h"],
            "tickfont": {"size": 18},
            "gridcolor": "rgba(0, 0, 0, 0.35)",
            "gridwidth": 1,
            "direction": "clockwise",
            "rotation": 90,  # Start at top (midnight)
            "linecolor": "rgba(0, 0, 0, 0.5)",
            "linewidth": 2,
        },
        "bgcolor": "white",
    },
    template="plotly_white",
    showlegend=False,
    margin={"l": 80, "r": 80, "t": 120, "b": 80},
)

# Save as PNG (4800x2700 px) and HTML for interactivity
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html")
