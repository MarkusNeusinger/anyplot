""" pyplots.ai
box-basic: Basic Box Plot
Library: matplotlib 3.10.8 | Python 3.14
Quality: 92/100 | Created: 2025-12-23
"""

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np


# Data - simulating performance scores (0-100 scale) across 5 departments
np.random.seed(42)
categories = ["Engineering", "Marketing", "Sales", "Support", "Design"]
colors = ["#306998", "#E07B39", "#8B5CF6", "#2CA02C", "#4ECDC4"]
edge_colors = ["#1E4266", "#A35525", "#5E3DA6", "#1C6E1C", "#2E9E97"]

# Generate realistic distributions with varied characteristics and clamped to 0-100
data = [
    np.clip(np.random.normal(74, 10, 80), 15, 100),  # Engineering: solid, moderate spread
    np.clip(np.random.normal(85, 6, 90), 15, 100),  # Marketing: high scores, tight cluster
    np.clip(np.random.normal(68, 14, 70), 15, 100),  # Sales: lower, widest spread
    np.clip(np.random.normal(78, 9, 85), 15, 100),  # Support: above average, moderate
    np.clip(np.random.normal(80, 11, 60), 15, 100),  # Design: high with some spread
]

# Inject deliberate outliers for feature coverage
data[0] = np.append(data[0], [38, 99])  # Engineering: one low, one high outlier
data[2] = np.append(data[2], [22, 25, 98])  # Sales: two low outliers, one high

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor="#FAFAFA")
ax.set_facecolor("#FAFAFA")

bp = ax.boxplot(
    data,
    tick_labels=categories,
    patch_artist=True,
    widths=0.55,
    showmeans=True,
    notch=True,
    meanprops={"marker": "D", "markerfacecolor": "white", "markeredgecolor": "#333333", "markersize": 9, "zorder": 5},
    flierprops={
        "marker": "o",
        "markerfacecolor": "#666666",
        "markersize": 8,
        "alpha": 0.6,
        "markeredgecolor": "white",
        "markeredgewidth": 0.5,
    },
    medianprops={"color": "#1a1a1a", "linewidth": 2.5},
    whiskerprops={"linewidth": 2, "color": "#555555", "linestyle": "--"},
    capprops={"linewidth": 2.5, "color": "#444444"},
)

# Apply colors with matching darker edges
for patch, color, edge in zip(bp["boxes"], colors, edge_colors, strict=True):
    patch.set_facecolor(color)
    patch.set_alpha(0.8)
    patch.set_edgecolor(edge)
    patch.set_linewidth(2.2)
    patch.set_path_effects([pe.withStroke(linewidth=3.5, foreground=edge)])

# Compute stats for storytelling annotations
iqrs = [np.percentile(d, 75) - np.percentile(d, 25) for d in data]
medians = [np.median(d) for d in data]
tightest_idx = int(np.argmin(iqrs))
widest_idx = int(np.argmax(iqrs))

# Annotation: tightest distribution (Marketing)
tightest_median = medians[tightest_idx]
ax.annotate(
    f"Tightest spread\nIQR = {iqrs[tightest_idx]:.1f}",
    xy=(tightest_idx + 1, tightest_median),
    xytext=(tightest_idx + 1.6, tightest_median + 12),
    fontsize=13,
    fontweight="bold",
    color="#1E4266",
    ha="left",
    arrowprops={
        "arrowstyle": "fancy,head_length=0.6,head_width=0.4,tail_width=0.15",
        "connectionstyle": "arc3,rad=-0.2",
        "facecolor": "#306998",
        "edgecolor": "#1E4266",
        "alpha": 0.7,
    },
    bbox={"boxstyle": "round,pad=0.4", "facecolor": "#E8F0FE", "edgecolor": "#306998", "alpha": 0.85},
)

# Annotation: widest spread (Sales)
widest_median = medians[widest_idx]
ax.annotate(
    f"Widest spread\nIQR = {iqrs[widest_idx]:.1f}",
    xy=(widest_idx + 1, widest_median),
    xytext=(widest_idx + 1.55, widest_median - 18),
    fontsize=13,
    fontweight="bold",
    color="#5E3DA6",
    ha="left",
    arrowprops={
        "arrowstyle": "fancy,head_length=0.6,head_width=0.4,tail_width=0.15",
        "connectionstyle": "arc3,rad=0.25",
        "facecolor": "#8B5CF6",
        "edgecolor": "#5E3DA6",
        "alpha": 0.7,
    },
    bbox={"boxstyle": "round,pad=0.4", "facecolor": "#F0E8FE", "edgecolor": "#8B5CF6", "alpha": 0.85},
)

# Annotation: highest median (Marketing)
best_idx = int(np.argmax(medians))
ax.annotate(
    f"Top performer\nMedian = {medians[best_idx]:.0f}",
    xy=(best_idx + 1, np.percentile(data[best_idx], 75) + 2),
    xytext=(best_idx + 0.3, 100),
    fontsize=13,
    fontweight="bold",
    color="#A35525",
    ha="center",
    arrowprops={
        "arrowstyle": "fancy,head_length=0.6,head_width=0.4,tail_width=0.15",
        "connectionstyle": "arc3,rad=0.15",
        "facecolor": "#E07B39",
        "edgecolor": "#A35525",
        "alpha": 0.7,
    },
    bbox={"boxstyle": "round,pad=0.4", "facecolor": "#FEF0E8", "edgecolor": "#E07B39", "alpha": 0.85},
)

# Style
ax.set_xlabel("Department", fontsize=20, fontweight="medium", labelpad=10)
ax.set_ylabel("Performance Score", fontsize=20, fontweight="medium", labelpad=10)
ax.set_title(
    "box-basic · matplotlib · pyplots.ai",
    fontsize=24,
    fontweight="medium",
    pad=20,
    path_effects=[pe.withStroke(linewidth=3, foreground="#FAFAFA")],
)
ax.tick_params(axis="both", labelsize=16)
ax.tick_params(axis="x", length=0, pad=8)
ax.set_ylim(10, 108)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color="#999999")
ax.set_axisbelow(True)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color("#CCCCCC")
ax.spines["bottom"].set_color("#CCCCCC")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="#FAFAFA")
