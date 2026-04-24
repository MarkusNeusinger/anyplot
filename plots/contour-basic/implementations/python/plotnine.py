"""anyplot.ai
contour-basic: Basic Contour Plot
Library: plotnine 0.15.3 | Python 3.14.4
"""

import os

import contourpy
import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_path,
    geom_raster,
    ggplot,
    ggsave,
    labs,
    scale_fill_cmap,
    theme,
    theme_minimal,
)


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

np.random.seed(42)
x = np.linspace(-3, 3, 100)
y = np.linspace(-3, 3, 100)
X, Y = np.meshgrid(x, y)
Z = (
    np.exp(-((X - 1) ** 2 + (Y - 1) ** 2))
    + 0.7 * np.exp(-((X + 1) ** 2 + (Y + 1) ** 2))
    - 0.3 * np.exp(-(X**2 + (Y - 1.5) ** 2) / 0.5)
)

tile_df = pd.DataFrame({"x": X.ravel(), "y": Y.ravel(), "z": Z.ravel()})

# Compute contour isoline segments via contourpy, render via plotnine geom_path
levels = np.linspace(Z.min(), Z.max(), 10)
generator = contourpy.contour_generator(x=X, y=Y, z=Z)
line_rows = []
group_id = 0
for level in levels:
    for segment in generator.lines(level):
        seg = np.asarray(segment)
        if seg.shape[0] < 2:
            continue
        for px, py in seg:
            line_rows.append({"x": px, "y": py, "group": group_id})
        group_id += 1
line_df = pd.DataFrame(line_rows)

anyplot_theme = theme(
    figure_size=(16, 9),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.08),
    panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.04),
    panel_border=element_rect(color=INK_SOFT, fill=None, size=0.5),
    axis_title=element_text(color=INK, size=20),
    axis_text=element_text(color=INK_SOFT, size=16),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK, size=24),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=16),
    legend_title=element_text(color=INK, size=18),
    legend_key=element_rect(fill=PAGE_BG, color=PAGE_BG),
)

plot = (
    ggplot()
    + geom_raster(tile_df, aes(x="x", y="y", fill="z"))
    + geom_path(line_df, aes(x="x", y="y", group="group"), color=PAGE_BG, size=0.7, alpha=0.85)
    + scale_fill_cmap(cmap_name="viridis", name="Value")
    + labs(x="X Coordinate", y="Y Coordinate", title="contour-basic · plotnine · anyplot.ai")
    + theme_minimal()
    + anyplot_theme
)

ggsave(plot, filename=f"plot-{THEME}.png", dpi=300, width=16, height=9)
