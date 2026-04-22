""" pyplots.ai
violin-box: Violin Plot with Embedded Box Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 95/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Generate groups with different distributions
np.random.seed(42)

# Four groups with varying distributions to showcase violin+box features
group_a = np.random.normal(65, 8, 80)  # Symmetric
group_b = np.concatenate([np.random.normal(45, 5, 40), np.random.normal(60, 5, 40)])  # Bimodal
group_c = np.random.exponential(10, 80) + 30  # Right-skewed
group_d = np.random.normal(55, 12, 80)  # Wide spread with outliers
group_d = np.append(group_d, [95, 100, 15, 10])  # Add outliers

data = [group_a, group_b, group_c, group_d]
labels = ["Control", "Treatment A", "Treatment B", "Treatment C"]

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Plot violins
positions = np.arange(1, len(data) + 1)
violin_parts = ax.violinplot(data, positions=positions, showmeans=False, showmedians=False, showextrema=False)

# Style violins with Python Blue
for body in violin_parts["bodies"]:
    body.set_facecolor("#306998")
    body.set_edgecolor("#1a3a4f")
    body.set_alpha(0.7)
    body.set_linewidth(2)

# Overlay box plots inside violins
box_parts = ax.boxplot(
    data, positions=positions, widths=0.15, patch_artist=True, tick_labels=labels, showfliers=True, zorder=3
)

# Style box plots with Python Yellow
for patch in box_parts["boxes"]:
    patch.set_facecolor("#FFD43B")
    patch.set_edgecolor("#1a3a4f")
    patch.set_linewidth(2)

for whisker in box_parts["whiskers"]:
    whisker.set_color("#1a3a4f")
    whisker.set_linewidth(2)

for cap in box_parts["caps"]:
    cap.set_color("#1a3a4f")
    cap.set_linewidth(2)

for median in box_parts["medians"]:
    median.set_color("#d62728")
    median.set_linewidth(3)

for flier in box_parts["fliers"]:
    flier.set(marker="o", markerfacecolor="#306998", markeredgecolor="#1a3a4f", markersize=8, alpha=0.8)

# Labels and styling
ax.set_xlabel("Experimental Group", fontsize=20)
ax.set_ylabel("Response Value (units)", fontsize=20)
ax.set_title("violin-box · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--", axis="y")

# Set y-axis range to accommodate all data
ax.set_ylim(0, 110)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
