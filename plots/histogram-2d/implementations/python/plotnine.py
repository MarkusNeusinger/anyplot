"""anyplot.ai
histogram-2d: 2D Histogram Heatmap
Library: plotnine | Python 3.13
Quality: pending | Created: 2025-05-08
"""

import os

import numpy as np
import pandas as pd
from plotnine import aes, element_line, element_rect, element_text, geom_bin2d, ggplot, labs, scale_fill_cmap, theme


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - Bivariate normal distribution with correlation
# Context: Financial returns across asset classes
np.random.seed(42)
n_points = 5000
mean = [5.2, 8.1]
cov = [[2.5, 1.8], [1.8, 4.2]]
xy = np.random.multivariate_normal(mean, cov, n_points)
df = pd.DataFrame({"asset_returns": xy[:, 0], "index_returns": xy[:, 1]})

# Create 2D histogram heatmap
plot = (
    ggplot(df, aes(x="asset_returns", y="index_returns"))
    + geom_bin2d(bins=40)
    + scale_fill_cmap(cmap_name="viridis", name="Density")
    + labs(x="Asset Returns (%)", y="Index Returns (%)", title="histogram-2d · plotnine · anyplot.ai")
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_border=element_rect(color=INK_SOFT, fill=None, size=0.5),
        panel_grid_major=element_line(color=INK_SOFT, size=0.2, alpha=0.08),
        panel_grid_minor=element_line(color=INK_SOFT, size=0.1, alpha=0.05),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.4),
        plot_title=element_text(size=24, color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT, size=0.5),
        legend_text=element_text(size=14, color=INK_SOFT),
        legend_title=element_text(size=16, color=INK),
        text=element_text(size=14),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
