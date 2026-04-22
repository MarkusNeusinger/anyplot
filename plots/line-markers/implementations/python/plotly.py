""" pyplots.ai
line-markers: Line Plot with Markers
Library: plotly 6.5.0 | Python 3.13.11
Quality: 94/100 | Created: 2025-12-30
"""

import numpy as np
import plotly.graph_objects as go


# Data - experimental temperature readings over time
np.random.seed(42)
x = np.arange(0, 15)

# Three sensor series with different patterns
sensor_a = 20 + np.cumsum(np.random.randn(15) * 0.8)
sensor_b = 22 + np.cumsum(np.random.randn(15) * 0.6) - 2
sensor_c = 18 + np.cumsum(np.random.randn(15) * 1.0) + 1

# Create figure
fig = go.Figure()

# Add traces with different marker styles
fig.add_trace(
    go.Scatter(
        x=x,
        y=sensor_a,
        mode="lines+markers",
        name="Sensor A",
        line=dict(color="#306998", width=4),
        marker=dict(size=16, symbol="circle", color="#306998", line=dict(width=2, color="white")),
    )
)

fig.add_trace(
    go.Scatter(
        x=x,
        y=sensor_b,
        mode="lines+markers",
        name="Sensor B",
        line=dict(color="#FFD43B", width=4),
        marker=dict(size=16, symbol="square", color="#FFD43B", line=dict(width=2, color="#333333")),
    )
)

fig.add_trace(
    go.Scatter(
        x=x,
        y=sensor_c,
        mode="lines+markers",
        name="Sensor C",
        line=dict(color="#E55934", width=4),
        marker=dict(size=16, symbol="diamond", color="#E55934", line=dict(width=2, color="white")),
    )
)

# Layout
fig.update_layout(
    title=dict(text="line-markers · plotly · pyplots.ai", font=dict(size=32), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Time (hours)", font=dict(size=24)),
        tickfont=dict(size=20),
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(0,0,0,0.1)",
        dtick=2,
    ),
    yaxis=dict(
        title=dict(text="Temperature (°C)", font=dict(size=24)),
        tickfont=dict(size=20),
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(0,0,0,0.1)",
    ),
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
    template="plotly_white",
    margin=dict(l=100, r=60, t=100, b=80),
    plot_bgcolor="white",
)

# Save as PNG and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
