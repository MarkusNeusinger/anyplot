""" pyplots.ai
heatmap-rainflow: Rainflow Counting Matrix for Fatigue Analysis
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 94/100 | Created: 2026-03-02
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, LogNorm
from matplotlib.ticker import LogFormatterSciNotation


# Data - simulate rainflow counting results from a variable-amplitude fatigue signal
np.random.seed(42)

n_amp_bins = 20
n_mean_bins = 20
amp_edges = np.linspace(0, 200, n_amp_bins + 1)
mean_edges = np.linspace(-50, 250, n_mean_bins + 1)
amp_centers = (amp_edges[:-1] + amp_edges[1:]) / 2
mean_centers = (mean_edges[:-1] + mean_edges[1:]) / 2

mean_grid, amp_grid = np.meshgrid(mean_centers, amp_centers)

# Realistic pattern: dominant cycles at low amplitude near mean load (~100 MPa)
raw_counts = 3000 * np.exp(-amp_grid / 30) * np.exp(-((mean_grid - 100) ** 2) / (2 * 50**2))

# Secondary cluster from occasional overload events (more prominent for storytelling)
raw_counts += 800 * np.exp(-((amp_grid - 75) ** 2) / (2 * 15**2)) * np.exp(-((mean_grid - 170) ** 2) / (2 * 25**2))

# Discretize to integer counts
cycle_counts = np.round(raw_counts).astype(int)
cycle_counts = np.clip(cycle_counts, 0, None)

# Mask zero-count bins for visual distinction
masked_counts = np.ma.masked_where(cycle_counts == 0, cycle_counts)

# Smooth version for contour overlay (numpy-based gaussian kernel)
k = np.arange(-3, 4)
kernel_1d = np.exp(-0.5 * (k / 1.2) ** 2)
kernel_1d /= kernel_1d.sum()
smooth_counts = np.apply_along_axis(lambda r: np.convolve(r, kernel_1d, mode="same"), 0, cycle_counts.astype(float))
smooth_counts = np.apply_along_axis(lambda r: np.convolve(r, kernel_1d, mode="same"), 1, smooth_counts)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Truncate inferno to start lighter (avoid near-black for low counts)
base_cmap = plt.cm.inferno
colors_arr = base_cmap(np.linspace(0.15, 0.95, 256))
cmap = LinearSegmentedColormap.from_list("inferno_trim", colors_arr)

im = ax.pcolormesh(
    mean_edges, amp_edges, masked_counts, cmap=cmap, norm=LogNorm(vmin=1, vmax=cycle_counts.max()), shading="flat"
)

ax.set_facecolor("#f0f0f0")

# Contour overlay at key cycle count thresholds
contour_levels = [10, 50, 200, 1000]
cs = ax.contour(
    mean_centers,
    amp_centers,
    smooth_counts,
    levels=contour_levels,
    colors="white",
    linewidths=[0.6, 0.8, 1.0, 1.2],
    alpha=0.5,
)
ax.clabel(cs, inline=True, fontsize=11, fmt="%d", colors="white")

# Colorbar with custom scientific formatter
cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03, aspect=30)
cbar.ax.tick_params(labelsize=16)
cbar.ax.yaxis.set_major_formatter(LogFormatterSciNotation(minor_thresholds=(2, 0.5)))
cbar.set_label("Cycle Count", fontsize=20, labelpad=12)
cbar.outline.set_visible(False)

# Annotate key regions for data storytelling
ax.annotate(
    "Dominant\ncycle zone",
    xy=(100, 15),
    xytext=(0, 80),
    fontsize=13,
    fontweight="bold",
    color="white",
    ha="center",
    arrowprops={"arrowstyle": "->", "color": "white", "lw": 1.5},
)
ax.annotate(
    "Overload\ncluster",
    xy=(170, 75),
    xytext=(220, 140),
    fontsize=13,
    fontweight="bold",
    color="#ffdd57",
    ha="center",
    arrowprops={"arrowstyle": "->", "color": "#ffdd57", "lw": 1.5},
)

# Style
ax.set_xlabel("Mean Stress (MPa)", fontsize=20)
ax.set_ylabel("Stress Amplitude (MPa)", fontsize=20)
ax.set_title("heatmap-rainflow · matplotlib · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
