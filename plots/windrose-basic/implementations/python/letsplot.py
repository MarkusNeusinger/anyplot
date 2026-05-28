""" anyplot.ai
windrose-basic: Wind Rose Chart
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 82/100 | Updated: 2026-05-07
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot import element_rect, element_text, ggsave, theme


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Generate realistic wind data (1 year of hourly measurements)
np.random.seed(42)
n_obs = 8760  # hours in a year

# Simulate prevailing westerly winds with secondary NE component
direction_weights = np.array([0.05, 0.08, 0.06, 0.04, 0.08, 0.12, 0.25, 0.32])
direction_centers = np.array([0, 45, 90, 135, 180, 225, 270, 315])

# Sample directions based on weights
chosen_sectors = np.random.choice(8, size=n_obs, p=direction_weights / direction_weights.sum())
# Add noise within each 45° sector
directions = direction_centers[chosen_sectors] + np.random.uniform(-22.5, 22.5, n_obs)
directions = directions % 360

# Wind speeds - Weibull-like distribution, varying by direction
base_speed = np.random.weibull(2.2, n_obs) * 6
direction_speed_factor = 1 + 0.3 * np.sin(np.radians(directions - 250))
speeds = base_speed * direction_speed_factor
speeds = np.clip(speeds, 0, 25)

# Bin directions into 16 sectors
n_sectors = 16
sector_size = 360 / n_sectors
direction_bins = ((directions + sector_size / 2) % 360) // sector_size
direction_labels = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]

# Bin speeds into categories
speed_bins = pd.cut(
    speeds, bins=[0, 3, 6, 9, 12, 15, 25], labels=["0-3 m/s", "3-6 m/s", "6-9 m/s", "9-12 m/s", "12-15 m/s", "15+ m/s"]
)

# Create DataFrame for aggregation
df = pd.DataFrame({"direction_bin": direction_bins.astype(int), "speed_bin": speed_bins})

# Aggregate counts per direction/speed combination
counts = df.groupby(["direction_bin", "speed_bin"], observed=True).size().reset_index(name="count")
total_obs = counts["count"].sum()
counts["frequency"] = counts["count"] / total_obs * 100

# Direction as discrete variable for x-axis
counts["direction"] = counts["direction_bin"]

# Speed category order for proper stacking
speed_order = ["0-3 m/s", "3-6 m/s", "6-9 m/s", "9-12 m/s", "12-15 m/s", "15+ m/s"]
counts["speed_bin"] = pd.Categorical(counts["speed_bin"], categories=speed_order, ordered=True)
counts = counts.sort_values(["direction_bin", "speed_bin"])

# Okabe-Ito palette (cool to warm gradient)
colors = ["#009E73", "#2ABCCD", "#4467A3", "#954477", "#AE3030", "#C475FD"]

# Create wind rose using polar bar chart
plot = (
    ggplot(counts, aes(x="direction", y="frequency", fill="speed_bin"))
    + geom_bar(stat="identity", width=0.9, position="stack")
    + coord_polar(start=0, direction=1)
    + scale_x_continuous(
        breaks=list(range(0, 16, 2)),
        labels=["N", "NE", "E", "SE", "S", "SW", "W", "NW"],
        limits=[-0.5, 15.5],
        expand=[0, 0],
    )
    + scale_y_continuous(expand=[0, 0])
    + scale_fill_manual(values=colors, name="Wind Speed")
    + labs(title="windrose-basic · letsplot · anyplot.ai", x="", y="Frequency (%)")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        plot_title=element_text(size=24, color=INK, hjust=0.5),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_title_y=element_text(size=20, color=INK),
        legend_title=element_text(size=20, color=INK),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_position="right",
    )
    + ggsize(1600, 1600)
)

# Save as PNG and HTML (scale=3 to get 4800×4800 px)
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)
ggsave(plot, f"plot-{THEME}.html", path=".")
