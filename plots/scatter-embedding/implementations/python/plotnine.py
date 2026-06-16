""" anyplot.ai
scatter-embedding: t-SNE and UMAP Embedding Visualization
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 83/100 | Created: 2026-05-07
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_point,
    ggplot,
    labs,
    scale_color_manual,
    theme,
)
from sklearn.datasets import make_blobs
from sklearn.manifold import TSNE


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD"]

# Data
np.random.seed(42)
n_clusters = 6
X, y = make_blobs(n_samples=1200, centers=n_clusters, cluster_std=1.2, random_state=42)

tsne = TSNE(n_components=2, perplexity=30, random_state=42)
embedding = tsne.fit_transform(X)

cluster_names = [f"Cluster {i + 1}" for i in range(n_clusters)]
df = pd.DataFrame(
    {
        "tsne_1": embedding[:, 0],
        "tsne_2": embedding[:, 1],
        "Cluster": pd.Categorical([cluster_names[i] for i in y], categories=cluster_names),
    }
)

# Plot
anyplot_theme = theme(
    figure_size=(16, 9),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_minor=element_blank(),
    panel_border=element_rect(color=INK_SOFT, fill=None),
    axis_title=element_text(color=INK, size=20),
    axis_text=element_blank(),
    axis_ticks=element_blank(),
    plot_title=element_text(color=INK, size=24),
    plot_subtitle=element_text(color=INK_SOFT, size=16),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=16),
    legend_title=element_text(color=INK, size=18),
    legend_key=element_rect(fill=PAGE_BG),
)

plot = (
    ggplot(df, aes(x="tsne_1", y="tsne_2", color="Cluster"))
    + geom_point(size=2.5, alpha=0.7)
    + scale_color_manual(values=IMPRINT)
    + labs(
        title="scatter-embedding · plotnine · anyplot.ai",
        subtitle="t-SNE (perplexity=30) · 1200 points · 6 clusters",
        x="t-SNE Dimension 1",
        y="t-SNE Dimension 2",
    )
    + anyplot_theme
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300, width=16, height=9)
