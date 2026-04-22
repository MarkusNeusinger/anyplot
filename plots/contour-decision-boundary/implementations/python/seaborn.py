""" pyplots.ai
contour-decision-boundary: Decision Boundary Classifier Visualization
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-31
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from sklearn.datasets import make_moons
from sklearn.svm import SVC


# Data - Generate synthetic 2D classification data
np.random.seed(42)
X, y = make_moons(n_samples=200, noise=0.25, random_state=42)
X1 = X[:, 0]
X2 = X[:, 1]

# Train classifier
clf = SVC(kernel="rbf", C=1.0, gamma="scale")
clf.fit(X, y)

# Create mesh grid for decision boundary
x1_min, x1_max = X1.min() - 0.5, X1.max() + 0.5
x2_min, x2_max = X2.min() - 0.5, X2.max() + 0.5
xx1, xx2 = np.meshgrid(np.linspace(x1_min, x1_max, 200), np.linspace(x2_min, x2_max, 200))
grid_points = np.c_[xx1.ravel(), xx2.ravel()]

# Predict on mesh grid
Z = clf.predict(grid_points).reshape(xx1.shape)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))
sns.set_style("whitegrid")

# Plot decision regions as filled contours
cmap_light = sns.color_palette(["#306998", "#FFD43B"], as_cmap=False)
contour = ax.contourf(xx1, xx2, Z, levels=[-0.5, 0.5, 1.5], colors=["#306998", "#FFD43B"], alpha=0.4)

# Plot decision boundary line
ax.contour(xx1, xx2, Z, levels=[0.5], colors=["#1a3d5c"], linewidths=3)

# Overlay training points with seaborn scatterplot
# Create separate masks for correct and incorrect predictions
predictions = clf.predict(X)
correct_mask = predictions == y
incorrect_mask = ~correct_mask

# Correctly classified points - filled markers
scatter_correct = sns.scatterplot(
    x=X1[correct_mask],
    y=X2[correct_mask],
    hue=y[correct_mask],
    palette=["#306998", "#FFD43B"],
    s=200,
    edgecolor="white",
    linewidth=1.5,
    alpha=0.9,
    ax=ax,
    legend=False,
)

# Incorrectly classified points - with red edge
if np.any(incorrect_mask):
    sns.scatterplot(
        x=X1[incorrect_mask],
        y=X2[incorrect_mask],
        hue=y[incorrect_mask],
        palette=["#306998", "#FFD43B"],
        s=250,
        edgecolor="#d62728",
        linewidth=3,
        alpha=0.9,
        ax=ax,
        marker="X",
        legend=False,
    )

# Create legend manually for classes
legend_elements = [
    Patch(facecolor="#306998", alpha=0.4, edgecolor="#1a3d5c", label="Class 0 Region"),
    Patch(facecolor="#FFD43B", alpha=0.4, edgecolor="#1a3d5c", label="Class 1 Region"),
    Line2D(
        [0],
        [0],
        marker="o",
        color="w",
        markerfacecolor="#306998",
        markersize=14,
        markeredgecolor="white",
        markeredgewidth=1.5,
        label="Class 0 (correct)",
    ),
    Line2D(
        [0],
        [0],
        marker="o",
        color="w",
        markerfacecolor="#FFD43B",
        markersize=14,
        markeredgecolor="white",
        markeredgewidth=1.5,
        label="Class 1 (correct)",
    ),
    Line2D(
        [0],
        [0],
        marker="X",
        color="w",
        markerfacecolor="gray",
        markersize=14,
        markeredgecolor="#d62728",
        markeredgewidth=2,
        label="Misclassified",
    ),
]
ax.legend(handles=legend_elements, loc="upper right", fontsize=14, framealpha=0.9)

# Labels and styling
ax.set_xlabel("Feature X1", fontsize=20)
ax.set_ylabel("Feature X2", fontsize=20)
ax.set_title("contour-decision-boundary · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

# Calculate and display accuracy
accuracy = np.mean(predictions == y) * 100
ax.text(
    0.02,
    0.98,
    f"SVM Accuracy: {accuracy:.1f}%",
    transform=ax.transAxes,
    fontsize=16,
    verticalalignment="top",
    fontweight="bold",
    bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.8},
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
