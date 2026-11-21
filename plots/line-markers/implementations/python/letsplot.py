"""anyplot.ai
line-markers: Line Plot with Markers
Library: letsplot 4.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-12
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "#1A1A17" if THEME == "light" else "#F0EFE8"

# Imprint palette: all eight positions, one per series in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Marker shapes (lets-plot codes: circle, square, triangle, diamond, ...), one per series
MARKER_SHAPES = [16, 15, 17, 18, 8, 3, 4, 7]

# Columns: set these to your table's column names
QUARTER = "Quarter"  # role: x
REVENUE = ["Revenue (Million USD)"]  # role: y
PRODUCT = "Product"  # role: series

# Data: replace this block with your own table, for example df = pd.read_csv("revenue.csv")
np.random.seed(42)
quarters = np.arange(1, 13)
product_a = 45 + np.cumsum(np.random.randn(12) * 3) + np.arange(12) * 2
product_b = 60 + np.cumsum(np.random.randn(12) * 4) + np.arange(12) * 1.5
product_c = 35 + np.cumsum(np.random.randn(12) * 2.5) + np.arange(12) * 2.5
df = pd.DataFrame(
    {
        QUARTER: list(quarters) * 3,
        REVENUE[0]: np.concatenate([product_a, product_b, product_c]),
        PRODUCT: ["Product A"] * 12 + ["Product B"] * 12 + ["Product C"] * 12,
    }
)

# Plot
n_series = df[PRODUCT].nunique()
plot = (
    ggplot(df, aes(x=QUARTER, y=REVENUE[0], color=PRODUCT, shape=PRODUCT))
    + geom_line(size=1.0)
    + geom_point(size=3.5)
    + scale_color_manual(values=IMPRINT_PALETTE[:n_series])
    + scale_shape_manual(values=MARKER_SHAPES[:n_series])
    + scale_x_continuous(breaks=sorted(df[QUARTER].dropna().unique().tolist()))
    + labs(title="line-markers · python · letsplot · anyplot.ai")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color=GRID, size=0.3),
        plot_title=element_text(size=16, color=INK, face="bold"),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_title=element_text(size=12, color=INK),
        legend_position="right",
    )
    + ggsize(800, 450)
)

# Save outputs
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
