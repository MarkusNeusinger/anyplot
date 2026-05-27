""" anyplot.ai
scatter-embedding: t-SNE and UMAP Embedding Visualization
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 87/100 | Created: 2026-05-07
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.datasets import make_blobs
from sklearn.manifold import TSNE


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD"]

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

# Data
np.random.seed(42)
cluster_names = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta"]
n_clusters = len(cluster_names)

X, y = make_blobs(n_samples=1500, n_features=30, centers=n_clusters, cluster_std=2.5, random_state=42)

tsne = TSNE(n_components=2, perplexity=30, random_state=42, max_iter=1000)
X_embedded = tsne.fit_transform(X)

df = pd.DataFrame({"tsne_1": X_embedded[:, 0], "tsne_2": X_embedded[:, 1], "cluster": [cluster_names[i] for i in y]})

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

sns.scatterplot(
    data=df,
    x="tsne_1",
    y="tsne_2",
    hue="cluster",
    hue_order=cluster_names,
    palette=IMPRINT[:n_clusters],
    alpha=0.65,
    s=120,
    edgecolors=PAGE_BG,
    linewidth=0.4,
    ax=ax,
)

# Annotate cluster centroids
for i, name in enumerate(cluster_names):
    mask = df["cluster"] == name
    cx = df.loc[mask, "tsne_1"].mean()
    cy = df.loc[mask, "tsne_2"].mean()
    ax.text(
        cx,
        cy,
        name,
        fontsize=14,
        fontweight="semibold",
        color=IMPRINT[i],
        ha="center",
        va="center",
        bbox={
            "boxstyle": "round,pad=0.3",
            "facecolor": ELEVATED_BG,
            "edgecolor": IMPRINT[i],
            "alpha": 0.85,
            "linewidth": 1.5,
        },
    )

# Axes — no tick labels (embedding coordinates are not interpretable)
ax.set_xlabel("t-SNE 1", fontsize=20, color=INK)
ax.set_ylabel("t-SNE 2", fontsize=20, color=INK)
ax.set_xticks([])
ax.set_yticks([])

# Spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

# Legend
legend = ax.get_legend()
legend.set_title("Cluster", prop={"size": 16, "weight": "medium"})
legend.get_title().set_color(INK)
for text in legend.get_texts():
    text.set_fontsize(15)
    text.set_color(INK)
legend.get_frame().set_facecolor(ELEVATED_BG)
legend.get_frame().set_edgecolor(INK_SOFT)

# Title block
fig.suptitle("scatter-embedding · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK, y=0.98)
fig.text(
    0.5,
    0.92,
    "t-SNE (perplexity=30)  ·  1500 points  ·  6 clusters  ·  30-dimensional synthetic data",
    fontsize=15,
    ha="center",
    va="top",
    color=INK_SOFT,
)

plt.tight_layout(rect=[0, 0, 1, 0.90])
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
