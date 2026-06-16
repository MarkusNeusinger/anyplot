""" anyplot.ai
line-multi: Multi-Line Comparison Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-06
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_point,
    ggplot,
    labs,
    scale_color_manual,
    scale_x_continuous,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data - Monthly sales for 4 product lines over 12 months
np.random.seed(42)
months = np.arange(1, 13)
month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Generate realistic sales data with different trends
base_sales = 100
electronics = base_sales + np.cumsum(np.random.randn(12) * 8) + months * 5
clothing = base_sales + 20 + np.cumsum(np.random.randn(12) * 6) + np.sin(months * 0.5) * 15
furniture = base_sales - 10 + np.cumsum(np.random.randn(12) * 5) + months * 2
accessories = base_sales + 10 + np.cumsum(np.random.randn(12) * 7)

# Create long-format DataFrame for plotnine
df = pd.DataFrame(
    {
        "Month": np.tile(months, 4),
        "Sales": np.concatenate([electronics, clothing, furniture, accessories]),
        "Product": np.repeat(["Electronics", "Clothing", "Furniture", "Accessories"], 12),
    }
)

# Make Product a categorical with specific order
df["Product"] = pd.Categorical(
    df["Product"], categories=["Electronics", "Clothing", "Furniture", "Accessories"], ordered=True
)

# Map Okabe-Ito colors to products
color_map = {
    "Electronics": IMPRINT[0],
    "Clothing": IMPRINT[1],
    "Furniture": IMPRINT[2],
    "Accessories": IMPRINT[3],
}

# Create plot
plot = (
    ggplot(df, aes(x="Month", y="Sales", color="Product", group="Product"))
    + geom_line(size=2.5)
    + geom_point(size=5)
    + scale_color_manual(values=color_map)
    + scale_x_continuous(breaks=months, labels=month_labels)
    + labs(x="Month", y="Sales (thousands USD)", title="line-multi · plotnine · anyplot.ai", color="Product Line")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
        panel_border=element_rect(color=INK_SOFT, fill=None),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(size=24, color=INK, ha="center"),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_title=element_text(size=18, color=INK),
        legend_position="right",
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
