""" pyplots.ai
bar-basic: Basic Bar Chart
Library: seaborn 0.13.2 | Python 3.14
Quality: 89/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


# Data - Product sales by category with closely-spaced values for comparison nuance
data = pd.DataFrame(
    {
        "category": ["Electronics", "Groceries", "Clothing", "Sports", "Toys", "Home & Garden", "Automotive", "Books"],
        "sales": [218, 195, 164, 142, 112, 89, 58, 41],
    }
)

# Assign colors directly — Python Blue for top, muted grey for bottom, lighter blue for rest
colors = ["#306998"] + ["#7BAFD4"] * 6 + ["#A3BFCF"]

# Create plot (4800x2700 px)
sns.set_context("talk", font_scale=1.1)
sns.set_style("whitegrid", {"axes.grid": False})
fig, ax = plt.subplots(figsize=(16, 9))
sns.barplot(data=data, x="category", y="sales", palette=colors, hue="category", legend=False, width=0.7, ax=ax)

# Value labels on bars
for container in ax.containers:
    ax.bar_label(container, fmt="%d", fontsize=15, fontweight="bold", padding=4)

# Annotate top performer — positioned to the right of the bar
ax.annotate(
    f"Top seller\n{data.iloc[0]['sales']} units",
    xy=(0, data.iloc[0]["sales"]),
    xytext=(1.6, data.iloc[0]["sales"] + 8),
    fontsize=15,
    fontweight="bold",
    color="#1A3A5C",
    arrowprops={"arrowstyle": "->", "color": "#1A3A5C", "lw": 2},
    ha="left",
    va="bottom",
)

# Annotate bottom performer — compact positioning to avoid excess whitespace
ax.annotate(
    f"Lowest\n{data.iloc[-1]['sales']} units",
    xy=(7, data.iloc[-1]["sales"] + 14),
    xytext=(5.8, data.iloc[-1]["sales"] + 70),
    fontsize=13,
    color="#6B7B8D",
    arrowprops={"arrowstyle": "->", "color": "#6B7B8D", "lw": 1.5},
    ha="center",
    va="bottom",
)

# Labels and title
ax.set_xlabel("Product Category", fontsize=20)
ax.set_ylabel("Sales (units)", fontsize=20)
ax.set_title("bar-basic · seaborn · pyplots.ai", fontsize=24, fontweight="medium", pad=16)
ax.tick_params(axis="both", labelsize=16)

# Subtle y-axis grid and clean spines
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8)
ax.set_axisbelow(True)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Y-axis room for annotations and value labels
ax.set_ylim(0, data["sales"].max() * 1.18)

fig.subplots_adjust(left=0.08, right=0.96, top=0.92, bottom=0.10)
plt.savefig("plot.png", dpi=300)
