"""anyplot.ai
scatter-embedding: t-SNE and UMAP Embedding Visualization
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-08-11
"""

import os
import sys


# Work around naming conflict: pygal.py filename shadows pygal package
sys.path.pop(0)

import numpy as np
import pygal
from pygal.formatters import Significant
from pygal.style import Style
from sklearn.datasets import make_blobs
from sklearn.manifold import TSNE


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette positions 1-6 at 65% opacity to handle overlapping points
IMPRINT_ALPHA = (
    "rgba(0,158,115,0.65)",  # #009E73 brand green
    "rgba(196,117,253,0.65)",  # #C475FD lavender
    "rgba(68,103,163,0.65)",  # #4467A3 blue
    "rgba(189,130,51,0.65)",  # #BD8233 ochre
    "rgba(174,48,48,0.65)",  # #AE3030 matte red
    "rgba(42,188,205,0.65)",  # #2ABCCD cyan
)

CELL_TYPES = ["T-cells", "B-cells", "NK cells", "Monocytes", "Dendritic cells", "Neutrophils"]

# Data — 15-D single-cell RNA-seq-style blobs reduced to 2-D with t-SNE
np.random.seed(42)
X_high, labels = make_blobs(n_samples=600, n_features=15, centers=len(CELL_TYPES), cluster_std=2.0, random_state=42)

tsne = TSNE(n_components=2, perplexity=30, max_iter=500, random_state=42)
X_2d = tsne.fit_transform(X_high)

centroids = [X_2d[labels == i].mean(axis=0) for i in range(len(CELL_TYPES))]

# Plot — pygal splits the title on "\n" into stacked lines, giving a native
# subtitle slot for the algorithm + key parameter (pygal has no dedicated
# subtitle field). value_formatter trims hover-tooltip coordinates to 3
# significant digits instead of pygal's noisy float default.
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT_ALPHA + (INK,),
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
)

chart = pygal.XY(
    style=custom_style,
    width=3200,
    height=1800,
    title="scatter-embedding · python · pygal · anyplot.ai\nt-SNE embedding · perplexity=30",
    x_title="t-SNE Dimension 1",
    y_title="t-SNE Dimension 2",
    show_x_labels=False,
    show_y_labels=False,
    stroke=False,
    dots_size=6,
    print_values=False,
    value_formatter=Significant(3),
    truncate_legend=-1,
)

for i, name in enumerate(CELL_TYPES):
    points = [(float(x), float(y)) for x, y in X_2d[labels == i]]
    chart.add(name, points)

chart.add("Cluster centroids", [(float(x), float(y)) for x, y in centroids], dots_size=16)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
