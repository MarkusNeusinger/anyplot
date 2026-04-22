""" pyplots.ai
lollipop-grouped: Grouped Lollipop Chart
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-09
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
    scale_color_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Data - Quarterly revenue by product line across regions
regions = ["North", "South", "East", "West"]
products = ["Electronics", "Furniture", "Clothing"]

data_rows = []
revenue_data = {"North": [245, 180, 125], "South": [198, 165, 142], "East": [267, 195, 118], "West": [223, 172, 156]}

for i, region in enumerate(regions):
    for j, product in enumerate(products):
        data_rows.append(
            {
                "region": region,
                "product": product,
                "revenue": revenue_data[region][j],
                "x_pos": i + (j - 1) * 0.25,  # Offset within group
                "y_start": 0,
            }
        )

df = pd.DataFrame(data_rows)

# Colors - Python Blue first, then complementary colors
colors = ["#306998", "#FFD43B", "#DC2626"]

# Create plot with lollipop stems and markers
plot = (
    ggplot(df)
    # Stems - thin lines from baseline to value
    + geom_segment(mapping=aes(x="x_pos", xend="x_pos", y="y_start", yend="revenue", color="product"), size=2)
    # Markers - circular dots at values
    + geom_point(mapping=aes(x="x_pos", y="revenue", color="product"), size=8)
    + scale_color_manual(values=colors, name="Product Line")
    + labs(x="Region", y="Revenue ($ thousands)", title="lollipop-grouped · letsplot · pyplots.ai")
    # X axis with region labels at group centers
    + scale_x_continuous(breaks=list(range(len(regions))), labels=regions)
    + scale_y_continuous(limits=[0, 300])
    + ggsize(1600, 900)
    + theme_minimal()
    + theme(
        axis_text_x=element_text(size=16),
        axis_text_y=element_text(size=16),
        axis_title=element_text(size=20),
        plot_title=element_text(size=24, hjust=0.5),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        panel_grid_major_x=element_blank(),
    )
)

# Save
ggsave(plot, filename="plot.png", path=".", scale=3)
ggsave(plot, filename="plot.html", path=".")
