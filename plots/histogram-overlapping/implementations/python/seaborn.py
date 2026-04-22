""" pyplots.ai
histogram-overlapping: Overlapping Histograms
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 96/100 | Created: 2025-12-25
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Data - employee response times (ms) by department
np.random.seed(42)
engineering = np.random.normal(450, 80, 200)  # Fast responders
marketing = np.random.normal(520, 100, 180)  # Slightly slower, more variable
sales = np.random.normal(480, 60, 160)  # Consistent mid-range

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Plot overlapping histograms with seaborn
sns.histplot(
    engineering, bins=25, alpha=0.5, color="#306998", label="Engineering", edgecolor="white", linewidth=0.5, ax=ax
)
sns.histplot(marketing, bins=25, alpha=0.5, color="#FFD43B", label="Marketing", edgecolor="white", linewidth=0.5, ax=ax)
sns.histplot(sales, bins=25, alpha=0.5, color="#E57373", label="Sales", edgecolor="white", linewidth=0.5, ax=ax)

# Labels and styling
ax.set_xlabel("Response Time (ms)", fontsize=20)
ax.set_ylabel("Count", fontsize=20)
ax.set_title("histogram-overlapping · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.legend(fontsize=16, loc="upper right")
ax.grid(True, alpha=0.3, linestyle="--", axis="y")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
