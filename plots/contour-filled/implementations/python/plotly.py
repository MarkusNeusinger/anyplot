"""anyplot.ai
contour-filled: Filled Contour Plot
Library: plotly | Python 3.13
Quality: pending | Created: 2025-12-30
"""

import os
import sys

import numpy as np


# Ensure plotly module is imported from site-packages, not local file
for p in sys.path[:]:
    if p.endswith("python") and "contour-filled" in p:
        sys.path.remove(p)

from plotly import graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Data - Create a meshgrid with multiple Gaussian peaks for interesting contours
np.random.seed(42)
x = np.linspace(-3, 3, 80)
y = np.linspace(-3, 3, 80)
X, Y = np.meshgrid(x, y)

# Create surface with multiple Gaussian peaks and a saddle point
z1 = 2 * np.exp(-((X - 1) ** 2 + (Y - 1) ** 2))
z2 = 1.5 * np.exp(-((X + 1) ** 2 + (Y + 1) ** 2))
z3 = -1 * np.exp(-((X - 1) ** 2 + (Y + 1) ** 2))
z4 = 0.5 * np.exp(-((X + 1.5) ** 2 + (Y - 1.5) ** 2))
Z = z1 + z2 + z3 + z4

# Create filled contour plot
fig = go.Figure()

fig.add_trace(
    go.Contour(
        x=x,
        y=y,
        z=Z,
        colorscale="Viridis",
        contours=dict(coloring="heatmap", showlabels=True, labelfont=dict(size=14, color="white")),
        colorbar=dict(
            title=dict(text="Surface Value", font=dict(size=20, color=INK)),
            tickfont=dict(size=16, color=INK_SOFT),
            thickness=25,
            len=0.9,
            bgcolor=PAGE_BG,
            bordercolor=INK_SOFT,
            borderwidth=1,
        ),
        ncontours=15,
        line=dict(width=1, color="white"),
        hovertemplate="X: %{x:.2f}<br>Y: %{y:.2f}<br>Value: %{z:.3f}<extra></extra>",
    )
)

# Update layout for large canvas with theme-adaptive colors
fig.update_layout(
    title=dict(text="contour-filled · plotly · anyplot.ai", font=dict(size=28, color=INK), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="X Position", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        showgrid=True,
        gridwidth=1,
        gridcolor=GRID,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
    ),
    yaxis=dict(
        title=dict(text="Y Position", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        showgrid=True,
        gridwidth=1,
        gridcolor=GRID,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
        scaleanchor="x",
        scaleratio=1,
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    margin=dict(l=100, r=120, t=100, b=100),
)

# Save as PNG and HTML with theme suffix
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
