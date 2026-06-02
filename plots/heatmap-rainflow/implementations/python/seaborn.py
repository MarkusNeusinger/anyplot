""" anyplot.ai
heatmap-rainflow: Rainflow Counting Matrix for Fatigue Analysis
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 90/100 | Updated: 2026-06-02
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap, LogNorm


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint continuous colormap — sequential (brand green → blue)
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", ["#009E73", "#4467A3"])

sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.15,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Data — simulated rainflow counting matrix for a steel shaft under variable-amplitude loading
np.random.seed(42)

n_amp_bins = 20
n_mean_bins = 20
amplitude_edges = np.linspace(5, 200, n_amp_bins + 1)
mean_edges = np.linspace(-50, 250, n_mean_bins + 1)
amplitude_centers = (amplitude_edges[:-1] + amplitude_edges[1:]) / 2
mean_centers = (mean_edges[:-1] + mean_edges[1:]) / 2

# Realistic rainflow distribution: exponential decay with amplitude, Gaussian peak in mean
amp_idx, mean_idx = np.meshgrid(np.arange(n_amp_bins), np.arange(n_mean_bins), indexing="ij")
cycle_density = np.exp(-0.18 * amp_idx) * np.exp(-0.008 * (mean_idx - 10) ** 2)
cycle_counts = cycle_density * 4000 + np.random.exponential(30, cycle_density.shape)
cycle_counts = np.round(cycle_counts).astype(int)

# Add sparsity at high amplitudes (realistic: rare high-stress cycles)
cycle_counts[14:, :] = np.where(np.random.rand(n_amp_bins - 14, n_mean_bins) > 0.35, 0, cycle_counts[14:, :])
cycle_counts[cycle_counts < 3] = 0

# Bin labels (every other bin for readability)
amp_labels = [f"{v:.0f}" if i % 2 == 0 else "" for i, v in enumerate(amplitude_centers)]
mean_labels = [f"{v:.0f}" if i % 2 == 0 else "" for i, v in enumerate(mean_centers)]

# Plot — square canvas for symmetric 2D heatmap: 2400×2400 px
fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

mask = cycle_counts == 0
sns.heatmap(
    cycle_counts,
    mask=mask,
    norm=LogNorm(vmin=1, vmax=cycle_counts.max()),
    cmap=imprint_seq,
    xticklabels=mean_labels,
    yticklabels=amp_labels,
    linewidths=0.3,
    linecolor=INK_SOFT,
    cbar_kws={"shrink": 0.82},
    ax=ax,
)

# Invert y-axis so amplitudes increase upward (standard engineering convention)
ax.invert_yaxis()

# Zero-count bins show the page background
ax.set_facecolor(PAGE_BG)

# Style
title = "heatmap-rainflow · python · seaborn · anyplot.ai"
ax.set_xlabel("Mean Stress (MPa)", fontsize=10, labelpad=12, color=INK)
ax.set_ylabel("Stress Amplitude (MPa)", fontsize=10, labelpad=12, color=INK)
ax.set_title(title, fontsize=12, fontweight="medium", pad=16, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

# Colorbar styling
cbar = ax.collections[0].colorbar
cbar.ax.tick_params(labelsize=8, colors=INK_SOFT)
cbar.set_label("Cycle Count (log scale)", fontsize=10, labelpad=12, color=INK)

# Annotate peak count region — creates a clear focal point for data storytelling
peak_idx = np.unravel_index(cycle_counts.argmax(), cycle_counts.shape)
peak_val = cycle_counts[peak_idx]
ax.annotate(
    f"Peak: {peak_val:,} cycles",
    xy=(peak_idx[1] + 0.5, peak_idx[0] + 0.5),
    xytext=(peak_idx[1] + 4, peak_idx[0] + 4.5),
    fontsize=8,
    fontweight="semibold",
    color=INK,
    bbox={"boxstyle": "round,pad=0.3", "facecolor": ELEVATED_BG, "edgecolor": INK_SOFT, "alpha": 0.9},
    arrowprops={"arrowstyle": "-|>", "color": INK_SOFT, "lw": 1.5, "connectionstyle": "arc3,rad=-0.15"},
    zorder=10,
)

# Remove spines
sns.despine(ax=ax, left=True, bottom=True)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
