""" pyplots.ai
line-parametric: Parametric Curve Plot
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 92/100 | Created: 2026-03-20
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection


# Data
t_lissajous = np.linspace(0, 2 * np.pi, 1000)
x_lissajous = np.sin(3 * t_lissajous)
y_lissajous = np.sin(2 * t_lissajous)

t_spiral = np.linspace(0, 4 * np.pi, 1000)
x_spiral = t_spiral * np.cos(t_spiral)
y_spiral = t_spiral * np.sin(t_spiral)

# Plot
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 9), facecolor="#fafafa")

for ax in [ax1, ax2]:
    ax.set_facecolor("#fafafa")

# Lissajous figure with color gradient
points_l = np.array([x_lissajous, y_lissajous]).T.reshape(-1, 1, 2)
segments_l = np.concatenate([points_l[:-1], points_l[1:]], axis=1)
lc1 = LineCollection(segments_l, cmap="plasma", linewidth=2.8, capstyle="round")
lc1.set_array(t_lissajous[:-1])
ax1.add_collection(lc1)
ax1.set_xlim(x_lissajous.min() - 0.15, x_lissajous.max() + 0.15)
ax1.set_ylim(y_lissajous.min() - 0.15, y_lissajous.max() + 0.15)
ax1.plot(
    x_lissajous[0],
    y_lissajous[0],
    "o",
    color="#2d6a9f",
    markersize=11,
    zorder=5,
    label="Start (t = 0)",
    markeredgecolor="white",
    markeredgewidth=1.5,
)
ax1.plot(
    x_lissajous[-1],
    y_lissajous[-1],
    "s",
    color="#d45113",
    markersize=11,
    zorder=5,
    label="End (t = 2π)",
    markeredgecolor="white",
    markeredgewidth=1.5,
)
cb1 = fig.colorbar(lc1, ax=ax1, pad=0.03, aspect=30, shrink=0.85)
cb1.set_label("Parameter t (rad)", fontsize=16, labelpad=8)
cb1.ax.tick_params(labelsize=14)
cb1.outline.set_visible(False)

# Annotate self-intersection at origin for storytelling
ax1.annotate(
    "Self-intersection\nat origin (3:2 ratio)",
    xy=(0, 0),
    xytext=(0.45, -0.7),
    fontsize=14,
    color="#444444",
    fontstyle="italic",
    arrowprops={"arrowstyle": "->", "color": "#888888", "lw": 1.2},
    ha="center",
)

# Spiral with color gradient
points_s = np.array([x_spiral, y_spiral]).T.reshape(-1, 1, 2)
segments_s = np.concatenate([points_s[:-1], points_s[1:]], axis=1)
lc2 = LineCollection(segments_s, cmap="viridis", linewidth=2.8, capstyle="round")
lc2.set_array(t_spiral[:-1])
ax2.add_collection(lc2)
margin = t_spiral.max() * 0.1
ax2.set_xlim(x_spiral.min() - margin, x_spiral.max() + margin)
ax2.set_ylim(y_spiral.min() - margin, y_spiral.max() + margin)
ax2.plot(
    x_spiral[0],
    y_spiral[0],
    "o",
    color="#2d6a9f",
    markersize=11,
    zorder=5,
    label="Start (t = 0)",
    markeredgecolor="white",
    markeredgewidth=1.5,
)
ax2.plot(
    x_spiral[-1],
    y_spiral[-1],
    "s",
    color="#d45113",
    markersize=11,
    zorder=5,
    label="End (t = 4π)",
    markeredgecolor="white",
    markeredgewidth=1.5,
)
cb2 = fig.colorbar(lc2, ax=ax2, pad=0.03, aspect=30, shrink=0.85)
cb2.set_label("Parameter t (rad)", fontsize=16, labelpad=8)
cb2.ax.tick_params(labelsize=14)
cb2.outline.set_visible(False)

# Annotate outer spiral loop for storytelling
ax2.annotate(
    "Radius grows\nlinearly with t",
    xy=(x_spiral[750], y_spiral[750]),
    xytext=(6, 8),
    fontsize=14,
    color="#444444",
    fontstyle="italic",
    arrowprops={"arrowstyle": "->", "color": "#888888", "lw": 1.2},
    ha="center",
)

# Style — per-panel descriptive labels, all spines removed, refined legend
panel_info = [
    (ax1, "Lissajous Figure", "x(t) = sin(3t)", "y(t) = sin(2t)"),
    (ax2, "Archimedean Spiral", "x(t) = t · cos(t)", "y(t) = t · sin(t)"),
]
for ax, title_text, xlabel, ylabel in panel_info:
    ax.set_aspect("equal")
    ax.set_xlabel(xlabel, fontsize=20, labelpad=8)
    ax.set_ylabel(ylabel, fontsize=20, labelpad=8)
    ax.set_title(title_text, fontsize=24, fontweight="semibold", pad=14, color="#222222")
    ax.tick_params(axis="both", labelsize=16, colors="#555555")
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.legend(fontsize=16, loc="lower right", frameon=True, fancybox=True, framealpha=0.85, edgecolor="#cccccc")
    ax.grid(True, alpha=0.12, linewidth=0.6, color="#999999")

fig.suptitle("line-parametric · matplotlib · pyplots.ai", fontsize=26, fontweight="medium", y=0.98, color="#333333")

plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
