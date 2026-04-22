""" pyplots.ai
polar-scatter: Polar Scatter Plot
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Generate synthetic wind measurement data
np.random.seed(42)
n_points = 120

# Simulate wind direction with prevailing winds from SW and NE
# Use mixture of von Mises distributions for realistic directional clustering
direction_probs = np.array([0.05, 0.15, 0.08, 0.05, 0.05, 0.12, 0.30, 0.20])  # N, NE, E, SE, S, SW, W, NW
direction_centers = np.array([0, 45, 90, 135, 180, 225, 270, 315])

# Sample primary direction centers
chosen_sectors = np.random.choice(8, size=n_points, p=direction_probs / direction_probs.sum())
# Add variance within each sector
directions = direction_centers[chosen_sectors] + np.random.uniform(-20, 20, n_points)
directions = directions % 360

# Wind speed (m/s) - Weibull-like distribution, stronger from SW-W directions
base_speed = np.random.weibull(2.0, n_points) * 6 + 2
# Increase speed for SW-W winds
direction_factor = 1 + 0.4 * np.sin(np.radians(directions - 240))
speeds = base_speed * direction_factor
speeds = np.clip(speeds, 1, 22)

# Time of day for color encoding (morning: 6-12, afternoon: 12-18, evening: 18-24, night: 0-6)
hour = np.random.choice([6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21], size=n_points)
time_of_day = np.where(hour < 12, "Morning", np.where(hour < 18, "Afternoon", "Evening"))

# Create DataFrame
df = pd.DataFrame({"direction": directions, "speed": speeds, "time_of_day": time_of_day})

# Order time of day for legend
df["time_of_day"] = pd.Categorical(df["time_of_day"], categories=["Morning", "Afternoon", "Evening"], ordered=True)

# Colors for time of day - Python Blue, Yellow, and an evening color (accessible)
time_colors = ["#306998", "#FFD43B", "#9B59B6"]

# Create polar scatter plot
# coord_polar: start=0 means 12 o'clock (North), direction=1 is clockwise
plot = (
    ggplot(df, aes(x="direction", y="speed", color="time_of_day"))
    + geom_point(size=5, alpha=0.75)
    + coord_polar(start=0, direction=1)
    + scale_x_continuous(
        breaks=[0, 45, 90, 135, 180, 225, 270, 315],
        labels=["N", "NE", "E", "SE", "S", "SW", "W", "NW"],
        limits=[0, 360],
        expand=[0, 0],
    )
    + scale_y_continuous(limits=[0, None], expand=[0, 0.05])
    + scale_color_manual(values=time_colors, name="Time of Day")
    + labs(title="Wind Observations · polar-scatter · letsplot · pyplots.ai", x="", y="Wind Speed (m/s)")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, hjust=0.5),
        axis_text=element_text(size=16),
        axis_title_y=element_text(size=18),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        legend_position="right",
        panel_grid_major=element_line(color="#CCCCCC", size=0.5),
        panel_grid_minor=element_line(color="#EEEEEE", size=0.3),
    )
    + ggsize(1200, 1200)  # Square format for polar plot, scaled 3x = 3600x3600
)

# Save as PNG and HTML
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
