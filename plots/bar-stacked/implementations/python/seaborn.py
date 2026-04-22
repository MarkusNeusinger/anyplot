""" pyplots.ai
bar-stacked: Stacked Bar Chart
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


# Data - Monthly sales by product category (realistic business scenario)
categories = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
products = ["Electronics", "Clothing", "Home & Garden", "Sports"]

# Create realistic sales data (in thousands)
data = {
    "Month": categories * len(products),
    "Product": [p for p in products for _ in categories],
    "Sales": [
        # Electronics - highest, growing trend
        120,
        135,
        145,
        160,
        175,
        190,
        # Clothing - seasonal variation
        85,
        70,
        95,
        110,
        90,
        75,
        # Home & Garden - spring/summer peak
        45,
        55,
        80,
        95,
        85,
        60,
        # Sports - summer peak
        35,
        40,
        55,
        70,
        85,
        65,
    ],
}

df = pd.DataFrame(data)

# Preserve category order
df["Month"] = pd.Categorical(df["Month"], categories=categories, ordered=True)
# Order products by total sales (largest at bottom of stack)
product_totals = df.groupby("Product")["Sales"].sum().sort_values(ascending=False)
ordered_products = product_totals.index.tolist()
df["Product"] = pd.Categorical(df["Product"], categories=ordered_products, ordered=True)

# Create plot with seaborn styling
sns.set_style("whitegrid")
sns.set_context("talk", font_scale=1.2)

fig, ax = plt.subplots(figsize=(16, 9))

# Python-themed color palette with distinct colors (avoiding similar yellows)
# Map colors to original product order, then reorder based on totals
original_colors = {
    "Electronics": "#306998",  # Python Blue
    "Clothing": "#FFD43B",  # Python Yellow
    "Home & Garden": "#4B8BBE",  # Light Blue
    "Sports": "#E57373",  # Coral/Salmon for contrast
}
colors = [original_colors[p] for p in ordered_products]

# Use seaborn's histplot with weights for stacked bar chart
# This is seaborn's native approach for stacked categorical bars
sns.histplot(
    data=df,
    x="Month",
    weights="Sales",
    hue="Product",
    multiple="stack",
    palette=colors,
    shrink=0.7,
    edgecolor="white",
    linewidth=1.5,
    ax=ax,
)

# Calculate totals for labels on top of stacks
totals = df.groupby("Month", observed=True)["Sales"].sum()
for i, (_month, total) in enumerate(totals.items()):
    ax.text(i, total + 8, f"${int(total)}K", ha="center", va="bottom", fontsize=16, fontweight="bold")

# Styling
ax.set_xlabel("Month", fontsize=20)
ax.set_ylabel("Sales (Thousands $)", fontsize=20)
ax.set_title("bar-stacked · seaborn · pyplots.ai", fontsize=24, fontweight="bold")
ax.tick_params(axis="both", labelsize=16)

# Legend - move to right and adjust styling
legend = ax.get_legend()
legend.set_title("Product Category")
legend.get_title().set_fontsize(18)
for text in legend.get_texts():
    text.set_fontsize(16)
legend.set_bbox_to_anchor((1.02, 1))
legend.set_loc("upper left")
legend.get_frame().set_edgecolor("gray")

# Grid styling
ax.yaxis.grid(True, alpha=0.3, linestyle="--")
ax.xaxis.grid(False)
ax.set_axisbelow(True)

# Remove top and right spines
sns.despine()

# Adjust y-axis to accommodate total labels
ax.set_ylim(0, totals.max() * 1.15)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
