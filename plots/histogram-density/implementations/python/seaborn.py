""" pyplots.ai
histogram-density: Density Histogram
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 94/100 | Created: 2025-12-29
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Data - Generate realistic test scores with bimodal distribution
np.random.seed(42)
# Create bimodal distribution (two groups of students with different means)
group1 = np.random.normal(loc=65, scale=10, size=300)  # Average performers
group2 = np.random.normal(loc=85, scale=5, size=200)  # High performers
test_scores = np.concatenate([group1, group2])
# Clip to realistic test score range
test_scores = np.clip(test_scores, 0, 100)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Plot density histogram
sns.histplot(
    test_scores,
    stat="density",
    bins=25,
    color="#306998",
    alpha=0.7,
    edgecolor="white",
    linewidth=1.5,
    ax=ax,
    kde=False,
    label="Density Histogram",
)

# Add KDE overlay for smooth density estimate (seaborn feature)
sns.kdeplot(test_scores, ax=ax, color="#FFD43B", linewidth=4, label="Kernel Density Estimate (KDE)")

# Style and labels
ax.set_xlabel("Test Score (points)", fontsize=20)
ax.set_ylabel("Probability Density", fontsize=20)
ax.set_title("histogram-density · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--")

# Legend
ax.legend(fontsize=14, loc="upper left")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
