"""pyplots.ai
bump-basic: Basic Bump Chart
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: /100 | Updated: 2026-02-22
"""

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np


# Data - Formula 1 driver standings over a 10-race season
drivers = ["Verstappen", "Hamilton", "Norris", "Leclerc", "Sainz", "Piastri", "Russell"]
races = ["Bahrain", "Jeddah", "Melbourne", "Suzuka", "Shanghai", "Miami", "Imola", "Monaco"]

# Rankings per driver across races (1 = championship leader)
rankings = {
    "Verstappen": [1, 1, 1, 2, 3, 3, 2, 1],
    "Hamilton": [4, 3, 2, 1, 1, 2, 1, 2],
    "Norris": [5, 5, 4, 3, 2, 1, 3, 3],
    "Leclerc": [2, 2, 3, 4, 5, 5, 4, 4],
    "Sainz": [3, 4, 5, 5, 4, 4, 5, 5],
    "Piastri": [6, 6, 7, 7, 6, 6, 6, 7],
    "Russell": [7, 7, 6, 6, 7, 7, 7, 6],
}

# Colors - Python Blue first, then colorblind-safe palette
colors = ["#306998", "#e8963e", "#2ca02c", "#d62728", "#ff7f0e", "#8c564b", "#7f7f7f"]

# Plot
fig, ax = plt.subplots(figsize=(16, 9))
x = np.arange(len(races))

for i, (driver, ranks) in enumerate(rankings.items()):
    ax.plot(
        x,
        ranks,
        marker="o",
        markersize=14,
        linewidth=3.5,
        color=colors[i],
        zorder=3,
        path_effects=[pe.Stroke(linewidth=5.5, foreground="white"), pe.Normal()],
    )
    # End-of-line labels (replaces legend, more direct)
    ax.text(
        x[-1] + 0.15,
        ranks[-1],
        driver,
        fontsize=15,
        fontweight="bold",
        color=colors[i],
        va="center",
        path_effects=[pe.withStroke(linewidth=3, foreground="white")],
    )

# Invert Y-axis so rank 1 is at top
ax.invert_yaxis()

# Style
ax.set_xlabel("Grand Prix", fontsize=20)
ax.set_ylabel("Championship Position", fontsize=20)
ax.set_title("bump-basic \u00b7 matplotlib \u00b7 pyplots.ai", fontsize=24, fontweight="medium")

ax.set_xticks(x)
ax.set_xticklabels(races, rotation=25, ha="right")
ax.set_yticks(range(1, len(drivers) + 1))
ax.tick_params(axis="both", labelsize=16)

ax.yaxis.grid(True, alpha=0.2, linewidth=0.8)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

ax.set_xlim(-0.3, len(races) - 1 + 1.5)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
