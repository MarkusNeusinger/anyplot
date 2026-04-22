""" pyplots.ai
heatmap-clustered: Clustered Heatmap
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.patches import Patch


# Data: Gene expression matrix (simulated)
np.random.seed(42)

# Create realistic gene expression data with natural clusters
n_genes = 30
n_samples = 20

# Gene groups (3 clusters)
gene_groups = np.repeat(["Immune", "Metabolic", "Signaling"], [10, 10, 10])

# Sample groups (2 conditions)
sample_groups = np.repeat(["Control", "Treatment"], [10, 10])

# Generate base expression patterns for each gene cluster
expression = np.zeros((n_genes, n_samples))

# Immune genes: higher in treatment
expression[0:10, 0:10] = np.random.normal(-1, 0.5, (10, 10))
expression[0:10, 10:20] = np.random.normal(1.5, 0.5, (10, 10))

# Metabolic genes: lower in treatment
expression[10:20, 0:10] = np.random.normal(1, 0.5, (10, 10))
expression[10:20, 10:20] = np.random.normal(-1.2, 0.5, (10, 10))

# Signaling genes: mixed response
expression[20:30, 0:10] = np.random.normal(0.3, 0.8, (10, 10))
expression[20:30, 10:20] = np.random.normal(-0.3, 0.8, (10, 10))

# Create gene and sample labels
gene_labels = [f"{gene_groups[i][0]}{i + 1:02d}" for i in range(n_genes)]
sample_labels = [f"{sample_groups[i][0]}{i + 1:02d}" for i in range(n_samples)]

# Create DataFrame
df = pd.DataFrame(expression, index=gene_labels, columns=sample_labels)

# Create color palettes for annotations
gene_palette = {"Immune": "#306998", "Metabolic": "#FFD43B", "Signaling": "#7B9F35"}
sample_palette = {"Control": "#E57373", "Treatment": "#64B5F6"}

gene_colors = pd.Series([gene_palette[g] for g in gene_groups], index=gene_labels)
sample_colors = pd.Series([sample_palette[s] for s in sample_groups], index=sample_labels)

# Plot: Clustered heatmap with dendrograms
sns.set_context("talk", font_scale=1.1)

g = sns.clustermap(
    df,
    method="ward",
    metric="euclidean",
    cmap="RdBu_r",
    center=0,
    vmin=-3,
    vmax=3,
    row_colors=gene_colors,
    col_colors=sample_colors,
    dendrogram_ratio=(0.15, 0.15),
    cbar_pos=(0.02, 0.3, 0.03, 0.4),
    figsize=(14, 12),
    linewidths=0.5,
    linecolor="white",
    xticklabels=True,
    yticklabels=True,
    tree_kws={"linewidths": 2},
)

# Style adjustments
g.ax_heatmap.set_xlabel("Samples", fontsize=20)
g.ax_heatmap.set_ylabel("Genes", fontsize=20)
g.ax_heatmap.tick_params(axis="x", labelsize=12, rotation=45)
g.ax_heatmap.tick_params(axis="y", labelsize=12)

# Title
g.figure.suptitle("heatmap-clustered · seaborn · pyplots.ai", fontsize=24, y=1.02)

# Colorbar label
g.cax.set_ylabel("Expression (z-score)", fontsize=14)
g.cax.tick_params(labelsize=12)

# Add legends for row/column colors
# Gene group legend
gene_legend = [Patch(facecolor=gene_palette[k], label=k) for k in gene_palette]
g.ax_heatmap.legend(
    handles=gene_legend,
    title="Gene Group",
    loc="upper left",
    bbox_to_anchor=(1.15, 1.0),
    fontsize=12,
    title_fontsize=14,
)

# Sample group legend (as second legend)
sample_legend = [Patch(facecolor=sample_palette[k], label=k) for k in sample_palette]
g.figure.legend(
    handles=sample_legend,
    title="Condition",
    loc="upper left",
    bbox_to_anchor=(0.88, 0.45),
    fontsize=12,
    title_fontsize=14,
)

plt.savefig("plot.png", dpi=300, bbox_inches="tight")
