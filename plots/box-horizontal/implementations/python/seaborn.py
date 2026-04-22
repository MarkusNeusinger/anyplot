""" pyplots.ai
box-horizontal: Horizontal Box Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data - response times by service type (with intentional outliers and different distributions)
np.random.seed(42)

categories = ["Database Query", "API Gateway", "File Upload", "Authentication", "Cache Lookup"]

data = []
# Database Query - moderate spread with some outliers
data.extend(
    [
        {"Service Type": "Database Query", "Response Time (ms)": v}
        for v in np.concatenate(
            [
                np.random.normal(150, 40, 80),
                np.random.normal(350, 20, 5),  # outliers
            ]
        )
    ]
)

# API Gateway - tight distribution
data.extend([{"Service Type": "API Gateway", "Response Time (ms)": v} for v in np.random.normal(80, 15, 85)])

# File Upload - wide spread with high values
data.extend(
    [
        {"Service Type": "File Upload", "Response Time (ms)": v}
        for v in np.concatenate(
            [
                np.random.normal(500, 150, 75),
                np.random.normal(900, 50, 10),  # outliers
            ]
        )
    ]
)

# Authentication - moderate values
data.extend([{"Service Type": "Authentication", "Response Time (ms)": v} for v in np.random.normal(120, 30, 85)])

# Cache Lookup - very fast, tight distribution
data.extend([{"Service Type": "Cache Lookup", "Response Time (ms)": v} for v in np.random.normal(25, 8, 90)])

df = pd.DataFrame(data)

# Sort categories by median for easier comparison
category_order = df.groupby("Service Type")["Response Time (ms)"].median().sort_values().index.tolist()

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Horizontal box plot
sns.boxplot(
    data=df,
    x="Response Time (ms)",
    y="Service Type",
    hue="Service Type",
    order=category_order,
    palette=["#306998", "#FFD43B", "#306998", "#FFD43B", "#306998"],
    linewidth=2,
    width=0.6,
    flierprops={"marker": "o", "markersize": 8, "alpha": 0.6},
    legend=False,
    ax=ax,
)

# Labels and styling
ax.set_xlabel("Response Time (ms)", fontsize=20)
ax.set_ylabel("Service Type", fontsize=20)
ax.set_title("box-horizontal · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, axis="x", alpha=0.3, linestyle="--")

# Adjust layout
plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
