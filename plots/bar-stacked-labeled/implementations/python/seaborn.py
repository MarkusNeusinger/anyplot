""" pyplots.ai
bar-stacked-labeled: Stacked Bar Chart with Total Labels
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-09
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data - Quarterly revenue by product category
np.random.seed(42)

categories = ["Q1", "Q2", "Q3", "Q4"]
components = ["Electronics", "Software", "Services", "Hardware"]

# Create data with realistic revenue values (in millions)
data = {
    "Electronics": [45, 52, 48, 61],
    "Software": [32, 38, 42, 55],
    "Services": [28, 31, 35, 40],
    "Hardware": [18, 22, 25, 28],
}

# Convert to long format for seaborn
df_long = pd.DataFrame(
    [
        {"Quarter": cat, "Product": comp, "Revenue": data[comp][i]}
        for i, cat in enumerate(categories)
        for comp in components
    ]
)

# Calculate totals for each quarter
totals = df_long.groupby("Quarter")["Revenue"].sum().reindex(categories)

# Create stacked bar data
df_wide = pd.DataFrame(data, index=categories)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Colors - Python Blue first, then complementary colors
colors = ["#306998", "#FFD43B", "#4CAF50", "#E91E63"]

# Create stacked bars manually for proper stacking
bottom = np.zeros(len(categories))
bars_list = []

for idx, comp in enumerate(components):
    bars = ax.bar(
        categories, df_wide[comp], bottom=bottom, label=comp, color=colors[idx], edgecolor="white", linewidth=1.5
    )
    bars_list.append(bars)
    bottom += df_wide[comp].values

# Add total labels above each bar stack
for i, total in enumerate(totals):
    ax.annotate(
        f"${total:.0f}M",
        xy=(i, total),
        xytext=(0, 12),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=18,
        fontweight="bold",
        color="#333333",
    )

# Styling
ax.set_xlabel("Quarter", fontsize=20)
ax.set_ylabel("Revenue (Millions USD)", fontsize=20)
ax.set_title("bar-stacked-labeled · seaborn · pyplots.ai", fontsize=24, pad=20)
ax.tick_params(axis="both", labelsize=16)

# Legend
ax.legend(title="Product Category", title_fontsize=16, fontsize=14, loc="upper left", framealpha=0.9)

# Grid - subtle horizontal only
ax.yaxis.grid(True, alpha=0.3, linestyle="--")
ax.set_axisbelow(True)

# Adjust y-axis limit to accommodate labels
ax.set_ylim(0, max(totals) * 1.15)

# Remove top and right spines for cleaner look
sns.despine(ax=ax)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
