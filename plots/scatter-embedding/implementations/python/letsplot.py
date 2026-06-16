""" anyplot.ai
scatter-embedding: t-SNE and UMAP Embedding Visualization
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 86/100 | Created: 2026-05-07
"""

import os
import shutil

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F401,F403
from sklearn.datasets import make_blobs
from sklearn.manifold import TSNE


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD"]

# Data — simulate single-cell RNA-seq gene expression then embed via t-SNE
np.random.seed(42)
X, y = make_blobs(n_samples=1500, centers=6, n_features=20, cluster_std=2.8)
cell_types = ["T-cell", "B-cell", "NK-cell", "Monocyte", "Dendritic", "Neutrophil"]
labels = [cell_types[i] for i in y]

tsne = TSNE(n_components=2, perplexity=30, random_state=42, max_iter=1000)
coords = tsne.fit_transform(X)

df = pd.DataFrame({"tsne_1": coords[:, 0], "tsne_2": coords[:, 1], "cell_type": labels})

# Theme
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_blank(),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=20),
    axis_text=element_blank(),
    axis_ticks=element_blank(),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK, size=24),
    plot_subtitle=element_text(color=INK_SOFT, size=18),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=16),
    legend_title=element_text(color=INK, size=16),
)

# Plot
plot = (
    ggplot(df, aes(x="tsne_1", y="tsne_2", color="cell_type"))
    + geom_point(size=3, alpha=0.65)
    + scale_color_manual(values=IMPRINT)
    + labs(
        x="t-SNE 1",
        y="t-SNE 2",
        color="Cell Type",
        title="scatter-embedding · letsplot · anyplot.ai",
        subtitle="t-SNE (perplexity=30) · Single-cell RNA-seq Cell Type Clusters",
    )
    + ggsize(1600, 900)
    + anyplot_theme
)

# Save
ggsave(plot, f"plot-{THEME}.png", scale=3, path=".")
ggsave(plot, f"plot-{THEME}.html", path=".")

if os.path.exists("lets-plot-images"):
    shutil.rmtree("lets-plot-images")
