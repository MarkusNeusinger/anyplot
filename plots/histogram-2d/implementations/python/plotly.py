""" pyplots.ai
histogram-2d: 2D Histogram Heatmap
Library: plotly 6.5.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Data - financial returns for two correlated assets (5000 daily returns)
np.random.seed(42)
n_points = 5000

# Create correlated returns with realistic financial structure
mean = [0.05, 0.03]  # Mean daily returns in percent
cov = [[0.8, 0.56], [0.56, 0.8]]  # Positive correlation (0.7)
data = np.random.multivariate_normal(mean, cov, n_points)
x = data[:, 0]
y = data[:, 1]

# Create figure with marginal histograms using shared_xaxes/shared_yaxes
fig = make_subplots(
    rows=2,
    cols=2,
    column_widths=[0.8, 0.2],
    row_heights=[0.2, 0.8],
    horizontal_spacing=0.01,
    vertical_spacing=0.01,
    shared_xaxes=True,
    shared_yaxes=True,
    specs=[[{"type": "histogram"}, None], [{"type": "histogram2d"}, {"type": "histogram"}]],
)

# Main 2D histogram heatmap
fig.add_trace(
    go.Histogram2d(
        x=x,
        y=y,
        colorscale="Viridis",
        nbinsx=40,
        nbinsy=40,
        colorbar=dict(
            title=dict(text="Count", font=dict(size=20)), tickfont=dict(size=16), len=0.65, y=0.35, yanchor="middle"
        ),
    ),
    row=2,
    col=1,
)

# Marginal histogram for X (top)
fig.add_trace(
    go.Histogram(x=x, nbinsx=40, marker=dict(color="#306998", line=dict(width=0)), showlegend=False), row=1, col=1
)

# Marginal histogram for Y (right)
fig.add_trace(
    go.Histogram(y=y, nbinsy=40, marker=dict(color="#306998", line=dict(width=0)), showlegend=False), row=2, col=2
)

# Update layout
fig.update_layout(
    title=dict(text="histogram-2d · plotly · pyplots.ai", font=dict(size=32), x=0.5, xanchor="center", y=0.98),
    template="plotly_white",
    bargap=0.02,
)

# Update axes for main plot with application context labels
fig.update_xaxes(title=dict(text="Stock A Daily Return (%)", font=dict(size=22)), tickfont=dict(size=18), row=2, col=1)
fig.update_yaxes(title=dict(text="Stock B Daily Return (%)", font=dict(size=22)), tickfont=dict(size=18), row=2, col=1)

# Hide axis labels for marginal plots
fig.update_xaxes(showticklabels=False, row=1, col=1)
fig.update_yaxes(showticklabels=False, row=1, col=1)
fig.update_xaxes(showticklabels=False, row=2, col=2)
fig.update_yaxes(showticklabels=False, row=2, col=2)

# Save as PNG (4800 x 2700 px)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save as interactive HTML
fig.write_html("plot.html", include_plotlyjs="cdn")
