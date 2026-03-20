""" pyplots.ai
bifurcation-basic: Bifurcation Diagram for Dynamical Systems
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 94/100 | Created: 2026-03-20
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import PowerNorm


# Data
r_min, r_max = 2.5, 4.0
num_r = 2000
transient = 200
iterations = 100

r_values = np.linspace(r_min, r_max, num_r)
r_plot = np.empty(num_r * iterations)
x_plot = np.empty(num_r * iterations)

for i, r in enumerate(r_values):
    x = 0.5
    for _ in range(transient):
        x = r * x * (1 - x)
    for j in range(iterations):
        x = r * x * (1 - x)
        r_plot[i * iterations + j] = r
        x_plot[i * iterations + j] = x

# Create 2D histogram for density-based rendering of the chaotic region
# This reveals structure (periodic windows, attractor density) far better than scatter
r_bins = 800
x_bins = 600
hist, r_edges, x_edges = np.histogram2d(r_plot, x_plot, bins=[r_bins, x_bins], range=[[r_min, r_max], [0, 1]])

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Subtle regime background shading
ax.axvspan(r_min, 3.0, color="#E8F4FD", alpha=0.3, zorder=0)
ax.axvspan(3.0, 3.57, color="#F0EBF8", alpha=0.3, zorder=0)
ax.axvspan(3.57, r_max, color="#FDE8E8", alpha=0.2, zorder=0)

# Density heatmap with PowerNorm to reveal structure across the full range
# cividis is perceptually uniform and colorblind-safe
ax.pcolormesh(
    r_edges,
    x_edges,
    hist.T,
    cmap="cividis",
    norm=PowerNorm(gamma=0.35, vmin=0, vmax=hist.max()),
    rasterized=True,
    zorder=1,
)

# Regime labels at bottom with semi-transparent background for readability
label_bbox = {"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "none", "alpha": 0.7}
for rx, label in [(2.75, "Stable"), (3.28, "Periodic"), (3.78, "Chaotic")]:
    ax.text(
        rx,
        0.04,
        label,
        transform=ax.get_xaxis_transform(),
        fontsize=14,
        color="#666666",
        ha="center",
        va="bottom",
        fontstyle="italic",
        bbox=label_bbox,
        zorder=3,
    )

# Annotations for key bifurcation points — well spaced
bifurcation_points = [(3.0, "Period-2", -14, 0.97), (3.449, "Period-4", -60, 0.97), (3.544, "Period-8", -60, 0.87)]
for r_bif, label, x_offset, y_frac in bifurcation_points:
    ax.axvline(r_bif, color="#CCCCCC", linewidth=0.8, linestyle="--", alpha=0.6, zorder=2)
    ha = "right" if x_offset < 0 else "left"
    ann_bbox = {"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "none", "alpha": 0.8}
    ax.annotate(
        f"{label}  r ≈ {r_bif}",
        xy=(r_bif, y_frac),
        xycoords=("data", "axes fraction"),
        xytext=(x_offset, 0),
        textcoords="offset points",
        fontsize=14,
        color="#444444",
        ha=ha,
        va="top",
        bbox=ann_bbox,
        zorder=4,
    )

# Onset of chaos annotation
ax.annotate(
    "Onset of chaos\nr ≈ 3.57",
    xy=(3.57, 0.75),
    xytext=(3.75, 0.93),
    fontsize=14,
    color="#444444",
    ha="center",
    bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "none", "alpha": 0.8},
    arrowprops={"arrowstyle": "->", "color": "#666666", "connectionstyle": "arc3,rad=-0.2"},
    zorder=4,
)

# Style
ax.set_xlabel("Growth Rate (r)", fontsize=20)
ax.set_ylabel("Steady-State Population (x)", fontsize=20)
ax.set_title("bifurcation-basic · matplotlib · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.set_xlim(r_min, r_max)
ax.set_ylim(0, 1)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.savefig("plot.png", dpi=300, bbox_inches="tight")
