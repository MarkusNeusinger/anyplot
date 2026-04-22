""" pyplots.ai
bar-stacked-percent: 100% Stacked Bar Chart
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data: Market share by quarter for tech companies
np.random.seed(42)
quarters = ["Q1 2023", "Q2 2023", "Q3 2023", "Q4 2023", "Q1 2024", "Q2 2024"]
companies = ["Company A", "Company B", "Company C", "Company D"]

# Create realistic market share data with variation
data = {
    "Company A": [35, 33, 30, 28, 26, 24],
    "Company B": [25, 27, 28, 30, 32, 34],
    "Company C": [22, 22, 24, 25, 26, 27],
    "Company D": [18, 18, 18, 17, 16, 15],
}

df = pd.DataFrame(data, index=quarters)

# Normalize to percentages
df_percent = df.div(df.sum(axis=1), axis=0) * 100

# Create cumulative sums for stacking
df_cumsum = df_percent.cumsum(axis=1)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Colors - Python Blue, Python Yellow, and colorblind-safe additions
colors = ["#306998", "#FFD43B", "#4ECDC4", "#E76F51"]

# Plot stacked bars by drawing each segment
x = np.arange(len(quarters))
bar_width = 0.6

# Draw bars from bottom to top
for i, company in enumerate(companies):
    bottom = df_cumsum.iloc[:, i - 1].values if i > 0 else np.zeros(len(quarters))
    heights = df_percent[company].values
    ax.bar(
        x, heights, bar_width, bottom=bottom, label=company, color=colors[i], edgecolor="white", linewidth=1.5
    )

    # Add percentage labels inside segments (only if segment is large enough)
    for j, (h, b) in enumerate(zip(heights, bottom, strict=True)):
        if h > 8:  # Only label if segment is > 8%
            ax.text(
                x[j],
                b + h / 2,
                f"{h:.0f}%",
                ha="center",
                va="center",
                fontsize=14,
                fontweight="bold",
                color="white" if colors[i] != "#FFD43B" else "#333333",
            )

# Styling
ax.set_xlabel("Quarter", fontsize=20)
ax.set_ylabel("Market Share (%)", fontsize=20)
ax.set_title("bar-stacked-percent · seaborn · pyplots.ai", fontsize=24)
ax.set_xticks(x)
ax.set_xticklabels(quarters, fontsize=16)
ax.tick_params(axis="y", labelsize=16)
ax.set_ylim(0, 100)
ax.set_yticks([0, 20, 40, 60, 80, 100])

# Legend
ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), fontsize=14, frameon=True, edgecolor="#cccccc")

# Grid
ax.yaxis.grid(True, alpha=0.3, linestyle="--")
ax.set_axisbelow(True)

# Remove top and right spines
sns.despine()

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
