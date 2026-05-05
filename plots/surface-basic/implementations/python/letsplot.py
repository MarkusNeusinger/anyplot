""" anyplot.ai
surface-basic: Basic 3D Surface Plot
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-05
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_polygon,
    ggplot,
    ggsize,
    labs,
    scale_fill_viridis,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - create a smooth surface z = sin(x) * cos(y)
np.random.seed(42)

# Grid setup - 40x40 for smooth surface
n_points = 40
x = np.linspace(-3, 3, n_points)
y = np.linspace(-3, 3, n_points)
X, Y = np.meshgrid(x, y)

# Surface function
Z = np.sin(X) * np.cos(Y)

# 3D to 2D projection (elevation=25, azimuth=45)
elev_rad = np.radians(25)
azim_rad = np.radians(45)

# Rotation around z-axis (azimuth)
X_rot = X * np.cos(azim_rad) - Y * np.sin(azim_rad)
Y_rot = X * np.sin(azim_rad) + Y * np.cos(azim_rad)

# Rotation around x-axis (elevation) and project
X_proj = X_rot
Z_proj = Y_rot * np.sin(elev_rad) + Z * np.cos(elev_rad)

# Build quads sorted by depth (painter's algorithm - back to front)
quads = []
for i in range(n_points - 1):
    for j in range(n_points - 1):
        # Four corners of each quad (in order for polygon)
        corners_x = [X_proj[i, j], X_proj[i, j + 1], X_proj[i + 1, j + 1], X_proj[i + 1, j]]
        corners_y = [Z_proj[i, j], Z_proj[i, j + 1], Z_proj[i + 1, j + 1], Z_proj[i + 1, j]]

        # Average z for color (original Z, not projected)
        avg_z = (Z[i, j] + Z[i, j + 1] + Z[i + 1, j + 1] + Z[i + 1, j]) / 4

        # Depth for sorting (average Y_rot for painter's algorithm)
        depth = (Y_rot[i, j] + Y_rot[i, j + 1] + Y_rot[i + 1, j + 1] + Y_rot[i + 1, j]) / 4

        quads.append((depth, corners_x, corners_y, avg_z))

# Sort by depth (back to front - painter's algorithm)
quads.sort(key=lambda q: q[0], reverse=True)

# Build DataFrame with sorted polygons
poly_data = []
for group_id, (_, corners_x, corners_y, avg_z) in enumerate(quads):
    for cx, cy in zip(corners_x, corners_y, strict=True):
        poly_data.append({"x": cx, "y": cy, "z": avg_z, "group": group_id})

df = pd.DataFrame(poly_data)

# Create surface plot with filled polygons
plot = (
    ggplot(df, aes(x="x", y="y", group="group", fill="z"))
    + geom_polygon(color=INK_SOFT, size=0.2, alpha=1.0)
    + scale_fill_viridis(name="Z Value")
    + labs(x="X (projected)", y="Z (height)", title="surface-basic · letsplot · anyplot.ai")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        plot_title=element_text(size=24, color=INK),
        legend_background=element_rect(fill=PAGE_BG),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_title=element_text(size=18, color=INK),
        panel_grid=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save PNG (scale=3 gives 4800x2700)
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)

# Save HTML for interactivity
ggsave(plot, f"plot-{THEME}.html", path=".")
