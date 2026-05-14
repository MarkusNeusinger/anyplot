"""anyplot.ai
streamline-basic: Basic Streamline Plot
Library: plotly | Python 3.13
Quality: pending | Created: 2025-05-14
"""

import os

import numpy as np
import plotly.graph_objects as go
from scipy.integrate import solve_ivp


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
BRAND = "#009E73"

# Data - Vortex flow field: u = -y, v = x (circular streamlines)
fig = go.Figure()


# Function to compute velocity at any point
def velocity_field(t, state):
    x, y = state
    dx = -y
    dy = x
    return [dx, dy]


# Create streamlines from starting points on a circle
num_streamlines = 18
for angle in np.linspace(0, 2 * np.pi, num_streamlines, endpoint=False):
    start_x = 2.5 * np.cos(angle)
    start_y = 2.5 * np.sin(angle)

    # Integrate forward
    sol_forward = solve_ivp(
        velocity_field, (0, 5), [start_x, start_y], t_eval=np.linspace(0, 5, 150), dense_output=True
    )

    # Integrate backward
    sol_backward = solve_ivp(
        velocity_field, (0, -5), [start_x, start_y], t_eval=np.linspace(0, -5, 150), dense_output=True
    )

    # Plot forward streamline
    if sol_forward.t.size > 0:
        fig.add_trace(
            go.Scatter(
                x=sol_forward.y[0],
                y=sol_forward.y[1],
                mode="lines",
                line={"color": BRAND, "width": 3},
                hoverinfo="none",
                showlegend=False,
            )
        )

    # Plot backward streamline
    if sol_backward.t.size > 0:
        fig.add_trace(
            go.Scatter(
                x=sol_backward.y[0],
                y=sol_backward.y[1],
                mode="lines",
                line={"color": BRAND, "width": 3},
                hoverinfo="none",
                showlegend=False,
            )
        )

# Update layout for large canvas with theme support
fig.update_layout(
    title={"text": "streamline-basic · plotly · anyplot.ai", "font": {"size": 28, "color": INK}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "X Position (dimensionless)", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": GRID,
        "zeroline": True,
        "zerolinewidth": 2,
        "zerolinecolor": INK_SOFT,
        "range": [-4, 4],
        "autorange": False,
        "linecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": "Y Position (dimensionless)", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": GRID,
        "zeroline": True,
        "zerolinewidth": 2,
        "zerolinecolor": INK_SOFT,
        "range": [-4, 4],
        "autorange": False,
        "scaleanchor": "x",
        "scaleratio": 1,
        "linecolor": INK_SOFT,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    margin={"l": 120, "r": 50, "t": 100, "b": 100},
    showlegend=False,
)

# Save as PNG and HTML
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
