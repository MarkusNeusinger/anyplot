""" pyplots.ai
waffle-basic: Basic Waffle Chart
Library: plotnine 0.15.1 | Python 3.13.11
Quality: 95/100 | Created: 2025-12-16
"""

import pandas as pd
from plotnine import (
    aes,
    coord_equal,
    element_blank,
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


# Data - Budget allocation by category
categories = ["Housing", "Food", "Transport", "Entertainment", "Savings"]
values = [35, 25, 18, 12, 10]  # Percentages (sum to 100)
colors = ["#306998", "#FFD43B", "#4ECDC4", "#E76F51", "#95A5A6"]

# Create waffle grid (10x10 = 100 squares)
grid_size = 10
squares = []
square_id = 0

for val, cat in sorted(zip(values, categories, strict=True), reverse=True):
    for _ in range(val):
        row = square_id // grid_size
        col = square_id % grid_size
        squares.append({"x": col, "y": grid_size - 1 - row, "category": cat})
        square_id += 1

df = pd.DataFrame(squares)

# Create category order for legend (by value, descending)
category_order = [cat for _, cat in sorted(zip(values, categories, strict=True), reverse=True)]
df["category"] = pd.Categorical(df["category"], categories=category_order, ordered=True)

# Create color mapping in same order
color_map = dict(zip(categories, colors, strict=True))
ordered_colors = [color_map[cat] for cat in category_order]

# Build legend labels with percentages
value_map = dict(zip(categories, values, strict=True))
legend_labels = {cat: f"{cat} ({value_map[cat]}%)" for cat in category_order}

# Plot
plot = (
    ggplot(df, aes(x="x", y="y", fill="category"))
    + geom_tile(color="white", size=0.5)
    + scale_fill_manual(values=ordered_colors, labels=lambda x: [legend_labels[c] for c in x])
    + coord_equal()
    + labs(title="waffle-basic · plotnine · pyplots.ai", fill="Category")
    + guides(fill=guide_legend(ncol=1))
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, ha="center"),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        legend_position="right",
        axis_text=element_blank(),
        axis_title=element_blank(),
        axis_ticks=element_blank(),
        panel_grid=element_blank(),
    )
)

plot.save("plot.png", dpi=300, verbose=False)
