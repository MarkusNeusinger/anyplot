"""anyplot.ai
radar-basic: Basic Radar Chart
Library: plotnine | Python 3.13
Quality: pending | Updated: 2026-04-29
"""

import math
import os
import sys


# Prevent this file from shadowing the plotnine library when run from its own directory
sys.path = [p for p in sys.path if not p or os.path.abspath(p) != os.path.abspath(os.path.dirname(__file__))]

import numpy as np
import pandas as pd
from plotnine import (
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


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID_COLOR = "#C8C8C0" if THEME == "light" else "#3A3A35"

OKABE_ITO = ["#009E73", "#D55E00"]

# Data — employee performance metrics
categories = ["Technical", "Communication", "Leadership", "Creativity", "Teamwork", "Problem Solving"]
values_alice = [85, 70, 60, 90, 75, 80]
values_bob = [70, 85, 75, 65, 90, 70]

n = len(categories)
angles = [i * 2 * math.pi / n for i in range(n)]

# Build cartesian coordinates for each series
data_rows = []
for i, (cat, val_a, val_b, angle) in enumerate(zip(categories, values_alice, values_bob, angles, strict=True)):
    data_rows.append({"category": cat, "value": val_a, "angle": angle, "series": "Alice", "order": i})
    data_rows.append({"category": cat, "value": val_b, "angle": angle, "series": "Bob", "order": i})

# Close polygons by repeating the first point
data_rows.append(
    {"category": categories[0], "value": values_alice[0], "angle": angles[0], "series": "Alice", "order": n}
)
data_rows.append({"category": categories[0], "value": values_bob[0], "angle": angles[0], "series": "Bob", "order": n})

df = pd.DataFrame(data_rows)
df["x"] = df["value"] * np.cos(df["angle"] - math.pi / 2)
df["y"] = df["value"] * np.sin(df["angle"] - math.pi / 2)

# Gridlines (concentric circles at 20, 40, 60, 80, 100)
grid_rows = []
grid_angles = np.linspace(0, 2 * math.pi, 101)
for radius in [20, 40, 60, 80, 100]:
    for a in grid_angles:
        grid_rows.append(
            {"x": radius * math.cos(a - math.pi / 2), "y": radius * math.sin(a - math.pi / 2), "radius": radius}
        )
grid_df = pd.DataFrame(grid_rows)

# Spokes (axis lines from center to edge)
spoke_rows = []
for angle in angles:
    spoke_rows.append({"x": 0, "y": 0, "angle_group": angle})
    spoke_rows.append(
        {"x": 105 * math.cos(angle - math.pi / 2), "y": 105 * math.sin(angle - math.pi / 2), "angle_group": angle}
    )
spoke_df = pd.DataFrame(spoke_rows)

# Category labels positioned just outside the chart
label_rows = []
for cat, angle in zip(categories, angles, strict=True):
    label_rows.append(
        {"label": cat, "x": 122 * math.cos(angle - math.pi / 2), "y": 122 * math.sin(angle - math.pi / 2)}
    )
label_df = pd.DataFrame(label_rows)

# Plot
plot = (
    ggplot()
    + geom_line(aes(x="x", y="y", group="radius"), data=grid_df, color=GRID_COLOR, size=0.5, linetype="dashed")
    + geom_line(aes(x="x", y="y", group="angle_group"), data=spoke_df, color=GRID_COLOR, size=0.5)
    + geom_polygon(aes(x="x", y="y", fill="series", group="series"), data=df, alpha=0.25)
    + geom_line(aes(x="x", y="y", color="series", group="series"), data=df, size=1.5)
    + geom_point(aes(x="x", y="y", color="series"), data=df[df["order"] < n], size=5)
    + geom_text(aes(x="x", y="y", label="label"), data=label_df, size=16, color=INK)
    + scale_fill_manual(values=OKABE_ITO)
    + scale_color_manual(values=OKABE_ITO)
    + scale_x_continuous(limits=(-150, 150))
    + scale_y_continuous(limits=(-150, 150))
    + labs(title="radar-basic · plotnine · anyplot.ai", fill="Employee", color="Employee")
    + theme(
        figure_size=(12, 12),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        plot_title=element_text(size=24, color=INK),
        legend_title=element_text(size=16, color=INK),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
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
