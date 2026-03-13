""" pyplots.ai
scatter-connected-temporal: Connected Scatter Plot with Temporal Path
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 77/100 | Created: 2026-03-13
"""

import matplotlib.collections as mcoll
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap


# Data - Unemployment vs inflation (Phillips curve dynamics, 1990-2023)
np.random.seed(42)
years = np.arange(1990, 2024)
n = len(years)

unemployment = np.array(
    [
        5.6,
        6.8,
        7.5,
        6.9,
        6.1,
        5.6,
        5.4,
        4.9,
        4.5,
        4.2,
        4.0,
        4.7,
        5.8,
        6.0,
        5.5,
        5.1,
        4.6,
        4.6,
        5.8,
        9.3,
        9.6,
        8.9,
        8.1,
        7.4,
        6.2,
        5.3,
        4.9,
        4.4,
        3.9,
        3.7,
        8.1,
        5.4,
        3.6,
        3.6,
    ]
)

inflation = np.array(
    [
        5.4,
        4.2,
        3.0,
        3.0,
        2.6,
        2.8,
        2.9,
        2.3,
        1.6,
        2.2,
        3.4,
        2.8,
        1.6,
        2.3,
        2.7,
        3.4,
        3.2,
        2.8,
        3.8,
        -0.4,
        1.6,
        3.2,
        2.1,
        1.5,
        1.6,
        0.1,
        1.3,
        2.1,
        2.4,
        1.8,
        1.2,
        4.7,
        8.0,
        4.1,
    ]
)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

cmap = LinearSegmentedColormap.from_list("temporal", ["#a8c4e0", "#306998", "#1a3a5c"])
colors = cmap(np.linspace(0, 1, n))

segments = []
for i in range(n - 1):
    segments.append([(unemployment[i], inflation[i]), (unemployment[i + 1], inflation[i + 1])])

lc = mcoll.LineCollection(segments, colors=colors[:-1], linewidths=2.5, zorder=2)
ax.add_collection(lc)

ax.scatter(
    unemployment, inflation, c=np.linspace(0, 1, n), cmap=cmap, s=150, edgecolors="white", linewidth=1.2, zorder=3
)

# Annotate key time points
annotations = {0: (-15, 15), 10: (15, 12), 19: (15, -18), 22: (-30, -18), 29: (15, 12), n - 1: (15, -15)}

for idx, offset in annotations.items():
    ax.annotate(
        str(years[idx]),
        (unemployment[idx], inflation[idx]),
        textcoords="offset points",
        xytext=offset,
        fontsize=14,
        fontweight="bold",
        color=colors[idx],
        arrowprops={"arrowstyle": "-", "color": colors[idx], "lw": 1.0},
    )

# Style
ax.set_xlabel("Unemployment Rate (%)", fontsize=20)
ax.set_ylabel("Inflation Rate (%)", fontsize=20)
ax.set_title("scatter-connected-temporal \u00b7 seaborn \u00b7 pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8)
ax.xaxis.grid(True, alpha=0.2, linewidth=0.8)

ax.set_xlim(unemployment.min() - 0.6, unemployment.max() + 0.6)
ax.set_ylim(inflation.min() - 0.8, inflation.max() + 0.8)

sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(years[0], years[-1]))
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax, pad=0.02, aspect=30)
cbar.set_label("Year", fontsize=16)
cbar.ax.tick_params(labelsize=14)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
