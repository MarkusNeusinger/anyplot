""" pyplots.ai
windrose-basic: Wind Rose Chart
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 90/100 | Created: 2025-12-24
"""

import math

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


# Data - Simulated wind measurements from a coastal weather station
# 8 direction bins: N, NE, E, SE, S, SW, W, NW
# 5 speed bins: 0-5, 5-10, 10-15, 15-20, 20+ m/s
np.random.seed(42)

directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
n_dirs = len(directions)

# Wind speed bins and their labels
speed_bins = ["0-5", "5-10", "10-15", "15-20", "20+"]

# Frequencies (%) for each direction and speed bin
# Coastal station with prevailing SW winds
frequencies = {
    "N": [2.5, 1.5, 0.8, 0.3, 0.1],
    "NE": [3.0, 2.0, 1.0, 0.4, 0.1],
    "E": [2.8, 1.8, 0.9, 0.3, 0.1],
    "SE": [3.5, 2.5, 1.2, 0.5, 0.2],
    "S": [4.0, 3.0, 1.8, 0.8, 0.3],
    "SW": [5.5, 4.5, 3.0, 1.5, 0.6],  # Prevailing wind direction
    "W": [4.8, 3.8, 2.2, 1.0, 0.4],
    "NW": [3.2, 2.2, 1.2, 0.5, 0.2],
}

# Colors for wind speed bins (cool to warm progression)
speed_colors = {
    "0-5": "#306998",  # Python Blue (calm)
    "5-10": "#4A90C2",  # Light blue
    "10-15": "#7FB069",  # Green
    "15-20": "#FFD43B",  # Python Yellow
    "20+": "#E85D04",  # Orange (strong)
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
    # Position labels at top of each circle (90 degrees) with slight offset
    angle = math.pi / 2 + 0.15  # Slightly offset from North spoke
    freq_label_rows.append({"label": f"{radius}%", "x": radius * math.cos(angle) + 1.8, "y": radius * math.sin(angle)})

freq_label_df = pd.DataFrame(freq_label_rows)

# Create "Frequency (%)" label to explain what gridlines represent
freq_axis_label_df = pd.DataFrame([{"label": "Frequency (%)", "x": -3, "y": 22}])

# Plot
plot = (
    ggplot()
    # Gridlines (circles)
    + geom_line(
        aes(x="x", y="y", group="radius"), data=grid_df, color="#AAAAAA", size=0.5, alpha=0.7, linetype="dashed"
    )
    # Spoke lines
    + geom_line(aes(x="x", y="y", group="spoke_id"), data=spoke_df, color="#CCCCCC", size=0.4, alpha=0.6)
    # Wind rose wedges (stacked)
    + geom_polygon(aes(x="x", y="y", fill="speed", group="wedge_id"), data=df, color="#FFFFFF", size=0.2, alpha=0.9)
    # Direction labels
    + geom_text(aes(x="x", y="y", label="label"), data=label_df, size=16, fontweight="bold", color="#333333")
    # Frequency labels
    + geom_text(aes(x="x", y="y", label="label"), data=freq_label_df, size=18, color="#333333", fontweight="bold")
    # Frequency axis label
    + geom_text(aes(x="x", y="y", label="label"), data=freq_axis_label_df, size=16, color="#333333", fontstyle="italic")
    # Colors with native legend
    + scale_fill_manual(values=speed_colors, name="Wind Speed (m/s)", guide=guide_legend(reverse=False))
    # Axis scaling
    + scale_x_continuous(limits=(-24, 24))
    + scale_y_continuous(limits=(-26, 24))
    # Title
    + labs(title="windrose-basic · plotnine · pyplots.ai")
    # Theme for clean wind rose appearance
    + theme(
        figure_size=(12, 12),
        plot_title=element_text(size=24, ha="center", color="#333333"),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_background=element_rect(fill="#FFFFFF"),
        plot_background=element_rect(fill="#FFFFFF"),
        legend_position="right",
        legend_title=element_text(size=14, fontweight="bold"),
        legend_text=element_text(size=12),
        legend_background=element_rect(fill="#FFFFFF", color="#CCCCCC", size=0.5),
        legend_key_size=20,
    )
)

# Save
plot.save("plot.png", dpi=300)
