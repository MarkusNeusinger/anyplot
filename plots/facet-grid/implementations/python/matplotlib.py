""" pyplots.ai
facet-grid: Faceted Grid Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Data
np.random.seed(42)

# Create sample data with two categorical variables for faceting
regions = ["North", "South", "East"]
seasons = ["Spring", "Summer", "Fall", "Winter"]

data = []
for region in regions:
    for season in seasons:
        n_points = 25
        # Generate temperature vs energy consumption relationship
        # Different patterns per region/season combination
        base_temp = {"North": 10, "South": 25, "East": 18}[region]
        season_offset = {"Spring": 5, "Summer": 15, "Fall": 0, "Winter": -10}[season]

        temp = np.random.normal(base_temp + season_offset, 5, n_points)
        # Energy consumption varies with temperature
        energy = 100 + (temp - 15) ** 2 * 0.3 + np.random.normal(0, 10, n_points)

        for t, e in zip(temp, energy, strict=True):
            data.append({"Temperature": t, "Energy": e, "Region": region, "Season": season})

df = pd.DataFrame(data)

# Plot - Faceted grid: rows = regions, columns = seasons
fig, axes = plt.subplots(nrows=len(regions), ncols=len(seasons), figsize=(16, 9), sharex=True, sharey=True)

# Colors for regions
colors = {"North": "#306998", "South": "#FFD43B", "East": "#4DAF4A"}

# Create scatter plots in each facet
for i, region in enumerate(regions):
    for j, season in enumerate(seasons):
        ax = axes[i, j]
        subset = df[(df["Region"] == region) & (df["Season"] == season)]

        ax.scatter(
            subset["Temperature"],
            subset["Energy"],
            s=120,
            alpha=0.7,
            color=colors[region],
            edgecolor="white",
            linewidth=0.5,
        )

        # Add grid
        ax.grid(True, alpha=0.3, linestyle="--")

        # Column headers (top row only)
        if i == 0:
            ax.set_title(season, fontsize=18, fontweight="bold")

        # Row labels (rightmost column only)
        if j == len(seasons) - 1:
            ax.annotate(
                region, xy=(1.05, 0.5), xycoords="axes fraction", fontsize=16, fontweight="bold", va="center", ha="left"
            )

        # Tick parameters
        ax.tick_params(axis="both", labelsize=12)

# Shared axis labels
fig.supxlabel("Temperature (°C)", fontsize=20, y=0.02)
fig.supylabel("Energy Consumption (kWh)", fontsize=20, x=0.02)

# Main title
fig.suptitle("facet-grid · matplotlib · pyplots.ai", fontsize=24, y=0.98)

plt.tight_layout(rect=[0.04, 0.04, 0.95, 0.95])
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
