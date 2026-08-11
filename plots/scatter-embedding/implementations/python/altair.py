""" anyplot.ai
scatter-embedding: t-SNE and UMAP Embedding Visualization
Library: altair 6.2.2 | Python 3.13.14
Quality: 93/100 | Updated: 2026-08-11
"""

import os
import sys


sys.path = [p for p in sys.path if not p.endswith("implementations/python")]

import altair as alt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import Image  # noqa: E402
from sklearn.datasets import make_blobs  # noqa: E402
from sklearn.manifold import TSNE  # noqa: E402


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette (positions 1-7, canonical order)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

# Single-cell RNA-seq scenario with domain-specific cell type labels
CELL_TYPES = ["T cells", "B cells", "NK cells", "Monocytes", "Dendritic cells", "Macrophages", "Plasma cells"]
CELL_ABBR = {
    "T cells": "T",
    "B cells": "B",
    "NK cells": "NK",
    "Monocytes": "Mono",
    "Dendritic cells": "DC",
    "Macrophages": "Mac",
    "Plasma cells": "PC",
}

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
centroids["abbr"] = [CELL_ABBR[c] for c in centroids["cluster"]]

# Tighten the scale domain to the data extent (+6% pad) instead of Altair's
# default "nice" auto-domain — sparse t-SNE clusters otherwise leave large
# unused margins on the canvas.
x_min, x_max = df["tsne_1"].min(), df["tsne_1"].max()
y_min, y_max = df["tsne_2"].min(), df["tsne_2"].max()
x_pad, y_pad = (x_max - x_min) * 0.06, (y_max - y_min) * 0.06
x_domain = [x_min - x_pad, x_max + x_pad]
y_domain = [y_min - y_pad, y_max + y_pad]

# Interactive selection bound to legend — clicking a cell type highlights its cluster
selection = alt.selection_point(fields=["cluster"], bind="legend")

# Marker size/opacity tuned for 700 overlapping points (high-density heuristic)
scatter = (
    alt.Chart(df)
    .mark_circle(size=45, strokeWidth=0.5)
    .encode(
        x=alt.X(
            "tsne_1:Q",
            scale=alt.Scale(domain=x_domain, nice=False),
            axis=alt.Axis(labels=False, ticks=False, domain=False, grid=False, title="t-SNE Dimension 1"),
        ),
        y=alt.Y(
            "tsne_2:Q",
            scale=alt.Scale(domain=y_domain, nice=False),
            axis=alt.Axis(labels=False, ticks=False, domain=False, grid=False, title="t-SNE Dimension 2"),
        ),
        color=alt.Color(
            "cluster:N", scale=alt.Scale(domain=CELL_TYPES, range=IMPRINT), legend=alt.Legend(title="Cell Type")
        ),
        opacity=alt.condition(selection, alt.value(0.55), alt.value(0.12)),
        stroke=alt.value(PAGE_BG),
        tooltip=[
            "cluster:N",
            alt.Tooltip("tsne_1:Q", title="t-SNE 1", format=".2f"),
            alt.Tooltip("tsne_2:Q", title="t-SNE 2", format=".2f"),
        ],
    )
    .add_params(selection)
)

# Direct abbreviated-name labels on centroids (no legend cross-referencing needed).
# A background-colored halo stroke behind the text keeps labels legible against
# every cluster hue in both themes, independent of the underlying data color.
centroid_marks = (
    alt.Chart(centroids)
    .mark_text(fontSize=13, fontWeight="bold", dy=-9, stroke=PAGE_BG, strokeWidth=0.75)
    .encode(
        x=alt.X("tsne_1:Q", scale=alt.Scale(domain=x_domain, nice=False)),
        y=alt.Y("tsne_2:Q", scale=alt.Scale(domain=y_domain, nice=False)),
        text="abbr:N",
        color=alt.value(INK),
    )
)

title_text = "scatter-embedding · python · altair · anyplot.ai"
title_params = alt.TitleParams(
    text=title_text,
    subtitle="t-SNE (perplexity=30) · 20-dimensional synthetic scRNA-seq · 7 cell types, 700 cells",
    fontSize=round(18 * min(1.0, 67 / len(title_text))),
    subtitleFontSize=12,
    color=INK,
    subtitleColor=INK_SOFT,
    anchor="start",
)

chart = (
    alt.layer(scatter, centroid_marks)
    .properties(
        width=620,
        height=320,
        padding={"left": 0, "right": 0, "top": 0, "bottom": 0},
        title=title_params,
        background=PAGE_BG,
    )
    .interactive()
    .configure_view(continuousWidth=620, continuousHeight=320, fill=PAGE_BG, stroke="transparent")
    .configure_axis(titleColor=INK, titleFontSize=12)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=10,
        titleFontSize=10,
        cornerRadius=4,
        padding=8,
    )
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)

# Pad-only to the canonical canvas — vl-convert's title/legend padding makes the
# saved PNG larger than width*scale_factor. Never crop: cropping clips title/axis
# labels and trips the AR-09 edge-clipping auto-reject.
TW, TH = 3200, 1800
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
_w, _h = _img.size
if _w > TW or _h > TH:
    raise SystemExit(
        f"altair vl-convert produced {_w}x{_h}, exceeds target {TW}x{TH}. "
        f"Shrink chart .properties(width=, height=) values and re-render."
    )
if _w < TW or _h < TH:
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _w) // 2, (TH - _h) // 2))
    _canvas.save(f"plot-{THEME}.png")

chart.save(f"plot-{THEME}.html")
