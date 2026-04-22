""" pyplots.ai
confusion-matrix: Confusion Matrix Heatmap
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Data - Multi-class classification results for a sentiment analysis model
class_names = ["Negative", "Neutral", "Positive", "Mixed"]

# Create realistic confusion matrix with strong diagonal (good model)
# but with some systematic confusion patterns
confusion_matrix = np.array(
    [
        [156, 12, 5, 8],  # Negative: mostly correct, some confused with Neutral
        [18, 142, 15, 10],  # Neutral: hardest to classify, confused with all
        [3, 8, 168, 6],  # Positive: good accuracy
        [11, 14, 9, 125],  # Mixed: often confused with Neutral
    ]
)

# Create figure (square format for symmetric matrix)
fig, ax = plt.subplots(figsize=(12, 12))

# Create heatmap with annotations
sns.heatmap(
    confusion_matrix,
    annot=True,
    fmt="d",
    cmap="Blues",
    xticklabels=class_names,
    yticklabels=class_names,
    square=True,
    linewidths=2,
    linecolor="white",
    cbar_kws={"shrink": 0.8, "label": "Count"},
    annot_kws={"size": 20, "weight": "bold"},
    ax=ax,
)

# Style the colorbar
cbar = ax.collections[0].colorbar
cbar.ax.tick_params(labelsize=16)
cbar.ax.set_ylabel("Count", fontsize=18, labelpad=15)

# Labels and title
ax.set_xlabel("Predicted Label", fontsize=22, labelpad=15)
ax.set_ylabel("True Label", fontsize=22, labelpad=15)
ax.set_title("Sentiment Analysis Model · confusion-matrix · seaborn · pyplots.ai", fontsize=24, pad=20)

# Style tick labels
ax.tick_params(axis="both", labelsize=18)

# Rotate x-axis labels for better readability
plt.xticks(rotation=45, ha="right")
plt.yticks(rotation=0)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
