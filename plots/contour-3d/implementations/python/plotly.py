""" pyplots.ai
contour-3d: 3D Contour Plot
Library: plotly 6.5.1 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-07
"""

import numpy as np
import plotly.graph_objects as go


# Data - create a mathematical surface with interesting contour features
np.random.seed(42)
n = 40  # Grid size for clear visualization

x = np.linspace(-3, 3, n)
y = np.linspace(-3, 3, n)
X, Y = np.meshgrid(x, y)

# Create a surface with peaks and valleys - good for showing contours
# Combination of Gaussian peaks and a saddle point
Z = (
    1.5 * np.exp(-((X - 1) ** 2 + (Y - 1) ** 2))  # Peak at (1, 1)
    + 1.0 * np.exp(-((X + 1) ** 2 + (Y + 1) ** 2))  # Peak at (-1, -1)
    - 0.8 * np.exp(-((X + 1) ** 2 + (Y - 1) ** 2))  # Valley at (-1, 1)
    + 0.3 * (X**2 - Y**2) * 0.1  # Subtle saddle point contribution
)

# Create figure with 3D contour surface
fig = go.Figure()

# Add the 3D surface with contour lines
fig.add_trace(
    go.Surface(
        x=X,
        y=Y,
        z=Z,
        colorscale="Viridis",
        showscale=True,
        contours={
            "z": {
                "show": True,
                "usecolormap": True,
                "highlightcolor": "white",
                "project_z": True,  # Project contours onto the base plane
                "width": 2,
            },
            "x": {"show": False},
            "y": {"show": False},
        },
        colorbar={
            "title": {"text": "Height (z)", "font": {"size": 18}},
            "tickfont": {"size": 14},
            "len": 0.7,
            "thickness": 25,
            "x": 1.02,
        },
    )
)

# Update layout for large canvas and clear visualization
fig.update_layout(
    title={
        "text": "contour-3d · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#306998"},
        "x": 0.5,
        "xanchor": "center",
    },
    scene={
        "xaxis": {
            "title": {"text": "X Coordinate", "font": {"size": 18}},
            "tickfont": {"size": 14},
            "gridcolor": "rgba(0,0,0,0.1)",
            "showbackground": True,
            "backgroundcolor": "rgba(240,240,240,0.9)",
        },
        "yaxis": {
            "title": {"text": "Y Coordinate", "font": {"size": 18}},
            "tickfont": {"size": 14},
            "gridcolor": "rgba(0,0,0,0.1)",
            "showbackground": True,
            "backgroundcolor": "rgba(240,240,240,0.9)",
        },
        "zaxis": {
            "title": {"text": "Height (z)", "font": {"size": 18}},
            "tickfont": {"size": 14},
            "gridcolor": "rgba(0,0,0,0.1)",
            "showbackground": True,
            "backgroundcolor": "rgba(240,240,240,0.9)",
        },
        "camera": {"eye": {"x": 1.5, "y": 1.5, "z": 1.2}},  # Good viewing angle
        "aspectratio": {"x": 1, "y": 1, "z": 0.7},
    },
    template="plotly_white",
    margin={"l": 20, "r": 80, "t": 80, "b": 20},
    paper_bgcolor="white",
)

# Save as PNG (4800 x 2700 px)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save interactive HTML version
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
