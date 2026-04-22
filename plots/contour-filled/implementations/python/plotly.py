""" pyplots.ai
contour-filled: Filled Contour Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-30
"""

import numpy as np
import plotly.graph_objects as go


# Data - Create a meshgrid with multiple Gaussian peaks for interesting contours
np.random.seed(42)
x = np.linspace(-3, 3, 80)
y = np.linspace(-3, 3, 80)
X, Y = np.meshgrid(x, y)

# Create surface with multiple Gaussian peaks and a saddle point
z1 = 2 * np.exp(-((X - 1) ** 2 + (Y - 1) ** 2))  # Peak at (1, 1)
z2 = 1.5 * np.exp(-((X + 1) ** 2 + (Y + 1) ** 2))  # Peak at (-1, -1)
z3 = -1 * np.exp(-((X - 1) ** 2 + (Y + 1) ** 2))  # Valley at (1, -1)
z4 = 0.5 * np.exp(-((X + 1.5) ** 2 + (Y - 1.5) ** 2))  # Smaller peak
Z = z1 + z2 + z3 + z4

# Create filled contour plot
fig = go.Figure()

# Add filled contours
fig.add_trace(
    go.Contour(
        x=x,
        y=y,
        z=Z,
        colorscale="Viridis",
        contours=dict(coloring="heatmap", showlabels=True, labelfont=dict(size=14, color="white")),
        colorbar=dict(
            title=dict(text="Surface Value", font=dict(size=20)), tickfont=dict(size=16), thickness=25, len=0.9
        ),
        ncontours=15,
        line=dict(width=1, color="white"),
    )
)

# Update layout for large canvas
fig.update_layout(
    title=dict(text="contour-filled · plotly · pyplots.ai", font=dict(size=28), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="X Coordinate", font=dict(size=22)),
        tickfont=dict(size=18),
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(128, 128, 128, 0.3)",
    ),
    yaxis=dict(
        title=dict(text="Y Coordinate", font=dict(size=22)),
        tickfont=dict(size=18),
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(128, 128, 128, 0.3)",
        scaleanchor="x",
        scaleratio=1,
    ),
    template="plotly_white",
    margin=dict(l=100, r=120, t=100, b=100),
)

# Save as PNG and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
