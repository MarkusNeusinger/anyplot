"""anyplot.ai
ternary-density: Ternary Density Plot
Library: plotnine 0.15.8 | Python 3.13
Quality: pending | Updated: 2026-11-09
"""

import os

import numpy as np
import pandas as pd
from contourpy import contour_generator
from plotnine import (
    aes,
    coord_fixed,
    element_rect,
    element_text,
    geom_path,
    geom_polygon,
    geom_raster,
    geom_segment,
    geom_text,
    ggplot,
    guide_colorbar,
    labs,
    scale_fill_gradient,
    theme,
    theme_void,
)
from scipy.stats import gaussian_kde


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint continuous colormap imprint_seq: brand green (low density) → blue (high density)
IMPRINT_SEQ = ["#009E73", "#4467A3"]

# Constants
GRID_STEPS = [0.2, 0.4, 0.6, 0.8]  # ternary grid every 20 %
CONTOUR_LEVELS = [0.2, 0.4, 0.6, 0.8]  # contour levels as shares of the peak density
GRID_RESOLUTION = 240  # KDE evaluation points along the triangle's base

# Columns: set these to your table's column names
SAND = "Sand (%)"  # role: component_a
SILT = "Silt (%)"  # role: component_b
CLAY = "Clay (%)"  # role: component_c

# Data: replace this block with your own table, for example df = pd.read_csv("sediments.csv")
np.random.seed(42)
sand_rich = np.random.beta(5, 2, 300) * 60 + 35
silt_sandy = np.random.beta(2, 3, 300) * (100 - sand_rich) * 0.6
silt_rich = np.random.beta(5, 2, 250) * 50 + 40
sand_silty = np.random.beta(2, 4, 250) * (100 - silt_rich) * 0.5
clay_rich = np.random.beta(4, 2, 250) * 45 + 40
sand_clayey = np.random.beta(2, 5, 250) * (100 - clay_rich) * 0.4
sand = np.concatenate([sand_rich, sand_silty, sand_clayey])
silt = np.concatenate([silt_sandy, silt_rich, 100 - sand_clayey - clay_rich])
clay = np.concatenate([100 - sand_rich - silt_sandy, 100 - sand_silty - silt_rich, clay_rich])
compositions = np.clip(np.column_stack([sand, silt, clay]), 0, None)
compositions = compositions / compositions.sum(axis=1, keepdims=True) * 100
df = pd.DataFrame(compositions, columns=[SAND, SILT, CLAY])

# Plot: reads only df and the constants above
# Ternary → Cartesian: sand vertex at (0, 0), silt at (1, 0), clay at (0.5, √3/2)
height = np.sqrt(3) / 2
parts = df[[SAND, SILT, CLAY]].dropna()
shares = parts.div(parts.sum(axis=1), axis=0)
x_data = shares[SILT] + shares[CLAY] / 2
y_data = shares[CLAY] * height

# Kernel density on a regular grid covering the triangle's bounding box
kde = gaussian_kde(np.vstack([x_data, y_data]))
x_grid = np.linspace(0, 1, GRID_RESOLUTION)
y_grid = np.linspace(0, height, round(GRID_RESOLUTION * height))
xx, yy = np.meshgrid(x_grid, y_grid)
density = kde(np.vstack([xx.ravel(), yy.ravel()])).reshape(xx.shape)
inside = (yy <= 2 * height * xx + 1e-9) & (yy <= 2 * height * (1 - xx) + 1e-9)
density = density / density[inside].max()
density_df = pd.DataFrame({"x": xx.ravel(), "y": yy.ravel(), "density": density.ravel()})

# Contour lines traced on the same density surface
contours = contour_generator(x_grid, y_grid, density)
contour_rows = []
for level in CONTOUR_LEVELS:
    for k, line in enumerate(contours.lines(level)):
        contour_rows.append(pd.DataFrame({"x": line[:, 0], "y": line[:, 1], "path": f"{level}-{k}"}))
contour_df = pd.concat(contour_rows, ignore_index=True)

# Page-coloured masks outside the triangle keep the density and contours inside its edges
mask_df = pd.DataFrame(
    {
        "x": [-1, 2, 2, -1, 0, 0.5, 0.5, -1, -1, 1, 0.5, 0.5, 2, 2],
        "y": [-1, -1, 0, 0, 0, height, 2, 2, 0, 0, height, 2, 2, 0],
        "side": ["bottom"] * 4 + ["left"] * 5 + ["right"] * 5,
    }
)
frame_df = pd.DataFrame({"x": [0, 1, 0.5, 0], "y": [0, 0, height, 0]})

# Grid lines parallel to each side: constant clay, constant silt, constant sand
steps = np.array(GRID_STEPS)
grid_df = pd.DataFrame(
    {
        "x": np.concatenate([steps / 2, steps, 1 - steps]),
        "y": np.concatenate([steps * height, np.zeros_like(steps), np.zeros_like(steps)]),
        "xend": np.concatenate([1 - steps / 2, steps + (1 - steps) / 2, (1 - steps) / 2]),
        "yend": np.concatenate([steps * height, (1 - steps) * height, (1 - steps) * height]),
    }
)

# Tick labels at the outer end of each grid line, read along the matching edge
pct = [f"{round(s * 100)}" for s in GRID_STEPS]
tick_df = pd.DataFrame(
    {
        "x": np.concatenate([steps, 1 - steps / 2 + 0.035, (1 - steps) / 2 - 0.035]),
        "y": np.concatenate([np.full_like(steps, -0.04), steps * height + 0.02, (1 - steps) * height + 0.02]),
        "label": pct * 3,
    }
)
vertex_df = pd.DataFrame({"x": [-0.03, 1.03, 0.5], "y": [-0.085, -0.085, height + 0.055], "label": [SAND, SILT, CLAY]})

plot = (
    ggplot()
    + geom_raster(data=density_df, mapping=aes(x="x", y="y", fill="density"), interpolation="bilinear")
    + geom_path(data=contour_df, mapping=aes(x="x", y="y", group="path"), color=PAGE_BG, size=0.6, alpha=0.9)
    + geom_polygon(data=mask_df, mapping=aes(x="x", y="y", group="side"), fill=PAGE_BG, color=None)
    + geom_segment(data=grid_df, mapping=aes(x="x", y="y", xend="xend", yend="yend"), color=INK, size=0.3, alpha=0.3)
    + geom_polygon(data=frame_df, mapping=aes(x="x", y="y"), fill=None, color=INK_SOFT, size=0.8)
    + geom_text(data=tick_df, mapping=aes(x="x", y="y", label="label"), size=8, color=INK_SOFT)
    + geom_text(data=vertex_df, mapping=aes(x="x", y="y", label="label"), size=10, fontweight="bold", color=INK)
    + scale_fill_gradient(
        low=IMPRINT_SEQ[0],
        high=IMPRINT_SEQ[1],
        limits=(0, 1),
        breaks=[0, 0.5, 1],
        labels=["Low", "Medium", "High"],
        name="Relative\ndensity",
        guide=guide_colorbar(),
    )
    + labs(title="ternary-density · python · plotnine · anyplot.ai")
    + coord_fixed(ratio=1, xlim=(-0.12, 1.12), ylim=(-0.13, height + 0.09), expand=False)
    + theme_void()
    + theme(
        figure_size=(6, 6),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=12, ha="center", weight="bold", color=INK),
        plot_margin=0.03,
        legend_position="bottom",
        legend_direction="horizontal",
        legend_title=element_text(size=8, color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_key_width=120,
        legend_key_height=12,
        legend_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=6, height=6, units="in", verbose=False)
