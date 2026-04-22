""" pyplots.ai
bar-error: Bar Chart with Error Bars
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-27
"""

import matplotlib.pyplot as plt
import numpy as np


# Data: A/B test results comparing feature variants with confidence intervals
np.random.seed(42)
categories = ["Control", "Variant A", "Variant B", "Variant C", "Variant D"]
values = [12.3, 15.8, 14.2, 18.5, 11.7]  # Conversion rates (%)
errors = [1.2, 2.1, 1.5, 2.8, 1.0]  # 95% CI half-widths

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Bar positions
x = np.arange(len(categories))
bar_width = 0.6

# Plot bars with error bars
bars = ax.bar(x, values, bar_width, color="#306998", edgecolor="#1e4466", linewidth=2)
ax.errorbar(x, values, yerr=errors, fmt="none", ecolor="#1e4466", elinewidth=3, capsize=10, capthick=3)

# Labels and styling
ax.set_xlabel("Test Group", fontsize=20)
ax.set_ylabel("Conversion Rate (%)", fontsize=20)
ax.set_title("bar-error · matplotlib · pyplots.ai", fontsize=24)
ax.set_xticks(x)
ax.set_xticklabels(categories, fontsize=16)
ax.tick_params(axis="y", labelsize=16)

# Add annotation explaining error bars
ax.annotate(
    "Error bars: 95% CI",
    xy=(0.98, 0.02),
    xycoords="axes fraction",
    fontsize=14,
    ha="right",
    va="bottom",
    bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "gray", "alpha": 0.8},
)

# Grid and layout
ax.grid(True, axis="y", alpha=0.3, linestyle="--")
ax.set_ylim(0, max(values) * 1.3)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
