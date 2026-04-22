""" pyplots.ai
lollipop-basic: Basic Lollipop Chart
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


# Data - Product sales by category, sorted by value
categories = [
    "Electronics",
    "Clothing",
    "Home & Garden",
    "Sports",
    "Books",
    "Toys",
    "Beauty",
    "Automotive",
    "Food & Grocery",
    "Health",
]
values = [85000, 72000, 58000, 45000, 42000, 38000, 35000, 28000, 25000, 18000]

# Create DataFrame and sort by value (ascending for horizontal lollipop)
df = pd.DataFrame({"category": categories, "value": values})
df = df.sort_values("value", ascending=True)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Draw stems (thin lines from baseline to marker)
ax.hlines(y=df["category"], xmin=0, xmax=df["value"], color="#306998", linewidth=2.5, alpha=0.8)

# Draw markers (circular dots at data values) using seaborn
sns.scatterplot(
    data=df, x="value", y="category", s=400, color="#FFD43B", edgecolor="#306998", linewidth=2, ax=ax, zorder=3
)

# Styling
ax.set_xlabel("Sales ($)", fontsize=20)
ax.set_ylabel("Product Category", fontsize=20)
ax.set_title("lollipop-basic · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.set_xlim(0, None)
ax.grid(True, axis="x", alpha=0.3, linestyle="--")

# Remove top and right spines for cleaner look
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
