""" pyplots.ai
heatmap-clustered: Clustered Heatmap
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

import altair as alt
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import pdist


# Data - Gene expression analysis with 20 genes and 15 samples
np.random.seed(42)

n_genes = 20
n_samples = 15

# Create gene and sample labels
gene_labels = [f"Gene_{i + 1:02d}" for i in range(n_genes)]
sample_labels = [f"Sample_{i + 1:02d}" for i in range(n_samples)]

# Generate realistic gene expression data with natural clusters
# Create 4 gene clusters with correlated expression patterns
base_expression = np.random.randn(n_genes, n_samples)

# Cluster 1: Genes 0-4 (upregulated in samples 0-4)
base_expression[0:5, 0:5] += 2.5
base_expression[0:5, 10:15] -= 1.5

# Cluster 2: Genes 5-9 (upregulated in samples 5-9)
base_expression[5:10, 5:10] += 2.0
base_expression[5:10, 0:3] -= 1.0

# Cluster 3: Genes 10-14 (upregulated in samples 10-14)
base_expression[10:15, 10:15] += 2.5
base_expression[10:15, 5:8] -= 1.5

# Cluster 4: Genes 15-19 (varied pattern)
base_expression[15:20, 0:5] += 1.5
base_expression[15:20, 5:10] -= 2.0
base_expression[15:20, 10:15] += 1.0

expression_data = base_expression

# Perform hierarchical clustering on rows (genes) and columns (samples)
row_linkage = linkage(pdist(expression_data, metric="euclidean"), method="ward")
col_linkage = linkage(pdist(expression_data.T, metric="euclidean"), method="ward")

# Get dendrogram ordering
row_dendro = dendrogram(row_linkage, no_plot=True)
col_dendro = dendrogram(col_linkage, no_plot=True)

row_order = row_dendro["leaves"]
col_order = col_dendro["leaves"]

# Reorder data and labels
clustered_data = expression_data[row_order, :][:, col_order]
ordered_gene_labels = [gene_labels[i] for i in row_order]
ordered_sample_labels = [sample_labels[i] for i in col_order]

# Create DataFrame for heatmap
heatmap_data = []
for i, gene in enumerate(ordered_gene_labels):
    for j, sample in enumerate(ordered_sample_labels):
        heatmap_data.append(
            {"Gene": gene, "Sample": sample, "Expression": clustered_data[i, j], "row_idx": i, "col_idx": j}
        )

df_heatmap = pd.DataFrame(heatmap_data)

# Create row dendrogram data (left side, vertical orientation)
row_lines = []
for i in range(len(row_dendro["icoord"])):
    xs = row_dendro["icoord"][i]
    ys = row_dendro["dcoord"][i]
    for j in range(3):
        row_lines.append({"x": ys[j], "y": xs[j], "x2": ys[j + 1], "y2": xs[j + 1], "group": i})
row_dendro_lines = pd.DataFrame(row_lines)

# Flip y-coordinates to match heatmap orientation
max_y = row_dendro_lines["y"].max()
row_dendro_lines["y"] = max_y - row_dendro_lines["y"]
row_dendro_lines["y2"] = max_y - row_dendro_lines["y2"]

# Normalize row dendrogram coordinates
row_max_height = row_dendro_lines["x"].max()
row_dendro_lines["x"] = row_max_height - row_dendro_lines["x"]
row_dendro_lines["x2"] = row_max_height - row_dendro_lines["x2"]
row_dendro_lines["y"] = row_dendro_lines["y"] / 10 - 0.5
row_dendro_lines["y2"] = row_dendro_lines["y2"] / 10 - 0.5

# Create column dendrogram data (top, horizontal orientation)
col_lines = []
for i in range(len(col_dendro["icoord"])):
    xs = col_dendro["icoord"][i]
    ys = col_dendro["dcoord"][i]
    for j in range(3):
        col_lines.append({"x": xs[j], "y": ys[j], "x2": xs[j + 1], "y2": ys[j + 1], "group": i})
col_dendro_lines = pd.DataFrame(col_lines)

# Normalize column dendrogram coordinates
col_dendro_lines["x"] = col_dendro_lines["x"] / 10 - 0.5
col_dendro_lines["x2"] = col_dendro_lines["x2"] / 10 - 0.5

# Row dendrogram chart (left side)
row_dendro_chart = (
    alt.Chart(row_dendro_lines)
    .mark_rule(strokeWidth=2, color="#333333")
    .encode(
        x=alt.X("x:Q", axis=None, scale=alt.Scale(domain=[0, row_max_height])),
        y=alt.Y("y:Q", axis=None, scale=alt.Scale(domain=[-0.5, n_genes - 0.5])),
        x2="x2:Q",
        y2="y2:Q",
    )
    .properties(width=150, height=600)
)

# Column dendrogram chart (top)
col_max_height = col_dendro_lines["y"].max()
col_dendro_chart = (
    alt.Chart(col_dendro_lines)
    .mark_rule(strokeWidth=2, color="#333333")
    .encode(
        x=alt.X("x:Q", axis=None, scale=alt.Scale(domain=[-0.5, n_samples - 0.5])),
        y=alt.Y("y:Q", axis=None, scale=alt.Scale(domain=[0, col_max_height])),
        x2="x2:Q",
        y2="y2:Q",
    )
    .properties(width=800, height=120)
)

# Heatmap
heatmap = (
    alt.Chart(df_heatmap)
    .mark_rect()
    .encode(
        x=alt.X(
            "Sample:N",
            sort=ordered_sample_labels,
            axis=alt.Axis(title="Samples", labelFontSize=14, titleFontSize=18, labelAngle=-45),
        ),
        y=alt.Y("Gene:N", sort=ordered_gene_labels, axis=alt.Axis(title="Genes", labelFontSize=14, titleFontSize=18)),
        color=alt.Color(
            "Expression:Q",
            scale=alt.Scale(scheme="redblue", domainMid=0, reverse=True),
            legend=alt.Legend(title="Expression", titleFontSize=16, labelFontSize=14, gradientLength=400),
        ),
        tooltip=["Gene:N", "Sample:N", alt.Tooltip("Expression:Q", format=".2f")],
    )
    .properties(width=800, height=600)
)

# Create empty corner space for composition
empty_corner = (
    alt.Chart(pd.DataFrame({"x": [0]}))
    .mark_point(opacity=0)
    .encode(x=alt.X("x:Q", axis=None), y=alt.Y("x:Q", axis=None))
    .properties(width=150, height=120)
)

# Combine charts into clustered heatmap layout
top_row = alt.hconcat(empty_corner, col_dendro_chart, spacing=0)
bottom_row = alt.hconcat(row_dendro_chart, heatmap, spacing=0)

chart = (
    alt.vconcat(top_row, bottom_row, spacing=0)
    .properties(title=alt.Title("heatmap-clustered · altair · pyplots.ai", fontSize=28, anchor="middle"))
    .configure_view(strokeWidth=0)
    .configure_concat(spacing=0)
)

# Save outputs
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
