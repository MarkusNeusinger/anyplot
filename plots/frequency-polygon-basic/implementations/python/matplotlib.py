""" pyplots.ai
frequency-polygon-basic: Frequency Polygon for Distribution Comparison
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 94/100 | Created: 2026-01-09
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Heights by age group
np.random.seed(42)
n_per_group = 200

# Generate three distinct distributions representing height measurements (cm)
young_adults = np.random.normal(loc=172, scale=8, size=n_per_group)  # 18-25 years
middle_aged = np.random.normal(loc=170, scale=9, size=n_per_group)  # 40-50 years
seniors = np.random.normal(loc=166, scale=10, size=n_per_group)  # 65+ years

groups = [young_adults, middle_aged, seniors]
group_names = ["Young Adults (18-25)", "Middle-Aged (40-50)", "Seniors (65+)"]
colors = ["#306998", "#FFD43B", "#8B4513"]  # Python Blue, Python Yellow, Brown

# Create common bin edges for all groups
all_data = np.concatenate(groups)
bin_edges = np.linspace(all_data.min() - 5, all_data.max() + 5, 20)
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

for data, name, color in zip(groups, group_names, colors, strict=True):
    # Calculate histogram frequencies
    counts, _ = np.histogram(data, bins=bin_edges)

    # Extend to zero at both ends to close the polygon
    x_extended = np.concatenate([[bin_edges[0]], bin_centers, [bin_edges[-1]]])
    y_extended = np.concatenate([[0], counts, [0]])

    # Plot frequency polygon line
    ax.plot(
        x_extended,
        y_extended,
        linewidth=3,
        color=color,
        label=name,
        marker="o",
        markersize=6,
        markerfacecolor=color,
        markeredgecolor="white",
        markeredgewidth=1,
    )

    # Add semi-transparent fill
    ax.fill(x_extended, y_extended, color=color, alpha=0.15)

# Labels and styling
ax.set_xlabel("Height (cm)", fontsize=20)
ax.set_ylabel("Frequency", fontsize=20)
ax.set_title("frequency-polygon-basic · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.legend(fontsize=16, loc="upper right")
ax.grid(True, alpha=0.3, linestyle="--")

# Ensure y-axis starts at 0
ax.set_ylim(bottom=0)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
