""" pyplots.ai
elbow-curve: Elbow Curve for K-Means Clustering
Library: plotly 6.5.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import numpy as np
import plotly.graph_objects as go


# Data - simulate K-means inertia values for k=1 to k=12
np.random.seed(42)
k_values = np.arange(1, 13)

# Generate realistic inertia values that decrease with k
# Using exponential decay with some noise to simulate real clustering behavior
base_inertia = 5000
inertia = base_inertia * np.exp(-0.25 * (k_values - 1)) + np.random.normal(0, 30, len(k_values))
inertia = np.maximum(inertia, 100)  # Ensure positive values
inertia = np.sort(inertia)[::-1]  # Ensure monotonic decrease

# Optimal k (elbow point) is around k=4
optimal_k = 4
optimal_inertia = inertia[optimal_k - 1]

# Create figure
fig = go.Figure()

# Main curve with markers
fig.add_trace(
    go.Scatter(
        x=k_values,
        y=inertia,
        mode="lines+markers",
        name="Inertia",
        line=dict(color="#306998", width=4),
        marker=dict(size=16, color="#306998", line=dict(color="white", width=2)),
        hovertemplate="k=%{x}<br>Inertia=%{y:.0f}<extra></extra>",
    )
)

# Highlight the elbow point
fig.add_trace(
    go.Scatter(
        x=[optimal_k],
        y=[optimal_inertia],
        mode="markers",
        name=f"Elbow (k={optimal_k})",
        marker=dict(size=24, color="#FFD43B", symbol="circle", line=dict(color="#306998", width=3)),
        hovertemplate=f"Optimal k={optimal_k}<br>Inertia={optimal_inertia:.0f}<extra></extra>",
    )
)

# Add annotation for the elbow point
fig.add_annotation(
    x=optimal_k,
    y=optimal_inertia,
    text=f"Elbow Point<br>k = {optimal_k}",
    showarrow=True,
    arrowhead=2,
    arrowsize=1.5,
    arrowwidth=2,
    arrowcolor="#306998",
    ax=80,
    ay=-80,
    font=dict(size=20, color="#306998"),
    bgcolor="rgba(255, 255, 255, 0.9)",
    bordercolor="#306998",
    borderwidth=2,
    borderpad=8,
)

# Update layout
fig.update_layout(
    title=dict(text="elbow-curve · plotly · pyplots.ai", font=dict(size=32, color="#333333"), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Number of Clusters (k)", font=dict(size=24)),
        tickfont=dict(size=18),
        tickmode="linear",
        tick0=1,
        dtick=1,
        showgrid=True,
        gridcolor="rgba(0, 0, 0, 0.1)",
        gridwidth=1,
        zeroline=False,
    ),
    yaxis=dict(
        title=dict(text="Within-Cluster Sum of Squares (Inertia)", font=dict(size=24)),
        tickfont=dict(size=18),
        showgrid=True,
        gridcolor="rgba(0, 0, 0, 0.1)",
        gridwidth=1,
        zeroline=False,
    ),
    template="plotly_white",
    showlegend=True,
    legend=dict(
        x=0.95,
        y=0.95,
        xanchor="right",
        yanchor="top",
        font=dict(size=18),
        bgcolor="rgba(255, 255, 255, 0.9)",
        bordercolor="#cccccc",
        borderwidth=1,
    ),
    margin=dict(l=100, r=80, t=100, b=100),
)

# Save as PNG (4800x2700 via scale=3)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save interactive HTML
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
