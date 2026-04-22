""" pyplots.ai
density-rug: Density Plot with Rug Marks
Library: plotly 6.5.1 | Python 3.13.11
Quality: 93/100 | Created: 2026-01-09
"""

import numpy as np
import plotly.graph_objects as go
from scipy.stats import gaussian_kde


# Data - Response times for a web application (in milliseconds)
np.random.seed(42)
# Create a bimodal distribution to show interesting KDE behavior
response_times = np.concatenate(
    [
        np.random.normal(120, 25, 80),  # Fast responses
        np.random.normal(250, 40, 40),  # Slower responses
    ]
)

# Compute KDE
kde = gaussian_kde(response_times)
x_range = np.linspace(response_times.min() - 30, response_times.max() + 30, 500)
density = kde(x_range)

# Create figure
fig = go.Figure()

# Add filled KDE curve
fig.add_trace(
    go.Scatter(
        x=x_range,
        y=density,
        mode="lines",
        fill="tozeroy",
        fillcolor="rgba(48, 105, 152, 0.35)",
        line=dict(color="#306998", width=3),
        name="Density",
        hovertemplate="Time: %{x:.1f} ms<br>Density: %{y:.4f}<extra></extra>",
    )
)

# Add rug marks at y=0
rug_height = max(density) * 0.04
fig.add_trace(
    go.Scatter(
        x=response_times,
        y=np.zeros_like(response_times) - rug_height * 0.5,
        mode="markers",
        marker=dict(
            symbol="line-ns",
            size=14,
            line=dict(width=2, color="rgba(48, 105, 152, 0.6)"),
            color="rgba(48, 105, 152, 0.6)",
        ),
        name="Observations",
        hovertemplate="Response Time: %{x:.1f} ms<extra></extra>",
    )
)

# Layout
fig.update_layout(
    title=dict(text="density-rug · plotly · pyplots.ai", font=dict(size=32, color="#333"), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Response Time (ms)", font=dict(size=24)),
        tickfont=dict(size=18),
        gridcolor="rgba(0, 0, 0, 0.1)",
        gridwidth=1,
        zeroline=False,
        showline=True,
        linewidth=2,
        linecolor="#666",
    ),
    yaxis=dict(
        title=dict(text="Density", font=dict(size=24)),
        tickfont=dict(size=18),
        gridcolor="rgba(0, 0, 0, 0.1)",
        gridwidth=1,
        zeroline=False,
        showline=True,
        linewidth=2,
        linecolor="#666",
        rangemode="tozero",
    ),
    template="plotly_white",
    showlegend=True,
    legend=dict(
        font=dict(size=18),
        x=0.98,
        y=0.98,
        xanchor="right",
        yanchor="top",
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="rgba(0, 0, 0, 0.2)",
        borderwidth=1,
    ),
    margin=dict(l=100, r=60, t=100, b=100),
    plot_bgcolor="white",
)

# Adjust y-axis range to include rug marks below zero
fig.update_yaxes(range=[-rug_height * 1.5, max(density) * 1.08])

# Save as PNG (4800 x 2700 px)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save interactive HTML
fig.write_html("plot.html", include_plotlyjs="cdn")
