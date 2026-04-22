""" pyplots.ai
ecdf-basic: Basic ECDF Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import numpy as np
import plotly.graph_objects as go


# Data
np.random.seed(42)
values = np.random.normal(loc=50, scale=15, size=200)

# Compute ECDF
sorted_values = np.sort(values)
ecdf_y = np.arange(1, len(sorted_values) + 1) / len(sorted_values)

# Create figure
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=sorted_values, y=ecdf_y, mode="lines", line={"color": "#306998", "width": 4, "shape": "hv"}, name="ECDF"
    )
)

# Layout
fig.update_layout(
    title={"text": "ecdf-basic · plotly · pyplots.ai", "font": {"size": 48}},
    xaxis={
        "title": {"text": "Value", "font": {"size": 36}},
        "tickfont": {"size": 28},
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": "rgba(0,0,0,0.1)",
    },
    yaxis={
        "title": {"text": "Cumulative Proportion", "font": {"size": 36}},
        "tickfont": {"size": 28},
        "range": [0, 1],
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": "rgba(0,0,0,0.1)",
    },
    template="plotly_white",
    showlegend=False,
    margin={"l": 100, "r": 50, "t": 120, "b": 100},
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html")
