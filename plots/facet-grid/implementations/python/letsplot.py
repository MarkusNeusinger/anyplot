""" anyplot.ai
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

# Okabe-Ito palette (categorical)
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data - sales analysis by category and region
np.random.seed(42)

categories = ["Electronics", "Clothing", "Home"]
regions = ["North", "South", "East", "West"]

# Generate all combinations of categories and regions
category_list = []
region_list = []
price_list = []
units_list = []

for cat in categories:
    for region in regions:
        n_points = 25
        base_price = {"Electronics": 200, "Clothing": 50, "Home": 100}[cat]
        region_factor = {"North": 1.2, "South": 0.9, "East": 1.0, "West": 1.1}[region]

        price = np.random.uniform(base_price * 0.5, base_price * 1.5, n_points)
        units = (base_price * 100 / price) * region_factor + np.random.randn(n_points) * 10
        units = np.maximum(units, 0)

        category_list.extend([cat] * n_points)
        region_list.extend([region] * n_points)
        price_list.extend(price)
        units_list.extend(units)

df = pd.DataFrame({"Category": category_list, "Region": region_list, "Price": price_list, "Units Sold": units_list})

# Theme-adaptive styling
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_grid_major=element_line(color=RULE, size=0.3),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=20),
    axis_text=element_text(color=INK_SOFT, size=16),
    axis_line=element_line(color=INK_SOFT, size=0.5),
    plot_title=element_text(color=INK, size=24),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=16),
    legend_title=element_text(color=INK, size=18),
    strip_text=element_text(color=INK, size=16),
    strip_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
)

# Plot
plot = (
    ggplot(df, aes(x="Price", y="Units Sold", color="Category"))
    + geom_point(size=3, alpha=0.7)
    + geom_smooth(method="lm", se=False, size=1.5)
    + facet_grid(x="Region", y="Category")
    + scale_color_manual(values=IMPRINT)
    + labs(title="facet-grid · letsplot · anyplot.ai", x="Unit Price ($)", y="Units Sold")
    + theme_minimal()
    + anyplot_theme
    + ggsize(1600, 900)
)

# Save PNG and HTML with theme-suffixed names
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)
ggsave(plot, f"plot-{THEME}.html", path=".")
