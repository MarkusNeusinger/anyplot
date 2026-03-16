""" pyplots.ai
heatmap-cohort-retention: Cohort Retention Heatmap
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-16
"""

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np


# Data
np.random.seed(42)
cohort_labels = [
    "Jan 2024",
    "Feb 2024",
    "Mar 2024",
    "Apr 2024",
    "May 2024",
    "Jun 2024",
    "Jul 2024",
    "Aug 2024",
    "Sep 2024",
    "Oct 2024",
]
cohort_sizes = [1200, 1350, 980, 1100, 1450, 1280, 1050, 1320, 1180, 1400]
n_cohorts = len(cohort_labels)
n_periods = n_cohorts

# Generate realistic retention data (triangular: cohort i has n_periods - i periods)
retention = np.full((n_cohorts, n_periods), np.nan)
for i in range(n_cohorts):
    max_periods = n_periods - i
    retention[i, 0] = 100.0
    for j in range(1, max_periods):
        # Retention decays with diminishing drops, plus some noise
        base_drop = 18 * np.exp(-0.3 * j) + 2
        noise = np.random.uniform(-3, 3)
        retention[i, j] = max(retention[i, j - 1] - base_drop - noise, 8)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Custom blue-green sequential colormap
cmap = plt.cm.GnBu
norm = mcolors.Normalize(vmin=0, vmax=100)

# Draw heatmap cells manually for triangular shape
for i in range(n_cohorts):
    for j in range(n_periods):
        if np.isnan(retention[i, j]):
            continue
        val = retention[i, j]
        color = cmap(norm(val))
        rect = plt.Rectangle((j - 0.5, i - 0.5), 1, 1, facecolor=color, edgecolor="white", linewidth=2)
        ax.add_patch(rect)
        # Text color: white on dark cells, dark on light cells
        text_color = "white" if val < 50 else "#1a1a2e"
        ax.text(j, i, f"{val:.0f}%", ha="center", va="center", fontsize=13, fontweight="medium", color=text_color)

# Style
ax.set_xlim(-0.5, n_periods - 0.5)
ax.set_ylim(n_cohorts - 0.5, -0.5)
ax.set_xticks(range(n_periods))
ax.set_xticklabels([f"Month {p}" for p in range(n_periods)], fontsize=14)
ax.set_yticks(range(n_cohorts))
ax.set_yticklabels([f"{label}  (n={size:,})" for label, size in zip(cohort_labels, cohort_sizes, strict=True)], fontsize=14)
ax.set_xlabel("Months Since Signup", fontsize=20)
ax.set_ylabel("Signup Cohort", fontsize=20)
ax.set_title("heatmap-cohort-retention · matplotlib · pyplots.ai", fontsize=24, fontweight="medium", pad=20)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)
ax.spines["bottom"].set_visible(False)
ax.tick_params(axis="both", length=0)

# Colorbar
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])
cbar = fig.colorbar(sm, ax=ax, shrink=0.6, aspect=25, pad=0.02)
cbar.set_label("Retention Rate (%)", fontsize=16)
cbar.ax.tick_params(labelsize=14)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
