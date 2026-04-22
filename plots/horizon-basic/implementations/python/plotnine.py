""" pyplots.ai
horizon-basic: Horizon Chart
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    facet_wrap,
    geom_area,
    ggplot,
    labs,
    scale_fill_manual,
    scale_x_continuous,
    theme,
    theme_minimal,
)


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

    for h, val in zip(hours, values, strict=True):
        data_records.append({"hour": h, "value": val, "series": name})

df = pd.DataFrame(data_records)

# Horizon chart parameters - fold values into bands
n_bands = 3
max_val = df["value"].abs().max()
band_size = max_val / n_bands

# Create horizon-folded data for visualization
horizon_records = []

# Band labels for legend (more descriptive)
band_labels = {"pos0": "+Low", "pos1": "+Medium", "pos2": "+High", "neg0": "-Low", "neg1": "-Medium", "neg2": "-High"}

# Band order for proper layering (darker bands on top)
band_order = ["pos0", "pos1", "pos2", "neg0", "neg1", "neg2"]

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

        for h, pv, nv in zip(hours_arr, pos, neg, strict=True):
            if pv > 0.01:
                horizon_records.append(
                    {"hour": h, "value": pv, "series": series, "band": f"pos{band}", "sign": "positive"}
                )
            if nv > 0.01:
                horizon_records.append(
                    {"hour": h, "value": nv, "series": series, "band": f"neg{band}", "sign": "negative"}
                )

horizon_df = pd.DataFrame(horizon_records)

# Set band as categorical with explicit order for proper layering
horizon_df["band"] = pd.Categorical(horizon_df["band"], categories=band_order, ordered=True)

# Color scheme: Python Blue for positive, Orange-Red for negative
colors = {
    "pos0": "#a6cee3",  # Light blue
    "pos1": "#4d94c7",  # Medium blue
    "pos2": "#306998",  # Python Blue (dark)
    "neg0": "#fdbe85",  # Light orange
    "neg1": "#fd8d3c",  # Medium orange
    "neg2": "#d94701",  # Dark orange
}

# Create the horizon chart
plot = (
    ggplot(horizon_df, aes(x="hour", y="value", fill="band"))
    + geom_area(position="identity", alpha=0.85, color="white", size=0.1)
    + scale_fill_manual(values=colors, labels=band_labels, breaks=band_order)
    + facet_wrap("~series", ncol=2)
    + scale_x_continuous(breaks=[0, 24, 48, 72, 96, 120, 144], labels=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
    + labs(
        title="Server CPU Usage Deviation · horizon-basic · plotnine · pyplots.ai",
        x="Day of Week",
        y="Folded Value (stacked bands)",
        fill="Band Intensity",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold"),
        axis_title=element_text(size=20),
        axis_text_x=element_text(size=14),
        axis_text_y=element_text(size=14),
        strip_text=element_text(size=18, weight="bold"),
        legend_position="right",
        legend_title=element_text(size=16, weight="bold"),
        legend_text=element_text(size=14),
        panel_grid_major=element_line(color="#e0e0e0", size=0.3),
        panel_grid_minor=element_blank(),
        panel_background=element_rect(fill="white"),
    )
)

# Save as PNG
plot.save("plot.png", dpi=300, verbose=False)
