""" pyplots.ai
violin-box: Violin Plot with Embedded Box Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 95/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data - Product quality scores across manufacturing batches
np.random.seed(42)

# Create varied distributions for each batch to show different shapes
batch_a = np.random.normal(75, 8, 120)  # Normal, centered around 75
batch_b = np.concatenate([np.random.normal(60, 5, 60), np.random.normal(80, 5, 60)])  # Bimodal
batch_c = np.random.exponential(10, 120) + 50  # Right-skewed
batch_d = 95 - np.random.exponential(10, 120)  # Left-skewed

# Combine into DataFrame
df = pd.DataFrame(
    {
        "Quality Score": np.concatenate([batch_a, batch_b, batch_c, batch_d]),
        "Batch": ["Batch A"] * 120 + ["Batch B"] * 120 + ["Batch C"] * 120 + ["Batch D"] * 120,
    }
)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Create violin plot with embedded box plot using inner='box'
sns.violinplot(
    data=df,
    x="Batch",
    y="Quality Score",
    hue="Batch",
    palette=["#306998", "#FFD43B", "#4A90A4", "#E8A838"],
    inner="box",
    linewidth=2,
    saturation=0.9,
    legend=False,
    ax=ax,
)

# Styling
ax.set_title("violin-box · seaborn · pyplots.ai", fontsize=24, fontweight="bold", pad=20)
ax.set_xlabel("Manufacturing Batch", fontsize=20)
ax.set_ylabel("Quality Score (0-100)", fontsize=20)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--", axis="y")

# Set y-axis limits for better visibility
ax.set_ylim(30, 100)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
