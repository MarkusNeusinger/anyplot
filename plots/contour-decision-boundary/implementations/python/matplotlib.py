"""anyplot.ai
contour-decision-boundary: Decision Boundary Classifier Visualization
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-16
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.datasets import make_moons
from sklearn.svm import SVC


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns
X1 = "Feature X1"  # role: X1
X2 = "Feature X2"  # role: X2
CLASS = "Class"  # role: y

# Data - two-moons classification sample
X, y = make_moons(n_samples=200, noise=0.25, random_state=42)
df = pd.DataFrame({X1: X[:, 0], X2: X[:, 1], CLASS: y})

# Plot: reads only df and the constants above
features = [X1, X2]
df = df.dropna(subset=[X1, X2, CLASS]).reset_index(drop=True)
classes = sorted(df[CLASS].unique())
palette = [IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i in range(len(classes))]
classifier = SVC(kernel="rbf", C=1.0, gamma="scale").fit(df[features].to_numpy(), df[CLASS])
x_lo, x_hi = df[X1].min() - 0.5, df[X1].max() + 0.5
y_lo, y_hi = df[X2].min() - 0.5, df[X2].max() + 0.5
xx, yy = np.meshgrid(np.linspace(x_lo, x_hi, 300), np.linspace(y_lo, y_hi, 300))
Z = classifier.predict(np.c_[xx.ravel(), yy.ravel()]).reshape(xx.shape)
is_correct = classifier.predict(df[features].to_numpy()) == df[CLASS].to_numpy()

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

boundaries = [classes[0] - 0.5] + [c + 0.5 for c in classes]
ax.contourf(xx, yy, Z, levels=boundaries, colors=palette, alpha=0.3)
ax.contour(xx, yy, Z, levels=boundaries[1:-1], colors=INK_SOFT, linewidths=1.2)

for i, cls in enumerate(classes):
    in_class = (df[CLASS] == cls).to_numpy()
    ok = df[in_class & is_correct]
    bad = df[in_class & ~is_correct]
    ax.scatter(
        ok[X1],
        ok[X2],
        c=palette[i],
        s=45,
        alpha=0.9,
        edgecolors=PAGE_BG,
        linewidths=0.6,
        marker="o",
        label=f"Class {cls} (correct)",
        zorder=3,
    )
    if len(bad):
        ax.scatter(
            bad[X1],
            bad[X2],
            c=palette[i],
            s=70,
            alpha=0.95,
            edgecolors=INK,
            linewidths=1.0,
            marker="X",
            label=f"Class {cls} (misclassified)",
            zorder=4,
        )

# Style
ax.set_xlabel(X1, fontsize=10, color=INK)
ax.set_ylabel(X2, fontsize=10, color=INK)
ax.set_title(
    "contour-decision-boundary · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK
)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
ax.grid(True, alpha=0.1, linewidth=0.8, color=INK)

leg = ax.legend(fontsize=8, loc="upper left")
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
