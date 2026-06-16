""" anyplot.ai
scatter-embedding: t-SNE and UMAP Embedding Visualization
Library: altair 6.1.0 | Python 3.13.13
Quality: 88/100 | Created: 2026-05-07
"""

import os
import sys


sys.path = [p for p in sys.path if not p.endswith("implementations/python")]

import altair as alt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.datasets import make_blobs  # noqa: E402
from sklearn.manifold import TSNE  # noqa: E402


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

# Single-cell RNA-seq scenario with domain-specific cell type labels
CELL_TYPES = ["T cells", "B cells", "NK cells", "Monocytes", "Dendritic cells", "Macrophages", "Plasma cells"]

# Data — varying cluster_std for realistic compactness differences across cell types
np.random.seed(42)
n_clusters = 7
cluster_stds = [1.2, 2.0, 1.5, 1.8, 1.0, 2.2, 1.6]
X_high, y_labels = make_blobs(
    n_samples=700, n_features=20, centers=n_clusters, cluster_std=cluster_stds, random_state=42
)
X_2d = TSNE(n_components=2, perplexity=30, random_state=42).fit_transform(X_high)

df = pd.DataFrame({"tsne_1": X_2d[:, 0], "tsne_2": X_2d[:, 1], "cluster": [CELL_TYPES[idx] for idx in y_labels]})

centroids = df.groupby("cluster")[["tsne_1", "tsne_2"]].mean()
centroids = centroids.loc[CELL_TYPES].reset_index()
centroids["num"] = [str(i + 1) for i in range(n_clusters)]

# Interactive selection bound to legend — clicking a cell type highlights its cluster
selection = alt.selection_point(fields=["cluster"], bind="legend")

# Plot
scatter = (
    alt.Chart(df)
    .mark_circle(size=100, strokeWidth=0.8)
    .encode(
        x=alt.X("tsne_1:Q", axis=alt.Axis(labels=False, ticks=False, title="t-SNE Dimension 1")),
        y=alt.Y("tsne_2:Q", axis=alt.Axis(labels=False, ticks=False, title="t-SNE Dimension 2")),
        color=alt.Color(
            "cluster:N", scale=alt.Scale(domain=CELL_TYPES, range=IMPRINT), legend=alt.Legend(title="Cell Type")
        ),
        opacity=alt.condition(selection, alt.value(0.70), alt.value(0.15)),
        stroke=alt.value(PAGE_BG),
        tooltip=[
            "cluster:N",
            alt.Tooltip("tsne_1:Q", title="t-SNE 1", format=".2f"),
            alt.Tooltip("tsne_2:Q", title="t-SNE 2", format=".2f"),
        ],
    )
    .add_params(selection)
)

centroid_marks = (
    alt.Chart(centroids)
    .mark_text(fontSize=18, fontWeight="bold", dy=-14)
    .encode(x=alt.X("tsne_1:Q"), y=alt.Y("tsne_2:Q"), text="num:N", color=alt.value(INK))
)

title_params = alt.TitleParams(
    text="scatter-embedding · altair · anyplot.ai",
    subtitle="t-SNE (perplexity=30) · 20-dimensional synthetic scRNA-seq · 7 cell types, 700 cells",
    fontSize=28,
    subtitleFontSize=18,
    color=INK,
    subtitleColor=INK_SOFT,
    anchor="start",
)

chart = (
    alt.layer(scatter, centroid_marks)
    .properties(width=1600, height=900, title=title_params, background=PAGE_BG)
    .interactive()
    .configure_view(fill=PAGE_BG, stroke="transparent")
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
        titleFontSize=22,
        labelFontSize=18,
    )
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=16,
        titleFontSize=18,
    )
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
