"""anyplot.ai
polar-scatter: Polar Scatter Plot
Library: letsplot 4.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-11-20
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

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
COMPASS_DEGREES = [0, 45, 90, 135, 180, 225, 270, 315]
COMPASS_LABELS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]

# Columns: set these to your table's column names
DIRECTION = "Wind direction (°)"  # role: theta
SPEED = "Wind speed (m/s)"  # role: radius
TIME_OF_DAY = "Time of day"  # role: category

# Data: replace this block with your own table, for example df = pd.read_csv("wind.csv")
np.random.seed(42)
n_points = 120

# Prevailing winds from W and SW, drawn per 45-degree sector
direction_probs = np.array([0.05, 0.15, 0.08, 0.05, 0.05, 0.12, 0.30, 0.20])  # N, NE, E, SE, S, SW, W, NW
direction_centers = np.array(COMPASS_DEGREES)
chosen_sectors = np.random.choice(8, size=n_points, p=direction_probs / direction_probs.sum())
directions = (direction_centers[chosen_sectors] + np.random.uniform(-20, 20, n_points)) % 360

# Weibull-like speeds, stronger from the SW-W side
base_speed = np.random.weibull(2.0, n_points) * 6 + 2
speeds = np.clip(base_speed * (1 + 0.4 * np.sin(np.radians(directions - 240))), 1, 22)

hour = np.random.choice(np.arange(6, 22), size=n_points)
time_of_day = np.where(hour < 12, "Morning", np.where(hour < 18, "Afternoon", "Evening"))

df = pd.DataFrame({DIRECTION: directions, SPEED: speeds, TIME_OF_DAY: time_of_day})
df[TIME_OF_DAY] = pd.Categorical(df[TIME_OF_DAY], categories=["Morning", "Afternoon", "Evening"], ordered=True)

# Plot: coord_polar starts at 12 o'clock and runs clockwise
plot = (
    ggplot(df, aes(x=DIRECTION, y=SPEED, color=TIME_OF_DAY))
    + geom_point(size=3, alpha=0.75)
    + coord_polar(start=0, direction=1)
    + scale_x_continuous(breaks=COMPASS_DEGREES, labels=COMPASS_LABELS, limits=[0, 360], expand=[0, 0])
    + scale_y_continuous(limits=[0, df[SPEED].max() * 1.08], expand=[0, 0])
    + scale_color_manual(values=IMPRINT_PALETTE)
    + labs(title="polar-scatter · python · letsplot · anyplot.ai", x="")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK_SOFT, size=0.3),
        panel_grid_minor=element_line(color=INK_SOFT, size=0.2),
        plot_title=element_text(size=16, hjust=0.5, color=INK),
        axis_text=element_text(size=11, color=INK_SOFT),
        axis_title_y=element_text(size=13, color=INK),
        axis_line=element_line(color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_title=element_text(size=10, color=INK),
        legend_text=element_text(size=9, color=INK_SOFT),
        legend_position=[1.0, 1.0],
        legend_justification=[1, 1],
    )
    + ggsize(600, 600)
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
