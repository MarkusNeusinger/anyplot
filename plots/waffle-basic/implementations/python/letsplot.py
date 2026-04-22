""" pyplots.ai
waffle-basic: Basic Waffle Chart
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-24
"""

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_blank,
    element_text,
    geom_tile,
    ggplot,
    ggsize,
    labs,
    scale_fill_manual,
    theme,
    theme_void,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Data - Market share by category (values sum to 100%)
categories = ["Product A", "Product B", "Product C", "Product D"]
values = [42, 28, 18, 12]  # Percentages

# Colors - Python Blue first, then colorblind-safe palette
colors = ["#306998", "#FFD43B", "#4CAF50", "#FF7043"]

# Build 10x10 waffle grid (100 squares, each = 1%)
# Fill from top-left, row by row
grid_data = []
square_idx = 0

for cat, val in zip(categories, values, strict=True):
    for _ in range(val):
        row = 9 - (square_idx // 10)  # Start from top (row 9) going down
        col = square_idx % 10
        grid_data.append({"x": col, "y": row, "category": cat})
        square_idx += 1

df = pd.DataFrame(grid_data)

# Preserve category order for legend
df["category"] = pd.Categorical(df["category"], categories=categories, ordered=True)

# Create legend labels with percentages
legend_labels = {cat: f"{cat} ({val}%)" for cat, val in zip(categories, values, strict=True)}
df["legend_label"] = df["category"].map(legend_labels)
df["legend_label"] = pd.Categorical(
    df["legend_label"], categories=[legend_labels[cat] for cat in categories], ordered=True
)

# Plot
plot = (
    ggplot(df, aes(x="x", y="y", fill="legend_label"))
    + geom_tile(width=0.9, height=0.9, size=0)
    + coord_fixed(ratio=1)
    + scale_fill_manual(values=colors)
    + labs(title="waffle-basic · letsplot · pyplots.ai", fill="Category")
    + theme_void()
    + theme(
        plot_title=element_text(size=24, hjust=0.5),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        axis_title=element_blank(),
        axis_text=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save PNG (scale=3 gives 4800x2700)
ggsave(plot, "plot.png", path=".", scale=3)

# Save HTML for interactivity
ggsave(plot, "plot.html", path=".")
