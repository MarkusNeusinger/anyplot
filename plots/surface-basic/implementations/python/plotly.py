""" anyplot.ai
surface-basic: Basic 3D Surface Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-05
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Data - Create a smooth mathematical surface
np.random.seed(42)
x = np.linspace(-5, 5, 40)
y = np.linspace(-5, 5, 40)
X, Y = np.meshgrid(x, y)

# Create an interesting surface combining sinusoidal patterns
Z = np.sin(np.sqrt(X**2 + Y**2)) * np.cos(X / 2) + 0.5 * np.exp(-0.1 * (X**2 + Y**2))

# Plot
fig = go.Figure(
    data=[
        go.Surface(
            x=X,
            y=Y,
            z=Z,
            colorscale="Viridis",
            colorbar={
                "title": {"text": "Z Value", "font": {"size": 20, "color": INK}},
                "tickfont": {"size": 16, "color": INK_SOFT},
                "len": 0.7,
            },
        )
    ]
)

# Style
fig.update_layout(
    title={
        "text": "surface-basic · plotly · anyplot.ai",
        "font": {"size": 28, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    scene={
        "xaxis": {
            "title": {"text": "X Axis", "font": {"size": 22, "color": INK}},
            "tickfont": {"size": 18, "color": INK_SOFT},
            "gridcolor": GRID,
            "showbackground": True,
            "backgroundcolor": PAGE_BG,
        },
        "yaxis": {
            "title": {"text": "Y Axis", "font": {"size": 22, "color": INK}},
            "tickfont": {"size": 18, "color": INK_SOFT},
            "gridcolor": GRID,
            "showbackground": True,
            "backgroundcolor": PAGE_BG,
        },
        "zaxis": {
            "title": {"text": "Z Value", "font": {"size": 22, "color": INK}},
            "tickfont": {"size": 18, "color": INK_SOFT},
            "gridcolor": GRID,
            "showbackground": True,
            "backgroundcolor": PAGE_BG,
        },
        "camera": {"eye": {"x": 1.5, "y": 1.5, "z": 1.2}},
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    margin={"l": 20, "r": 20, "t": 80, "b": 20},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
