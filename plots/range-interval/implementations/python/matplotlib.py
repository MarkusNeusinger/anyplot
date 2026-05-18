"""anyplot.ai
range-interval: Range Interval Chart
Library: matplotlib | Python 3.13
Quality: 92 | Updated: 2026-05-18
"""

import os

import matplotlib.pyplot as plt
import numpy as np


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
RULE = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
BRAND = "#009E73"

# Data: Monthly temperature ranges (high/low) for a coastal city
np.random.seed(42)

months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Simulate realistic temperature ranges (Celsius) - warmer in summer
base_temps = np.array([5, 7, 11, 15, 19, 23, 26, 25, 21, 16, 10, 6])
variation = np.random.uniform(3, 7, size=12)

min_temps = base_temps - variation / 2 + np.random.uniform(-2, 2, size=12)
max_temps = base_temps + variation / 2 + np.random.uniform(2, 5, size=12)

# Ensure max > min
min_temps = np.round(min_temps, 1)
max_temps = np.round(max_temps, 1)

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Create range bars using bar plot with bottom parameter
x_positions = np.arange(len(months))
range_heights = max_temps - min_temps

# Draw range bars
ax.bar(x_positions, range_heights, bottom=min_temps, width=0.6, color=BRAND, alpha=0.7, edgecolor=INK_SOFT, linewidth=2)

# Add min/max markers for emphasis - with distinct marker styles
ax.scatter(
    x_positions,
    min_temps,
    s=150,
    color=BRAND,
    zorder=5,
    marker="v",
    linewidths=2,
    edgecolors=INK_SOFT,
    label="Min Temperature",
)
ax.scatter(
    x_positions,
    max_temps,
    s=150,
    color=BRAND,
    zorder=5,
    marker="^",
    linewidths=2,
    edgecolors=INK_SOFT,
    label="Max Temperature",
)

# Add midpoint markers
midpoints = (min_temps + max_temps) / 2
ax.scatter(
    x_positions,
    midpoints,
    s=100,
    color=INK_MUTED,
    zorder=6,
    marker="o",
    edgecolor=INK_SOFT,
    linewidth=1.5,
    label="Midpoint",
)

# Add value annotations at top and bottom of each bar
for i, (low, high) in enumerate(zip(min_temps, max_temps, strict=True)):
    ax.annotate(
        f"{low:.0f}°",
        (x_positions[i], low),
        textcoords="offset points",
        xytext=(0, -20),
        ha="center",
        fontsize=12,
        color=INK_SOFT,
    )
    ax.annotate(
        f"{high:.0f}°",
        (x_positions[i], high),
        textcoords="offset points",
        xytext=(0, 10),
        ha="center",
        fontsize=12,
        color=INK_SOFT,
    )

# Styling
ax.set_xlabel("Month", fontsize=20, color=INK)
ax.set_ylabel("Temperature (°C)", fontsize=20, color=INK)
ax.set_title("range-interval · python · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)

ax.set_xticks(x_positions)
ax.set_xticklabels(months, color=INK_SOFT)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Remove top and right spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)

# Add horizontal grid for easier reading
ax.grid(True, axis="y", alpha=0.10, linewidth=0.8, color=INK)
ax.set_axisbelow(True)

# Legend with styled frame
legend = ax.legend(fontsize=14, loc="upper right", framealpha=0.9)
if legend:
    legend.get_frame().set_facecolor(ELEVATED_BG)
    legend.get_frame().set_edgecolor(INK_SOFT)
    legend.get_frame().set_linewidth(1.5)
    for text in legend.get_texts():
        text.set_color(INK_SOFT)

# Set y-axis range with padding
y_min = min_temps.min() - 5
y_max = max_temps.max() + 5
ax.set_ylim(y_min, y_max)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
