""" anyplot.ai
polar-basic: Basic Polar Chart
Library: plotnine 0.15.3 | Python 3.13.13
Quality: 87/100 | Updated: 2026-04-30
"""

import math
import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_blank,
    element_rect,
    element_text,
    geom_path,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"  # Okabe-Ito position 1

# Data - Hourly activity levels throughout the day (cyclical pattern)
np.random.seed(42)
hours = np.arange(0, 24)
base_activity = 20 + 40 * np.sin((hours - 6) * np.pi / 12) ** 2
activity = base_activity + np.random.uniform(-8, 8, 24)
activity = np.clip(activity, 5, 100)

# Convert hours to angles (0 hours = top, clockwise)
theta = hours * 2 * math.pi / 24 - math.pi / 2

# Convert polar to Cartesian coordinates
x = activity * np.cos(theta)
y = activity * np.sin(theta)

df = pd.DataFrame({"hour": hours, "activity": activity, "theta": theta, "x": x, "y": y})

# Close the loop by adding first point at end
df_closed = pd.concat([df, df.iloc[[0]]], ignore_index=True)

# Circular gridlines (at 25, 50, 75, 100 radius)
grid_rows = []
grid_angles = np.linspace(0, 2 * math.pi, 101)
for radius in [25, 50, 75, 100]:
    for angle in grid_angles:
        grid_rows.append({"x": radius * np.cos(angle), "y": radius * np.sin(angle), "radius": radius})

grid_df = pd.DataFrame(grid_rows)

# Radial spokes (every 3 hours = 8 spokes)
spoke_rows = []
spoke_hours = [0, 3, 6, 9, 12, 15, 18, 21]
for h in spoke_hours:
    angle = h * 2 * math.pi / 24 - math.pi / 2
    spoke_rows.append({"x1": 0, "y1": 0, "x2": 105 * np.cos(angle), "y2": 105 * np.sin(angle)})

spoke_df = pd.DataFrame(spoke_rows)

# Hour labels positioned outside the chart
label_rows = []
for h in spoke_hours:
    angle = h * 2 * math.pi / 24 - math.pi / 2
    label_rows.append({"label": f"{h:02d}:00", "x": 122 * np.cos(angle), "y": 122 * np.sin(angle)})

label_df = pd.DataFrame(label_rows)

# Radius labels (activity level scale)
radius_labels = [{"label": str(r), "x": r + 4, "y": 6} for r in [25, 50, 75, 100]]
radius_label_df = pd.DataFrame(radius_labels)

# Plot
plot = (
    ggplot()
    # Circular gridlines
    + geom_path(aes(x="x", y="y", group="radius"), data=grid_df, color=INK_SOFT, size=0.4, alpha=0.4, linetype="dashed")
    # Radial spokes
    + geom_segment(aes(x="x1", y="y1", xend="x2", yend="y2"), data=spoke_df, color=INK_SOFT, size=0.4, alpha=0.4)
    # Data line
    + geom_path(aes(x="x", y="y"), data=df_closed, color=BRAND, size=1.5, alpha=0.9)
    # Data points
    + geom_point(aes(x="x", y="y"), data=df, color=PAGE_BG, fill=BRAND, size=4, stroke=1.5)
    # Hour labels
    + geom_text(aes(x="x", y="y", label="label"), data=label_df, size=14, color=INK_SOFT)
    # Radius value labels
    + geom_text(aes(x="x", y="y", label="label"), data=radius_label_df, size=10, color=INK_MUTED, ha="left")
    + coord_fixed(ratio=1)
    + scale_x_continuous(limits=(-145, 145))
    + scale_y_continuous(limits=(-145, 145))
    + labs(title="Hourly Activity Levels · polar-basic · plotnine · anyplot.ai")
    + theme(
        figure_size=(12, 12),
        plot_title=element_text(size=24, ha="center", color=INK),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300)
