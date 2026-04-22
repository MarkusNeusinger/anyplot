""" pyplots.ai
histogram-kde: Histogram with KDE Overlay
Library: plotly 6.5.0 | Python 3.13.11
Quality: 98/100 | Created: 2025-12-24
"""

import numpy as np
import plotly.graph_objects as go
from scipy import stats


# Data - Stock returns simulation with realistic distribution
np.random.seed(42)
# Mix of normal returns with slight negative skew (typical for stock returns)
returns = np.concatenate(
    [
        np.random.normal(0.05, 0.8, 400),  # Main distribution
        np.random.normal(-1.5, 0.5, 80),  # Left tail (market drops)
        np.random.normal(1.2, 0.4, 70),  # Right tail (gains)
    ]
)
# Shuffle to mix
np.random.shuffle(returns)

# Calculate KDE
kde = stats.gaussian_kde(returns)
x_kde = np.linspace(returns.min() - 0.5, returns.max() + 0.5, 300)
y_kde = kde(x_kde)

# Calculate histogram for density normalization
hist_counts, bin_edges = np.histogram(returns, bins=35, density=True)
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

# Create figure
fig = go.Figure()

# Add histogram (density normalized)
fig.add_trace(
    go.Bar(
        x=bin_centers,
        y=hist_counts,
        width=(bin_edges[1] - bin_edges[0]) * 0.9,
        marker={"color": "#306998", "opacity": 0.5, "line": {"color": "#306998", "width": 1}},
        name="Histogram",
        hovertemplate="Return: %{x:.2f}%<br>Density: %{y:.3f}<extra></extra>",
    )
)

# Add KDE curve
fig.add_trace(
    go.Scatter(
        x=x_kde,
        y=y_kde,
        mode="lines",
        line={"color": "#FFD43B", "width": 4},
        name="KDE",
        hovertemplate="Return: %{x:.2f}%<br>Density: %{y:.3f}<extra></extra>",
    )
)

# Update layout for 4800x2700 px canvas
fig.update_layout(
    title={
        "text": "histogram-kde · plotly · pyplots.ai",
        "font": {"size": 32, "color": "#333333"},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Daily Return (%)", "font": {"size": 24}},
        "tickfont": {"size": 18},
        "gridcolor": "rgba(0,0,0,0.1)",
        "gridwidth": 1,
        "zeroline": True,
        "zerolinecolor": "rgba(0,0,0,0.2)",
        "zerolinewidth": 2,
    },
    yaxis={
        "title": {"text": "Density", "font": {"size": 24}},
        "tickfont": {"size": 18},
        "gridcolor": "rgba(0,0,0,0.1)",
        "gridwidth": 1,
    },
    template="plotly_white",
    legend={
        "font": {"size": 20},
        "x": 0.98,
        "y": 0.98,
        "xanchor": "right",
        "yanchor": "top",
        "bgcolor": "rgba(255,255,255,0.8)",
        "bordercolor": "rgba(0,0,0,0.1)",
        "borderwidth": 1,
    },
    margin={"l": 100, "r": 80, "t": 120, "b": 100},
    bargap=0.05,
)

# Save as PNG
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save as HTML for interactivity
fig.write_html("plot.html", include_plotlyjs="cdn")
