""" pyplots.ai
facet-grid: Faceted Grid Plot
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
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

# Data - create dataset with two categorical faceting variables
np.random.seed(42)

# Product categories and regions for a sales analysis scenario
categories = ["Electronics", "Clothing", "Home"]
regions = ["North", "South", "East", "West"]

data = []
for cat in categories:
    for region in regions:
        n_points = 25
        # Base relationship varies by category and region
        base_price = {"Electronics": 200, "Clothing": 50, "Home": 100}[cat]
        region_factor = {"North": 1.2, "South": 0.9, "East": 1.0, "West": 1.1}[region]

        price = np.random.uniform(base_price * 0.5, base_price * 1.5, n_points)
        # Sales units inversely related to price with some noise
        units = (base_price * 100 / price) * region_factor + np.random.randn(n_points) * 10

        for p, u in zip(price, units, strict=True):
            data.append({"Category": cat, "Region": region, "Price": p, "Units Sold": max(0, u)})

df = pd.DataFrame(data)

# Plot - faceted grid with scatter and smooth trend
plot = (
    ggplot(df, aes(x="Price", y="Units Sold", color="Category"))
    + geom_point(size=3, alpha=0.7)
    + geom_smooth(method="lm", se=False, size=1.5)
    + facet_grid(x="Region", y="Category")
    + scale_color_manual(values=["#306998", "#FFD43B", "#DC2626"])
    + labs(title="facet-grid \u00b7 letsplot \u00b7 pyplots.ai", x="Unit Price ($)", y="Units Sold")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24),
        axis_title=element_text(size=20),
        axis_text=element_text(size=14),
        legend_text=element_text(size=16),
        legend_title=element_text(size=18),
        strip_text=element_text(size=16),
    )
    + ggsize(1600, 900)
)

# Save PNG and HTML
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
