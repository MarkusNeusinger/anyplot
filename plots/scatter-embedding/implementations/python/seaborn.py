""" anyplot.ai
scatter-embedding: t-SNE and UMAP Embedding Visualization
Library: seaborn 0.13.2 | Python 3.13.14
Quality: 89/100 | Updated: 2026-08-11
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
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Data — synthetic customer behavioral feature vectors (purchase frequency, order
# value, session depth, email engagement, support load, tenure, ...), reduced to
# 2D via t-SNE to surface latent segment structure, mirroring a clustering-QC workflow.
np.random.seed(42)
segment_names = [
    "Power Users",
    "Loyal Subscribers",
    "Occasional Buyers",
    "New Signups",
    "Cart Abandoners",
    "Churn Risk",
]
segment_colors = {
    "Power Users": "#009E73",
    "Loyal Subscribers": "#C475FD",
    "Occasional Buyers": "#4467A3",
    "New Signups": "#BD8233",
    "Cart Abandoners": "#2ABCCD",
    "Churn Risk": "#AE3030",
}
n_segments = len(segment_names)

X, y = make_blobs(n_samples=1500, n_features=32, centers=n_segments, cluster_std=8.0, random_state=42)

tsne = TSNE(n_components=2, perplexity=30, random_state=42, max_iter=1000)
X_embedded = tsne.fit_transform(X)

df = pd.DataFrame({"tsne_1": X_embedded[:, 0], "tsne_2": X_embedded[:, 1], "segment": [segment_names[i] for i in y]})

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

sns.scatterplot(
    data=df,
    x="tsne_1",
    y="tsne_2",
    hue="segment",
    hue_order=segment_names,
    palette=segment_colors,
    alpha=0.5,
    s=45,
    edgecolors=PAGE_BG,
    linewidth=0.3,
    ax=ax,
)

# Pad the data range so centroid labels near the edges (e.g. the rightmost
# cluster) never reach the legend placed just outside the axes, and the
# leftmost cluster's label clears the left spine
ax.margins(x=0.20, y=0.12)

# Annotate segment centroids
for name in segment_names:
    mask = df["segment"] == name
    cx = df.loc[mask, "tsne_1"].mean()
    cy = df.loc[mask, "tsne_2"].mean()
    ax.text(
        cx,
        cy,
        name,
        fontsize=10,
        fontweight="semibold",
        color=segment_colors[name],
        ha="center",
        va="center",
        bbox={
            "boxstyle": "round,pad=0.3",
            "facecolor": ELEVATED_BG,
            "edgecolor": segment_colors[name],
            "alpha": 0.9,
            "linewidth": 1.2,
        },
    )

# Axes — no tick labels (embedding coordinates are not interpretable)
ax.set_xlabel("t-SNE 1", fontsize=11, color=INK)
ax.set_ylabel("t-SNE 2", fontsize=11, color=INK)
ax.set_xticks([])
ax.set_yticks([])

# Spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

# Legend — placed outside the axes so it never overlaps a cluster (t-SNE
# layout is data-dependent and any in-plot corner risks landing on a cluster)
sns.move_legend(ax, "center left", bbox_to_anchor=(1.02, 0.5))
legend = ax.get_legend()
legend.set_title("Segment", prop={"size": 11, "weight": "medium"})
legend.get_title().set_color(INK)
for text in legend.get_texts():
    text.set_fontsize(10)
    text.set_color(INK)
legend.get_frame().set_facecolor(ELEVATED_BG)
legend.get_frame().set_edgecolor(INK_SOFT)

# Title block
fig.suptitle("scatter-embedding · python · seaborn · anyplot.ai", fontsize=13, fontweight="medium", color=INK, y=0.98)
fig.text(
    0.5,
    0.92,
    "t-SNE (perplexity=30)  ·  1500 customers  ·  6 behavioral segments  ·  clustering QC",
    fontsize=10,
    ha="center",
    va="top",
    color=INK_SOFT,
)

plt.tight_layout(rect=[0, 0, 0.97, 0.90])
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
