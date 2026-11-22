""" anyplot.ai
contour-3d: 3D Contour Plot
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 78/100 | Updated: 2026-11-22
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_contour,
    geom_tile,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_fill_gradient2,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: diverging ramp red - midpoint - blue (midpoint follows the theme surface)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
IMPRINT_NEG, IMPRINT_POS = IMPRINT_PALETTE[4], IMPRINT_PALETTE[2]

# Constants
CONTOUR_LEVELS = 12  # regular-interval level curves across the height range

# Columns: set these to your table's column names
X_COORD = "X coordinate"  # role: x
Y_COORD = "Y coordinate"  # role: y
HEIGHT = "Height (z)"  # role: z

# Data: replace this block with your own table, for example df = pd.read_csv("surface.csv")
grid = np.linspace(-3, 3, 45)
X, Y = np.meshgrid(grid, grid)
Z = (
    1.5 * np.exp(-((X - 1) ** 2 + (Y - 1) ** 2))
    + 1.0 * np.exp(-((X + 1) ** 2 + (Y + 1) ** 2))
    - 0.8 * np.exp(-((X + 1) ** 2 + (Y - 1) ** 2))
    + 0.03 * (X**2 - Y**2)
)
df = pd.DataFrame({X_COORD: X.ravel(), Y_COORD: Y.ravel(), HEIGHT: Z.ravel()})

# Plot: reads only df and the constants above
plot = (
    ggplot(df.dropna(subset=[HEIGHT]), aes(x=X_COORD, y=Y_COORD))
    + geom_tile(aes(fill=HEIGHT))
    + geom_contour(aes(z=HEIGHT), bins=CONTOUR_LEVELS, color=INK, size=0.5, alpha=0.7)
    + scale_fill_gradient2(low=IMPRINT_NEG, mid=PAGE_BG, high=IMPRINT_POS, midpoint=0)
    + scale_x_continuous(expand=[0, 0])
    + scale_y_continuous(expand=[0, 0])
    + labs(title="contour-3d · python · letsplot · anyplot.ai")
    + ggsize(800, 450)
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid=element_blank(),
        axis_title=element_text(color=INK, size=12),
        axis_text=element_text(color=INK_SOFT, size=10),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(color=INK, size=16),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(color=INK_SOFT, size=10),
        legend_title=element_text(color=INK, size=12),
    )
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
