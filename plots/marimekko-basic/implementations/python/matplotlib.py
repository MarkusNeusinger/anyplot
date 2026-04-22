""" pyplots.ai
marimekko-basic: Basic Marimekko Chart
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np


# Data: Market share by region (x-category) and product line (y-category)
# Regions have different total market sizes (determines bar widths)
# Products have different shares within each region (determines segment heights)
regions = ["North America", "Europe", "Asia Pacific", "Latin America"]
products = ["Electronics", "Apparel", "Home & Garden", "Sports"]

# Values matrix: rows = products, columns = regions
# Each column total determines that region's bar width
values = np.array(
    [
        [120, 85, 200, 35],  # Electronics
        [80, 110, 150, 45],  # Apparel
        [60, 70, 80, 25],  # Home & Garden
        [40, 35, 70, 15],  # Sports
    ]
)

# Colors - Python blue/yellow first, then colorblind-safe additions
colors = ["#306998", "#FFD43B", "#4DAF4A", "#984EA3"]

# Calculate bar widths (proportional to column totals)
column_totals = values.sum(axis=0)
total = column_totals.sum()
bar_widths = column_totals / total

# Calculate cumulative widths for x-positioning
cum_widths = np.concatenate([[0], np.cumsum(bar_widths)[:-1]])

# Create figure (4800x2700 px at dpi=300)
fig, ax = plt.subplots(figsize=(16, 9))

# Draw each segment
for i, (product, color) in enumerate(zip(products, colors, strict=True)):
    # Calculate heights as proportion of column total
    heights = values[i] / column_totals

    # Calculate bottom positions (cumulative heights of products below)
    bottoms = values[:i].sum(axis=0) / column_totals if i > 0 else np.zeros(len(regions))

    # Draw bars for this product across all regions
    for j in range(len(regions)):
        ax.bar(
            cum_widths[j] + bar_widths[j] / 2,
            heights[j],
            width=bar_widths[j] * 0.98,  # Small gap between bars
            bottom=bottoms[j],
            color=color,
            edgecolor="white",
            linewidth=2,
            label=product if j == 0 else None,
        )

        # Add value labels on larger segments
        if heights[j] > 0.12:
            ax.text(
                cum_widths[j] + bar_widths[j] / 2,
                bottoms[j] + heights[j] / 2,
                f"${values[i, j]}M",
                ha="center",
                va="center",
                fontsize=14,
                fontweight="bold",
                color="white" if color == "#306998" else "black",
            )

# Add region labels at the bottom
for j, region in enumerate(regions):
    ax.text(
        cum_widths[j] + bar_widths[j] / 2,
        -0.05,
        f"{region}\n(${column_totals[j]:.0f}M)",
        ha="center",
        va="top",
        fontsize=16,
        fontweight="bold",
    )

# Style the plot
ax.set_xlim(0, 1)
ax.set_ylim(-0.15, 1)
ax.set_ylabel("Share within Region", fontsize=20)
ax.set_title("marimekko-basic · matplotlib · pyplots.ai", fontsize=24)

# Format y-axis as percentage
ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
ax.tick_params(axis="y", labelsize=16)

# Remove x-axis ticks (we have custom labels)
ax.set_xticks([])

# Add legend
ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), fontsize=16, title="Product Lines", title_fontsize=18)

# Subtle grid on y-axis only
ax.yaxis.grid(True, alpha=0.3, linestyle="--")
ax.set_axisbelow(True)

# Remove top and right spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["bottom"].set_visible(False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
