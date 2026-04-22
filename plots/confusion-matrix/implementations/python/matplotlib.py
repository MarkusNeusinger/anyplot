""" pyplots.ai
confusion-matrix: Confusion Matrix Heatmap
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-26
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Multi-class classification results (4 classes)
np.random.seed(42)

class_names = ["Cat", "Dog", "Bird", "Fish"]
n_classes = len(class_names)

# Create realistic confusion matrix with some misclassifications
# Diagonal has highest values (correct predictions)
# Off-diagonal shows realistic confusion patterns
confusion_matrix = np.array(
    [
        [85, 8, 4, 3],  # Cat: mostly correct, some confused with Dog
        [12, 78, 6, 4],  # Dog: mostly correct, some confused with Cat
        [3, 5, 88, 4],  # Bird: high accuracy
        [2, 3, 5, 90],  # Fish: highest accuracy
    ]
)

# Create plot (square format for symmetric matrix)
fig, ax = plt.subplots(figsize=(12, 12))

# Create heatmap with Blues colormap
im = ax.imshow(confusion_matrix, cmap="Blues", aspect="equal")

# Add colorbar
cbar = ax.figure.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
cbar.ax.tick_params(labelsize=16)
cbar.set_label("Count", fontsize=18)

# Set ticks and labels
ax.set_xticks(np.arange(n_classes))
ax.set_yticks(np.arange(n_classes))
ax.set_xticklabels(class_names, fontsize=18)
ax.set_yticklabels(class_names, fontsize=18)

# Rotate x-axis labels for better readability
plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

# Annotate cells with counts and percentages
for i in range(n_classes):
    for j in range(n_classes):
        count = confusion_matrix[i, j]
        row_total = confusion_matrix[i, :].sum()
        percentage = count / row_total * 100

        # Choose text color based on background intensity
        text_color = "white" if count > confusion_matrix.max() * 0.5 else "black"

        # Display count and percentage
        text = ax.text(
            j,
            i,
            f"{count}\n({percentage:.1f}%)",
            ha="center",
            va="center",
            color=text_color,
            fontsize=16,
            fontweight="bold",
        )

# Labels and title
ax.set_xlabel("Predicted Label", fontsize=20)
ax.set_ylabel("True Label", fontsize=20)
ax.set_title("confusion-matrix · matplotlib · pyplots.ai", fontsize=24, pad=20)

# Add subtle grid lines between cells
ax.set_xticks(np.arange(n_classes + 1) - 0.5, minor=True)
ax.set_yticks(np.arange(n_classes + 1) - 0.5, minor=True)
ax.grid(which="minor", color="white", linestyle="-", linewidth=2)
ax.tick_params(which="minor", bottom=False, left=False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
