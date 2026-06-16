""" anyplot.ai
contour-decision-boundary: Decision Boundary Classifier Visualization
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-16
"""

import os

import matplotlib.pyplot as plt
import numpy as np
from sklearn.datasets import make_moons
from sklearn.svm import SVC


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

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

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Plot decision regions with contourf
ax.contourf(xx, yy, Z, alpha=0.3, colors=[IMPRINT[0], IMPRINT[1]], levels=[-0.5, 0.5, 1.5])

# Add decision boundary line
ax.contour(xx, yy, Z, colors=INK_SOFT, linewidths=2, levels=[0.5])

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
    c=IMPRINT[0],
    s=150,
    alpha=0.9,
    edgecolors=PAGE_BG,
    linewidths=2,
    marker="o",
    label="Class 0 (correct)",
    zorder=3,
)
ax.scatter(
    X[class_1_correct, 0],
    X[class_1_correct, 1],
    c=IMPRINT[1],
    s=150,
    alpha=0.9,
    edgecolors=PAGE_BG,
    linewidths=2,
    marker="o",
    label="Class 1 (correct)",
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
            c=IMPRINT[0],
            s=200,
            alpha=0.9,
            edgecolors=INK_SOFT,
            linewidths=3,
            marker="X",
            label="Class 0 (misclassified)",
            zorder=4,
        )
    if np.any(class_1_incorrect):
        ax.scatter(
            X[class_1_incorrect, 0],
            X[class_1_incorrect, 1],
            c=IMPRINT[1],
            s=200,
            alpha=0.9,
            edgecolors=INK_SOFT,
            linewidths=3,
            marker="X",
            label="Class 1 (misclassified)",
            zorder=4,
        )

# Style
ax.set_xlabel("Feature X1", fontsize=20, color=INK)
ax.set_ylabel("Feature X2", fontsize=20, color=INK)
ax.set_title("contour-decision-boundary · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
ax.grid(True, alpha=0.1, linewidth=0.8, color=INK)

leg = ax.legend(fontsize=14, loc="upper left")
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    plt.setp(leg.get_texts(), color=INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
