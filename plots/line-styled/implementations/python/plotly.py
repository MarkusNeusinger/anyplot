""" pyplots.ai
line-styled: Styled Line Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 94/100 | Created: 2025-12-30
"""

import numpy as np
import plotly.graph_objects as go


# Data - Temperature readings from different sensors over 24 hours
np.random.seed(42)
hours = np.arange(0, 24)

# Simulate temperature patterns for different locations
sensor_a = 15 + 8 * np.sin((hours - 6) * np.pi / 12) + np.random.normal(0, 0.5, 24)  # Outdoor
sensor_b = 20 + 3 * np.sin((hours - 8) * np.pi / 12) + np.random.normal(0, 0.3, 24)  # Indoor
sensor_c = 18 + 5 * np.sin((hours - 7) * np.pi / 12) + np.random.normal(0, 0.4, 24)  # Greenhouse
sensor_d = 22 + 2 * np.sin((hours - 10) * np.pi / 12) + np.random.normal(0, 0.2, 24)  # Storage

# Create figure
fig = go.Figure()

# Add traces with different line styles
fig.add_trace(
    go.Scatter(
        x=hours, y=sensor_a, mode="lines", name="Outdoor Sensor", line=dict(dash="solid", width=4, color="#306998")
    )
)

fig.add_trace(
    go.Scatter(
        x=hours, y=sensor_b, mode="lines", name="Indoor Sensor", line=dict(dash="dash", width=4, color="#FFD43B")
    )
)

fig.add_trace(
    go.Scatter(
        x=hours, y=sensor_c, mode="lines", name="Greenhouse Sensor", line=dict(dash="dot", width=4, color="#4CAF50")
    )
)

fig.add_trace(
    go.Scatter(
        x=hours, y=sensor_d, mode="lines", name="Storage Sensor", line=dict(dash="dashdot", width=4, color="#9C27B0")
    )
)

# Update layout
fig.update_layout(
    title=dict(text="line-styled · plotly · pyplots.ai", font=dict(size=32), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Hour of Day", font=dict(size=24)),
        tickfont=dict(size=20),
        tickmode="linear",
        tick0=0,
        dtick=4,
        gridcolor="rgba(0,0,0,0.1)",
        gridwidth=1,
        range=[-0.5, 23.5],
    ),
    yaxis=dict(
        title=dict(text="Temperature (°C)", font=dict(size=24)),
        tickfont=dict(size=20),
        gridcolor="rgba(0,0,0,0.1)",
        gridwidth=1,
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
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(l=100, r=60, t=100, b=80),
)

# Save as PNG (4800 x 2700 px)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save as HTML for interactivity
fig.write_html("plot.html", include_plotlyjs="cdn")
