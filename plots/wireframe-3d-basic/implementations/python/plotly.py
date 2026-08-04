""" anyplot.ai
wireframe-3d-basic: Basic 3D Wireframe Plot
Library: plotly 6.9.0 | Python 3.13.14
Quality: 85/100 | Updated: 2026-08-04
"""

import os

import numpy as np
import plotly.graph_objects as go


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint diverging colormap - height is a signed deviation around z=0
imprint_div = [[0.0, "#AE3030"], [0.5, PAGE_BG], [1.0, "#4467A3"]]

# Data - 30x30 grid with ripple function z = sin(sqrt(x^2 + y^2))
x = np.linspace(-5, 5, 30)
y = np.linspace(-5, 5, 30)
X, Y = np.meshgrid(x, y)
R = np.sqrt(X**2 + Y**2)
Z = np.sin(R)

fig = go.Figure()

# Lines along the x-direction (rows), height-mapped via the Imprint diverging scale
for i in range(Z.shape[0]):
    z_values = Z[i, :]
    fig.add_trace(
        go.Scatter3d(
            x=X[i, :],
            y=Y[i, :],
            z=z_values,
            mode="lines",
            line={
                "color": z_values,
                "colorscale": imprint_div,
                "showscale": False,
                "width": 3.5,
                "cmin": -1,
                "cmax": 1,
            },
            showlegend=False,
            hovertemplate="<b>Point</b><br>X: %{x:.2f}<br>Y: %{y:.2f}<br>Z: %{z:.3f}<extra></extra>",
        )
    )

# Lines along the y-direction (columns) - the last one carries the shared colorbar
for j in range(Z.shape[1]):
    z_values = Z[:, j]
    is_last = j == Z.shape[1] - 1
    fig.add_trace(
        go.Scatter3d(
            x=X[:, j],
            y=Y[:, j],
            z=z_values,
            mode="lines",
            line={
                "color": z_values,
                "colorscale": imprint_div,
                "showscale": is_last,
                "width": 3.5,
                "cmin": -1,
                "cmax": 1,
                "colorbar": {
                    "title": {"text": "Height", "font": {"size": 14, "color": INK}},
                    "tickfont": {"size": 11, "color": INK_SOFT},
                    "outlinecolor": INK_SOFT,
                    "outlinewidth": 1,
                    "bgcolor": ELEVATED_BG,
                    "len": 0.6,
                    "thickness": 18,
                    "x": 0.8,
                }
                if is_last
                else None,
            },
            showlegend=False,
            hovertemplate="<b>Point</b><br>X: %{x:.2f}<br>Y: %{y:.2f}<br>Z: %{z:.3f}<extra></extra>",
        )
    )

fig.update_layout(
    autosize=False,
    title={
        "text": "wireframe-3d-basic · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    # Short axis titles avoid rotated-label collisions on the mandated canvas;
    # the formula lives in the annotation below instead of the z-axis title.
    scene={
        "xaxis": {
            "title": {"text": "Radius (x)", "font": {"size": 14, "color": INK}},
            "tickfont": {"size": 11, "color": INK_SOFT},
            "gridcolor": GRID,
            "backgroundcolor": PAGE_BG,
        },
        "yaxis": {
            "title": {"text": "Radius (y)", "font": {"size": 14, "color": INK}},
            "tickfont": {"size": 11, "color": INK_SOFT},
            "gridcolor": GRID,
            "backgroundcolor": PAGE_BG,
        },
        "zaxis": {
            "title": {"text": "Height (z)", "font": {"size": 14, "color": INK}},
            "tickfont": {"size": 11, "color": INK_SOFT},
            "gridcolor": GRID,
            "backgroundcolor": PAGE_BG,
        },
        "camera": {
            "eye": {"x": 1.6, "y": 1.6, "z": 1.0}  # ~30° elevation, ~45° azimuth
        },
        "aspectmode": "cube",
        "domain": {"x": [0.0, 0.78], "y": [0.0, 0.94]},
    },
    annotations=[
        {
            "text": "z = sin(√(x² + y²))",
            "font": {"size": 12, "color": INK_SOFT},
            "x": 0.5,
            "y": 0.95,
            "xref": "paper",
            "yref": "paper",
            "showarrow": False,
        }
    ],
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    margin={"l": 20, "r": 110, "t": 90, "b": 30},
)

# Save PNG (3200x1800) and interactive HTML
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
