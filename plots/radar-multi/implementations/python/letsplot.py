""" anyplot.ai
radar-multi: Multi-Series Radar Chart
Library: letsplot 4.11.0 | Python 3.13.15
Quality: 87/100 | Updated: 2026-08-17
"""

import math
import os

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_path,
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

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data - Smartphone comparison across 6 key attributes (4 products)
categories = ["Battery", "Camera", "Display", "Performance", "Storage", "Price Value"]
products = {
    "Galaxy S24": [85, 92, 90, 88, 75, 70],
    "iPhone 15": [75, 95, 88, 92, 70, 65],
    "Pixel 8": [80, 90, 82, 85, 65, 85],
    "OnePlus 12": [90, 78, 85, 90, 80, 90],
}

n = len(categories)

# Product with the highest average score gets a subtle emphasis (focal point)
hero = max(products, key=lambda name: sum(products[name]) / len(products[name]))

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

# Create grid value labels (placed in the gap between the Performance and
# Storage spokes: a near-vertical sector, so the stacked labels don't overlap
# each other, with a low combined data range so they clear the polygons too)
gap_angle = (angles[3] + angles[4]) / 2
value_label_rows = []
for val in grid_values:
    x = val * math.cos(gap_angle - math.pi / 2)
    y = val * math.sin(gap_angle - math.pi / 2)
    value_label_rows.append({"label": str(val), "x": x, "y": y})

value_label_df = pd.DataFrame(value_label_rows)

# Build the plot
# Note: geom_line() connects points sorted by x, which turns a circular/radial
# path into a chaotic zigzag; geom_path() preserves the data's own point order,
# which is required for these polar-via-cartesian shapes.
plot = (
    ggplot()
    # Gridlines (concentric circles) - thin solid low-alpha rings
    + geom_path(aes(x="x", y="y", group="radius"), data=grid_df, color=INK_SOFT, size=0.4, alpha=0.15)
    # Spokes (radial lines)
    + geom_path(aes(x="x", y="y", group="group"), data=spoke_df, color=INK_SOFT, size=0.4, alpha=0.3)
    # Filled polygons for each series (lower alpha for 4 overlapping series)
    + geom_polygon(aes(x="x", y="y", fill="series", group="series"), data=df, alpha=0.2)
    # Lines connecting points, in category order (not x-sorted)
    + geom_path(aes(x="x", y="y", color="series", group="series"), data=df, size=1.2)
    # Emphasize the top-scoring product as a focal point (thicker outline)
    + geom_path(
        aes(x="x", y="y", color="series", group="series"), data=df[df["series"] == hero], size=2.2, show_legend=False
    )
    # Points at each vertex (exclude the closing point to avoid double dot)
    + geom_point(aes(x="x", y="y", color="series"), data=df[df["order"] < n], size=3.5)
    # Custom color palette (Imprint)
    + scale_fill_manual(values=IMPRINT)
    + scale_color_manual(values=IMPRINT)
    # Axis limits for square plot
    + scale_x_continuous(limits=(-160, 160))
    + scale_y_continuous(limits=(-160, 160))
    # Title and legend
    + labs(
        title="Smartphone Comparison · radar-multi · python · letsplot · anyplot.ai", fill="Product", color="Product"
    )
    # Square format for symmetric radar chart (600x600 @ scale=4 -> 2400x2400)
    + ggsize(600, 600)
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        plot_title=element_text(size=16, color=INK),
        legend_title=element_text(size=13, color=INK),
        legend_text=element_text(size=12, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_position="right",
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid=element_blank(),
    )
)

# Add category labels as text
plot = plot + geom_text(aes(x="x", y="y", label="label"), data=label_df, size=5.5, color=INK)

# Add grid value labels
plot = plot + geom_text(aes(x="x", y="y", label="label"), data=value_label_df, size=4.5, color=INK_SOFT)

# Save outputs
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
