""" pyplots.ai
errorbar-basic: Basic Error Bar Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data - experimental measurements with error ranges
np.random.seed(42)
categories = ["Control", "Treatment A", "Treatment B", "Treatment C", "Treatment D", "Treatment E"]
means = [45.2, 52.8, 61.3, 48.7, 57.4, 43.1]
errors = [4.5, 6.2, 5.8, 7.1, 4.9, 5.5]

df = pd.DataFrame({"Treatment": categories, "Response": means, "Error": errors})

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))
sns.set_style("whitegrid")

# Plot using seaborn pointplot with custom error bars via matplotlib
# Seaborn's barplot/pointplot can handle error bars; using pointplot for clarity
colors = ["#306998", "#FFD43B", "#306998", "#FFD43B", "#306998", "#FFD43B"]

# Use seaborn's barplot with error bars
bars = sns.barplot(
    data=df,
    x="Treatment",
    y="Response",
    hue="Treatment",
    palette=colors,
    legend=False,
    ax=ax,
    edgecolor="black",
    linewidth=1.5,
)

# Add error bars manually for control over appearance
x_positions = range(len(categories))
ax.errorbar(
    x_positions, means, yerr=errors, fmt="none", color="black", capsize=8, capthick=2.5, elinewidth=2.5, zorder=5
)

# Labels and styling
ax.set_xlabel("Treatment Group", fontsize=20)
ax.set_ylabel("Response Value (units)", fontsize=20)
ax.set_title("errorbar-basic · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--", axis="y")
ax.set_axisbelow(True)

# Adjust y-axis to give room for error bars
ax.set_ylim(0, max([m + e for m, e in zip(means, errors, strict=True)]) * 1.15)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
