""" pyplots.ai
bump-basic: Basic Bump Chart
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 90/100 | Updated: 2026-02-22
"""

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np


# Data - Formula 1 driver standings over an 8-race season
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

# Colorblind-safe palette — distinct hues, no similar oranges
colors = {
    "Verstappen": "#306998",
    "Hamilton": "#9467bd",
    "Norris": "#17becf",
    "Leclerc": "#d62728",
    "Sainz": "#e8963e",
    "Piastri": "#8c564b",
    "Russell": "#7f7f7f",
}

# Top-3 finishers get visual emphasis for storytelling hierarchy
top_drivers = {"Verstappen", "Hamilton", "Norris"}

# Plot
fig, ax = plt.subplots(figsize=(16, 9))
x = np.arange(len(races))

for driver, ranks in rankings.items():
    is_top = driver in top_drivers
    lw = 4.0 if is_top else 2.5
    ms = 16 if is_top else 10
    zo = 4 if is_top else 3
    alpha = 1.0 if is_top else 0.55

    ax.plot(
        x,
        ranks,
        marker="o",
        markersize=ms,
        linewidth=lw,
        color=colors[driver],
        zorder=zo,
        alpha=alpha,
        path_effects=[pe.Stroke(linewidth=lw + 2, foreground="white"), pe.Normal()],
    )
    # End-of-line labels (replaces legend, more direct)
    ax.text(
        x[-1] + 0.15,
        ranks[-1],
        driver,
        fontsize=16,
        fontweight="bold",
        color=colors[driver],
        va="center",
        alpha=1.0 if is_top else 0.8,
        path_effects=[pe.withStroke(linewidth=3, foreground="white")],
    )

# Annotate key lead changes for data storytelling
ax.annotate(
    "Hamilton\ntakes the lead",
    xy=(3, 1),
    xytext=(1.5, -0.6),
    fontsize=12,
    fontweight="bold",
    color=colors["Hamilton"],
    ha="center",
    va="bottom",
    path_effects=[pe.withStroke(linewidth=2, foreground="white")],
    arrowprops={"arrowstyle": "->", "color": colors["Hamilton"], "lw": 1.5, "connectionstyle": "arc3,rad=-0.15"},
)

ax.annotate(
    "Norris\npeaks at P1",
    xy=(5, 1),
    xytext=(5.8, -0.6),
    fontsize=12,
    fontweight="bold",
    color=colors["Norris"],
    ha="center",
    va="bottom",
    path_effects=[pe.withStroke(linewidth=2, foreground="white")],
    arrowprops={"arrowstyle": "->", "color": colors["Norris"], "lw": 1.5, "connectionstyle": "arc3,rad=0.15"},
)

# Invert Y-axis so rank 1 is at top
ax.set_ylim(-1.2, len(drivers) + 0.5)
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
