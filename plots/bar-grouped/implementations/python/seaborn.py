""" pyplots.ai
bar-grouped: Grouped Bar Chart
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 96/100 | Created: 2025-12-24
"""

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


# Data: Quarterly sales by product line (in thousands $)
data = {
    "Quarter": ["Q1", "Q1", "Q1", "Q2", "Q2", "Q2", "Q3", "Q3", "Q3", "Q4", "Q4", "Q4"],
    "Product": ["Electronics", "Clothing", "Home & Garden"] * 4,
    "Sales": [245, 180, 120, 280, 195, 145, 310, 210, 165, 395, 245, 190],
}
df = pd.DataFrame(data)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Plot grouped bars with seaborn
colors = ["#306998", "#FFD43B", "#4ECDC4"]  # Python Blue, Python Yellow, Teal
sns.barplot(data=df, x="Quarter", y="Sales", hue="Product", palette=colors, edgecolor="white", linewidth=1.5, ax=ax)

# Styling
ax.set_xlabel("Quarter", fontsize=20)
ax.set_ylabel("Sales (thousands $)", fontsize=20)
ax.set_title("bar-grouped · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, axis="y", alpha=0.3, linestyle="--")

# Legend
ax.legend(title="Product Line", fontsize=14, title_fontsize=16, loc="upper left")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
