""" anyplot.ai
wireframe-3d-basic: Basic 3D Wireframe Plot
Library: plotnine 0.15.8 | Python 3.13.15
Quality: 72/100 | Created: 2026-09-10
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_rect,
    element_text,
    geom_path,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    theme,
    theme_void,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Imprint palette position 1 — ALWAYS first series

# Camera: orthographic projection at elevation 30 deg / azimuth 45 deg, per spec.
# plotnine has no 3D grammar, so the mesh is projected to 2D screen coordinates
# ourselves (the same technique any static 3D renderer uses under the hood),
# then drawn with plotnine's own geom_path / geom_segment / geom_text.
elev = np.radians(30)
azim = np.radians(45)

view_dir = np.array([np.cos(elev) * np.cos(azim), np.cos(elev) * np.sin(azim), np.sin(elev)])
world_up = np.array([0.0, 0.0, 1.0])
right_axis = np.cross(view_dir, world_up)
right_axis /= np.linalg.norm(right_axis)
up_axis = np.cross(right_axis, view_dir)

Z_LIFT = 3.2  # visual height exaggeration so the shallow membrane displacement reads clearly


def project(x, y, z):
    px = x * right_axis[0] + y * right_axis[1] + z * Z_LIFT * right_axis[2]
    py = x * up_axis[0] + y * up_axis[1] + z * Z_LIFT * up_axis[2]
    return px, py


# Data — circular drumhead vibration mode: displacement z = sin(sqrt(x^2 + y^2))
np.random.seed(42)
grid_n = 26
x_vals = np.linspace(-6, 6, grid_n)
y_vals = np.linspace(-6, 6, grid_n)
grid_x, grid_y = np.meshgrid(x_vals, y_vals)
grid_z = np.sin(np.sqrt(grid_x**2 + grid_y**2))

z_min, z_max = float(grid_z.min()), float(grid_z.max())
floor_z = z_min - 0.3
ceil_z = z_max + 0.3

# Wireframe mesh lines running in both x and y directions (per spec)
mesh_rows = []
for j in range(grid_n):
    px, py = project(grid_x[:, j], grid_y[:, j], grid_z[:, j])
    for i in range(grid_n):
        mesh_rows.append({"px": px[i], "py": py[i], "line": f"col_{j}"})
for i in range(grid_n):
    px, py = project(grid_x[i, :], grid_y[i, :], grid_z[i, :])
    for j in range(grid_n):
        mesh_rows.append({"px": px[j], "py": py[j], "line": f"row_{i}"})
mesh = pd.DataFrame(mesh_rows)
mesh_cols = mesh[mesh["line"].str.startswith("col_")]
mesh_rows_df = mesh[mesh["line"].str.startswith("row_")]

# Axis box: three edges meeting at the front-left-bottom corner
axis_lines = pd.DataFrame(
    {
        "x": [-6, -6, -6],
        "y": [-6, -6, -6],
        "z": [floor_z, floor_z, floor_z],
        "xend": [6, -6, -6],
        "yend": [-6, 6, -6],
        "zend": [floor_z, floor_z, ceil_z],
    }
)
axis_lines["px"], axis_lines["py"] = project(axis_lines["x"], axis_lines["y"], axis_lines["z"])
axis_lines["pxend"], axis_lines["pyend"] = project(axis_lines["xend"], axis_lines["yend"], axis_lines["zend"])

x_breaks = np.array([-6, -3, 0, 3, 6])
y_breaks = np.array([-6, -3, 0, 3, 6])
z_breaks = np.array([-1, 0, 1])

ticks = pd.concat(
    [
        pd.DataFrame({"x": x_breaks, "y": -9.6, "z": floor_z, "label": [f"{v:g}" for v in x_breaks]}),
        pd.DataFrame({"x": -9.6, "y": y_breaks, "z": floor_z, "label": [f"{v:g}" for v in y_breaks]}),
    ],
    ignore_index=True,
)
ticks["px"], ticks["py"] = project(ticks["x"], ticks["y"], ticks["z"])

# Z ticks sit on the vertical axis line itself; nudge the label text (not the
# axis line) sideways past the Y-axis tick column so the two groups don't merge.
z_ticks = pd.DataFrame({"x": -6, "y": -6, "z": z_breaks, "label": [f"{v:g}" for v in z_breaks]})
z_px, z_py = project(z_ticks["x"], z_ticks["y"], z_ticks["z"])
z_ticks["px"] = z_px - 13
z_ticks["py"] = z_py

axis_labels = pd.DataFrame(
    {
        "x": [9.4, -6, -6],
        "y": [-6, 9.4, -6],
        "z": [floor_z, floor_z, ceil_z + 1.0],
        "label": ["X (cm)", "Y (cm)", "Z (mm)"],
    }
)
axis_labels["px"], axis_labels["py"] = project(axis_labels["x"], axis_labels["y"], axis_labels["z"])

# Plot
plot = (
    ggplot()
    + geom_path(aes("px", "py", group="line"), mesh_cols, color=BRAND, size=0.3, alpha=0.35)
    + geom_path(aes("px", "py", group="line"), mesh_rows_df, color=BRAND, size=0.3, alpha=0.35)
    + geom_segment(aes(x="px", y="py", xend="pxend", yend="pyend"), axis_lines, color=INK_SOFT, size=0.6)
    + geom_text(aes("px", "py", label="label"), ticks, color=INK_SOFT, size=3.3)
    + geom_text(aes("px", "py", label="label"), z_ticks, color=INK_SOFT, size=3.3)
    + geom_text(aes("px", "py", label="label"), axis_labels, color=INK, size=3.6, fontweight="bold")
    + labs(title="wireframe-3d-basic · python · plotnine · anyplot.ai")
    + coord_fixed(ratio=1)
    + theme_void(base_size=7)
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(color=INK, size=12, ha="center"),
        figure_size=(8, 4.5),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
