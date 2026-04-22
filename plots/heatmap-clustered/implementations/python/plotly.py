""" pyplots.ai
heatmap-clustered: Clustered Heatmap
Library: plotly 6.5.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import pdist


# Data: Gene expression analysis (20 genes x 12 samples)
np.random.seed(42)
n_genes = 20
n_samples = 12

# Gene names representing biological pathways
gene_labels = [
    "CDK1",
    "CCNB1",
    "PLK1",
    "AURKA",
    "BUB1",  # Cell cycle
    "GAPDH",
    "LDHA",
    "PKM",
    "HK2",
    "ENO1",  # Metabolism
    "IL6",
    "TNF",
    "IFNG",
    "IL1B",
    "CXCL8",  # Immune response
    "MYC",
    "TP53",
    "BRCA1",
    "EGFR",
    "VEGFA",  # Cancer-related
]

# Sample names (tumor vs normal comparisons)
sample_labels = [
    "T1_A",
    "T1_B",
    "T1_C",
    "T2_A",
    "T2_B",
    "T2_C",  # Tumor
    "N1_A",
    "N1_B",
    "N1_C",
    "N2_A",
    "N2_B",
    "N2_C",  # Normal
]

# Generate expression data with cluster structure
data = np.random.randn(n_genes, n_samples) * 0.5

# Cell cycle genes upregulated in tumors
data[0:5, 0:6] += 2.0
data[0:5, 6:12] -= 1.5

# Metabolism genes moderately upregulated in tumors
data[5:10, 0:6] += 1.2
data[5:10, 6:12] -= 0.8

# Immune genes show mixed pattern
data[10:15, 0:3] += 1.5
data[10:15, 3:6] -= 0.5
data[10:15, 6:9] += 0.8
data[10:15, 9:12] -= 1.2

# Cancer-related genes upregulated in tumors
data[15:20, 0:6] += 1.8
data[15:20, 6:12] -= 1.0

# Hierarchical clustering
row_linkage = linkage(pdist(data, metric="euclidean"), method="ward")
col_linkage = linkage(pdist(data.T, metric="euclidean"), method="ward")

# Get dendrogram order
row_dendro = dendrogram(row_linkage, no_plot=True)
col_dendro = dendrogram(col_linkage, no_plot=True)
row_order = row_dendro["leaves"]
col_order = col_dendro["leaves"]

# Reorder data and labels
data_ordered = data[row_order, :][:, col_order]
row_labels_ordered = [gene_labels[i] for i in row_order]
col_labels_ordered = [sample_labels[i] for i in col_order]

# Create subplots: top dendrogram, left dendrogram, main heatmap, colorbar space
fig = make_subplots(
    rows=2,
    cols=2,
    column_widths=[0.15, 0.85],
    row_heights=[0.15, 0.85],
    horizontal_spacing=0.005,
    vertical_spacing=0.005,
    specs=[[None, {}], [{}, {}]],
)

# Add top dendrogram (column clustering)
col_icoord = np.array(col_dendro["icoord"])
col_dcoord = np.array(col_dendro["dcoord"])
for i in range(len(col_icoord)):
    fig.add_trace(
        go.Scatter(
            x=col_icoord[i],
            y=col_dcoord[i],
            mode="lines",
            line={"color": "#306998", "width": 1.5},
            showlegend=False,
            hoverinfo="skip",
        ),
        row=1,
        col=2,
    )

# Add left dendrogram (row clustering) - rotated
row_icoord = np.array(row_dendro["icoord"])
row_dcoord = np.array(row_dendro["dcoord"])
for i in range(len(row_icoord)):
    fig.add_trace(
        go.Scatter(
            x=row_dcoord[i],  # Swap x/y for left orientation
            y=row_icoord[i],
            mode="lines",
            line={"color": "#306998", "width": 1.5},
            showlegend=False,
            hoverinfo="skip",
        ),
        row=2,
        col=1,
    )

# Add heatmap
fig.add_trace(
    go.Heatmap(
        z=data_ordered,
        x=col_labels_ordered,
        y=row_labels_ordered,
        colorscale="RdBu_r",
        zmid=0,
        colorbar={
            "title": {"text": "Expression (z-score)", "font": {"size": 20}},
            "tickfont": {"size": 16},
            "len": 0.75,
            "thickness": 25,
            "x": 1.02,
        },
        hovertemplate="%{y}<br>%{x}<br>Value: %{z:.2f}<extra></extra>",
    ),
    row=2,
    col=2,
)

# Update axes for top dendrogram
fig.update_xaxes(
    showticklabels=False,
    showgrid=False,
    zeroline=False,
    showline=False,
    range=[0, max(col_dendro["icoord"][-1])],
    row=1,
    col=2,
)
fig.update_yaxes(
    showticklabels=False,
    showgrid=False,
    zeroline=False,
    showline=False,
    range=[0, max(col_dendro["dcoord"][-1]) * 1.05],
    row=1,
    col=2,
)

# Update axes for left dendrogram
fig.update_xaxes(
    showticklabels=False,
    showgrid=False,
    zeroline=False,
    showline=False,
    range=[max(row_dendro["dcoord"][-1]) * 1.05, 0],
    row=2,
    col=1,
)
fig.update_yaxes(
    showticklabels=False,
    showgrid=False,
    zeroline=False,
    showline=False,
    range=[0, max(row_dendro["icoord"][-1])],
    row=2,
    col=1,
)

# Update heatmap axes
fig.update_xaxes(tickfont={"size": 16}, tickangle=45, side="bottom", row=2, col=2)
fig.update_yaxes(tickfont={"size": 16}, row=2, col=2)

# Update layout
fig.update_layout(
    title={"text": "heatmap-clustered · plotly · pyplots.ai", "font": {"size": 32}, "x": 0.5, "xanchor": "center"},
    template="plotly_white",
    showlegend=False,
    margin={"l": 100, "r": 120, "t": 120, "b": 120},
)

# Save outputs
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
