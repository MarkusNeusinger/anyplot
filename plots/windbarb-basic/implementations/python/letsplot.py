""" pyplots.ai
windbarb-basic: Wind Barb Plot for Meteorological Data
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-11
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_blank,
    element_line,
    element_text,
    geom_point,
    geom_polygon,
    geom_segment,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Set seed for reproducibility
np.random.seed(42)

# Generate grid of weather stations (8x6 grid = 48 stations)
n_x, n_y = 8, 6
x_coords = np.linspace(0, 140, n_x)
y_coords = np.linspace(0, 100, n_y)
X, Y = np.meshgrid(x_coords, y_coords)
x = X.flatten()
y = Y.flatten()

# Generate wind components (u = east-west, v = north-south) in knots
# Create varying wind patterns simulating a weather system
u = 15 * np.sin(x / 30) + np.random.normal(0, 3, len(x))
v = 10 * np.cos(y / 20) + np.random.normal(0, 3, len(y))

# Calculate wind speed
wind_speed = np.sqrt(u**2 + v**2)

# Wind barb parameters
barb_length = 8
barb_spacing = 1.5
barb_tick_length = 2.5

# Create wind barb segments and pennants
segments = []
pennants = []

for i in range(len(x)):
    speed = np.sqrt(u[i] ** 2 + v[i] ** 2)

    # Wind barbs point in direction FROM which wind blows (reverse direction)
    angle = np.arctan2(-v[i], -u[i])

    if speed < 2.5:
        continue

    cos_a, sin_a = np.cos(angle), np.sin(angle)
    x_end = x[i] + barb_length * cos_a
    y_end = y[i] + barb_length * sin_a

    # Main staff
    segments.append({"x": x[i], "y": y[i], "xend": x_end, "yend": y_end})

    remaining_speed = speed
    barb_position = barb_length - 0.5
    perp_angle = angle + np.pi / 2

    # Pennants (50 knots each)
    while remaining_speed >= 47.5:
        bx = x[i] + barb_position * cos_a
        by = y[i] + barb_position * sin_a
        tip_x = bx + barb_tick_length * np.cos(perp_angle)
        tip_y = by + barb_tick_length * np.sin(perp_angle)
        base_x = x[i] + (barb_position - barb_spacing) * cos_a
        base_y = y[i] + (barb_position - barb_spacing) * sin_a
        pennants.append({"x": [bx, tip_x, base_x], "y": [by, tip_y, base_y]})
        remaining_speed -= 50
        barb_position -= barb_spacing

    # Full barbs (10 knots each)
    while remaining_speed >= 7.5:
        bx = x[i] + barb_position * cos_a
        by = y[i] + barb_position * sin_a
        segments.append(
            {
                "x": bx,
                "y": by,
                "xend": bx + barb_tick_length * np.cos(perp_angle),
                "yend": by + barb_tick_length * np.sin(perp_angle),
            }
        )
        remaining_speed -= 10
        barb_position -= barb_spacing

    # Half barb (5 knots)
    if remaining_speed >= 2.5:
        bx = x[i] + barb_position * cos_a
        by = y[i] + barb_position * sin_a
        segments.append(
            {
                "x": bx,
                "y": by,
                "xend": bx + barb_tick_length * 0.5 * np.cos(perp_angle),
                "yend": by + barb_tick_length * 0.5 * np.sin(perp_angle),
            }
        )

# Create DataFrames
segment_df = pd.DataFrame(segments)
station_df = pd.DataFrame({"x": x, "y": y, "speed": wind_speed})
calm_df = station_df[station_df["speed"] < 2.5].copy()

# Build the plot
plot = ggplot() + theme_minimal()

# Wind barb segments (staffs and barbs)
if len(segment_df) > 0:
    plot = plot + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=segment_df, color="#306998", size=1.2)

# Pennants as filled polygons
for pennant in pennants:
    pennant_df = pd.DataFrame({"x": pennant["x"], "y": pennant["y"]})
    plot = plot + geom_polygon(aes(x="x", y="y"), data=pennant_df, fill="#306998", color="#306998", size=0.5)

# Calm wind circles (open circles for < 2.5 knots)
if len(calm_df) > 0:
    plot = plot + geom_point(aes(x="x", y="y"), data=calm_df, shape=1, size=6, color="#306998", stroke=1.5)

# Station markers
plot = plot + geom_point(aes(x="x", y="y"), data=station_df, size=2, color="#306998")

# Styling
plot = (
    plot
    + labs(x="Longitude (°E)", y="Latitude (°N)", title="windbarb-basic · letsplot · pyplots.ai")
    + coord_fixed(ratio=1)
    + scale_x_continuous(expand=[0.1, 0])
    + scale_y_continuous(expand=[0.1, 0])
    + theme(
        plot_title=element_text(size=24),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        panel_grid_major=element_line(color="#CCCCCC", size=0.5),
        panel_grid_minor=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save outputs
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
