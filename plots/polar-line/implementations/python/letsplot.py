""" pyplots.ai
polar-line: Polar Line Plot
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_text,
    geom_path,
    geom_point,
    geom_text,
    ggplot,
    ggsize,
    labs,
    scale_color_manual,
    theme,
    theme_void,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Data - Monthly average temperature pattern (cyclical)
np.random.seed(42)
months = np.arange(0, 360, 30)  # 12 months as angles (0, 30, 60, ... 330)
month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Simulated temperature pattern (warm summer, cold winter)
temp_city_a = np.array([2, 4, 10, 15, 20, 25, 28, 27, 22, 14, 7, 3])
temp_city_b = np.array([5, 7, 12, 17, 22, 27, 30, 29, 24, 16, 10, 6])

# Close the loop by adding the first point at the end
angles_closed = np.append(months, 360)
temp_a_closed = np.append(temp_city_a, temp_city_a[0])
temp_b_closed = np.append(temp_city_b, temp_city_b[0])

# Convert to radians for polar coordinates
theta_a = np.radians(angles_closed)
theta_b = np.radians(angles_closed)

# Create x, y coordinates from polar (for lets-plot which uses Cartesian)
x_a = temp_a_closed * np.cos(theta_a)
y_a = temp_a_closed * np.sin(theta_a)
x_b = temp_b_closed * np.cos(theta_b)
y_b = temp_b_closed * np.sin(theta_b)

# Create DataFrame
df = pd.DataFrame(
    {
        "x": np.concatenate([x_a, x_b]),
        "y": np.concatenate([y_a, y_b]),
        "radius": np.concatenate([temp_a_closed, temp_b_closed]),
        "angle": np.concatenate([angles_closed, angles_closed]),
        "city": ["City A"] * len(x_a) + ["City B"] * len(x_b),
    }
)

# Create concentric circles for polar grid
grid_radii = [10, 20, 30]
circle_points = 100
grid_circles = []
for r in grid_radii:
    theta_grid = np.linspace(0, 2 * np.pi, circle_points)
    grid_circles.append(pd.DataFrame({"x": r * np.cos(theta_grid), "y": r * np.sin(theta_grid), "radius": r}))
grid_df = pd.concat(grid_circles, ignore_index=True)

# Create radial lines for grid (every 30 degrees = each month)
radial_lines = []
for angle_deg in range(0, 360, 30):
    angle_rad = np.radians(angle_deg)
    radial_lines.append(
        pd.DataFrame({"x": [0, 35 * np.cos(angle_rad)], "y": [0, 35 * np.sin(angle_rad)], "angle": angle_deg})
    )
radial_df = pd.concat(radial_lines, ignore_index=True)

# Month labels positions
label_radius = 34
month_labels_df = pd.DataFrame(
    {
        "x": [label_radius * np.cos(np.radians(a)) for a in months],
        "y": [label_radius * np.sin(np.radians(a)) for a in months],
        "label": month_names,
    }
)

# Plot
plot = (
    ggplot()
    # Concentric grid circles
    + geom_path(aes(x="x", y="y", group="radius"), data=grid_df, color="#CCCCCC", size=0.5, alpha=0.6)
    # Radial grid lines
    + geom_path(aes(x="x", y="y", group="angle"), data=radial_df, color="#CCCCCC", size=0.5, alpha=0.6)
    # Data lines
    + geom_path(aes(x="x", y="y", color="city"), data=df, size=2)
    # Data points
    + geom_point(aes(x="x", y="y", color="city"), data=df, size=5)
    # Month labels
    + geom_text(aes(x="x", y="y", label="label"), data=month_labels_df, size=14, color="#333333")
    # Colors
    + scale_color_manual(values=["#306998", "#FFD43B"])
    # Theme and labels
    + labs(title="polar-line · letsplot · pyplots.ai", color="Location")
    + theme_void()
    + theme(
        plot_title=element_text(size=24, hjust=0.5),
        legend_position="right",
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
    )
    + coord_fixed()
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)

# Also save HTML for interactive version
ggsave(plot, "plot.html", path=".")
