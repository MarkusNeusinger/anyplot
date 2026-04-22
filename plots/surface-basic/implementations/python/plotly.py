""" pyplots.ai
surface-basic: Basic 3D Surface Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import numpy as np
import plotly.graph_objects as go


# Data - Create a smooth mathematical surface
np.random.seed(42)
x = np.linspace(-5, 5, 40)
y = np.linspace(-5, 5, 40)
X, Y = np.meshgrid(x, y)

# Create an interesting surface combining sinusoidal patterns
Z = np.sin(np.sqrt(X**2 + Y**2)) * np.cos(X / 2) + 0.5 * np.exp(-0.1 * (X**2 + Y**2))

# Create 3D surface plot
fig = go.Figure(
    data=[
        go.Surface(
            x=X,
            y=Y,
            z=Z,
            colorscale="Viridis",
            colorbar={"title": {"text": "Z Value", "font": {"size": 20}}, "tickfont": {"size": 16}, "len": 0.7},
        )
    ]
)

# Layout and styling for 4800x2700 px
fig.update_layout(
    title={"text": "surface-basic · plotly · pyplots.ai", "font": {"size": 28}, "x": 0.5, "xanchor": "center"},
    scene={
        "xaxis": {
            "title": {"text": "X Axis", "font": {"size": 20}},
            "tickfont": {"size": 14},
            "gridcolor": "rgba(0, 0, 0, 0.1)",
        },
        "yaxis": {
            "title": {"text": "Y Axis", "font": {"size": 20}},
            "tickfont": {"size": 14},
            "gridcolor": "rgba(0, 0, 0, 0.1)",
        },
        "zaxis": {
            "title": {"text": "Z Value", "font": {"size": 20}},
            "tickfont": {"size": 14},
            "gridcolor": "rgba(0, 0, 0, 0.1)",
        },
        "camera": {"eye": {"x": 1.5, "y": 1.5, "z": 1.2}},
    },
    template="plotly_white",
    margin={"l": 20, "r": 20, "t": 80, "b": 20},
)

# Save as PNG and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
