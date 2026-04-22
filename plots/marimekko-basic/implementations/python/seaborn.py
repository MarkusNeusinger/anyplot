""" pyplots.ai
marimekko-basic: Basic Marimekko Chart
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Set seaborn style
sns.set_style("whitegrid")
sns.set_context("talk", font_scale=1.2)

# Data: Market share by region and product line
np.random.seed(42)

regions = ["North America", "Europe", "Asia Pacific", "Latin America", "Middle East"]
products = ["Electronics", "Apparel", "Food & Beverage", "Home Goods"]

# Create market data (values in billions)
data = {
    "North America": [45, 32, 28, 25],
    "Europe": [38, 42, 35, 22],
    "Asia Pacific": [65, 48, 52, 38],
    "Latin America": [18, 15, 22, 12],
    "Middle East": [12, 8, 15, 10],
}

# Convert to DataFrame
df_data = []
for region in regions:
    for i, product in enumerate(products):
        df_data.append({"Region": region, "Product": product, "Revenue": data[region][i]})
df = pd.DataFrame(df_data)

# Calculate totals for each region (determines bar width)
region_totals = df.groupby("Region")["Revenue"].sum()
total_revenue = region_totals.sum()

# Calculate relative widths (proportional to region totals)
widths = region_totals / total_revenue

# Color palette - using seaborn's colorblind palette
colors = sns.color_palette("colorblind", n_colors=len(products))

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Calculate x positions for variable-width bars
x_positions = np.zeros(len(regions))
cumsum = 0
for i, region in enumerate(regions):
    x_positions[i] = cumsum
    cumsum += widths[region]

# Draw marimekko chart
for region_idx, region in enumerate(regions):
    region_data = df[df["Region"] == region]
    region_total = region_totals[region]
    bar_width = widths[region]
    x_start = x_positions[region_idx]

    # Stack products within each region bar
    y_bottom = 0
    for prod_idx, product in enumerate(products):
        value = region_data[region_data["Product"] == product]["Revenue"].values[0]
        height = value / region_total  # Normalized height (proportion)

        # Draw rectangle using matplotlib (seaborn doesn't have native marimekko)
        rect = mpatches.Rectangle(
            (x_start, y_bottom), bar_width, height, facecolor=colors[prod_idx], edgecolor="white", linewidth=2
        )
        ax.add_patch(rect)

        # Add value label for larger segments
        if height > 0.12:
            ax.text(
                x_start + bar_width / 2,
                y_bottom + height / 2,
                f"${value}B",
                ha="center",
                va="center",
                fontsize=14,
                fontweight="bold",
                color="white",
            )

        y_bottom += height

# Set axis limits
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)

# X-axis: Region labels centered under each bar
x_centers = x_positions + widths.values / 2
ax.set_xticks(x_centers)
ax.set_xticklabels(regions, fontsize=16)

# Y-axis: Percentage
ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=16)

# Labels and title
ax.set_xlabel("Region (width proportional to total revenue)", fontsize=20)
ax.set_ylabel("Product Mix (%)", fontsize=20)
ax.set_title("marimekko-basic · seaborn · pyplots.ai", fontsize=24, fontweight="bold", pad=20)

# Legend
legend_handles = [
    mpatches.Patch(facecolor=colors[i], edgecolor="white", label=products[i]) for i in range(len(products))
]
ax.legend(
    handles=legend_handles,
    loc="upper left",
    bbox_to_anchor=(1.02, 1),
    fontsize=14,
    title="Product Line",
    title_fontsize=16,
)

# Grid styling
ax.grid(True, alpha=0.3, linestyle="--", axis="y")
ax.set_axisbelow(True)

# Remove top and right spines for cleaner look
sns.despine(ax=ax, top=True, right=True)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
