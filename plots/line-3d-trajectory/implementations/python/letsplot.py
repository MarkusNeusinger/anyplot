"""anyplot.ai
line-3d-trajectory: 3D Line Plot for Trajectory Visualization
Library: letsplot 4.9.0 | Python 3.13.13
Quality: pending | Created: 2026-05-16
"""

import os
import pathlib
import shutil

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_path,
    geom_segment,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_color_gradient,
    theme,
)


LetsPlot.setup_html()

# Theme
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: sequential ramp for the time encoding
SEQ_LOW = "#009E73"
SEQ_HIGH = "#4467A3"

# Constants
SIGMA = 10.0
RHO = 28.0
BETA = 8.0 / 3.0
DT = 0.01
NUM_STEPS = 1200
AZIMUTH = np.radians(40)  # rotation about the z axis
ELEVATION = np.radians(25)  # tilt of the view above the xy plane

# Columns
X = "x"  # role: x
Y = "y"  # role: y
Z = "z"  # role: z
STEP = "time step"  # role: color
U = "u"  # derived: horizontal picture-plane position
V = "v"  # derived: vertical picture-plane position

# Data: Lorenz attractor integrated with explicit Euler steps
px, py, pz = 0.1, 0.1, 0.1
rows = []
for step in range(NUM_STEPS):
    dx = SIGMA * (py - px)
    dy = px * (RHO - pz) - py
    dz = px * py - BETA * pz
    px += DT * dx
    py += DT * dy
    pz += DT * dz
    rows.append((px, py, pz, step))
df = pd.DataFrame(rows, columns=[X, Y, Z, STEP])


# Plot
def project(x, y, z):
    """Oblique projection of (x, y, z) onto the picture plane."""
    depth = x * np.sin(AZIMUTH) + y * np.cos(AZIMUTH)
    return x * np.cos(AZIMUTH) - y * np.sin(AZIMUTH), z * np.cos(ELEVATION) + depth * np.sin(ELEVATION)


path = df.copy()
path[U], path[V] = project(df[X], df[Y], df[Z])

# Three axes drawn from the corner of the data's bounding box
corner = df[[X, Y, Z]].min()
top = df[[X, Y, Z]].max()
span_u = path[U].max() - path[U].min()
span_v = path[V].max() - path[V].min()
axis_rows = []
for name in (X, Y, Z):
    end = corner.copy()
    end[name] = top[name]
    u0, v0 = project(corner[X], corner[Y], corner[Z])
    u1, v1 = project(end[X], end[Y], end[Z])
    axis_rows.append(
        {
            "u0": u0,
            "v0": v0,
            "u1": u1,
            "v1": v1,
            "lu": u1 + np.sign(u1 - u0) * 0.05 * span_u,
            "lv": v1 + np.sign(v1 - v0) * 0.05 * span_v,
            "label": f"{name.upper()} axis",
        }
    )
axes = pd.DataFrame(axis_rows)

plot = (
    ggplot(path)
    + geom_segment(aes(x="u0", y="v0", xend="u1", yend="v1"), data=axes, color=INK_SOFT, size=0.8, show_legend=False)
    + geom_text(aes(x="lu", y="lv", label="label"), data=axes, color=INK, size=7, show_legend=False)
    + geom_path(aes(x=U, y=V, color=STEP), size=1.0, alpha=0.85)
    + scale_color_gradient(low=SEQ_LOW, high=SEQ_HIGH)
    + ggsize(800, 450)
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid=element_blank(),
        panel_border=element_blank(),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        plot_title=element_text(color=INK, size=16),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(color=INK_SOFT, size=10),
        legend_title=element_text(color=INK, size=12),
        legend_position="right",
    )
    + labs(title="Lorenz Attractor · line-3d-trajectory · python · letsplot · anyplot.ai", color="Time step")
)

# Save
ggsave(plot, f"plot-{THEME}.png", scale=4)
ggsave(plot, f"plot-{THEME}.html")

# lets-plot writes into a lets-plot-images subdirectory; move the files next to the script
lpi_dir = pathlib.Path("lets-plot-images")
if lpi_dir.exists():
    for ext in ["png", "html"]:
        src = lpi_dir / f"plot-{THEME}.{ext}"
        dst = pathlib.Path(f"plot-{THEME}.{ext}")
        if src.exists() and not dst.exists():
            shutil.copy(src, dst)
