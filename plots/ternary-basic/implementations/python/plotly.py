""" pyplots.ai
ternary-basic: Basic Ternary Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

import numpy as np
import plotly.graph_objects as go


# Data - Soil composition samples (sand, silt, clay) that sum to 100%
np.random.seed(42)
n_points = 50

# Generate random compositions that sum to 100
raw = np.random.rand(n_points, 3)
totals = raw.sum(axis=1, keepdims=True)
compositions = (raw / totals) * 100

sand = compositions[:, 0]
silt = compositions[:, 1]
clay = compositions[:, 2]

# Create ternary plot
fig = go.Figure(
    go.Scatterternary(
        a=sand,
        b=silt,
        c=clay,
        mode="markers",
        marker={"size": 18, "color": "#306998", "opacity": 0.7, "line": {"width": 1, "color": "white"}},
        hovertemplate="Sand: %{a:.1f}%<br>Silt: %{b:.1f}%<br>Clay: %{c:.1f}%<extra></extra>",
    )
)

# Layout and styling
fig.update_layout(
    title={"text": "ternary-basic · plotly · pyplots.ai", "font": {"size": 48}, "x": 0.5, "xanchor": "center"},
    ternary={
        "sum": 100,
        "aaxis": {
            "title": {"text": "Sand (%)", "font": {"size": 32}},
            "tickmode": "linear",
            "tick0": 0,
            "dtick": 20,
            "tickfont": {"size": 22},
            "linewidth": 2,
            "gridwidth": 1,
            "gridcolor": "rgba(0,0,0,0.2)",
        },
        "baxis": {
            "title": {"text": "Silt (%)", "font": {"size": 32}},
            "tickmode": "linear",
            "tick0": 0,
            "dtick": 20,
            "tickfont": {"size": 22},
            "linewidth": 2,
            "gridwidth": 1,
            "gridcolor": "rgba(0,0,0,0.2)",
        },
        "caxis": {
            "title": {"text": "Clay (%)", "font": {"size": 32}},
            "tickmode": "linear",
            "tick0": 0,
            "dtick": 20,
            "tickfont": {"size": 22},
            "linewidth": 2,
            "gridwidth": 1,
            "gridcolor": "rgba(0,0,0,0.2)",
        },
        "bgcolor": "white",
    },
    paper_bgcolor="white",
    plot_bgcolor="white",
    margin={"l": 100, "r": 100, "t": 150, "b": 100},
)

# Save as PNG (4800x2700 px)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save interactive HTML
fig.write_html("plot.html", include_plotlyjs="cdn")
