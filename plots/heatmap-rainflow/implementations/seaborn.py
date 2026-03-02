""" pyplots.ai
heatmap-rainflow: Rainflow Counting Matrix for Fatigue Analysis
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-02
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.colors import LogNorm


# Data - Simulated rainflow counting matrix for a steel shaft under variable-amplitude loading
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

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

mask = cycle_counts == 0
sns.heatmap(
    cycle_counts,
    mask=mask,
    norm=LogNorm(vmin=1, vmax=cycle_counts.max()),
    cmap="inferno",
    xticklabels=mean_labels,
    yticklabels=amp_labels,
    linewidths=0.3,
    linecolor="#e8e8e8",
    cbar_kws={"label": "Cycle Count (log scale)", "shrink": 0.82},
    ax=ax,
)

# Style
ax.set_xlabel("Mean Stress (MPa)", fontsize=20, labelpad=12)
ax.set_ylabel("Stress Amplitude (MPa)", fontsize=20, labelpad=12)
ax.set_title("heatmap-rainflow · seaborn · pyplots.ai", fontsize=24, fontweight="medium", pad=16)
ax.tick_params(axis="both", labelsize=14)

# Colorbar styling
cbar = ax.collections[0].colorbar
cbar.ax.tick_params(labelsize=14)
cbar.set_label("Cycle Count (log scale)", fontsize=18, labelpad=12)

# Zero-count bins shown as light background
ax.set_facecolor("#f5f5f5")

# Remove spines
for spine in ax.spines.values():
    spine.set_visible(False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
