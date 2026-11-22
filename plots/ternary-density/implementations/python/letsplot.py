"""anyplot.ai
ternary-density: Ternary Density Plot
Library: letsplot | Python 3.13
Quality: pending | Created: 2026-11-22
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_blank,
    element_rect,
    element_text,
    geom_contour,
    geom_path,
    geom_point,
    geom_raster,
    geom_segment,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    guide_colorbar,
    guides,
    labs,
    layer_tooltips,
    scale_fill_gradient,
    theme,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: the sequential density ramp runs from position 1 to position 3
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
DENSITY_LOW, DENSITY_HIGH = IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]

# Constants
CONTOUR_STEP = 0.25  # contour every quarter of the peak density (25 %, 50 %, 75 %)
GRID_SHARES = [0.2, 0.4, 0.6, 0.8]  # ternary grid line every 20 %
GRID_RESOLUTION = 360  # density cells across the triangle's base
SQRT3_2 = np.sqrt(3) / 2  # height of the unit equilateral triangle

# Columns: set these to your table's column names
SAND = "Sand"  # role: component_a
SILT = "Silt"  # role: component_b
CLAY = "Clay"  # role: component_c

# Data: replace this block with your own table, for example df = pd.read_csv("sediment.csv")
rng = np.random.default_rng(42)
clusters = [([8, 2, 1], 180), ([2, 7, 2], 160), ([1, 2, 8], 160)]  # sand-rich, silt-rich, clay-rich samples
parts = np.vstack([rng.dirichlet(alpha, size) * 100 for alpha, size in clusters])
df = pd.DataFrame({SAND: parts[:, 0], SILT: parts[:, 1], CLAY: parts[:, 2]})

# Plot: reads only df and the constants above
# Ternary to Cartesian: bottom-left = Sand, bottom-right = Silt, top = Clay
share = df[[SAND, SILT, CLAY]].div(df[[SAND, SILT, CLAY]].sum(axis=1), axis=0)
points = pd.DataFrame(
    {
        "x": share[SILT] + share[CLAY] / 2,
        "y": SQRT3_2 * share[CLAY],
        SAND: df[SAND].round(1),
        SILT: df[SILT].round(1),
        CLAY: df[CLAY].round(1),
    }
)

# Gaussian KDE on a grid; the kernel is separable, so the grid is one matrix product
kde = points.dropna(subset=["x", "y"])  # a missing component leaves the sample out of the density
n = len(kde)
bw = n ** (-1.0 / 6)  # Scott's rule for two dimensions
bw_x, bw_y = kde["x"].std() * bw, kde["y"].std() * bw
gx = np.linspace(0, 1, GRID_RESOLUTION)
gy = np.linspace(0, SQRT3_2, round(GRID_RESOLUTION * SQRT3_2))
kernel_x = np.exp(-0.5 * ((gx[:, None] - kde["x"].to_numpy()) / bw_x) ** 2)
kernel_y = np.exp(-0.5 * ((gy[:, None] - kde["y"].to_numpy()) / bw_y) ** 2)
density = kernel_y @ kernel_x.T / (n * 2 * np.pi * bw_x * bw_y)

# Keep only cells whose centre lies inside the triangle
X, Y = np.meshgrid(gx, gy)
inside = (Y <= 2 * SQRT3_2 * X) & (Y <= 2 * SQRT3_2 * (1 - X))
density = np.where(inside, density, 0.0)
peak = density.max()
cells = pd.DataFrame({"x": X[inside], "y": Y[inside], "density": density[inside] / peak})

# Contour lines at shares of the peak density come from lets-plot on the same surface
surface = pd.DataFrame({"x": X.ravel(), "y": Y.ravel(), "density": (density / peak).ravel()})

# Ternary grid: three sets of lines parallel to the triangle's sides
grid = pd.DataFrame(
    [
        segment
        for s in GRID_SHARES
        for segment in (
            {"x": s / 2, "xend": 1 - s / 2, "y": s * SQRT3_2, "yend": s * SQRT3_2},  # constant clay
            {"x": s, "xend": s + (1 - s) / 2, "y": 0.0, "yend": (1 - s) * SQRT3_2},  # constant silt
            {"x": 1 - s, "xend": (1 - s) / 2, "y": 0.0, "yend": (1 - s) * SQRT3_2},  # constant sand
        )
    ]
)
triangle = pd.DataFrame({"x": [0, 1, 0.5, 0], "y": [0, 0, SQRT3_2, 0]})
vertices = pd.DataFrame({"x": [-0.05, 1.05, 0.5], "y": [-0.05, -0.05, SQRT3_2 + 0.06], "label": [SAND, SILT, CLAY]})

plot = (
    ggplot()
    + geom_raster(aes(x="x", y="y", fill="density"), data=cells)
    + scale_fill_gradient(low=DENSITY_LOW, high=DENSITY_HIGH, name="Relative density (peak = 1)")
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=grid, color="white", size=0.5, alpha=0.4)
    + geom_contour(aes(x="x", y="y", z="density"), data=surface, binwidth=CONTOUR_STEP, color="white", size=1.2)
    + geom_path(aes(x="x", y="y"), data=triangle, color=INK, size=1.2)
    + geom_point(
        aes(x="x", y="y"),
        data=points,
        size=3,
        alpha=0.01,
        tooltips=layer_tooltips().line(f"{SAND}: @{SAND}%").line(f"{SILT}: @{SILT}%").line(f"{CLAY}: @{CLAY}%"),
    )
    + geom_text(aes(x="x", y="y", label="label"), data=vertices, color=INK, size=9, fontface="bold")
    + labs(title="Sediment Composition · ternary-density · python · letsplot · anyplot.ai", x="", y="")
    + guides(fill=guide_colorbar(barwidth=260, barheight=14))
    + coord_fixed(ratio=1)
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid=element_blank(),
        panel_border=element_blank(),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        plot_title=element_text(size=13, face="bold", color=INK),
        legend_position="bottom",
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_title=element_text(size=12, color=INK),
        legend_text=element_text(size=11, color=INK_SOFT),
    )
    + ggsize(600, 600)
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
