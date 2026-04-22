""" pyplots.ai
forest-basic: Meta-Analysis Forest Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-27
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np


# Data: Meta-analysis of RCTs comparing treatment efficacy (standardized mean difference)
studies = [
    "Johnson 2018",
    "Smith 2019",
    "Garcia 2020",
    "Williams 2020",
    "Brown 2021",
    "Davis 2021",
    "Miller 2022",
    "Wilson 2022",
    "Anderson 2023",
    "Taylor 2023",
]

# Effect sizes (standardized mean difference) and 95% CIs
effect_sizes = np.array([-0.45, -0.32, -0.58, -0.21, -0.67, -0.38, -0.52, -0.29, -0.41, -0.55])
ci_lower = np.array([-0.78, -0.61, -0.95, -0.48, -1.02, -0.69, -0.88, -0.56, -0.72, -0.91])
ci_upper = np.array([-0.12, -0.03, -0.21, 0.06, -0.32, -0.07, -0.16, -0.02, -0.10, -0.19])

# Study weights (based on sample size / inverse variance)
weights = np.array([8.5, 10.2, 7.8, 11.5, 6.9, 9.3, 8.1, 10.8, 9.7, 7.2])

# Pooled estimate (random effects meta-analysis)
pooled_effect = -0.42
pooled_ci_lower = -0.53
pooled_ci_upper = -0.31

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

n_studies = len(studies)
y_positions = np.arange(n_studies, 0, -1)

# Normalize weights for marker sizing (scale between 80 and 300)
weight_normalized = (weights - weights.min()) / (weights.max() - weights.min())
marker_sizes = 80 + weight_normalized * 220

# Plot vertical reference line at null effect (0)
ax.axvline(x=0, color="#888888", linestyle="--", linewidth=2, alpha=0.7, zorder=1)

# Plot confidence intervals as horizontal lines
for y, lower, upper in zip(y_positions, ci_lower, ci_upper, strict=True):
    ax.hlines(y=y, xmin=lower, xmax=upper, color="#306998", linewidth=3, zorder=2)

# Plot effect size points
ax.scatter(effect_sizes, y_positions, s=marker_sizes, color="#306998", edgecolors="white", linewidths=1.5, zorder=3)

# Plot pooled estimate as diamond
diamond_y = 0
diamond_height = 0.4

# Create diamond shape using polygon
diamond_vertices = np.array(
    [
        [pooled_effect, diamond_y + diamond_height],
        [pooled_ci_upper, diamond_y],
        [pooled_effect, diamond_y - diamond_height],
        [pooled_ci_lower, diamond_y],
    ]
)
diamond_patch = mpatches.Polygon(
    diamond_vertices, closed=True, facecolor="#FFD43B", edgecolor="#306998", linewidth=2.5, zorder=4
)
ax.add_patch(diamond_patch)

# Add study labels on y-axis
ax.set_yticks(list(y_positions) + [0])
ax.set_yticklabels(studies + ["Pooled Estimate"])

# Styling
ax.set_xlabel("Standardized Mean Difference (95% CI)", fontsize=20)
ax.set_title("forest-basic \u00b7 matplotlib \u00b7 pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.tick_params(axis="y", length=0)

# Set x-axis limits with padding
x_min = min(ci_lower.min(), pooled_ci_lower) - 0.15
x_max = max(ci_upper.max(), pooled_ci_upper) + 0.15
ax.set_xlim(x_min, x_max)

# Set y-axis limits
ax.set_ylim(-0.8, n_studies + 0.8)

# Add subtle grid for x-axis only
ax.grid(True, axis="x", alpha=0.3, linestyle="--", zorder=0)
ax.set_axisbelow(True)

# Add annotation for "Favors Treatment" and "Favors Control"
ax.text(x_min + 0.05, -0.6, "\u2190 Favors Treatment", fontsize=14, ha="left", va="top", color="#555555")
ax.text(x_max - 0.05, -0.6, "Favors Control \u2192", fontsize=14, ha="right", va="top", color="#555555")

# Remove top and right spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
