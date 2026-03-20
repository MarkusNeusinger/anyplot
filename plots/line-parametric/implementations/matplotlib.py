"""pyplots.ai
line-parametric: Parametric Curve Plot
Library: matplotlib | Python 3.13
Quality: pending | Created: 2026-03-20
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
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 9))

# Lissajous figure with color gradient
points_l = np.array([x_lissajous, y_lissajous]).T.reshape(-1, 1, 2)
segments_l = np.concatenate([points_l[:-1], points_l[1:]], axis=1)
lc1 = LineCollection(segments_l, cmap="plasma", linewidth=3)
lc1.set_array(t_lissajous[:-1])
ax1.add_collection(lc1)
ax1.set_xlim(x_lissajous.min() - 0.15, x_lissajous.max() + 0.15)
ax1.set_ylim(y_lissajous.min() - 0.15, y_lissajous.max() + 0.15)
ax1.plot(x_lissajous[0], y_lissajous[0], "o", color="#306998", markersize=12, zorder=5, label="Start (t=0)")
ax1.plot(x_lissajous[-1], y_lissajous[-1], "s", color="#e04006", markersize=12, zorder=5, label="End (t=2\u03c0)")
cb1 = fig.colorbar(lc1, ax=ax1, pad=0.02, aspect=30)
cb1.set_label("Parameter t", fontsize=16)
cb1.ax.tick_params(labelsize=13)

# Spiral with color gradient
points_s = np.array([x_spiral, y_spiral]).T.reshape(-1, 1, 2)
segments_s = np.concatenate([points_s[:-1], points_s[1:]], axis=1)
lc2 = LineCollection(segments_s, cmap="viridis", linewidth=3)
lc2.set_array(t_spiral[:-1])
ax2.add_collection(lc2)
margin = t_spiral.max() * 0.1
ax2.set_xlim(x_spiral.min() - margin, x_spiral.max() + margin)
ax2.set_ylim(y_spiral.min() - margin, y_spiral.max() + margin)
ax2.plot(x_spiral[0], y_spiral[0], "o", color="#306998", markersize=12, zorder=5, label="Start (t=0)")
ax2.plot(x_spiral[-1], y_spiral[-1], "s", color="#e04006", markersize=12, zorder=5, label="End (t=4\u03c0)")
cb2 = fig.colorbar(lc2, ax=ax2, pad=0.02, aspect=30)
cb2.set_label("Parameter t", fontsize=16)
cb2.ax.tick_params(labelsize=13)

# Style
for ax, title_text in [(ax1, "Lissajous: x=sin(3t), y=sin(2t)"), (ax2, "Spiral: x=t\u00b7cos(t), y=t\u00b7sin(t)")]:
    ax.set_aspect("equal")
    ax.set_xlabel("x(t)", fontsize=20)
    ax.set_ylabel("y(t)", fontsize=20)
    ax.set_title(title_text, fontsize=20, fontweight="medium")
    ax.tick_params(axis="both", labelsize=16)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(fontsize=14, loc="lower right")
    ax.grid(True, alpha=0.15, linewidth=0.8)

fig.suptitle("line-parametric \u00b7 matplotlib \u00b7 pyplots.ai", fontsize=24, fontweight="medium", y=0.98)

plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
