"""anyplot.ai
contour-filled: Filled Contour Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-11
"""

import os
import sys

import numpy as np


# Ensure plotly module is imported from site-packages, not local file
for p in sys.path[:]:
    if p.endswith("python") and "contour-filled" in p:
        sys.path.remove(p)

from plotly import graph_objects as go  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Data - Create a meshgrid with multiple Gaussian peaks for interesting contours
np.random.seed(42)
x = np.linspace(-3, 3, 100)
y = np.linspace(-3, 3, 100)
X, Y = np.meshgrid(x, y)

# Create surface with multiple Gaussian peaks and a saddle point
z1 = 2 * np.exp(-((X - 1) ** 2 + (Y - 1) ** 2))
z2 = 1.5 * np.exp(-((X + 1) ** 2 + (Y + 1) ** 2))
z3 = -1 * np.exp(-((X - 1) ** 2 + (Y + 1) ** 2))
z4 = 0.5 * np.exp(-((X + 1.5) ** 2 + (Y - 1.5) ** 2))
Z = z1 + z2 + z3 + z4

# Create filled contour plot with enhanced visualization
fig = go.Figure()

# Custom diverging colorscale for more sophisticated aesthetics
fig.add_trace(
    go.Contour(
        x=x,
        y=y,
        z=Z,
        colorscale="RdBu_r",
        contours=dict(
            coloring="heatmap",
            showlabels=True,
            labelfont=dict(size=16, color="white", family="Arial"),
            labelformat=".2f",
        ),
        colorbar=dict(
            title=dict(text="Surface Value", font=dict(size=20, color=INK, family="Arial")),
            tickfont=dict(size=16, color=INK_SOFT, family="Arial"),
            thickness=28,
            len=0.85,
            x=1.02,
            bgcolor=ELEVATED_BG,
            bordercolor=INK_SOFT,
            borderwidth=2,
        ),
        ncontours=18,
        line=dict(width=1.5, color="white"),
        hovertemplate="<b>Position</b><br>X: %{x:.2f}<br>Y: %{y:.2f}<br><b>Value: %{z:.3f}</b><extra></extra>",
        name="Surface",
    )
)

# Overlay scatter points at the peak locations for visual emphasis
peak_locations = np.array([[1, 1], [-1, -1], [1.5, -1.5]])
peak_values = np.array([2.0, 1.5, 0.5])
fig.add_trace(
    go.Scatter(
        x=peak_locations[:, 0],
        y=peak_locations[:, 1],
        mode="markers",
        marker=dict(size=14, color="white", line=dict(color=INK, width=2), symbol="star"),
        hovertemplate="<b>Peak</b><br>X: %{x:.2f}<br>Y: %{y:.2f}<extra></extra>",
        name="Peaks",
        showlegend=True,
    )
)

# Update layout for large canvas with theme-adaptive colors
fig.update_layout(
    title=dict(
        text="contour-filled · plotly · anyplot.ai",
        font=dict(size=28, color=INK, family="Arial", weight="bold"),
        x=0.5,
        xanchor="center",
        y=0.98,
        yanchor="top",
    ),
    xaxis=dict(
        title=dict(text="X Position", font=dict(size=22, color=INK, family="Arial")),
        tickfont=dict(size=18, color=INK_SOFT, family="Arial"),
        showgrid=True,
        gridwidth=1,
        gridcolor=GRID,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
        zeroline=True,
    ),
    yaxis=dict(
        title=dict(text="Y Position", font=dict(size=22, color=INK, family="Arial")),
        tickfont=dict(size=18, color=INK_SOFT, family="Arial"),
        showgrid=True,
        gridwidth=1,
        gridcolor=GRID,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
        zeroline=True,
        scaleanchor="x",
        scaleratio=1,
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    margin=dict(l=100, r=140, t=100, b=100),
    legend=dict(
        x=0.02,
        y=0.98,
        bgcolor="rgba(255,255,255,0)" if THEME == "light" else "rgba(0,0,0,0)",
        bordercolor=INK_SOFT,
        borderwidth=0,
        font=dict(size=14, color=INK_SOFT, family="Arial"),
    ),
    hovermode="closest",
)

# Save as PNG and HTML with theme suffix
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
