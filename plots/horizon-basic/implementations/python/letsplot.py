""" anyplot.ai
horizon-basic: Horizon Chart
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-07
"""

import os
import shutil

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first series ALWAYS #009E73)
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9"]

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
# Each band clips values to its range and overlays them
horizon_records = []

# Band labels for legend
band_labels = {"pos0": "+Low", "pos1": "+Medium", "pos2": "+High", "neg0": "-Low", "neg1": "-Medium", "neg2": "-High"}

for idx, series in enumerate(series_names):
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
                    {
                        "hour": h,
                        "value": pv,
                        "series": series,
                        "band": f"pos{band}",
                        "sign": "positive",
                        "series_idx": idx,
                    }
                )
            if nv > 0.01:
                horizon_records.append(
                    {
                        "hour": h,
                        "value": nv,
                        "series": series,
                        "band": f"neg{band}",
                        "sign": "negative",
                        "series_idx": idx,
                    }
                )

horizon_df = pd.DataFrame(horizon_records)

# Color mapping: Okabe-Ito positions with intensity variation for bands
# Positive bands: use Okabe-Ito color, varying brightness
# Negative bands: use dimmer version of the color
colors = {}
for band_idx in range(n_bands):
    color = OKABE_ITO[0]  # Use first series color for all bands
    # Positive: increase intensity across bands
    if band_idx == 0:
        colors[f"pos{band_idx}"] = "#B3E5B0"  # Light
    elif band_idx == 1:
        colors[f"pos{band_idx}"] = "#6BBE77"  # Medium
    else:
        colors[f"pos{band_idx}"] = "#009E73"  # Full intensity

    # Negative: reddish palette for negative deviations
    neg_color = OKABE_ITO[1]  # Use second series color for negatives
    if band_idx == 0:
        colors[f"neg{band_idx}"] = "#F5C4A0"  # Light
    elif band_idx == 1:
        colors[f"neg{band_idx}"] = "#E89354"  # Medium
    else:
        colors[f"neg{band_idx}"] = "#D55E00"  # Full intensity

# Create the horizon chart
plot = (
    ggplot(horizon_df, aes(x="hour", y="value", fill="band"))
    + geom_area(position="identity", alpha=0.85, color=PAGE_BG, size=0.1)
    + scale_fill_manual(values=colors, labels=band_labels)
    + facet_wrap("series", ncol=2)
    + scale_x_continuous(breaks=[0, 24, 48, 72, 96, 120, 144], labels=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
    + labs(
        title="horizon-basic · letsplot · anyplot.ai",
        x="Day of Week",
        y="Folded Value (stacked bands)",
        fill="Band Intensity",
    )
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK_SOFT, size=0.2),
        panel_grid_minor=element_blank(),
        plot_title=element_text(size=24, face="bold", color=INK),
        axis_title=element_text(size=20, color=INK),
        axis_text_x=element_text(size=16, color=INK_SOFT),
        axis_text_y=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.3),
        strip_text=element_text(size=18, face="bold", color=INK),
        legend_position="right",
        legend_background=element_rect(fill=PAGE_BG, color=INK_SOFT),
        legend_title=element_text(size=16, face="bold", color=INK),
        legend_text=element_text(size=16, color=INK_SOFT),
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800x2700)
ggsave(plot, f"plot-{THEME}.png", scale=3)

# Save as HTML for interactive version
ggsave(plot, f"plot-{THEME}.html")

# Move files from lets-plot-images subdirectory to current directory
if os.path.exists("lets-plot-images"):
    for filename in [f"plot-{THEME}.png", f"plot-{THEME}.html"]:
        src = os.path.join("lets-plot-images", filename)
        if os.path.exists(src):
            shutil.move(src, filename)
    if not os.listdir("lets-plot-images"):
        shutil.rmtree("lets-plot-images")
