""" anyplot.ai
polar-scatter: Polar Scatter Plot
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 84/100 | Updated: 2026-05-09
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (categorical)
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

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

# Time of day for color encoding (morning: 6-12, afternoon: 12-18, evening: 18-24)
hour = np.random.choice([6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21], size=n_points)
time_of_day = np.where(hour < 12, "Morning", np.where(hour < 18, "Afternoon", "Evening"))

# Create DataFrame
df = pd.DataFrame({"direction": directions, "speed": speeds, "time_of_day": time_of_day})

# Order time of day for legend
df["time_of_day"] = pd.Categorical(df["time_of_day"], categories=["Morning", "Afternoon", "Evening"], ordered=True)

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
    + scale_color_manual(values=IMPRINT, name="Time of Day")
    + labs(title="polar-scatter · letsplot · anyplot.ai", x="", y="Wind Speed (m/s)")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK_SOFT, size=0.3),
        panel_grid_minor=element_line(color=INK_SOFT, size=0.2),
        plot_title=element_text(size=24, hjust=0.5, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_title_y=element_text(size=20, color=INK),
        axis_line=element_line(color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_title=element_text(size=18, color=INK),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_position="right",
    )
    + ggsize(1200, 1200)  # Square format for polar plot, scaled 3x = 3600x3600
)

# Save as PNG and HTML
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)
ggsave(plot, f"plot-{THEME}.html", path=".")
