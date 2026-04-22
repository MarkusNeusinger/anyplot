""" pyplots.ai
lollipop-basic: Basic Lollipop Chart
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_text,
    geom_point,
    geom_segment,
    ggplot,
    ggsize,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Data - Product sales by category, sorted by value
categories = ["Electronics", "Clothing", "Home & Garden", "Sports", "Books", "Toys", "Grocery", "Beauty"]
values = [45200, 32800, 28500, 21300, 18900, 15600, 12400, 9800]

df = pd.DataFrame({"category": categories, "value": values})

# Sort by value for better readability
df = df.sort_values("value", ascending=True).reset_index(drop=True)

# Create numeric x positions for categories
df["x_pos"] = range(len(df))
df["y_start"] = 0  # Baseline for segments

# Plot
plot = (
    ggplot(df)
    # Stems - thin lines from baseline (0) to value
    + geom_segment(mapping=aes(x="x_pos", xend="x_pos", y="y_start", yend="value"), size=1.5, color="#306998")
    # Markers - circular dots at data values
    + geom_point(mapping=aes(x="x_pos", y="value"), size=8, color="#306998")
    + labs(x="Product Category", y="Sales ($)", title="lollipop-basic · letsplot · pyplots.ai")
    # X axis with category labels
    + scale_x_continuous(breaks=df["x_pos"].tolist(), labels=df["category"].tolist())
    + scale_y_continuous(limits=[0, 50000])
    + ggsize(1600, 900)
    + theme_minimal()
    + theme(
        axis_text_x=element_text(angle=45, hjust=1, size=16),
        axis_text_y=element_text(size=16),
        axis_title=element_text(size=20),
        plot_title=element_text(size=24, hjust=0.5),
        panel_grid_major_x=element_blank(),
    )
)

# Save
ggsave(plot, filename="plot.png", path=".", scale=3)
ggsave(plot, filename="plot.html", path=".")
