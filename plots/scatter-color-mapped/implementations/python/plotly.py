""" pyplots.ai
scatter-color-mapped: Color-Mapped Scatter Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-26
"""

import numpy as np
import plotly.graph_objects as go


# Data - Temperature readings across geographic coordinates
np.random.seed(42)
n_points = 150

# Geographic-like coordinates
longitude = np.random.uniform(-120, -70, n_points)
latitude = np.random.uniform(25, 50, n_points)

# Temperature varies with latitude (cooler north, warmer south) plus random variation
temperature = 40 - 0.6 * (latitude - 25) + np.random.randn(n_points) * 5

# Create scatter plot with color mapping
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=longitude,
        y=latitude,
        mode="markers",
        marker=dict(
            size=18,
            color=temperature,
            colorscale="Viridis",
            colorbar=dict(
                title=dict(text="Temperature (°F)", font=dict(size=20)), tickfont=dict(size=16), thickness=25, len=0.8
            ),
            opacity=0.8,
            line=dict(width=1, color="white"),
        ),
        hovertemplate="Longitude: %{x:.1f}°<br>Latitude: %{y:.1f}°<br>Temperature: %{marker.color:.1f}°F<extra></extra>",
    )
)

# Update layout for large canvas
fig.update_layout(
    title=dict(text="scatter-color-mapped · plotly · pyplots.ai", font=dict(size=28), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Longitude (°W)", font=dict(size=22)),
        tickfont=dict(size=18),
        gridcolor="rgba(128, 128, 128, 0.3)",
        gridwidth=1,
        zeroline=False,
    ),
    yaxis=dict(
        title=dict(text="Latitude (°N)", font=dict(size=22)),
        tickfont=dict(size=18),
        gridcolor="rgba(128, 128, 128, 0.3)",
        gridwidth=1,
        zeroline=False,
    ),
    template="plotly_white",
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(l=100, r=120, t=100, b=100),
)

# Save as PNG (4800 x 2700 px) and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
