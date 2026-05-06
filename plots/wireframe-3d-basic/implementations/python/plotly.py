"""anyplot.ai
wireframe-3d-basic: Basic 3D Wireframe Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Updated: 2025-12-24
"""

import os

import numpy as np
import plotly.graph_objects as go


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - Create a 30x30 grid with ripple function z = sin(sqrt(x^2 + y^2))
x = np.linspace(-5, 5, 30)
y = np.linspace(-5, 5, 30)
X, Y = np.meshgrid(x, y)
R = np.sqrt(X**2 + Y**2)
Z = np.sin(R)

# Create wireframe using line traces with height-based coloring
fig = go.Figure()

# Add lines along x-direction (rows) with height-based coloring
for i in range(Z.shape[0]):
    z_values = Z[i, :]
    # Map Z values to colorscale (normalized between -1 and 1 for sin function)
    fig.add_trace(
        go.Scatter3d(
            x=X[i, :],
            y=Y[i, :],
            z=z_values,
            mode="lines",
            line={"color": z_values, "colorscale": "viridis", "showscale": False, "width": 3, "cmin": -1, "cmax": 1},
            showlegend=False,
            hovertemplate="<b>Point</b><br>X: %{x:.2f}<br>Y: %{y:.2f}<br>Z: %{z:.3f}<extra></extra>",
        )
    )

# Add lines along y-direction (columns) with height-based coloring
for j in range(Z.shape[1]):
    z_values = Z[:, j]
    fig.add_trace(
        go.Scatter3d(
            x=X[:, j],
            y=Y[:, j],
            z=z_values,
            mode="lines",
            line={"color": z_values, "colorscale": "viridis", "showscale": False, "width": 3, "cmin": -1, "cmax": 1},
            showlegend=False,
            hovertemplate="<b>Point</b><br>X: %{x:.2f}<br>Y: %{y:.2f}<br>Z: %{z:.3f}<extra></extra>",
        )
    )

# Layout for 4800x2700 px with 3D camera settings and theme-adaptive colors
fig.update_layout(
    title={"text": "wireframe-3d-basic · plotly · anyplot.ai", "font": {"size": 32, "color": INK}, "x": 0.5, "xanchor": "center"},
    scene={
        "xaxis": {
            "title": {"text": "Radius (x-coordinate)", "font": {"size": 22, "color": INK}},
            "tickfont": {"size": 16, "color": INK_SOFT},
            "gridcolor": "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)",
            "backgroundcolor": PAGE_BG,
        },
        "yaxis": {
            "title": {"text": "Radius (y-coordinate)", "font": {"size": 22, "color": INK}},
            "tickfont": {"size": 16, "color": INK_SOFT},
            "gridcolor": "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)",
            "backgroundcolor": PAGE_BG,
        },
        "zaxis": {
            "title": {"text": "Height: sin(√(x² + y²))", "font": {"size": 22, "color": INK}},
            "tickfont": {"size": 16, "color": INK_SOFT},
            "gridcolor": "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)",
            "backgroundcolor": PAGE_BG,
        },
        "camera": {
            "eye": {"x": 1.6, "y": 1.6, "z": 1.0}  # ~30° elevation, ~45° azimuth
        },
        "aspectmode": "cube",
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    margin={"l": 20, "r": 20, "t": 100, "b": 20},
)

# Save as PNG (4800x2700 px)
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)

# Save interactive HTML
fig.write_html(f"plot-{THEME}.html")
