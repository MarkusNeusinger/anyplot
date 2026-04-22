""" pyplots.ai
contour-decision-boundary: Decision Boundary Classifier Visualization
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import matplotlib.pyplot as plt
import numpy as np
from sklearn.datasets import make_moons
from sklearn.svm import SVC


# Data - generate synthetic two-moon classification data
np.random.seed(42)
X, y = make_moons(n_samples=200, noise=0.25, random_state=42)

# Train a classifier (SVM with RBF kernel)
classifier = SVC(kernel="rbf", C=1.0, gamma="scale")
classifier.fit(X, y)

# Create mesh grid for decision boundary
x_min, x_max = X[:, 0].min() - 0.5, X[:, 0].max() + 0.5
y_min, y_max = X[:, 1].min() - 0.5, X[:, 1].max() + 0.5
xx, yy = np.meshgrid(np.linspace(x_min, x_max, 200), np.linspace(y_min, y_max, 200))

# Predict class for each point in mesh
Z = classifier.predict(np.c_[xx.ravel(), yy.ravel()])
Z = Z.reshape(xx.shape)

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Plot decision regions with contourf
ax.contourf(xx, yy, Z, alpha=0.4, cmap="coolwarm", levels=[-0.5, 0.5, 1.5])

# Add decision boundary line
ax.contour(xx, yy, Z, colors="white", linewidths=2, levels=[0.5])

# Identify correctly and incorrectly classified points
predictions = classifier.predict(X)
correct = predictions == y
incorrect = ~correct

# Plot training points - correctly classified
class_0_correct = (y == 0) & correct
class_1_correct = (y == 1) & correct
ax.scatter(
    X[class_0_correct, 0],
    X[class_0_correct, 1],
    c="#306998",
    s=150,
    alpha=0.9,
    edgecolors="white",
    linewidths=2,
    marker="o",
    label="Class A (correct)",
    zorder=3,
)
ax.scatter(
    X[class_1_correct, 0],
    X[class_1_correct, 1],
    c="#FFD43B",
    s=150,
    alpha=0.9,
    edgecolors="black",
    linewidths=2,
    marker="o",
    label="Class B (correct)",
    zorder=3,
)

# Plot incorrectly classified points with X marker
if np.any(incorrect):
    class_0_incorrect = (y == 0) & incorrect
    class_1_incorrect = (y == 1) & incorrect
    if np.any(class_0_incorrect):
        ax.scatter(
            X[class_0_incorrect, 0],
            X[class_0_incorrect, 1],
            c="#306998",
            s=200,
            alpha=0.9,
            edgecolors="red",
            linewidths=3,
            marker="X",
            label="Class A (misclassified)",
            zorder=4,
        )
    if np.any(class_1_incorrect):
        ax.scatter(
            X[class_1_incorrect, 0],
            X[class_1_incorrect, 1],
            c="#FFD43B",
            s=200,
            alpha=0.9,
            edgecolors="red",
            linewidths=3,
            marker="X",
            label="Class B (misclassified)",
            zorder=4,
        )

# Labels and styling
ax.set_xlabel("Feature X1", fontsize=20)
ax.set_ylabel("Feature X2", fontsize=20)
ax.set_title("contour-decision-boundary · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.legend(fontsize=14, loc="upper left", framealpha=0.9)
ax.grid(True, alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
