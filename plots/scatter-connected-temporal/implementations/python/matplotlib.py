""" pyplots.ai
scatter-connected-temporal: Connected Scatter Plot with Temporal Path
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-13
"""

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch


# Data - Phillips curve: unemployment vs inflation over 30 years
np.random.seed(42)
years = np.arange(1994, 2024)
n = len(years)

unemployment = np.zeros(n)
inflation = np.zeros(n)
unemployment[0] = 6.5
inflation[0] = 2.8

for i in range(1, n):
    cycle = np.sin(2 * np.pi * i / 10)
    unemployment[i] = unemployment[i - 1] + cycle * 0.4 + np.random.normal(0, 0.3)
    inflation[i] = inflation[i - 1] - 0.3 * (unemployment[i] - unemployment[i - 1]) + np.random.normal(0, 0.2)

unemployment = np.clip(unemployment, 3.0, 10.0)
inflation = np.clip(inflation, 0.5, 6.0)

# Custom colormap: deep indigo -> teal -> amber for distinctive look
cmap = mcolors.LinearSegmentedColormap.from_list(
    "temporal_path", ["#1B0A3C", "#2D4A7A", "#1A9E8F", "#7EC87A", "#F5B041", "#F9E547"], N=256
)
norm = mcolors.Normalize(vmin=0, vmax=n - 1)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))
fig.set_facecolor("#FAFAFA")
ax.set_facecolor("#FAFAFA")

# Draw path segments with color gradient
for i in range(n - 1):
    ax.plot(
        unemployment[i : i + 2],
        inflation[i : i + 2],
        color=cmap(norm(i)),
        linewidth=2.5,
        solid_capstyle="round",
        zorder=2,
    )

# Add directional arrows at key intervals along the path
arrow_indices = [4, 11, 18, 25]
for idx in arrow_indices:
    arrow = FancyArrowPatch(
        (unemployment[idx], inflation[idx]),
        (unemployment[idx + 1], inflation[idx + 1]),
        arrowstyle="-|>",
        mutation_scale=16,
        color=cmap(norm(idx)),
        linewidth=2.0,
        zorder=3,
    )
    ax.add_patch(arrow)

# Scatter points with white edge highlighting
ax.scatter(
    unemployment, inflation, c=np.arange(n), cmap=cmap, norm=norm, s=200, edgecolors="white", linewidth=1.2, zorder=5
)

# Annotate key time points with adjusted offsets to avoid crowding
label_indices = [0, 9, 19, n - 1]
offsets = [(14, -16), (-16, 16), (14, 12), (-16, -16)]
for idx, (dx, dy) in zip(label_indices, offsets, strict=True):
    ax.annotate(
        str(years[idx]),
        (unemployment[idx], inflation[idx]),
        textcoords="offset points",
        xytext=(dx, dy),
        fontsize=16,
        fontweight="bold",
        color=cmap(norm(idx)),
        arrowprops={"arrowstyle": "-", "color": cmap(norm(idx)), "alpha": 0.4, "linewidth": 0.8},
    )

# Colorbar for temporal progression
sm = plt.cm.ScalarMappable(cmap=cmap, norm=mcolors.Normalize(vmin=years[0], vmax=years[-1]))
sm.set_array([])
cbar = fig.colorbar(sm, ax=ax, pad=0.02, aspect=30, shrink=0.8)
cbar.set_label("Year", fontsize=18)
cbar.ax.tick_params(labelsize=14)
cbar.outline.set_visible(False)

# Style
ax.set_xlabel("Unemployment Rate (%)", fontsize=20)
ax.set_ylabel("Inflation Rate (%)", fontsize=20)
ax.set_title("scatter-connected-temporal · matplotlib · pyplots.ai", fontsize=24, fontweight="medium", pad=16)
ax.tick_params(axis="both", labelsize=16)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_linewidth(0.6)
ax.spines["bottom"].set_linewidth(0.6)
ax.spines["left"].set_color("#888888")
ax.spines["bottom"].set_color("#888888")
ax.yaxis.grid(True, alpha=0.15, linewidth=0.6, color="#999999")
ax.xaxis.grid(True, alpha=0.15, linewidth=0.6, color="#999999")
ax.tick_params(axis="both", colors="#555555")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
