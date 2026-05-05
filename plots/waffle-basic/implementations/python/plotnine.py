""" anyplot.ai
waffle-basic: Basic Waffle Chart
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 42/100 | Created: 2026-05-05
"""

import os
import sys

import pandas as pd


sys.path.pop(0)
from plotnine import (
    aes,
    coord_equal,
    element_blank,
    element_rect,
    element_text,
    geom_tile,
    ggplot,
    guide_legend,
    guides,
    labs,
    scale_fill_manual,
    theme,
    theme_minimal,
)


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]

# Data - Budget allocation by category
categories = ["Housing", "Food", "Transport", "Entertainment"]
values = [35, 25, 18, 12]
category_order = categories

# Create waffle grid (10x10 = 100 squares)
grid_size = 10
squares = []
square_id = 0

for val, cat in zip(values, categories, strict=True):
    for _ in range(val):
        row = square_id // grid_size
        col = square_id % grid_size
        squares.append({"x": col, "y": grid_size - 1 - row, "category": cat})
        square_id += 1

df = pd.DataFrame(squares)
df["category"] = pd.Categorical(df["category"], categories=category_order, ordered=True)

# Create color mapping with Okabe-Ito palette
color_map = dict(zip(category_order, OKABE_ITO, strict=True))
value_map = dict(zip(categories, values, strict=True))

# Build legend labels with percentages
legend_labels = {cat: f"{cat} ({value_map[cat]}%)" for cat in category_order}

# Theme configuration
anyplot_theme = theme(
    figure_size=(16, 9),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    plot_title=element_text(size=24, color=INK, ha="center"),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_title=element_text(size=18, color=INK),
    legend_text=element_text(size=16, color=INK_SOFT),
    legend_position="right",
    axis_text=element_blank(),
    axis_title=element_blank(),
    axis_ticks=element_blank(),
    panel_grid=element_blank(),
)

# Plot
plot = (
    ggplot(df, aes(x="x", y="y", fill="category"))
    + geom_tile(color=PAGE_BG, size=0.8)
    + scale_fill_manual(values=color_map, labels=lambda x: [legend_labels[c] for c in x])
    + coord_equal()
    + labs(title="waffle-basic · plotnine · anyplot.ai", fill="Category")
    + guides(fill=guide_legend(ncol=1))
    + theme_minimal()
    + anyplot_theme
)

plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
