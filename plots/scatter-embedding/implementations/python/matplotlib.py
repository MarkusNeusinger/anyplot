""" anyplot.ai
scatter-embedding: t-SNE and UMAP Embedding Visualization
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 87/100 | Created: 2026-05-07
"""

import os
import sys


sys.path.pop(0)
import matplotlib.pyplot as plt
import numpy as np
from sklearn.datasets import make_blobs
from sklearn.manifold import TSNE


# Theme
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

CLUSTER_LABELS = ["Finance", "Healthcare", "Technology", "Sports", "Politics", "Science", "Entertainment"]

# Data — 1050 document embeddings (150 per topic) in 50-dimensional space
np.random.seed(42)
X_high, labels = make_blobs(n_samples=1050, n_features=50, centers=7, cluster_std=2.5, random_state=42)
tsne = TSNE(n_components=2, perplexity=30, random_state=42)
X_2d = tsne.fit_transform(X_high)

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

for i, (label, color) in enumerate(zip(CLUSTER_LABELS, IMPRINT, strict=False)):
    mask = labels == i
    ax.scatter(X_2d[mask, 0], X_2d[mask, 1], c=color, s=90, alpha=0.65, edgecolors=PAGE_BG, linewidth=0.5, label=label)

# Centroid annotations
for i, label in enumerate(CLUSTER_LABELS):
    mask = labels == i
    cx, cy = X_2d[mask, 0].mean(), X_2d[mask, 1].mean()
    ax.text(
        cx,
        cy,
        label,
        fontsize=13,
        fontweight="bold",
        color=INK,
        ha="center",
        va="center",
        bbox={
            "facecolor": ELEVATED_BG,
            "edgecolor": INK_SOFT,
            "alpha": 0.85,
            "boxstyle": "round,pad=0.3",
            "linewidth": 0.8,
        },
    )

# Style
ax.set_xlabel("t-SNE 1", fontsize=20, color=INK)
ax.set_ylabel("t-SNE 2", fontsize=20, color=INK)
ax.set_title(
    "Document Topic Embeddings · scatter-embedding · matplotlib · anyplot.ai",
    fontsize=24,
    fontweight="medium",
    color=INK,
)
ax.tick_params(axis="both", length=0)
ax.set_xticks([])
ax.set_yticks([])

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

# Legend
leg = ax.legend(fontsize=15, loc="lower right", framealpha=0.9, title="Topic", title_fontsize=16)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)
leg.get_title().set_color(INK_SOFT)

# Algorithm subtitle
fig.text(
    0.5,
    0.01,
    "t-SNE (perplexity=30)  ·  50-dimensional document embeddings  ·  7 topic clusters",
    ha="center",
    va="bottom",
    fontsize=15,
    color=INK_MUTED,
)

plt.tight_layout(rect=[0, 0.04, 1, 1])
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
