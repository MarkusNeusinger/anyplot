""" pyplots.ai
line-parametric: Parametric Curve Plot
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 81/100 | Created: 2026-03-20
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.collections import LineCollection
from matplotlib.gridspec import GridSpec


sns.set_theme(style="whitegrid")
sns.set_context("talk", font_scale=1.1)

# Data - Lissajous figure
t_liss = np.linspace(0, 2 * np.pi, 1000)
x_liss = np.sin(3 * t_liss)
y_liss = np.sin(2 * t_liss)

# Data - Archimedean spiral
t_spiral = np.linspace(0, 4 * np.pi, 1000)
x_spiral = t_spiral * np.cos(t_spiral)
y_spiral = t_spiral * np.sin(t_spiral)

# Figure with extra right padding for spiral colorbar
fig = plt.figure(figsize=(18, 9))
gs = GridSpec(1, 2, figure=fig, wspace=0.5)
ax1 = fig.add_subplot(gs[0, 0])
ax2 = fig.add_subplot(gs[0, 1])


def make_segments(x, y):
    """Create line segments for LineCollection."""
    points = np.column_stack([x, y]).reshape(-1, 1, 2)
    return np.concatenate([points[:-1], points[1:]], axis=1)


# Lissajous curve via LineCollection for smooth rendering
segments_l = make_segments(x_liss, y_liss)
lc1 = LineCollection(segments_l, cmap="viridis", linewidths=3)
lc1.set_array(t_liss[:-1])
lc1.set_clim(0, 2 * np.pi)
ax1.add_collection(lc1)
ax1.autoscale()

# Spiral curve via LineCollection for smooth rendering
segments_s = make_segments(x_spiral, y_spiral)
lc2 = LineCollection(segments_s, cmap="plasma", linewidths=3)
lc2.set_array(t_spiral[:-1])
lc2.set_clim(0, 4 * np.pi)
ax2.add_collection(lc2)
ax2.autoscale()

# Start/end markers using seaborn for both panels
markers = pd.DataFrame(
    {
        "x": [x_liss[0], x_liss[-1], x_spiral[0], x_spiral[-1]],
        "y": [y_liss[0], y_liss[-1], y_spiral[0], y_spiral[-1]],
        "label": ["Start (t = 0)", "End (t = 2\u03c0)", "Start (t = 0)", "End (t = 4\u03c0)"],
        "panel": ["liss", "liss", "spiral", "spiral"],
        "kind": ["start", "end", "start", "end"],
    }
)

for ax, panel, mk_shapes in [(ax1, "liss", {"start": "o", "end": "s"}), (ax2, "spiral", {"start": "o", "end": "s"})]:
    subset = markers[markers["panel"] == panel]
    for _, row in subset.iterrows():
        sns.scatterplot(
            x=[row["x"]],
            y=[row["y"]],
            s=300,
            color="#306998" if row["kind"] == "start" else "#e74c3c",
            marker=mk_shapes[row["kind"]],
            zorder=5,
            label=row["label"],
            edgecolor="white",
            linewidth=1.5,
            ax=ax,
        )

# Colorbars
cb1 = fig.colorbar(lc1, ax=ax1, shrink=0.7, pad=0.03)
cb1.set_label("Parameter t (radians)", fontsize=18)
cb1.ax.tick_params(labelsize=14)
cb2 = fig.colorbar(lc2, ax=ax2, shrink=0.7, pad=0.08)
cb2.set_label("Parameter t (radians)", fontsize=18)
cb2.ax.tick_params(labelsize=14)

# Style both panels
for ax, title in [(ax1, "Lissajous: x = sin(3t), y = sin(2t)"), (ax2, "Spiral: x = t\u00b7cos(t), y = t\u00b7sin(t)")]:
    ax.set_aspect("equal")
    ax.set_title(title, fontsize=24, fontweight="medium")
    ax.set_xlabel("Horizontal position x(t)", fontsize=20)
    ax.set_ylabel("Vertical position y(t)", fontsize=20)
    ax.tick_params(axis="both", labelsize=16)
    ax.legend(fontsize=14, loc="lower right", framealpha=0.9)
    ax.grid(True, alpha=0.15, linewidth=0.5)
    sns.despine(ax=ax)

fig.suptitle("line-parametric \u00b7 seaborn \u00b7 pyplots.ai", fontsize=26, fontweight="medium", y=0.98)

# Save
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
