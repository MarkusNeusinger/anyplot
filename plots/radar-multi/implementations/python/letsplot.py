""" pyplots.ai
radar-multi: Multi-Series Radar Chart
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

import math

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_text,
    geom_line,
    geom_point,
    geom_polygon,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_color_manual,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)


LetsPlot.setup_html()

# Data - Smartphone comparison across 6 key attributes (4 products)
categories = ["Battery", "Camera", "Display", "Performance", "Storage", "Price Value"]
products = {
    "Galaxy S24": [85, 92, 90, 88, 75, 70],
    "iPhone 15": [75, 95, 88, 92, 70, 65],
    "Pixel 8": [80, 90, 82, 85, 65, 85],
    "OnePlus 12": [90, 78, 85, 90, 80, 90],
}

n = len(categories)
colors = ["#306998", "#FFD43B", "#DC2626", "#22C55E"]  # Python Blue, Yellow, Red, Green

# Create angles for each category (evenly spaced, starting from top)
angles = [i * 2 * math.pi / n for i in range(n)]

# Build dataframe with cartesian coordinates for each product
data_rows = []
for product_name, values in products.items():
    for i, (cat, val, angle) in enumerate(zip(categories, values, angles, strict=True)):
        # Convert polar to cartesian (0 degrees at top, clockwise)
        x = val * math.cos(angle - math.pi / 2)
        y = val * math.sin(angle - math.pi / 2)
        data_rows.append({"category": cat, "value": val, "x": x, "y": y, "series": product_name, "order": i})

    # Close the polygon by repeating first point
    x = values[0] * math.cos(angles[0] - math.pi / 2)
    y = values[0] * math.sin(angles[0] - math.pi / 2)
    data_rows.append(
        {"category": categories[0], "value": values[0], "x": x, "y": y, "series": product_name, "order": n}
    )

df = pd.DataFrame(data_rows)

# Create gridlines data (circles at 20, 40, 60, 80, 100)
grid_rows = []
grid_values = [20, 40, 60, 80, 100]
grid_angles = [i * 2 * math.pi / 72 for i in range(73)]  # 73 points for smooth circles
for radius in grid_values:
    for angle in grid_angles:
        x = radius * math.cos(angle - math.pi / 2)
        y = radius * math.sin(angle - math.pi / 2)
        grid_rows.append({"x": x, "y": y, "radius": radius})

grid_df = pd.DataFrame(grid_rows)

# Create axis lines (spokes from center to edge)
spoke_rows = []
for i, angle in enumerate(angles):
    x = 105 * math.cos(angle - math.pi / 2)
    y = 105 * math.sin(angle - math.pi / 2)
    spoke_rows.append({"x": 0, "y": 0, "group": i})
    spoke_rows.append({"x": x, "y": y, "group": i})

spoke_df = pd.DataFrame(spoke_rows)

# Create axis labels (category names at outer edge)
label_rows = []
for cat, angle in zip(categories, angles, strict=True):
    x = 125 * math.cos(angle - math.pi / 2)
    y = 125 * math.sin(angle - math.pi / 2)
    label_rows.append({"label": cat, "x": x, "y": y})

label_df = pd.DataFrame(label_rows)

# Create grid value labels (scale indicators on first spoke)
value_label_rows = []
for val in grid_values:
    x = val * math.cos(-math.pi / 2) + 10  # Offset right for readability
    y = val * math.sin(-math.pi / 2)
    value_label_rows.append({"label": str(val), "x": x, "y": y})

value_label_df = pd.DataFrame(value_label_rows)

# Build the plot
plot = (
    ggplot()
    # Gridlines (concentric circles)
    + geom_line(
        aes(x="x", y="y", group="radius"), data=grid_df, color="#CCCCCC", size=0.6, alpha=0.6, linetype="dashed"
    )
    # Spokes (radial lines)
    + geom_line(aes(x="x", y="y", group="group"), data=spoke_df, color="#CCCCCC", size=0.6, alpha=0.6)
    # Filled polygons for each series (lower alpha for 4 overlapping series)
    + geom_polygon(aes(x="x", y="y", fill="series", group="series"), data=df, alpha=0.2)
    # Lines connecting points
    + geom_line(aes(x="x", y="y", color="series", group="series"), data=df, size=2.5)
    # Points at each vertex (exclude the closing point to avoid double dot)
    + geom_point(aes(x="x", y="y", color="series"), data=df[df["order"] < n], size=7)
    # Custom color palette
    + scale_fill_manual(values=colors)
    + scale_color_manual(values=colors)
    # Axis limits for square plot
    + scale_x_continuous(limits=(-160, 160))
    + scale_y_continuous(limits=(-160, 160))
    # Title and legend
    + labs(title="Smartphone Comparison · radar-multi · letsplot · pyplots.ai", fill="Product", color="Product")
    # Square format for symmetric radar chart
    + ggsize(1200, 1200)
    + theme(
        plot_title=element_text(size=22),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        legend_position="right",
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid=element_blank(),
    )
)

# Add category labels as text
plot = plot + geom_text(aes(x="x", y="y", label="label"), data=label_df, size=16, color="#333333")

# Add grid value labels
plot = plot + geom_text(aes(x="x", y="y", label="label"), data=value_label_df, size=12, color="#666666")

# Save outputs
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
