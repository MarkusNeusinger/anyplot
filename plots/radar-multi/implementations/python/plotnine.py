""" anyplot.ai
radar-multi: Multi-Series Radar Chart
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-07
"""

import math
import os
import sys


# Ensure we import plotnine module, not this file
sys.path = [p for p in sys.path if p != os.path.dirname(__file__)]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from plotnine import (  # noqa: E402
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_line,
    geom_point,
    geom_polygon,
    geom_text,
    ggplot,
    labs,
    scale_color_manual,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - Product comparison across key attributes
categories = ["Price", "Quality", "Durability", "Support", "Features", "Design"]
n = len(categories)

# Four products for comparison (scale 0-100)
products = {
    "Product A": [85, 90, 75, 80, 70, 85],
    "Product B": [70, 75, 90, 65, 85, 70],
    "Product C": [95, 60, 70, 90, 75, 60],
    "Product D": [60, 80, 85, 75, 90, 80],
}

# Okabe-Ito palette - first series is always #009E73
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Create angles for each category (evenly spaced around circle)
angles = [i * 2 * math.pi / n for i in range(n)]

# Build dataframe with x,y coordinates for polar plotting
# For radar chart, we need to close each polygon by repeating first point
data_rows = []
for series_name, values in products.items():
    for i, (cat, val, angle) in enumerate(zip(categories, values, angles, strict=True)):
        data_rows.append({"category": cat, "value": val, "angle": angle, "series": series_name, "order": i})
    # Close the polygon
    data_rows.append(
        {"category": categories[0], "value": values[0], "angle": angles[0], "series": series_name, "order": n}
    )

df = pd.DataFrame(data_rows)

# Convert to cartesian coordinates for plotting
df["x"] = df["value"] * np.cos(df["angle"] - math.pi / 2)
df["y"] = df["value"] * np.sin(df["angle"] - math.pi / 2)

# Create gridlines data (circles at 20, 40, 60, 80, 100)
grid_rows = []
grid_angles = np.linspace(0, 2 * math.pi, 101)
for radius in [20, 40, 60, 80, 100]:
    for angle in grid_angles:
        grid_rows.append(
            {"x": radius * math.cos(angle - math.pi / 2), "y": radius * math.sin(angle - math.pi / 2), "radius": radius}
        )

grid_df = pd.DataFrame(grid_rows)

# Create axis lines (spokes)
spoke_rows = []
for angle in angles:
    spoke_rows.append({"x": 0, "y": 0, "angle_group": angle})
    spoke_rows.append(
        {"x": 105 * math.cos(angle - math.pi / 2), "y": 105 * math.sin(angle - math.pi / 2), "angle_group": angle}
    )

spoke_df = pd.DataFrame(spoke_rows)

# Create axis labels data (positioned just outside the chart)
label_rows = []
for cat, angle in zip(categories, angles, strict=True):
    label_rows.append(
        {"label": cat, "x": 120 * math.cos(angle - math.pi / 2), "y": 120 * math.sin(angle - math.pi / 2)}
    )

label_df = pd.DataFrame(label_rows)

# Plot
plot = (
    ggplot()
    # Gridlines (circles)
    + geom_line(
        aes(x="x", y="y", group="radius"), data=grid_df, color=INK_SOFT, size=0.5, alpha=0.15, linetype="dashed"
    )
    # Spokes
    + geom_line(aes(x="x", y="y", group="angle_group"), data=spoke_df, color=INK_SOFT, size=0.5, alpha=0.15)
    # Filled polygons for each series (with transparency for overlap visibility)
    + geom_polygon(aes(x="x", y="y", fill="series", group="series"), data=df, alpha=0.2)
    # Lines connecting points
    + geom_line(aes(x="x", y="y", color="series", group="series"), data=df, size=1.5)
    # Points at each vertex (exclude closing points)
    + geom_point(aes(x="x", y="y", color="series"), data=df[df["order"] < n], size=5)
    # Category labels
    + geom_text(aes(x="x", y="y", label="label"), data=label_df, size=5, color=INK)
    # Apply Okabe-Ito colors
    + scale_fill_manual(values=IMPRINT)
    + scale_color_manual(values=IMPRINT)
    # Axis scaling
    + scale_x_continuous(limits=(-150, 150))
    + scale_y_continuous(limits=(-150, 150))
    # Labels and title
    + labs(title="radar-multi · plotnine · anyplot.ai", fill="Product", color="Product")
    # Theme for clean radar appearance with theme-adaptive colors
    + theme(
        figure_size=(12, 12),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=24, color=INK),
        legend_background=element_rect(fill=PAGE_BG, color=INK_SOFT),
        legend_title=element_text(size=18, color=INK),
        legend_text=element_text(size=16, color=INK_SOFT),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300)
