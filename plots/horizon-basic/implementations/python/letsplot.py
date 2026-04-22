""" pyplots.ai
horizon-basic: Horizon Chart
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

import os
import shutil

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data - Server metrics over 7 days for multiple servers
np.random.seed(42)

n_points = 168  # 7 days of hourly data
n_series = 6
series_names = ["Server A", "Server B", "Server C", "Server D", "Server E", "Server F"]

# Create time series data
hours = np.arange(n_points)

# Generate realistic CPU usage deviation data with different patterns per server
data_records = []
for i, name in enumerate(series_names):
    # Base sinusoidal pattern with phase shift per server (daily cycle)
    base = 18 * np.sin(2 * np.pi * hours / 24 + i * np.pi / 3)
    # Add weekly pattern
    weekly = 10 * np.sin(2 * np.pi * hours / 168 + i * 0.5)
    # Add noise
    noise = np.random.randn(n_points) * 4
    # Add occasional spikes
    spikes = np.zeros(n_points)
    spike_indices = np.random.choice(n_points, size=6, replace=False)
    spikes[spike_indices] = np.random.choice([-1, 1], size=6) * np.random.uniform(20, 35, size=6)
    values = base + weekly + noise + spikes

    for h, val in zip(hours, values):
        data_records.append({"hour": h, "value": val, "series": name})

df = pd.DataFrame(data_records)

# Horizon chart parameters - fold values into bands
n_bands = 3
max_val = df["value"].abs().max()
band_size = max_val / n_bands

# Create horizon-folded data for visualization
# Each band clips values to its range and overlays them
horizon_records = []

# Band labels for legend (more descriptive)
band_labels = {"pos0": "+Low", "pos1": "+Medium", "pos2": "+High", "neg0": "-Low", "neg1": "-Medium", "neg2": "-High"}

for series in series_names:
    series_data = df[df["series"] == series]
    values = series_data["value"].values
    hours_arr = series_data["hour"].values

    for band in range(n_bands):
        low = band * band_size
        high = (band + 1) * band_size

        # Process positive values
        pos = np.clip(np.maximum(values, 0) - low, 0, band_size)
        # Process negative values (mirror to positive for display)
        neg = np.clip(np.maximum(-values, 0) - low, 0, band_size)

        for h, pv, nv in zip(hours_arr, pos, neg):
            if pv > 0.01:
                horizon_records.append(
                    {"hour": h, "value": pv, "series": series, "band": f"pos{band}", "sign": "positive"}
                )
            if nv > 0.01:
                horizon_records.append(
                    {"hour": h, "value": nv, "series": series, "band": f"neg{band}", "sign": "negative"}
                )

horizon_df = pd.DataFrame(horizon_records)

# Color scheme: Colorblind-safe diverging palette (purple-orange)
# Purple for positive values (above baseline), orange for negative (below baseline)
colors = {
    "pos0": "#dadaeb",  # Light purple
    "pos1": "#9e9ac8",  # Medium purple
    "pos2": "#6a51a3",  # Dark purple
    "neg0": "#fdbe85",  # Light orange
    "neg1": "#fd8d3c",  # Medium orange
    "neg2": "#d94701",  # Dark orange
}

# Create the horizon chart
plot = (
    ggplot(horizon_df, aes(x="hour", y="value", fill="band"))
    + geom_area(position="identity", alpha=0.85, color="white", size=0.1)
    + scale_fill_manual(values=colors, labels=band_labels)
    + facet_wrap("series", ncol=2)
    + scale_x_continuous(breaks=[0, 24, 48, 72, 96, 120, 144], labels=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
    + labs(
        title="Server CPU Usage Deviation · horizon-basic · letsplot · pyplots.ai",
        x="Day of Week",
        y="Folded Value (stacked bands)",
        fill="Band Intensity",
    )
    + theme_minimal()
    + theme(
        plot_title=element_text(size=28, face="bold"),
        axis_title=element_text(size=20),
        axis_text_x=element_text(size=14),
        axis_text_y=element_text(size=14),
        strip_text=element_text(size=18, face="bold"),
        legend_position="right",
        legend_title=element_text(size=16, face="bold"),
        legend_text=element_text(size=14),
        panel_grid_major=element_line(color="#e0e0e0", size=0.3),
        panel_grid_minor=element_blank(),
        panel_background=element_rect(fill="white"),
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800x2700)
ggsave(plot, "plot.png", scale=3)

# Save as HTML for interactive version
ggsave(plot, "plot.html")

# Move files from lets-plot-images subdirectory to current directory
if os.path.exists("lets-plot-images"):
    for filename in ["plot.png", "plot.html"]:
        src = os.path.join("lets-plot-images", filename)
        if os.path.exists(src):
            shutil.move(src, filename)
    shutil.rmtree("lets-plot-images")
