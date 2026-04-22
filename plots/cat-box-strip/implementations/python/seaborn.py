""" pyplots.ai
cat-box-strip: Box Plot with Strip Overlay
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data - product quality scores across manufacturing batches
np.random.seed(42)

# Create groups with different distributions to show boxplot features
batch_a = np.random.normal(75, 8, 40)  # Centered, moderate spread
batch_b = np.random.normal(82, 5, 35)  # Higher center, tight spread
batch_c = np.concatenate(
    [
        np.random.normal(68, 6, 30),  # Main distribution
        [45, 48, 95, 97],  # Outliers
    ]
)
batch_d = np.random.normal(70, 12, 45)  # Wide spread

# Combine into DataFrame
df = pd.DataFrame(
    {
        "Batch": ["Batch A"] * len(batch_a)
        + ["Batch B"] * len(batch_b)
        + ["Batch C"] * len(batch_c)
        + ["Batch D"] * len(batch_d),
        "Quality Score": np.concatenate([batch_a, batch_b, batch_c, batch_d]),
    }
)

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Box plot with boxes in Python Blue
sns.boxplot(
    data=df,
    x="Batch",
    y="Quality Score",
    hue="Batch",
    palette=["#306998"] * 4,
    width=0.5,
    linewidth=2,
    fliersize=0,  # Hide box plot outliers (strip will show them)
    legend=False,
    ax=ax,
)

# Strip plot overlay with Python Yellow
sns.stripplot(
    data=df,
    x="Batch",
    y="Quality Score",
    color="#FFD43B",
    size=10,
    alpha=0.7,
    jitter=0.2,
    edgecolor="#333333",
    linewidth=0.5,
    ax=ax,
)

# Styling
ax.set_title("cat-box-strip · seaborn · pyplots.ai", fontsize=24)
ax.set_xlabel("Manufacturing Batch", fontsize=20)
ax.set_ylabel("Quality Score (points)", fontsize=20)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, axis="y", alpha=0.3, linestyle="--")

# Set y-axis limits with some padding
ax.set_ylim(35, 105)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
