"""anyplot.ai
contour-3d: 3D Contour Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-16
"""

import os
import sys


# Prevent self-import: remove this script's directory from sys.path so that
# 'import plotly' resolves to the installed package, not this file.
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if p != "" and os.path.abspath(p or ".") != _here]

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: sequential colormap from the first two positions
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
IMPRINT_SEQ = [[0.0, IMPRINT_PALETTE[0]], [1.0, IMPRINT_PALETTE[2]]]

# Constants
N_LEVELS = 12  # number of regularly spaced contour levels

# Columns: set these to your table's column names
X_POS = "Position x (cm)"  # role: x
Y_POS = "Position y (cm)"  # role: y
HEIGHT = "Water surface height (mm)"  # role: z

# Data: ripples spreading from a drop that hits a water tank, replace with your own long table of x, y, z
grid = np.linspace(-6, 6, 45)
gx, gy = np.meshgrid(grid, grid)
radius = np.hypot(gx, gy)
ripple = 4.0 * np.sinc(radius / 1.6) * np.exp(-0.12 * radius)
df = pd.DataFrame({X_POS: gx.ravel(), Y_POS: gy.ravel(), HEIGHT: ripple.ravel()})

# Plot: reads only df and the constants above
table = df.pivot_table(index=Y_POS, columns=X_POS, values=HEIGHT, sort=False)
z_min, z_max = np.nanmin(table.to_numpy()), np.nanmax(table.to_numpy())
level_size = (z_max - z_min) / N_LEVELS

fig = go.Figure(
    go.Surface(
        x=table.columns,
        y=table.index,
        z=table.to_numpy(),
        colorscale=IMPRINT_SEQ,
        cmin=z_min,
        cmax=z_max,
        contours={
            "z": {
                "show": True,
                "start": z_min,
                "end": z_max,
                "size": level_size,
                "usecolormap": False,
                "color": INK,
                "project": {"z": True},
                "width": 2,
            }
        },
        lighting={"ambient": 0.8, "diffuse": 0.6, "specular": 0.1},
        colorbar={
            "title": {"text": HEIGHT, "font": {"size": 12, "color": INK}, "side": "right"},
            "tickfont": {"size": 10, "color": INK_SOFT},
            "len": 0.7,
            "thickness": 16,
            "tickcolor": INK_SOFT,
            "bordercolor": INK_SOFT,
            "borderwidth": 1,
            "bgcolor": ELEVATED_BG,
        },
        hovertemplate="x: %{x:.1f}<br>y: %{y:.1f}<br>height: %{z:.2f}<extra></extra>",
    )
)

axis_style = {
    "tickfont": {"size": 10, "color": INK_SOFT},
    "gridcolor": GRID,
    "showbackground": True,
    "backgroundcolor": PAGE_BG,
    "linecolor": INK_SOFT,
    "zerolinecolor": INK_SOFT,
}

# Style
fig.update_layout(
    autosize=False,
    title={
        "text": "contour-3d · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    scene={
        "xaxis": {**axis_style, "title": {"text": X_POS, "font": {"size": 12, "color": INK}}},
        "yaxis": {**axis_style, "title": {"text": Y_POS, "font": {"size": 12, "color": INK}}},
        "zaxis": {**axis_style, "title": {"text": HEIGHT, "font": {"size": 12, "color": INK}}},
        "camera": {"eye": {"x": 1.4, "y": -1.4, "z": 0.9}},
        "aspectratio": {"x": 1, "y": 1, "z": 0.55},
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    margin={"l": 20, "r": 40, "t": 60, "b": 20},
    font={"color": INK},
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
