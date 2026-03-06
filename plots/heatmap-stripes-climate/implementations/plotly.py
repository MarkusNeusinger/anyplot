""" pyplots.ai
heatmap-stripes-climate: Climate Warming Stripes
Library: plotly 6.6.0 | Python 3.14.3
Quality: 76/100 | Created: 2026-03-06
"""

import numpy as np
import plotly.graph_objects as go


# Data
np.random.seed(42)
years = np.arange(1850, 2025)
n_years = len(years)

trend = np.linspace(-0.35, 0.85, n_years)
noise = np.random.normal(0, 0.12, n_years)
volcanic_dips = np.zeros(n_years)
volcanic_dips[33] = -0.25  # 1883 Krakatoa
volcanic_dips[62] = -0.15  # 1912 Novarupta
volcanic_dips[92] = -0.20  # 1942
volcanic_dips[141] = -0.15  # 1991 Pinatubo
anomalies = trend + noise + volcanic_dips

vmax = max(abs(anomalies.min()), abs(anomalies.max()))

# Colorscale (blue to white to red, symmetric around 0)
colorscale = [
    [0.0, "#08306b"],
    [0.25, "#2171b5"],
    [0.45, "#6baed6"],
    [0.5, "#ffffff"],
    [0.55, "#fb6a4a"],
    [0.75, "#cb181d"],
    [1.0, "#67000d"],
]

# Plot
fig = go.Figure(
    data=go.Heatmap(
        z=[anomalies], x=years, colorscale=colorscale, zmin=-vmax, zmax=vmax, showscale=False, xgap=0, ygap=0
    )
)

fig.update_layout(
    title={
        "text": "heatmap-stripes-climate · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#333333"},
        "x": 0.5,
        "y": 0.97,
    },
    paper_bgcolor="white",
    plot_bgcolor="white",
    xaxis={"showgrid": False, "showticklabels": False, "zeroline": False, "showline": False},
    yaxis={"showgrid": False, "showticklabels": False, "zeroline": False, "showline": False},
    margin={"l": 0, "r": 0, "t": 60, "b": 0},
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
