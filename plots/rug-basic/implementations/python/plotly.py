""" pyplots.ai
rug-basic: Basic Rug Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import numpy as np
import plotly.graph_objects as go


# Data - bimodal distribution to show clustering patterns and gaps
np.random.seed(42)
group1 = np.random.normal(loc=25, scale=5, size=80)
group2 = np.random.normal(loc=55, scale=8, size=60)
gap_region = np.array([38, 42])  # Few points in gap to show data sparsity
values = np.concatenate([group1, group2, gap_region])

# Create figure
fig = go.Figure()

# Rug plot as scatter trace with vertical line markers at y=0
fig.add_trace(
    go.Scatter(
        x=values,
        y=np.zeros_like(values),
        mode="markers",
        marker={"symbol": "line-ns", "size": 20, "line": {"width": 2, "color": "#306998"}, "color": "#306998"},
        opacity=0.6,
        hovertemplate="Value: %{x:.2f}<extra></extra>",
        showlegend=False,
    )
)

# Layout
fig.update_layout(
    title={"text": "rug-basic · plotly · pyplots.ai", "font": {"size": 48}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "Response Time (ms)", "font": {"size": 36}},
        "tickfont": {"size": 28},
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": "rgba(0,0,0,0.1)",
        "zeroline": False,
    },
    yaxis={
        "title": {"text": "", "font": {"size": 36}},
        "tickfont": {"size": 28},
        "showgrid": False,
        "zeroline": False,
        "showticklabels": False,
        "range": [-0.5, 0.5],
    },
    template="plotly_white",
    margin={"l": 100, "r": 100, "t": 150, "b": 100},
)

# Save as PNG and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
