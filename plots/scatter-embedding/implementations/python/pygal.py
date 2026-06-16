""" anyplot.ai
scatter-embedding: t-SNE and UMAP Embedding Visualization
Library: pygal 3.1.0 | Python 3.13.13
Quality: 80/100 | Created: 2026-05-07
"""

import os
import sys


# Work around naming conflict: pygal.py filename shadows pygal package
sys.path.pop(0)

import numpy as np
import pygal
from pygal.style import Style
from sklearn.datasets import make_blobs
from sklearn.manifold import TSNE


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito with 65 % opacity to handle overlapping points gracefully
OKABE_ITO_ALPHA = (
    "rgba(0,158,115,0.65)",
    "rgba(196, 117, 253, 0.65)",
    "rgba(68, 103, 163, 0.65)",
    "rgba(189, 130, 51, 0.65)",
    "rgba(174, 48, 48, 0.65)",
    "rgba(42, 188, 205, 0.65)",
)

CLUSTER_LABELS = ["Cluster A", "Cluster B", "Cluster C", "Cluster D", "Cluster E", "Cluster F"]

# Data — generate 15-D blobs then reduce to 2-D with t-SNE
np.random.seed(42)
X_high, labels = make_blobs(n_samples=600, n_features=15, centers=6, cluster_std=2.0, random_state=42)

tsne = TSNE(n_components=2, perplexity=30, max_iter=500, random_state=42)
X_2d = tsne.fit_transform(X_high)

# Plot
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=OKABE_ITO_ALPHA,
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=16,
    value_font_size=14,
)

chart = pygal.XY(
    style=custom_style,
    width=4800,
    height=2700,
    title="scatter-embedding · pygal · anyplot.ai",
    x_title="t-SNE Dimension 1  (perplexity=30)",
    y_title="t-SNE Dimension 2",
    show_x_labels=False,
    show_y_labels=False,
    stroke=False,
    dots_size=5,
    print_values=False,
)

for i, name in enumerate(CLUSTER_LABELS):
    mask = labels == i
    points = [(float(x), float(y)) for x, y in X_2d[mask]]
    chart.add(name, points)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
