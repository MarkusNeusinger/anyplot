""" pyplots.ai
scatter-regression-lowess: Scatter Plot with LOWESS Regression
Library: plotly 6.5.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import numpy as np
import plotly.graph_objects as go


# Data - Generate non-linear relationship with varying patterns
np.random.seed(42)
n_points = 200
x = np.linspace(0, 10, n_points)
# Complex non-linear relationship: combination of sinusoidal and polynomial
y = 2 * np.sin(x) + 0.3 * x**2 - x + np.random.normal(0, 1.5, n_points)

# LOWESS smoothing (Locally Weighted Scatterplot Smoothing)
frac = 0.3
n = len(x)
k = int(np.ceil(frac * n))  # Number of neighbors to use

# Sort data by x for processing
sorted_idx = np.argsort(x)
x_sorted = x[sorted_idx]
y_sorted = y[sorted_idx]
y_smooth = np.zeros(n)

# Calculate smoothed values for each point
for i in range(n):
    # Distances from current point to all points
    distances = np.abs(x_sorted - x_sorted[i])

    # Find k nearest neighbors
    neighbor_idx = np.argsort(distances)[:k]
    max_dist = distances[neighbor_idx[-1]]

    # Tricube weight function: w = (1 - (d/max_d)^3)^3
    if max_dist > 0:
        u = distances[neighbor_idx] / max_dist
        weights = (1 - u**3) ** 3
    else:
        weights = np.ones(k)

    # Weighted least squares regression
    x_neighbors = x_sorted[neighbor_idx]
    y_neighbors = y_sorted[neighbor_idx]

    sum_w = np.sum(weights)
    sum_wx = np.sum(weights * x_neighbors)
    sum_wy = np.sum(weights * y_neighbors)
    sum_wxx = np.sum(weights * x_neighbors**2)
    sum_wxy = np.sum(weights * x_neighbors * y_neighbors)

    denom = sum_w * sum_wxx - sum_wx**2
    if np.abs(denom) > 1e-10:
        b = (sum_w * sum_wxy - sum_wx * sum_wy) / denom
        a = (sum_wy - b * sum_wx) / sum_w
        y_smooth[i] = a + b * x_sorted[i]
    else:
        y_smooth[i] = sum_wy / sum_w if sum_w > 0 else y_sorted[i]

x_lowess = x_sorted
y_lowess = y_smooth

# Create figure
fig = go.Figure()

# Add scatter points
fig.add_trace(
    go.Scatter(
        x=x,
        y=y,
        mode="markers",
        name="Data Points",
        marker=dict(
            size=10,
            color="#306998",  # Python Blue
            opacity=0.6,
        ),
    )
)

# Add LOWESS curve
fig.add_trace(
    go.Scatter(
        x=x_lowess,
        y=y_lowess,
        mode="lines",
        name="LOWESS Curve",
        line=dict(
            color="#FFD43B",  # Python Yellow
            width=4,
        ),
    )
)

# Update layout for large canvas
fig.update_layout(
    title=dict(text="scatter-regression-lowess · plotly · pyplots.ai", font=dict(size=28), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="X Value", font=dict(size=22)), tickfont=dict(size=18), gridcolor="rgba(0,0,0,0.1)", gridwidth=1
    ),
    yaxis=dict(
        title=dict(text="Y Value", font=dict(size=22)), tickfont=dict(size=18), gridcolor="rgba(0,0,0,0.1)", gridwidth=1
    ),
    template="plotly_white",
    legend=dict(font=dict(size=18), x=0.02, y=0.98, xanchor="left", yanchor="top", bgcolor="rgba(255,255,255,0.8)"),
    margin=dict(l=80, r=40, t=80, b=80),
)

# Save as PNG (4800 x 2700 px)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save as HTML for interactivity
fig.write_html("plot.html")
