""" anyplot.ai
contour-basic: Basic Contour Plot
Library: plotnine 0.15.3 | Python 3.14.4
Quality: 80/100 | Created: 2026-04-24
"""

import os

import contourpy
import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_line,
    element_rect,
    element_text,
    geom_path,
    geom_point,
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
x = np.linspace(-3, 3, 200)
y = np.linspace(-3, 3, 200)
X, Y = np.meshgrid(x, y)
Z = (
    np.exp(-((X - 1) ** 2 + (Y - 1) ** 2))
    + 0.7 * np.exp(-((X + 1) ** 2 + (Y + 1) ** 2))
    - 0.3 * np.exp(-(X**2 + (Y - 1.5) ** 2) / 0.5)
)

tile_df = pd.DataFrame({"x": X.ravel(), "y": Y.ravel(), "z": Z.ravel()})

# Extract contour isoline segments via contourpy, render as grouped paths
levels = np.linspace(Z.min(), Z.max(), 10)
generator = contourpy.contour_generator(x=X, y=Y, z=Z)
segments = [
    (np.asarray(seg), gid)
    for gid, seg in enumerate(s for lvl in levels for s in generator.lines(lvl))
    if np.asarray(seg).shape[0] >= 2
]
line_df = pd.concat(
    [pd.DataFrame({"x": seg[:, 0], "y": seg[:, 1], "group": gid}) for seg, gid in segments], ignore_index=True
)

peak_df = pd.DataFrame({"x": [1.0], "y": [1.0]})

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
    + geom_path(line_df, aes(x="x", y="y", group="group"), color="#FFFFFF", size=0.7, alpha=0.55)
    + geom_point(peak_df, aes(x="x", y="y"), color="#1A1A17", size=3.5)
    + annotate("segment", x=1.0, y=1.05, xend=1.0, yend=1.35, color="#1A1A17", size=0.6, alpha=0.8)
    + annotate("text", x=1.0, y=1.5, label="Primary peak", color="#1A1A17", size=14, ha="center")
    + scale_fill_cmap(cmap_name="viridis", name="Value")
    + labs(x="X Coordinate", y="Y Coordinate", title="contour-basic · plotnine · anyplot.ai")
    + theme_minimal()
    + anyplot_theme
)

ggsave(plot, filename=f"plot-{THEME}.png", dpi=300, width=16, height=9)
