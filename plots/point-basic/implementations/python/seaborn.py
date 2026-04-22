""" pyplots.ai
point-basic: Point Estimate Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data: Product satisfaction ratings with confidence intervals
np.random.seed(42)
categories = ["Product A", "Product B", "Product C", "Product D", "Product E", "Product F"]
estimates = [7.2, 6.5, 8.1, 5.9, 7.8, 6.2]
# Varying confidence interval widths to show different uncertainty levels
ci_widths = [0.8, 1.2, 0.5, 1.5, 0.7, 1.1]
lower = [e - w for e, w in zip(estimates, ci_widths, strict=True)]
upper = [e + w for e, w in zip(estimates, ci_widths, strict=True)]

df = pd.DataFrame({"Product": categories, "Satisfaction": estimates, "Lower": lower, "Upper": upper})

# Create plot (4800x2700 px at 300 dpi = 16x9 inches)
fig, ax = plt.subplots(figsize=(16, 9))

# Plot points using seaborn pointplot
# Using horizontal orientation for better label readability
sns.pointplot(
    data=df,
    x="Satisfaction",
    y="Product",
    orient="h",
    color="#306998",
    markers="o",
    markersize=15,
    linestyle="none",  # Remove connecting lines between points
    err_kws={"linewidth": 0},  # We'll draw custom error bars for more control
    ax=ax,
)

# Draw error bars with caps manually for better control
for i, (_, row) in enumerate(df.iterrows()):
    ax.errorbar(
        x=row["Satisfaction"],
        y=i,
        xerr=[[row["Satisfaction"] - row["Lower"]], [row["Upper"] - row["Satisfaction"]]],
        fmt="none",
        color="#306998",
        capsize=8,
        capthick=3,
        elinewidth=3,
    )

# Add reference line at overall mean
overall_mean = np.mean(estimates)
ax.axvline(
    x=overall_mean,
    color="#FFD43B",
    linestyle="--",
    linewidth=2.5,
    alpha=0.8,
    label=f"Overall Mean ({overall_mean:.1f})",
)

# Labels and styling (scaled for 4800x2700)
ax.set_xlabel("Satisfaction Score (1-10)", fontsize=20)
ax.set_ylabel("Product", fontsize=20)
ax.set_title("point-basic · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--", axis="x")

# Legend
ax.legend(fontsize=16, loc="lower right")

# Set x-axis limits to show context
ax.set_xlim(3, 10)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
