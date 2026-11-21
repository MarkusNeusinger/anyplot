"""anyplot.ai
contour-filled: Filled Contour Plot
Library: plotnine 0.15.9 | Python 3.14
Quality: pending | Updated: 2026-05-11
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_tile,
    ggplot,
    guide_colorbar,
    labs,
    scale_fill_gradient2,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette (canonical order) and the diverging ramp built from it
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
DIV_LOW, DIV_MID, DIV_HIGH = "#AE3030", PAGE_BG, "#4467A3"

# Constants
N_LEVELS = 14  # number of evenly stepped bands

# Column constants
X = "X coordinate"  # role: x
Y = "Y coordinate"  # role: y
Z = "Field value"  # role: z

# Data: replace this block with your own grid, for example df = pd.read_csv("field.csv")
grid = np.linspace(-2 * np.pi, 2 * np.pi, 100)
gx, gy = np.meshgrid(grid, grid)
field = np.sin(gx) * np.cos(gy) + 0.5 * np.sin(2 * gx) * np.cos(gy) + 0.3 * np.cos(3 * gy) * np.sin(gx)
df = pd.DataFrame({X: gx.ravel(), Y: gy.ravel(), Z: field.ravel()})

# Plot
# Levels are evenly stepped and symmetric around zero, the diverging midpoint
bound = np.nanmax(np.abs(df[Z]))
levels = np.linspace(-bound, bound, N_LEVELS + 1)
centers = (levels[:-1] + levels[1:]) / 2
band = np.clip(np.digitize(df[Z], levels[1:-1]), 0, N_LEVELS - 1)
df["Band"] = centers[band]

plot = (
    ggplot(df, aes(x=X, y=Y))
    + geom_tile(aes(fill="Band"))
    + scale_fill_gradient2(
        low=DIV_LOW,
        mid=DIV_MID,
        high=DIV_HIGH,
        midpoint=0,
        limits=(-bound, bound),
        breaks=levels[::2],
        labels=lambda b: [f"{v:.1f}" for v in b],
        name=Z,
        guide=guide_colorbar(nbin=N_LEVELS),
    )
    + scale_x_continuous(expand=(0, 0))
    + scale_y_continuous(expand=(0, 0))
    + labs(title="Interference field · contour-filled · python · plotnine · anyplot.ai")
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
        panel_border=element_rect(color=INK_SOFT, fill=None),
        axis_title=element_text(color=INK, size=10),
        axis_text=element_text(color=INK_SOFT, size=8),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        plot_title=element_text(color=INK, size=12),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(color=INK_SOFT, size=8),
        legend_title=element_text(color=INK, size=9),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
