""" anyplot.ai
windrose-basic: Wind Rose Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-07
"""

import os
import sys


sys.path = [p for p in sys.path if p not in ("", ".", os.path.dirname(os.path.abspath(__file__)))]

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette for wind speed bins (starting with brand green)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD"]

# Data - Simulated annual wind measurements (8760 hourly readings)
np.random.seed(42)

n_observations = 8760  # One year of hourly data

# Generate realistic wind direction data with prevailing westerly winds
# Using mixture of normal distributions wrapped to [0, 360)
directions_main = np.random.normal(240, 30, int(n_observations * 0.5))  # SW prevailing
directions_secondary = np.random.normal(315, 25, int(n_observations * 0.3))  # NW secondary
directions_random = np.random.uniform(0, 360, int(n_observations * 0.2))  # Random

directions = np.concatenate([directions_main, directions_secondary, directions_random])
directions = directions % 360  # Wrap to [0, 360)

# Wind speeds using Weibull distribution (common for wind data)
speeds = np.random.weibull(2.2, len(directions)) * 6  # Scale for realistic m/s values
speeds = np.clip(speeds, 0, 25)

# Define bins - 16 direction sectors (22.5 degrees each)
n_dir_bins = 16
dir_bin_width = 360 / n_dir_bins
direction_centers = np.radians(np.arange(0, 360, dir_bin_width))

# Speed bins in m/s
speed_bins = [0, 3, 6, 9, 12, 15, 25]
speed_labels = ["0-3", "3-6", "6-9", "9-12", "12-15", "15+"]

# Calculate frequencies for each direction/speed combination
freq_matrix = np.zeros((n_dir_bins, len(speed_bins) - 1))

for i in range(n_dir_bins):
    # Calculate bin edges, centered on the direction
    bin_center = i * dir_bin_width
    bin_low = (bin_center - dir_bin_width / 2) % 360
    bin_high = (bin_center + dir_bin_width / 2) % 360

    # Handle wrap-around at 0/360 degrees
    if bin_low > bin_high:
        dir_mask = (directions >= bin_low) | (directions < bin_high)
    else:
        dir_mask = (directions >= bin_low) & (directions < bin_high)

    dir_speeds = speeds[dir_mask]

    for j in range(len(speed_bins) - 1):
        speed_mask = (dir_speeds >= speed_bins[j]) & (dir_speeds < speed_bins[j + 1])
        freq_matrix[i, j] = np.sum(speed_mask)

# Convert to percentage
freq_matrix = freq_matrix / len(directions) * 100

# Plot - square format for radial symmetry
fig, ax = plt.subplots(figsize=(12, 12), subplot_kw={"projection": "polar"}, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Bar width slightly less than bin width for visual clarity
bar_width = np.radians(20)

# Stack the bars for each speed category
bottoms = np.zeros(n_dir_bins)

for j in range(len(speed_bins) - 1):
    ax.bar(
        direction_centers,
        freq_matrix[:, j],
        width=bar_width,
        bottom=bottoms,
        color=IMPRINT[j],
        edgecolor=PAGE_BG,
        linewidth=0.5,
        label=f"{speed_labels[j]} m/s",
    )
    bottoms += freq_matrix[:, j]

# Configure polar plot - North at top, clockwise direction (meteorological convention)
ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)

# Direction labels for 16 sectors
direction_labels = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
ax.set_xticks(np.radians(np.arange(0, 360, 22.5)))
ax.set_xticklabels(direction_labels, fontsize=16, fontweight="bold", color=INK)

# Radial axis - frequency percentage
max_freq = np.ceil(bottoms.max() * 1.1)
ax.set_ylim(0, max_freq)
yticks = np.arange(0, max_freq + 1, 2)
ax.set_yticks(yticks)
ax.set_yticklabels([f"{int(y)}%" for y in yticks], fontsize=14, color=INK_SOFT)

# Grid styling - subtle, solid lines
ax.grid(True, alpha=0.15, linestyle="-", color=INK_SOFT, linewidth=0.8)

# Spine styling
ax.spines["polar"].set_color(INK_SOFT)
ax.spines["polar"].set_linewidth(0.5)

# Title
ax.set_title("windrose-basic · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK, pad=20)

# Legend - positioned in upper right area
leg = ax.legend(
    title="Wind Speed",
    title_fontsize=16,
    fontsize=14,
    loc="upper right",
    bbox_to_anchor=(1.15, 1.1),
    framealpha=0.95,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
)
if leg:
    plt.setp(leg.get_title(), color=INK)
    plt.setp(leg.get_texts(), color=INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
