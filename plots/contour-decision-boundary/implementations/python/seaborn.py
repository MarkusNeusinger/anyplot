""" anyplot.ai
contour-decision-boundary: Decision Boundary Classifier Visualization
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-16
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from sklearn.datasets import make_moons
from sklearn.svm import SVC


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

BRAND = "#009E73"
ALT_COLOR = "#C475FD"

np.random.seed(42)
X, y = make_moons(n_samples=200, noise=0.25, random_state=42)
X1 = X[:, 0]
X2 = X[:, 1]

clf = SVC(kernel="rbf", C=1.0, gamma="scale")
clf.fit(X, y)

x1_min, x1_max = X1.min() - 0.5, X1.max() + 0.5
x2_min, x2_max = X2.min() - 0.5, X2.max() + 0.5
xx1, xx2 = np.meshgrid(np.linspace(x1_min, x1_max, 200), np.linspace(x2_min, x2_max, 200))
grid_points = np.c_[xx1.ravel(), xx2.ravel()]

Z = clf.predict(grid_points).reshape(xx1.shape)

fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

contour = ax.contourf(xx1, xx2, Z, levels=[-0.5, 0.5, 1.5], colors=[BRAND, ALT_COLOR], alpha=0.3)

ax.contour(xx1, xx2, Z, levels=[0.5], colors=[INK_SOFT], linewidths=3)

predictions = clf.predict(X)
correct_mask = predictions == y
incorrect_mask = ~correct_mask

sns.scatterplot(
    x=X1[correct_mask],
    y=X2[correct_mask],
    hue=y[correct_mask],
    palette=[BRAND, ALT_COLOR],
    s=200,
    edgecolor=PAGE_BG,
    linewidth=1.5,
    alpha=0.9,
    ax=ax,
    legend=False,
)

if np.any(incorrect_mask):
    ax.scatter(
        X1[incorrect_mask],
        X2[incorrect_mask],
        s=300,
        edgecolors="#BD8233",
        linewidths=3.5,
        facecolors="none",
        alpha=0.95,
        marker="o",
    )

legend_elements = [
    Patch(facecolor=BRAND, alpha=0.3, edgecolor=INK_SOFT, label="Class 0 Region"),
    Patch(facecolor=ALT_COLOR, alpha=0.3, edgecolor=INK_SOFT, label="Class 1 Region"),
    Line2D(
        [0],
        [0],
        marker="o",
        color="w",
        markerfacecolor=BRAND,
        markersize=14,
        markeredgecolor=PAGE_BG,
        markeredgewidth=1.5,
        label="Class 0 (correct)",
    ),
    Line2D(
        [0],
        [0],
        marker="o",
        color="w",
        markerfacecolor=ALT_COLOR,
        markersize=14,
        markeredgecolor=PAGE_BG,
        markeredgewidth=1.5,
        label="Class 1 (correct)",
    ),
    Line2D(
        [0],
        [0],
        marker="o",
        color="w",
        markerfacecolor="none",
        markersize=14,
        markeredgecolor="#BD8233",
        markeredgewidth=3.5,
        label="Misclassified",
    ),
]
ax.legend(handles=legend_elements, loc="upper right", fontsize=14, framealpha=0.95)

ax.set_xlabel("Feature 1 (Normalized)", fontsize=20, color=INK)
ax.set_ylabel("Feature 2 (Normalized)", fontsize=20, color=INK)
ax.set_title("contour-decision-boundary · seaborn · anyplot.ai", fontsize=24, color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

accuracy = np.mean(predictions == y) * 100
ax.text(
    0.02,
    0.98,
    f"SVM Accuracy: {accuracy:.1f}%",
    transform=ax.transAxes,
    fontsize=16,
    verticalalignment="top",
    fontweight="bold",
    bbox={"boxstyle": "round", "facecolor": ELEVATED_BG, "alpha": 0.95, "edgecolor": INK_SOFT},
    color=INK,
)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
