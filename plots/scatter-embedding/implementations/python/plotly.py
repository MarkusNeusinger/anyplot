""" anyplot.ai
scatter-embedding: t-SNE and UMAP Embedding Visualization
Library: plotly 6.7.0 | Python 3.13.13
Quality: 91/100 | Created: 2026-05-07
"""

import os

import numpy as np
import plotly.graph_objects as go
from sklearn.datasets import make_blobs
from sklearn.manifold import TSNE


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD"]

# Data — simulate document embeddings in 50-dimensional topic space
np.random.seed(42)

topics = ["Technology", "Science", "Sports", "Politics", "Entertainment", "Health"]
n_clusters = len(topics)

X_high_dim, labels = make_blobs(n_samples=1500, n_features=50, centers=n_clusters, cluster_std=2.5, random_state=42)

# Reduce to 2D with t-SNE
tsne = TSNE(n_components=2, perplexity=30, random_state=42, max_iter=1000)
X_2d = tsne.fit_transform(X_high_dim)

# Plot — one trace per topic cluster
fig = go.Figure()

for i, topic in enumerate(topics):
    mask = labels == i
    fig.add_trace(
        go.Scatter(
            x=X_2d[mask, 0],
            y=X_2d[mask, 1],
            mode="markers",
            name=topic,
            marker={"color": IMPRINT[i], "size": 8, "opacity": 0.65, "line": {"color": PAGE_BG, "width": 0.5}},
        )
    )

# Annotate cluster centroids
for i, topic in enumerate(topics):
    mask = labels == i
    cx = float(X_2d[mask, 0].mean())
    cy = float(X_2d[mask, 1].mean())
    fig.add_annotation(
        x=cx,
        y=cy,
        text=f"<b>{topic}</b>",
        showarrow=False,
        font={"size": 16, "color": INK},
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
        opacity=0.9,
    )

# Layout
fig.update_layout(
    title={
        "text": (
            "Document Topic Clusters · scatter-embedding · plotly · anyplot.ai"
            "<br><sup>t-SNE (perplexity=30) | 1,500 document embeddings across 6 topics</sup>"
        ),
        "font": {"size": 28, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    xaxis={
        "title": {"text": "t-SNE Dimension 1", "font": {"size": 22, "color": INK}},
        "showticklabels": False,
        "showgrid": True,
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zeroline": False,
    },
    yaxis={
        "title": {"text": "t-SNE Dimension 2", "font": {"size": 22, "color": INK}},
        "showticklabels": False,
        "showgrid": True,
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zeroline": False,
    },
    legend={
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "font": {"size": 16, "color": INK_SOFT},
        "title": {"text": "Topic", "font": {"size": 18, "color": INK}},
    },
    margin={"l": 80, "r": 80, "t": 120, "b": 80},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
