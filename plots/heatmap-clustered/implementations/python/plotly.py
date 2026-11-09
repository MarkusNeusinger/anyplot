"""anyplot.ai
heatmap-clustered: Clustered Heatmap
Library: plotly | Python 3.13
Quality: pending | Updated: 2026-11-09
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.cluster.hierarchy import dendrogram, fcluster, linkage


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per gene cluster in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
# Imprint diverging scale for z-scores centered on zero; the midpoint follows the page
IMPRINT_DIV = [[0.0, "#AE3030"], [0.5, PAGE_BG], [1.0, "#4467A3"]]

# Constants
N_GENE_CLUSTERS = 4  # the row dendrogram is cut into this many annotated gene clusters

# Columns: set these to your table's labels
EXPRESSION = "Expression (z-score)"  # role: matrix
GENE = "Gene"  # role: row_labels
SAMPLE = "Sample"  # role: column_labels

# Data: replace this block with your own matrix, for example df = pd.read_csv("expression.csv", index_col=0)
np.random.seed(42)
genes = ["CDK1", "CCNB1", "PLK1", "AURKA", "BUB1"]  # cell cycle
genes += ["GAPDH", "LDHA", "PKM", "HK2", "ENO1"]  # metabolism
genes += ["IL6", "TNF", "IFNG", "IL1B", "CXCL8"]  # immune response
genes += ["MYC", "TP53", "BRCA1", "EGFR", "VEGFA"]  # cancer-related
samples = ["T1_A", "T1_B", "T1_C", "T2_A", "T2_B", "T2_C", "N1_A", "N1_B", "N1_C", "N2_A", "N2_B", "N2_C"]
expression = np.random.randn(len(genes), len(samples)) * 0.5
expression[0:5, 0:6] += 2.0  # cell cycle up in tumors
expression[0:5, 6:12] -= 1.5
expression[5:10, 0:6] += 1.2  # metabolism moderately up in tumors
expression[5:10, 6:12] -= 0.8
expression[10:15, 0:3] += 1.5  # immune response mixed
expression[10:15, 3:6] -= 0.5
expression[10:15, 6:9] += 0.8
expression[10:15, 9:12] -= 1.2
expression[15:20, 0:6] += 1.8  # cancer-related up in tumors
expression[15:20, 6:12] -= 1.0
df = pd.DataFrame(expression, index=genes, columns=samples)

# Plot: reads only df and the constants above
matrix = df.astype(float)
filled = matrix.fillna(matrix.mean().mean())  # clustering needs complete rows; the heatmap keeps the gaps
row_linkage = linkage(filled.to_numpy(), method="ward", metric="euclidean")
col_linkage = linkage(filled.to_numpy().T, method="ward", metric="euclidean")
row_dendro = dendrogram(row_linkage, no_plot=True)
col_dendro = dendrogram(col_linkage, no_plot=True)
ordered = matrix.iloc[row_dendro["leaves"], col_dendro["leaves"]]
n_rows, n_cols = ordered.shape

# Gene clusters from the row dendrogram, numbered in the order they appear from the bottom
raw_clusters = fcluster(row_linkage, t=min(N_GENE_CLUSTERS, n_rows), criterion="maxclust")[row_dendro["leaves"]]
cluster_ids = list(dict.fromkeys(raw_clusters))
gene_cluster = np.array([cluster_ids.index(c) for c in raw_clusters])
n_clusters = len(cluster_ids)
cluster_scale = []
for i in range(n_clusters):
    cluster_scale += [[i / n_clusters, IMPRINT_PALETTE[i]], [(i + 1) / n_clusters, IMPRINT_PALETTE[i]]]

z_limit = np.nanmax(np.abs(ordered.to_numpy()))

fig = make_subplots(
    rows=2,
    cols=3,
    column_widths=[0.13, 0.035, 0.835],
    row_heights=[0.15, 0.85],
    horizontal_spacing=0.006,
    vertical_spacing=0.008,
    specs=[[None, None, {}], [{}, {}, {}]],
)

# Column dendrogram above the matrix; scipy leaf positions 5, 15, 25, … map to cell indexes 0, 1, 2, …
for xs, ys in zip(col_dendro["icoord"], col_dendro["dcoord"], strict=True):
    fig.add_trace(
        go.Scatter(
            x=(np.array(xs) - 5) / 10,
            y=ys,
            mode="lines",
            line={"color": INK_SOFT, "width": 2},
            showlegend=False,
            hoverinfo="skip",
        ),
        row=1,
        col=3,
    )

# Row dendrogram left of the matrix, growing leftwards
for xs, ys in zip(row_dendro["icoord"], row_dendro["dcoord"], strict=True):
    fig.add_trace(
        go.Scatter(
            x=ys,
            y=(np.array(xs) - 5) / 10,
            mode="lines",
            line={"color": INK_SOFT, "width": 2},
            showlegend=False,
            hoverinfo="skip",
        ),
        row=2,
        col=1,
    )

# Gene cluster strip, one cell per row
fig.add_trace(
    go.Heatmap(
        z=gene_cluster.reshape(-1, 1),
        x=[0],
        y=np.arange(n_rows),
        colorscale=cluster_scale,
        zmin=-0.5,
        zmax=n_clusters - 0.5,
        showscale=False,
        xgap=0,
        ygap=1,
        customdata=(gene_cluster + 1).reshape(-1, 1),
        text=np.array(ordered.index, dtype=str).reshape(-1, 1),
        hovertemplate="%{text}<br>Gene cluster %{customdata}<extra></extra>",
    ),
    row=2,
    col=2,
)

# Clustered matrix
fig.add_trace(
    go.Heatmap(
        z=ordered.to_numpy(),
        x=np.arange(n_cols),
        y=np.arange(n_rows),
        colorscale=IMPRINT_DIV,
        zmid=0,
        zmin=-z_limit,
        zmax=z_limit,
        xgap=1,
        ygap=1,
        customdata=np.array([[(gene, sample) for sample in ordered.columns] for gene in ordered.index], dtype=str),
        hovertemplate=f"{GENE} %{{customdata[0]}}<br>{SAMPLE} %{{customdata[1]}}<br>"
        + f"{EXPRESSION}: %{{z:.2f}}<extra></extra>",
        colorbar={
            "title": {"text": EXPRESSION.replace(" (", "<br>("), "font": {"size": 12, "color": INK}, "side": "top"},
            "tickfont": {"size": 10, "color": INK_SOFT},
            "len": 0.5,
            "y": 0.3,
            "thickness": 16,
            "x": 1.19,
            "outlinewidth": 0,
            "bgcolor": PAGE_BG,
        },
    ),
    row=2,
    col=3,
)

# Legend entries for the cluster strip
for i in range(n_clusters):
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker={"symbol": "square", "size": 12, "color": IMPRINT_PALETTE[i]},
            name=f"Cluster {i + 1}",
            legendgroup="clusters",
            legendgrouptitle={"text": "Gene cluster", "font": {"size": 11, "color": INK}},
        ),
        row=2,
        col=3,
    )

# Axes
hidden = {"showticklabels": False, "showgrid": False, "zeroline": False, "showline": False, "ticks": ""}
cell_x = [-0.5, n_cols - 0.5]
cell_y = [-0.5, n_rows - 0.5]
fig.update_xaxes(range=cell_x, **hidden, row=1, col=3)
fig.update_yaxes(range=[0, max(max(d) for d in col_dendro["dcoord"]) * 1.05], **hidden, row=1, col=3)
fig.update_xaxes(range=[max(max(d) for d in row_dendro["dcoord"]) * 1.05, 0], **hidden, row=2, col=1)
fig.update_yaxes(range=cell_y, **hidden, row=2, col=1)
fig.update_xaxes(range=[-0.5, 0.5], **hidden, row=2, col=2)
fig.update_yaxes(range=cell_y, **hidden, row=2, col=2)
fig.update_xaxes(
    range=cell_x,
    tickmode="array",
    tickvals=np.arange(n_cols),
    ticktext=list(ordered.columns),
    title={"text": SAMPLE, "font": {"size": 12, "color": INK}},
    tickfont={"size": 10, "color": INK_SOFT},
    tickangle=-45,
    showgrid=False,
    zeroline=False,
    showline=False,
    ticks="",
    row=2,
    col=3,
)
fig.update_yaxes(
    range=cell_y,
    tickmode="array",
    tickvals=np.arange(n_rows),
    ticktext=list(ordered.index),
    title={"text": GENE, "font": {"size": 12, "color": INK}},
    tickfont={"size": 10, "color": INK_SOFT},
    side="right",
    showgrid=False,
    zeroline=False,
    showline=False,
    ticks="",
    row=2,
    col=3,
)

# Layout
fig.update_layout(
    autosize=False,
    width=600,
    height=600,
    title={
        "text": "heatmap-clustered · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    legend={
        "x": 1.19,
        "y": 1.0,
        "xanchor": "left",
        "yanchor": "top",
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "font": {"size": 10, "color": INK_SOFT},
    },
    margin={"l": 30, "r": 170, "t": 60, "b": 60},
    hovermode="closest",
)

# Save
fig.write_image(f"plot-{THEME}.png", width=600, height=600, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
