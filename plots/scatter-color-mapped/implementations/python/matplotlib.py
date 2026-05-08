"""anyplot.ai
scatter-color-mapped: Color-Mapped Scatter Plot
Library: matplotlib | Python 3.13
Quality: pending | Created: 2026-05-08
"""

import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import Normalize


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data: Weather station measurements with clustered wind speed patterns
np.random.seed(42)
n_points = 180

# Geographic coordinates with bias toward regions
latitude = np.concatenate(
    [
        np.random.normal(40, 3, 50),  # Northern cluster
        np.random.normal(25, 4, 50),  # Southern cluster
        np.random.normal(35, 2, 50),  # Central cluster
        np.random.normal(45, 5, 30),  # Northwest sparse
    ]
)

longitude = np.concatenate(
    [
        np.random.normal(-95, 4, 50),  # Central region
        np.random.normal(-75, 3, 50),  # Eastern region
        np.random.normal(-110, 5, 50),  # Western region
        np.random.normal(-85, 6, 30),  # Mixed
    ]
)

# Wind speed influenced by location with natural variability
wind_speed = np.concatenate(
    [
        np.random.uniform(12, 22, 50),  # Northern: moderate to strong winds
        np.random.uniform(8, 16, 50),  # Southern: lighter winds
        np.random.uniform(5, 14, 50),  # Central: variable winds
        np.random.uniform(10, 25, 30),  # Northwest: mixed conditions
    ]
)

# Create plot (4800x2700 px at 300 dpi = 16x9 inches)
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Normalize color range
norm = Normalize(vmin=wind_speed.min(), vmax=wind_speed.max())

# Scatter plot with viridis colormap
scatter = ax.scatter(
    latitude, longitude, c=wind_speed, cmap="viridis", s=200, alpha=0.75, edgecolors=PAGE_BG, linewidth=1, norm=norm
)

# Colorbar with label
cbar = plt.colorbar(scatter, ax=ax, pad=0.02)
cbar.set_label("Wind Speed (m/s)", fontsize=20, color=INK)
cbar.ax.tick_params(labelsize=20, colors=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

# Labels and styling
ax.set_xlabel("Latitude (°N)", fontsize=20, color=INK)
ax.set_ylabel("Longitude (°W)", fontsize=20, color=INK)
ax.set_title("scatter-color-mapped · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Subtle grid (y-axis preferred for scatter)
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8, color=INK)

# Spine styling
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)
    ax.spines[spine].set_linewidth(1)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
