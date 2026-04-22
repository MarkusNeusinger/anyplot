""" pyplots.ai
contour-basic: Basic Contour Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-23
"""

import numpy as np
import plotly.graph_objects as go


# Data - Create a 50x50 grid with a mathematical function
np.random.seed(42)
x = np.linspace(-3, 3, 50)
y = np.linspace(-3, 3, 50)
X, Y = np.meshgrid(x, y)

# z = peaks-like function (combination of Gaussians)
z = (
    3 * (1 - X) ** 2 * np.exp(-(X**2) - (Y + 1) ** 2)
    - 10 * (X / 5 - X**3 - Y**5) * np.exp(-(X**2) - Y**2)
    - 1 / 3 * np.exp(-((X + 1) ** 2) - Y**2)
)

# Create contour plot with filled regions and lines
fig = go.Figure()

# Filled contour
fig.add_trace(
    go.Contour(
        x=x,
        y=y,
        z=z,
        colorscale="Viridis",
        contours={"showlabels": True, "labelfont": {"size": 16, "color": "white"}},
        colorbar={
            "title": {"text": "Z Value", "font": {"size": 20}},
            "tickfont": {"size": 16},
            "thickness": 30,
            "len": 0.9,
        },
        line={"width": 2},
    )
)

# Layout for 4800x2700 px
fig.update_layout(
    title={"text": "contour-basic · plotly · pyplots.ai", "font": {"size": 32}, "x": 0.5, "xanchor": "center"},
    xaxis={"title": {"text": "X Coordinate", "font": {"size": 24}}, "tickfont": {"size": 18}},
    yaxis={"title": {"text": "Y Coordinate", "font": {"size": 24}}, "tickfont": {"size": 18}},
    template="plotly_white",
    margin={"l": 100, "r": 120, "t": 100, "b": 100},
)

# Save as PNG (4800x2700 px)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save interactive HTML
fig.write_html("plot.html")
