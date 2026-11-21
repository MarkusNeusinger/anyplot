"""anyplot.ai
facet-grid: Faceted Grid Plot
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 95/100 | Updated: 2026-05-13
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
    facet_grid,
    geom_point,
    geom_smooth,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_color_manual,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette (categorical)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Theme-adaptive styling
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_grid_major=element_line(color=RULE, size=0.3),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=12),
    axis_text=element_text(color=INK_SOFT, size=10),
    axis_line=element_line(color=INK_SOFT, size=0.5),
    plot_title=element_text(color=INK, size=16),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=10),
    legend_title=element_text(color=INK, size=12),
    strip_text=element_text(color=INK, size=10),
    strip_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
)

# Columns
CATEGORY = "Category"  # role: row_facet
REGION = "Region"  # role: col_facet
PRICE = "Price"  # role: x
UNITS = "Units Sold"  # role: y

# Data - sales analysis by category and region
np.random.seed(42)

categories = ["Electronics", "Clothing", "Home"]
regions = ["North", "South", "East", "West"]
base_prices = {"Electronics": 200, "Clothing": 50, "Home": 100}
region_factors = {"North": 1.2, "South": 0.9, "East": 1.0, "West": 1.1}
n_points = 25

frames = []
for cat in categories:
    for region in regions:
        base_price = base_prices[cat]
        price = np.random.uniform(base_price * 0.5, base_price * 1.5, n_points)
        units = (base_price * 100 / price) * region_factors[region] + np.random.randn(n_points) * 10
        frames.append(pd.DataFrame({CATEGORY: cat, REGION: region, PRICE: price, UNITS: np.maximum(units, 0)}))

df = pd.concat(frames, ignore_index=True)

# Plot
plot = (
    ggplot(df, aes(x=PRICE, y=UNITS, color=CATEGORY))
    + geom_point(size=2.5, alpha=0.7)
    + geom_smooth(method="lm", se=False, size=1.0)
    + facet_grid(x=REGION, y=CATEGORY)
    + scale_color_manual(values=IMPRINT_PALETTE)
    + labs(title="facet-grid · python · letsplot · anyplot.ai", x="Unit Price ($)", y=UNITS)
    + theme_minimal()
    + anyplot_theme
    + ggsize(800, 450)
)

# Save PNG and HTML with theme-suffixed names
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
