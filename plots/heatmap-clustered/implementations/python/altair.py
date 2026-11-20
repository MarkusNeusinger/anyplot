""" anyplot.ai
heatmap-clustered: Clustered Heatmap
Library: altair 6.3.0 | Python 3.14.10
Quality: 79/100 | Updated: 2026-11-20
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import pdist


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint diverging colormap: red - theme-adaptive midpoint - blue
IMPRINT_DIV = ["#AE3030", PAGE_BG, "#4467A3"]

# Columns: set these to your table's names
GENE = "Genes"  # role: row_labels
SAMPLE = "Samples"  # role: column_labels
EXPRESSION = "Expression (log2 ratio)"  # role: matrix

# Data: replace this block with your own labeled matrix, for example df = pd.read_csv("expression.csv", index_col=0)
# Gene expression of 20 genes in 15 samples with four co-expressed gene groups
np.random.seed(42)
matrix = np.random.randn(20, 15)
matrix[0:5, 0:5] += 2.5
matrix[0:5, 10:15] -= 1.5
matrix[5:10, 5:10] += 2.0
matrix[5:10, 0:3] -= 1.0
matrix[10:15, 10:15] += 2.5
matrix[10:15, 5:8] -= 1.5
matrix[15:20, 0:5] += 1.5
matrix[15:20, 5:10] -= 2.0
matrix[15:20, 10:15] += 1.0
df = pd.DataFrame(
    matrix,
    index=[f"Gene_{i + 1:02d}" for i in range(matrix.shape[0])],
    columns=[f"Sample_{j + 1:02d}" for j in range(matrix.shape[1])],
)

# Plot: reads only df and the constants above
n_genes, n_samples = df.shape

# Hierarchical clustering (Ward linkage, Euclidean distance) on rows and columns
row_dendro = dendrogram(linkage(pdist(df.to_numpy()), method="ward"), no_plot=True)
col_dendro = dendrogram(linkage(pdist(df.to_numpy().T), method="ward"), no_plot=True)
clustered = df.iloc[row_dendro["leaves"], col_dendro["leaves"]]
gene_order = list(clustered.index)
sample_order = list(clustered.columns)

# Long table of cells for the heatmap
cells = clustered.rename_axis(index=GENE, columns=SAMPLE).stack().rename(EXPRESSION).reset_index()

ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
gene_f, sample_f, expr_f = (name.translate(ESCAPE) for name in (GENE, SAMPLE, EXPRESSION))


def branches(dendro, leaf_axis):
    """Dendrogram links as segments; leaf k sits at position k, merge height on the other axis."""
    rows = []
    for leaf_c, height in zip(dendro["icoord"], dendro["dcoord"], strict=True):
        pos = [(c - 5) / 10 for c in leaf_c]
        for k in range(3):
            rows.append({"p1": pos[k], "h1": height[k], "p2": pos[k + 1], "h2": height[k + 1]})
    seg = pd.DataFrame(rows)
    return seg if leaf_axis == "x" else seg.assign(p1=n_genes - 1 - seg["p1"], p2=n_genes - 1 - seg["p2"])


# Layout in view pixels (square canvas, scale_factor 4)
DENDRO = 70
HEAT_W, HEAT_H = 295, 400

row_seg = branches(row_dendro, "y")
col_seg = branches(col_dendro, "x")
row_top = row_seg[["h1", "h2"]].to_numpy().max()
col_top = col_seg[["h1", "h2"]].to_numpy().max()

row_dendro_chart = (
    alt.Chart(row_seg)
    .mark_rule(strokeWidth=1.5, color=INK_SOFT)
    .encode(
        x=alt.X("h1:Q", axis=None, scale=alt.Scale(domain=[row_top, 0])),
        x2="h2:Q",
        y=alt.Y("p1:Q", axis=None, scale=alt.Scale(domain=[-0.5, n_genes - 0.5])),
        y2="p2:Q",
    )
    .properties(width=DENDRO, height=HEAT_H)
)

col_dendro_chart = (
    alt.Chart(col_seg)
    .mark_rule(strokeWidth=1.5, color=INK_SOFT)
    .encode(
        x=alt.X("p1:Q", axis=None, scale=alt.Scale(domain=[-0.5, n_samples - 0.5])),
        x2="p2:Q",
        y=alt.Y("h1:Q", axis=None, scale=alt.Scale(domain=[0, col_top])),
        y2="h2:Q",
    )
    .properties(width=HEAT_W, height=DENDRO)
)

heatmap = (
    alt.Chart(cells)
    .mark_rect()
    .encode(
        x=alt.X(
            sample_f,
            type="ordinal",
            sort=sample_order,
            title=SAMPLE,
            axis=alt.Axis(labelFontSize=9, titleFontSize=12, labelAngle=-45, labelColor=INK_SOFT, titleColor=INK),
        ),
        y=alt.Y(
            gene_f,
            type="ordinal",
            sort=gene_order,
            title=GENE,
            axis=alt.Axis(labelFontSize=9, titleFontSize=12, labelColor=INK_SOFT, titleColor=INK),
        ),
        color=alt.Color(
            expr_f,
            type="quantitative",
            title=EXPRESSION,
            scale=alt.Scale(range=IMPRINT_DIV, domainMid=0),
            legend=alt.Legend(
                titleFontSize=11,
                labelFontSize=10,
                gradientLength=200,
                titleLimit=120,
                fillColor=ELEVATED_BG,
                strokeColor=INK_SOFT,
                labelColor=INK_SOFT,
                titleColor=INK,
                padding=6,
            ),
        ),
        tooltip=[
            alt.Tooltip(gene_f, title=GENE),
            alt.Tooltip(sample_f, title=SAMPLE),
            alt.Tooltip(expr_f, title=EXPRESSION, format=".2f"),
        ],
    )
    .properties(width=HEAT_W, height=HEAT_H)
    .interactive()
)

# The empty corner keeps both dendrograms flush with the heatmap
corner = (
    alt.Chart(pd.DataFrame({"x": [0]}))
    .mark_point(opacity=0)
    .encode(x=alt.X("x:Q", axis=None), y=alt.Y("x:Q", axis=None))
    .properties(width=DENDRO, height=DENDRO)
)

chart = (
    alt.vconcat(alt.hconcat(corner, col_dendro_chart, spacing=0), alt.hconcat(row_dendro_chart, heatmap, spacing=0))
    .properties(
        title=alt.Title("heatmap-clustered · python · altair · anyplot.ai", fontSize=16, anchor="middle", color=INK),
        background=PAGE_BG,
        spacing=0,
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_axis(domainColor=INK_SOFT, tickColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save outputs
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad (never crop) to the square target canvas
TW, TH = 2400, 2400
img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TW or h > TH:
    raise SystemExit(f"altair produced {w}x{h}, exceeds target {TW}x{TH}; shrink the view sizes")
canvas = Image.new("RGB", (TW, TH), PAGE_BG)
canvas.paste(img, ((TW - w) // 2, (TH - h) // 2))
canvas.save(f"plot-{THEME}.png")
