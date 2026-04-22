""" pyplots.ai
wireframe-3d-basic: Basic 3D Wireframe Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-24
"""

import numpy as np
import plotly.graph_objects as go


# Data - Create a 30x30 grid with ripple function z = sin(sqrt(x^2 + y^2))
x = np.linspace(-5, 5, 30)
y = np.linspace(-5, 5, 30)
X, Y = np.meshgrid(x, y)
R = np.sqrt(X**2 + Y**2)
Z = np.sin(R)

# Create wireframe using line traces
fig = go.Figure()

# Python Blue color for wireframe lines
line_color = "#306998"

# Add lines along x-direction (rows)
for i in range(Z.shape[0]):
    fig.add_trace(
        go.Scatter3d(
            x=X[i, :],
            y=Y[i, :],
            z=Z[i, :],
            mode="lines",
            line={"color": line_color, "width": 3},
            showlegend=False,
            hoverinfo="skip",
        )
    )

# Add lines along y-direction (columns)
for j in range(Z.shape[1]):
    fig.add_trace(
        go.Scatter3d(
            x=X[:, j],
            y=Y[:, j],
            z=Z[:, j],
            mode="lines",
            line={"color": line_color, "width": 3},
            showlegend=False,
            hoverinfo="skip",
        )
    )

# Layout for 4800x2700 px with 3D camera settings
fig.update_layout(
    title={"text": "wireframe-3d-basic · plotly · pyplots.ai", "font": {"size": 32}, "x": 0.5, "xanchor": "center"},
    scene={
        "xaxis": {
            "title": {"text": "X Axis", "font": {"size": 22}},
            "tickfont": {"size": 16},
            "gridcolor": "rgba(0,0,0,0.15)",
            "backgroundcolor": "rgba(248,248,248,1)",
        },
        "yaxis": {
            "title": {"text": "Y Axis", "font": {"size": 22}},
            "tickfont": {"size": 16},
            "gridcolor": "rgba(0,0,0,0.15)",
            "backgroundcolor": "rgba(248,248,248,1)",
        },
        "zaxis": {
            "title": {"text": "Z = sin(√(x² + y²))", "font": {"size": 22}},
            "tickfont": {"size": 16},
            "gridcolor": "rgba(0,0,0,0.15)",
            "backgroundcolor": "rgba(248,248,248,1)",
        },
        "camera": {
            "eye": {"x": 1.6, "y": 1.6, "z": 1.0}  # ~30° elevation, ~45° azimuth
        },
        "aspectmode": "cube",
    },
    template="plotly_white",
    margin={"l": 20, "r": 20, "t": 100, "b": 20},
)

# Save as PNG (4800x2700 px)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save interactive HTML
fig.write_html("plot.html")
