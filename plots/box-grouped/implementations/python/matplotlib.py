""" pyplots.ai
box-grouped: Grouped Box Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 94/100 | Created: 2025-12-25
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Employee performance scores across departments and experience levels
np.random.seed(42)

categories = ["Sales", "Engineering", "Marketing", "Support"]
subcategories = ["Junior", "Mid-Level", "Senior"]
colors = ["#306998", "#FFD43B", "#4ECDC4"]  # Python Blue, Python Yellow, Teal

# Generate realistic performance data with varying distributions
data = {}
for cat in categories:
    data[cat] = {}
    for i, sub in enumerate(subcategories):
        # Different base performance and variance per experience level
        base = 55 + i * 12  # Junior ~55, Mid ~67, Senior ~79
        variance = 15 - i * 3  # Junior has more variance, Senior is more consistent
        n_points = np.random.randint(30, 60)
        scores = np.random.normal(base, variance, n_points)
        # Add some outliers
        if np.random.random() > 0.5:
            outliers = np.random.choice([base - 25, base + 25], size=np.random.randint(1, 4))
            scores = np.concatenate([scores, outliers])
        data[cat][sub] = np.clip(scores, 0, 100)  # Performance scores 0-100

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Calculate positions for grouped boxes
n_categories = len(categories)
n_subcategories = len(subcategories)
box_width = 0.25
group_gap = 0.4  # Gap between category groups
positions_per_category = n_subcategories * box_width + group_gap

# Plot boxes for each subcategory
all_box_plots = []
for sub_idx, sub in enumerate(subcategories):
    positions = []
    box_data = []
    for cat_idx, cat in enumerate(categories):
        pos = cat_idx * (n_subcategories * box_width + group_gap) + sub_idx * box_width
        positions.append(pos)
        box_data.append(data[cat][sub])

    bp = ax.boxplot(
        box_data,
        positions=positions,
        widths=box_width * 0.8,
        patch_artist=True,
        showfliers=True,
        flierprops={"marker": "o", "markerfacecolor": colors[sub_idx], "markersize": 8, "alpha": 0.6},
        medianprops={"color": "#333333", "linewidth": 2},
        whiskerprops={"color": "#666666", "linewidth": 1.5},
        capprops={"color": "#666666", "linewidth": 1.5},
    )

    # Color the boxes
    for patch in bp["boxes"]:
        patch.set_facecolor(colors[sub_idx])
        patch.set_alpha(0.8)
        patch.set_edgecolor("#333333")
        patch.set_linewidth(1.5)

    all_box_plots.append(bp)

# Set x-axis tick positions and labels
center_positions = [
    cat_idx * (n_subcategories * box_width + group_gap) + (n_subcategories - 1) * box_width / 2
    for cat_idx in range(n_categories)
]
ax.set_xticks(center_positions)
ax.set_xticklabels(categories, fontsize=18)

# Labels and title
ax.set_xlabel("Department", fontsize=20)
ax.set_ylabel("Performance Score (0-100)", fontsize=20)
ax.set_title("box-grouped · matplotlib · pyplots.ai", fontsize=24)

# Tick params
ax.tick_params(axis="both", labelsize=16)

# Legend
legend_patches = [
    plt.Rectangle((0, 0), 1, 1, facecolor=colors[i], edgecolor="#333333", alpha=0.8) for i in range(len(subcategories))
]
ax.legend(legend_patches, subcategories, loc="upper left", fontsize=16, framealpha=0.9)

# Grid
ax.grid(True, alpha=0.3, linestyle="--", axis="y")
ax.set_axisbelow(True)

# Set y-axis limits
ax.set_ylim(0, 110)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
