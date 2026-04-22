""" pyplots.ai
windrose-basic: Wind Rose Chart
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot import ggsave


LetsPlot.setup_html()

# Generate realistic wind data (1 year of hourly measurements)
np.random.seed(42)
n_obs = 8760  # hours in a year

# Simulate prevailing westerly winds with secondary NE component
direction_weights = np.array([0.05, 0.08, 0.06, 0.04, 0.08, 0.12, 0.25, 0.32])  # N, NE, E, SE, S, SW, W, NW
direction_centers = np.array([0, 45, 90, 135, 180, 225, 270, 315])

# Sample directions based on weights
chosen_sectors = np.random.choice(8, size=n_obs, p=direction_weights / direction_weights.sum())
# Add noise within each 45° sector
directions = direction_centers[chosen_sectors] + np.random.uniform(-22.5, 22.5, n_obs)
directions = directions % 360

# Wind speeds - Weibull-like distribution, varying by direction (stronger from W/SW)
base_speed = np.random.weibull(2.2, n_obs) * 6
direction_speed_factor = 1 + 0.3 * np.sin(np.radians(directions - 250))  # Stronger from SW-W
speeds = base_speed * direction_speed_factor
speeds = np.clip(speeds, 0, 25)

# Bin directions into 16 sectors
n_sectors = 16
sector_size = 360 / n_sectors
# Bin so that 0-11.25 is N, 11.25-33.75 is NNE, etc.
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

# Direction as discrete variable for x-axis (sectors 0-15)
counts["direction"] = counts["direction_bin"]

# Speed category order for proper stacking
speed_order = ["0-3 m/s", "3-6 m/s", "6-9 m/s", "9-12 m/s", "12-15 m/s", "15+ m/s"]
counts["speed_bin"] = pd.Categorical(counts["speed_bin"], categories=speed_order, ordered=True)
counts = counts.sort_values(["direction_bin", "speed_bin"])

# Colors from cool (calm) to warm (strong winds) - colorblind safe
colors = ["#306998", "#4A90D9", "#7BC8F6", "#FFD43B", "#F59E0B", "#DC2626"]

# Create wind rose using polar bar chart
# coord_polar: start=0 means 12 o'clock (North), direction=1 is clockwise
plot = (
    ggplot(counts, aes(x="direction", y="frequency", fill="speed_bin"))
    + geom_bar(stat="identity", width=0.9, position="stack", alpha=0.9)
    + coord_polar(start=0, direction=1)
    + scale_x_continuous(
        breaks=list(range(0, 16, 2)),  # Every other sector: N, NE, E, SE, S, SW, W, NW
        labels=["N", "NE", "E", "SE", "S", "SW", "W", "NW"],
        limits=[-0.5, 15.5],  # Full circle
        expand=[0, 0],
    )
    + scale_y_continuous(expand=[0, 0])
    + scale_fill_manual(values=colors, name="Wind Speed")
    + labs(title="windrose-basic · letsplot · pyplots.ai", x="", y="Frequency (%)")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, hjust=0.5),
        axis_text=element_text(size=16),
        axis_title_y=element_text(size=18),
        legend_title=element_text(size=18),
        legend_text=element_text(size=14),
        legend_position="right",
    )
    + ggsize(1200, 1200)  # Square format for polar plot, scaled 3x = 3600x3600
)

# Save as PNG and HTML
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
