"""anyplot.ai
facet-grid: Faceted Grid Plot
Library: matplotlib | Python 3.13
Quality: pending | Created: 2026-05-13
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette - first series is always #009E73
OKABE_ITO = [
    "#009E73",  # brand green
    "#D55E00",  # vermillion
    "#0072B2",  # blue
    "#CC79A7",  # reddish purple
]

# Data
np.random.seed(42)

regions = ["North", "South", "East"]
seasons = ["Spring", "Summer", "Fall", "Winter"]

data = []
for region in regions:
    for season in seasons:
        n_points = 25
        # Base temperature varies by region and season
        base_temps = {"North": 5, "South": 20, "East": 15}
        season_offsets = {"Spring": 5, "Summer": 10, "Fall": 2, "Winter": -8}

        base_temp = base_temps[region] + season_offsets[season]
        temp = np.random.normal(base_temp, 4, n_points)

        # Energy consumption: U-shaped relationship with temperature
        energy = 120 + (temp - base_temp) ** 2 * 0.2 + np.random.normal(0, 8, n_points)

        for t, e in zip(temp, energy, strict=True):
            data.append({"Temperature": t, "Energy": e, "Region": region, "Season": season})

df = pd.DataFrame(data)

# Plot
fig, axes = plt.subplots(
    nrows=len(regions), ncols=len(seasons), figsize=(16, 9), sharex=True, sharey=True, facecolor=PAGE_BG
)

# Color map: regions to Okabe-Ito palette
region_colors = {region: OKABE_ITO[i] for i, region in enumerate(regions)}

# Create scatter plots in each facet
for i, region in enumerate(regions):
    for j, season in enumerate(seasons):
        ax = axes[i, j]
        ax.set_facecolor(PAGE_BG)

        subset = df[(df["Region"] == region) & (df["Season"] == season)]

        ax.scatter(
            subset["Temperature"],
            subset["Energy"],
            s=120,
            alpha=0.7,
            color=region_colors[region],
            edgecolors=PAGE_BG,
            linewidth=0.5,
        )

        # Subtle grid
        ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

        # Column headers (top row only)
        if i == 0:
            ax.set_title(season, fontsize=18, color=INK, fontweight="medium")

        # Row labels (left side)
        if j == 0:
            ax.set_ylabel(region, fontsize=18, color=INK, fontweight="medium")

        # Tick styling
        ax.tick_params(axis="both", labelsize=14, colors=INK_SOFT, labelcolor=INK_SOFT)

        # Spine styling
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        for spine in ("left", "bottom"):
            ax.spines[spine].set_color(INK_SOFT)

# Shared axis labels
fig.text(0.5, 0.02, "Temperature (°C)", ha="center", fontsize=20, color=INK)
fig.text(0.02, 0.5, "Energy Consumption (kWh)", va="center", rotation="vertical", fontsize=20, color=INK)

# Main title
fig.suptitle("facet-grid · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK, y=0.98)

plt.tight_layout(rect=[0.05, 0.05, 1, 0.96])
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
