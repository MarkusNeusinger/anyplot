"""anyplot.ai
line-3d-trajectory: 3D Line Plot for Trajectory Visualization
Library: altair 6.1.0 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-16
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
AZIMUTH_DEG = 135  # view rotation around the vertical axis
ELEVATION_DEG = 20  # view tilt that opens the Lorenz wings

# Columns: set these to your table's column names
X = "X"  # role: x
Y = "Y"  # role: y
Z = "Z"  # role: z
TIME = "Time step"  # role: color

# Data: replace this block with your own table, for example df = pd.read_csv("trajectory.csv")
# Lorenz attractor (sigma=10, rho=28, beta=8/3) integrated with Euler steps
n_points = 1500
dt = 0.01
sigma, rho, beta = 10.0, 28.0, 8.0 / 3.0
path = np.zeros((n_points, 3))
path[0] = (1.0, 1.0, 1.0)
for i in range(1, n_points):
    px, py, pz = path[i - 1]
    path[i] = (px + sigma * (py - px) * dt, py + (px * (rho - pz) - py) * dt, pz + (px * py - beta * pz) * dt)
df = pd.DataFrame({X: path[:, 0], Y: path[:, 1], Z: path[:, 2], TIME: np.arange(n_points)})

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
azim = np.radians(AZIMUTH_DEG)
elev = np.radians(ELEVATION_DEG)

# Oblique projection: rotate around the vertical axis, then tilt toward the viewer
horizontal = df[X] * np.cos(azim) - df[Y] * np.sin(azim)
depth = df[X] * np.sin(azim) + df[Y] * np.cos(azim)
vertical = depth * np.sin(elev) + df[Z] * np.cos(elev)

# One row per segment: start point, end point, and the original 3D values for the tooltip
H0, V0, H1, V1 = "h0", "v0", "h1", "v1"
segments = pd.DataFrame(
    {
        H0: horizontal[:-1].to_numpy(),
        V0: vertical[:-1].to_numpy(),
        H1: horizontal[1:].to_numpy(),
        V1: vertical[1:].to_numpy(),
        X: df[X][:-1].to_numpy(),
        Y: df[Y][:-1].to_numpy(),
        Z: df[Z][:-1].to_numpy(),
        TIME: df[TIME][:-1].to_numpy(),
    }
)

trajectory = (
    alt.Chart(segments)
    .mark_rule(strokeWidth=2.2, strokeCap="round", opacity=0.9)
    .encode(
        x=alt.X(H0, type="quantitative", title="X-Y projection (horizontal)"),
        y=alt.Y(V0, type="quantitative", title="Z projection (vertical)"),
        x2=H1,
        y2=V1,
        color=alt.Color(
            TIME.translate(ESCAPE), type="quantitative", title=TIME, scale=alt.Scale(range=["#009E73", "#4467A3"])
        ),
        tooltip=[
            alt.Tooltip(X, type="quantitative", format=".2f"),
            alt.Tooltip(Y, type="quantitative", format=".2f"),
            alt.Tooltip(Z, type="quantitative", format=".2f"),
            alt.Tooltip(TIME.translate(ESCAPE), type="quantitative", title=TIME),
        ],
    )
)

# Pan and zoom
pan_zoom = alt.selection_interval(bind="scales", encodings=["x", "y"])

chart = (
    trajectory.add_params(pan_zoom)
    .properties(
        width=600,
        height=320,
        background=PAGE_BG,
        title=alt.Title(text="line-3d-trajectory · python · altair · anyplot.ai", fontSize=18, color=INK),
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=12,
        titleFontSize=14,
    )
    .configure_title(color=INK)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=12,
        titleFontSize=14,
        titleLimit=120,
        labelLimit=80,
    )
)

# Save outputs
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad to the canvas target (never crop)
TW, TH = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TW or h > TH:
    raise SystemExit(f"altair produced {w}x{h}, exceeds target {TW}x{TH}; shrink width/height")
if (w, h) != (TW, TH):
    canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    canvas.paste(img, ((TW - w) // 2, (TH - h) // 2))
    canvas.save(f"plot-{THEME}.png")
