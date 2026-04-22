""" pyplots.ai
line-filled: Filled Line Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 94/100 | Created: 2025-12-30
"""

import numpy as np
import plotly.graph_objects as go


# Data - Monthly website traffic over a year
np.random.seed(42)
months = np.arange(1, 13)
month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Generate realistic website traffic pattern (thousands of visitors)
base_traffic = 50
seasonal = 15 * np.sin(2 * np.pi * (months - 3) / 12)  # Peak in summer
trend = 2 * months  # Growing trend
noise = np.random.normal(0, 5, len(months))
traffic = base_traffic + seasonal + trend + noise
traffic = np.maximum(traffic, 10)  # Ensure positive values

# Create figure
fig = go.Figure()

# Add filled area trace
fig.add_trace(
    go.Scatter(
        x=month_labels,
        y=traffic,
        mode="lines",
        name="Website Traffic",
        line=dict(color="#306998", width=4),
        fill="tozeroy",
        fillcolor="rgba(48, 105, 152, 0.35)",
        hovertemplate="%{x}: %{y:.1f}K visitors<extra></extra>",
    )
)

# Update layout
fig.update_layout(
    title=dict(text="line-filled · plotly · pyplots.ai", font=dict(size=32, color="#333333"), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Month", font=dict(size=24)),
        tickfont=dict(size=18),
        showgrid=True,
        gridcolor="rgba(0, 0, 0, 0.1)",
        gridwidth=1,
    ),
    yaxis=dict(
        title=dict(text="Website Visitors (thousands)", font=dict(size=24)),
        tickfont=dict(size=18),
        showgrid=True,
        gridcolor="rgba(0, 0, 0, 0.1)",
        gridwidth=1,
        rangemode="tozero",
    ),
    template="plotly_white",
    showlegend=False,
    margin=dict(l=100, r=60, t=100, b=80),
    plot_bgcolor="white",
    paper_bgcolor="white",
)

# Save as PNG
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save as HTML for interactivity
fig.write_html("plot.html", include_plotlyjs="cdn")
