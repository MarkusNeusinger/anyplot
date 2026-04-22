""" pyplots.ai
line-navigator: Line Chart with Mini Navigator
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-20
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Data - Daily sensor readings over 3 years (1095 data points)
np.random.seed(42)
dates = pd.date_range("2022-01-01", periods=1095, freq="D")

# Generate realistic sensor data with trend, seasonality, and noise
trend = np.linspace(20, 25, 1095)
seasonal = 8 * np.sin(2 * np.pi * np.arange(1095) / 365)
noise = np.random.randn(1095) * 1.5
values = trend + seasonal + noise

# Define the "selected" range to display in the main view (about 4 months)
selected_start = 400
selected_end = 520

# Create figure with two subplots - main chart (80%) and navigator (20%)
fig, (ax_main, ax_nav) = plt.subplots(2, 1, figsize=(16, 9), height_ratios=[4, 1], sharex=False)
fig.subplots_adjust(hspace=0.15)

# Main chart - shows only the selected range in detail
ax_main.plot(dates[selected_start:selected_end], values[selected_start:selected_end], linewidth=2.5, color="#306998")
ax_main.fill_between(
    dates[selected_start:selected_end], values[selected_start:selected_end], alpha=0.15, color="#306998"
)

# Main chart styling
ax_main.set_ylabel("Temperature (°C)", fontsize=20)
ax_main.set_title("line-navigator · matplotlib · pyplots.ai", fontsize=24)
ax_main.tick_params(axis="both", labelsize=16)
ax_main.grid(True, alpha=0.3, linestyle="--")

# Format x-axis dates for main chart
ax_main.set_xlim(dates[selected_start], dates[selected_end])
y_min = values[selected_start:selected_end].min()
y_max = values[selected_start:selected_end].max()
y_padding = (y_max - y_min) * 0.1
ax_main.set_ylim(y_min - y_padding, y_max + y_padding)

# Add selected date range label
date_range_text = (
    f"Selected: {dates[selected_start].strftime('%Y-%m-%d')} to {dates[selected_end - 1].strftime('%Y-%m-%d')}"
)
ax_main.annotate(
    date_range_text,
    xy=(0.99, 0.97),
    xycoords="axes fraction",
    fontsize=14,
    ha="right",
    va="top",
    bbox={"boxstyle": "round,pad=0.4", "facecolor": "white", "edgecolor": "#306998", "alpha": 0.9},
)

# Navigator chart - shows full data extent
ax_nav.plot(dates, values, linewidth=1.5, color="#306998", alpha=0.7)
ax_nav.fill_between(dates, values, alpha=0.1, color="#306998")

# Navigator styling
ax_nav.set_xlabel("Date", fontsize=20)
ax_nav.set_ylabel("Temp", fontsize=14)
ax_nav.tick_params(axis="both", labelsize=14)
ax_nav.set_xlim(dates[0], dates[-1])

# Add selection window highlight in navigator
nav_y_min, nav_y_max = ax_nav.get_ylim()
selection_rect = mpatches.Rectangle(
    (dates[selected_start], nav_y_min),
    dates[selected_end] - dates[selected_start],
    nav_y_max - nav_y_min,
    linewidth=2.5,
    edgecolor="#FFD43B",
    facecolor="#FFD43B",
    alpha=0.3,
    zorder=5,
)
ax_nav.add_patch(selection_rect)

# Add selection handles (vertical lines at edges)
ax_nav.axvline(dates[selected_start], color="#FFD43B", linewidth=3, zorder=6)
ax_nav.axvline(dates[selected_end], color="#FFD43B", linewidth=3, zorder=6)

# Gray out non-selected regions in navigator
ax_nav.axvspan(dates[0], dates[selected_start], alpha=0.3, color="gray")
ax_nav.axvspan(dates[selected_end], dates[-1], alpha=0.3, color="gray")

# Navigator label
ax_nav.annotate(
    "Navigator",
    xy=(0.01, 0.85),
    xycoords="axes fraction",
    fontsize=12,
    ha="left",
    va="top",
    fontweight="bold",
    color="#555555",
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
