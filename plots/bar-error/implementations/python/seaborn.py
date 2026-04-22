""" pyplots.ai
bar-error: Bar Chart with Error Bars
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-27
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data - A/B test results with confidence intervals
np.random.seed(42)

categories = ["Control", "Variant A", "Variant B", "Variant C", "Variant D", "Variant E"]
# Conversion rates (percentage)
values = [4.2, 5.1, 4.8, 6.3, 5.5, 4.0]
# 95% CI error margins (asymmetric for realistic percentage data)
errors_lower = [0.3, 0.4, 0.35, 0.5, 0.45, 0.25]
errors_upper = [0.35, 0.45, 0.4, 0.55, 0.5, 0.3]

df = pd.DataFrame(
    {"Category": categories, "Conversion Rate (%)": values, "Error Lower": errors_lower, "Error Upper": errors_upper}
)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Create bar plot using seaborn
colors = ["#306998", "#FFD43B", "#306998", "#FFD43B", "#306998", "#FFD43B"]
sns.barplot(
    data=df,
    x="Category",
    y="Conversion Rate (%)",
    hue="Category",
    palette=colors,
    legend=False,
    ax=ax,
    edgecolor="black",
    linewidth=1.5,
    width=0.7,
)

# Add error bars with caps
x_positions = np.arange(len(categories))
ax.errorbar(
    x_positions,
    values,
    yerr=[errors_lower, errors_upper],
    fmt="none",
    ecolor="black",
    elinewidth=2.5,
    capsize=12,
    capthick=2.5,
)

# Styling for large canvas (4800x2700 px at dpi=300)
ax.set_xlabel("Test Group", fontsize=20)
ax.set_ylabel("Conversion Rate (%)", fontsize=20)
ax.set_title("bar-error · seaborn · pyplots.ai", fontsize=24, fontweight="bold")
ax.tick_params(axis="both", labelsize=16)

# Add annotation explaining error bars
ax.annotate(
    "Error bars: 95% CI",
    xy=(0.98, 0.95),
    xycoords="axes fraction",
    fontsize=14,
    ha="right",
    va="top",
    bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "gray", "alpha": 0.8},
)

# Subtle grid
ax.yaxis.grid(True, alpha=0.3, linestyle="--")
ax.set_axisbelow(True)

# Set y-axis to start from 0 for proper bar comparison
ax.set_ylim(0, max(values) * 1.25)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
