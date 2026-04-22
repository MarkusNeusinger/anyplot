""" pyplots.ai
marimekko-basic: Basic Marimekko Chart
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import os
import shutil

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_text,
    geom_rect,
    geom_text,
    ggplot,
    ggsize,
    labs,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Data - Market share by region and product line
# Regions as x-categories (bar widths), Product lines as y-categories (stacked segments)
regions = ["North America", "Europe", "Asia Pacific", "Latin America"]
products = ["Electronics", "Apparel", "Home Goods", "Food & Beverage"]

# Values in millions - each row is a product, each column is a region
# Values represent market size for each product in each region
values = {
    "North America": [120, 85, 65, 45],  # Total: 315
    "Europe": [95, 110, 55, 60],  # Total: 320
    "Asia Pacific": [180, 70, 90, 85],  # Total: 425
    "Latin America": [40, 35, 25, 30],  # Total: 130
}

# Calculate totals for each region (determines bar width)
region_totals = {region: sum(vals) for region, vals in values.items()}
grand_total = sum(region_totals.values())

# Calculate proportional widths (sum to 100%)
region_widths = {region: total / grand_total * 100 for region, total in region_totals.items()}

# Build rectangle coordinates for each segment
# xmin, xmax define horizontal position (variable width)
# ymin, ymax define vertical position (stacked from 0 to 100%)
rects = []
x_pos = 0

for region in regions:
    region_width = region_widths[region]
    region_vals = values[region]
    region_total = region_totals[region]

    y_pos = 0
    for i, product in enumerate(products):
        product_value = region_vals[i]
        segment_height = (product_value / region_total) * 100  # Height as percentage

        rects.append(
            {
                "region": region,
                "product": product,
                "value": product_value,
                "xmin": x_pos,
                "xmax": x_pos + region_width,
                "ymin": y_pos,
                "ymax": y_pos + segment_height,
                "x_center": x_pos + region_width / 2,
                "y_center": y_pos + segment_height / 2,
            }
        )
        y_pos += segment_height

    x_pos += region_width

df = pd.DataFrame(rects)

# Colors: Python Blue, Python Yellow, and two additional colorblind-safe colors
colors = ["#306998", "#FFD43B", "#2E8B57", "#DC2626"]

# Create the Marimekko chart using geom_rect
plot = (
    ggplot(df)
    + geom_rect(aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="product"), color="white", size=0.5)
    # Add value labels on larger segments
    + geom_text(
        aes(x="x_center", y="y_center", label="value"), size=12, color="white", fontface="bold", label_format="${}M"
    )
    + scale_fill_manual(values=colors, name="Product Line")
    + scale_x_continuous(
        name="Market Size Distribution",
        breaks=[df[df["region"] == r]["x_center"].iloc[0] for r in regions],  # Center of each region
        labels=regions,
        limits=[0, 100],
    )
    + scale_y_continuous(name="Share within Region (%)", limits=[0, 100])
    + labs(title="marimekko-basic · letsplot · pyplots.ai")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, hjust=0.5),
        axis_title=element_text(size=20),
        axis_text_x=element_text(size=16, angle=15),
        axis_text_y=element_text(size=16),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        legend_position="right",
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save as PNG (scaled 3x for 4800x2700)
ggsave(plot, "plot.png", scale=3)

# Save as HTML for interactive viewing
ggsave(plot, "plot.html")

# Move files from lets-plot-images subfolder to current directory
if os.path.exists("lets-plot-images/plot.png"):
    shutil.move("lets-plot-images/plot.png", "plot.png")
if os.path.exists("lets-plot-images/plot.html"):
    shutil.move("lets-plot-images/plot.html", "plot.html")
if os.path.exists("lets-plot-images"):
    shutil.rmtree("lets-plot-images")
