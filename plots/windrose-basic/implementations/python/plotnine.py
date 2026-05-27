""" anyplot.ai
windrose-basic: Wind Rose Chart
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-07
"""

import math
import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_line,
    geom_polygon,
    geom_text,
    ggplot,
    guide_legend,
    labs,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - Simulated wind measurements from an airport runway environment
# 8 direction bins: N, NE, E, SE, S, SW, W, NW
# 5 speed bins: 0-5, 5-10, 10-15, 15-20, 20+ m/s
# Airport wind patterns show influence from local terrain and seasonal variations
np.random.seed(42)

directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
n_dirs = len(directions)

# Wind speed bins and their labels
speed_bins = ["0-5", "5-10", "10-15", "15-20", "20+"]

# Frequencies (%) for each direction and speed bin
# Airport with variable wind patterns: N/S dominance, minimal calm winds
frequencies = {
    "N": [2.0, 2.5, 1.8, 0.8, 0.3],
    "NE": [1.8, 1.5, 0.8, 0.3, 0.1],
    "E": [1.5, 1.2, 0.6, 0.2, 0.0],
    "SE": [1.8, 1.5, 0.9, 0.4, 0.1],
    "S": [2.2, 2.8, 1.9, 0.9, 0.4],  # Secondary wind direction
    "SW": [2.0, 1.8, 1.0, 0.5, 0.2],
    "W": [1.5, 1.2, 0.6, 0.2, 0.0],
    "NW": [1.8, 1.5, 0.8, 0.3, 0.1],
}

# Colors for wind speed bins: cool (calm) to warm (strong) progression
# Using perceptually-uniform colors appropriate for wind speed ranges
speed_colors = {
    "0-5": "#4467A3",  # Okabe-Ito blue (calm)
    "5-10": "#2ABCCD",  # Okabe-Ito sky blue
    "10-15": "#009E73",  # Okabe-Ito green
    "15-20": "#AE3030",  # Okabe-Ito orange
    "20+": "#C475FD",  # Okabe-Ito red-orange (strong)
}

# Calculate direction angles (N=top, clockwise)
# N is at 90 degrees (top), going clockwise
dir_angles = {
    "N": math.pi / 2,
    "NE": math.pi / 4,
    "E": 0,
    "SE": -math.pi / 4,
    "S": -math.pi / 2,
    "SW": -3 * math.pi / 4,
    "W": math.pi,
    "NW": 3 * math.pi / 4,
}

# Create stacked wedges for each direction
wedge_rows = []
n_arc_points = 20  # Points along the arc for smooth edges
wedge_width = 2 * math.pi / n_dirs  # Width of each direction bin

wedge_id = 0
for direction in directions:
    center_angle = dir_angles[direction]
    start_angle = center_angle + wedge_width / 2 - 0.03  # Small gap
    end_angle = center_angle - wedge_width / 2 + 0.03

    cumulative_radius = 0
    for speed_idx, speed_bin in enumerate(speed_bins):
        freq = frequencies[direction][speed_idx]
        if freq <= 0:
            continue

        # Inner and outer radius for this stack segment
        inner_radius = cumulative_radius
        outer_radius = cumulative_radius + freq

        # Build wedge polygon: inner arc -> outer arc -> close
        # Start with inner arc (from start to end angle)
        arc_angles = np.linspace(start_angle, end_angle, n_arc_points)

        # Inner arc points (counterclockwise from start to end)
        for angle in arc_angles:
            x = inner_radius * math.cos(angle)
            y = inner_radius * math.sin(angle)
            wedge_rows.append({"x": x, "y": y, "wedge_id": wedge_id, "speed": speed_bin, "direction": direction})

        # Outer arc points (clockwise from end to start)
        for angle in reversed(arc_angles):
            x = outer_radius * math.cos(angle)
            y = outer_radius * math.sin(angle)
            wedge_rows.append({"x": x, "y": y, "wedge_id": wedge_id, "speed": speed_bin, "direction": direction})

        # Close the polygon
        first_x = inner_radius * math.cos(start_angle)
        first_y = inner_radius * math.sin(start_angle)
        wedge_rows.append(
            {"x": first_x, "y": first_y, "wedge_id": wedge_id, "speed": speed_bin, "direction": direction}
        )

        cumulative_radius = outer_radius
        wedge_id += 1

df = pd.DataFrame(wedge_rows)

# Preserve speed order for legend
df["speed"] = pd.Categorical(df["speed"], categories=speed_bins, ordered=True)

# Create radial gridlines (circles at frequency percentages)
grid_rows = []
grid_angles = np.linspace(0, 2 * math.pi, 101)
grid_radii = [5, 10, 15]  # Frequency percentage circles

for radius in grid_radii:
    for angle in grid_angles:
        grid_rows.append({"x": radius * math.cos(angle), "y": radius * math.sin(angle), "radius": radius})

grid_df = pd.DataFrame(grid_rows)

# Create spoke lines (one for each direction)
spoke_rows = []
max_radius = 18  # Extend spokes beyond data
for i, direction in enumerate(directions):
    angle = dir_angles[direction]
    spoke_rows.append({"x": 0, "y": 0, "spoke_id": i})
    spoke_rows.append({"x": max_radius * math.cos(angle), "y": max_radius * math.sin(angle), "spoke_id": i})

spoke_df = pd.DataFrame(spoke_rows)

# Create direction labels positioned outside the chart
label_rows = []
label_radius = 20
for direction in directions:
    angle = dir_angles[direction]
    label_rows.append({"label": direction, "x": label_radius * math.cos(angle), "y": label_radius * math.sin(angle)})

label_df = pd.DataFrame(label_rows)

# Create frequency labels on gridlines (positioned at top of circles for better visibility)
freq_label_rows = []
for radius in grid_radii:
    # Position labels at top of each circle (90 degrees) with offset
    angle = math.pi / 2 + 0.20
    freq_label_rows.append(
        {"label": f"{radius}%", "x": radius * math.cos(angle) + 1.5, "y": radius * math.sin(angle) + 0.5}
    )

freq_label_df = pd.DataFrame(freq_label_rows)

# Create "Frequency (%)" label to explain what gridlines represent
freq_axis_label_df = pd.DataFrame([{"label": "Frequency (%)", "x": -2.5, "y": 21.5}])

# Plot
plot = (
    ggplot()
    # Gridlines (circles)
    + geom_line(aes(x="x", y="y", group="radius"), data=grid_df, color=INK_SOFT, size=0.5, alpha=0.3, linetype="dashed")
    # Spoke lines
    + geom_line(aes(x="x", y="y", group="spoke_id"), data=spoke_df, color=INK_SOFT, size=0.4, alpha=0.4)
    # Wind rose wedges (stacked)
    + geom_polygon(aes(x="x", y="y", fill="speed", group="wedge_id"), data=df, color=PAGE_BG, size=0.3, alpha=0.95)
    # Direction labels
    + geom_text(aes(x="x", y="y", label="label"), data=label_df, size=18, fontweight="bold", color=INK)
    # Frequency labels
    + geom_text(aes(x="x", y="y", label="label"), data=freq_label_df, size=16, color=INK_SOFT, fontweight="bold")
    # Frequency axis label
    + geom_text(aes(x="x", y="y", label="label"), data=freq_axis_label_df, size=14, color=INK_SOFT, fontstyle="italic")
    # Colors with native legend
    + scale_fill_manual(values=speed_colors, name="Wind Speed (m/s)", guide=guide_legend(reverse=False))
    # Axis scaling
    + scale_x_continuous(limits=(-24, 24))
    + scale_y_continuous(limits=(-26, 24))
    # Title
    + labs(title="windrose-basic · plotnine · anyplot.ai")
    # Theme for clean wind rose appearance
    + theme(
        figure_size=(12, 12),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=None),
        plot_title=element_text(size=28, ha="center", color=INK, face="bold"),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        legend_position="right",
        legend_title=element_text(size=16, fontweight="bold", color=INK),
        legend_text=element_text(size=14, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT, size=0.5),
        legend_key=element_rect(fill=ELEVATED_BG, color=None),
        legend_key_size=24,
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300)
