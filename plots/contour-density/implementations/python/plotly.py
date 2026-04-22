""" pyplots.ai
contour-density: Density Contour Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import numpy as np
import plotly.graph_objects as go


# Data - bivariate distribution with multiple clusters
np.random.seed(42)

# Create three clusters to show density variations
n_points = 500
cluster1_x = np.random.normal(2, 0.8, n_points // 3)
cluster1_y = np.random.normal(3, 0.6, n_points // 3)

cluster2_x = np.random.normal(5, 1.0, n_points // 3)
cluster2_y = np.random.normal(5, 0.8, n_points // 3)

cluster3_x = np.random.normal(7, 0.5, n_points // 3)
cluster3_y = np.random.normal(2.5, 0.7, n_points // 3)

x = np.concatenate([cluster1_x, cluster2_x, cluster3_x])
y = np.concatenate([cluster1_y, cluster2_y, cluster3_y])

# Create figure with density contour
fig = go.Figure()

# Add density contour plot
fig.add_trace(
    go.Histogram2dContour(
        x=x,
        y=y,
        colorscale=[[0, "rgba(255,255,255,0)"], [0.2, "#FFD43B"], [0.5, "#306998"], [1, "#1a3d5c"]],
        contours=dict(showlabels=False, coloring="fill"),
        ncontours=12,
        showscale=True,
        colorbar=dict(title=dict(text="Density", font=dict(size=20)), tickfont=dict(size=16), len=0.8),
        line=dict(width=2, color="#306998"),
    )
)

# Add scatter points for context (semi-transparent)
fig.add_trace(
    go.Scatter(
        x=x,
        y=y,
        mode="markers",
        marker=dict(size=8, color="#306998", opacity=0.3, line=dict(width=0)),
        showlegend=False,
    )
)

# Update layout
fig.update_layout(
    title=dict(text="contour-density · plotly · pyplots.ai", font=dict(size=32), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="X Variable", font=dict(size=24)),
        tickfont=dict(size=18),
        showgrid=True,
        gridcolor="rgba(0,0,0,0.1)",
        gridwidth=1,
    ),
    yaxis=dict(
        title=dict(text="Y Variable", font=dict(size=24)),
        tickfont=dict(size=18),
        showgrid=True,
        gridcolor="rgba(0,0,0,0.1)",
        gridwidth=1,
    ),
    template="plotly_white",
    width=1600,
    height=900,
    margin=dict(l=100, r=120, t=100, b=100),
)

# Save as PNG and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
