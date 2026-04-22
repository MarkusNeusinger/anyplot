""" pyplots.ai
heatmap-clustered: Clustered Heatmap
Library: letsplot 4.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave
from scipy.cluster.hierarchy import dendrogram, linkage


LetsPlot.setup_html()  # noqa: F405

# Data - Gene expression data for clustering analysis
np.random.seed(42)

# Generate gene names and sample names
n_genes = 20
n_samples = 15
gene_names = [f"Gene_{i + 1:02d}" for i in range(n_genes)]
sample_names = [f"Sample_{chr(65 + i)}" for i in range(n_samples)]

# Create gene expression data with cluster structure
# Group 1: High expression in samples 0-4
# Group 2: High expression in samples 5-9
# Group 3: High expression in samples 10-14
expression_data = np.random.randn(n_genes, n_samples)

# Add cluster structure for genes
for i in range(0, 7):
    expression_data[i, 0:5] += 2.5
    expression_data[i, 10:15] -= 1.5

for i in range(7, 14):
    expression_data[i, 5:10] += 2.5
    expression_data[i, 0:5] -= 1.0

for i in range(14, 20):
    expression_data[i, 10:15] += 2.5
    expression_data[i, 5:10] -= 1.5

# Add some noise variation
expression_data += np.random.randn(n_genes, n_samples) * 0.3

# Hierarchical clustering of rows (genes) and columns (samples)
row_linkage = linkage(expression_data, method="ward")
col_linkage = linkage(expression_data.T, method="ward")

# Get dendrogram ordering
row_dendro = dendrogram(row_linkage, no_plot=True)
col_dendro = dendrogram(col_linkage, no_plot=True)
row_order = row_dendro["leaves"]
col_order = col_dendro["leaves"]

# Reorder data based on clustering
reordered_data = expression_data[row_order, :][:, col_order]
reordered_genes = [gene_names[i] for i in row_order]
reordered_samples = [sample_names[i] for i in col_order]


# Function to build dendrogram segments from scipy dendrogram
def get_dendrogram_segments(dendro_dict):
    """Extract line segments from scipy dendrogram output."""
    segments = []
    icoord = np.array(dendro_dict["icoord"])
    dcoord = np.array(dendro_dict["dcoord"])

    for i in range(len(icoord)):
        xs = icoord[i]
        ys = dcoord[i]
        # Draw the U-shape: 3 segments (left vertical, horizontal, right vertical)
        segments.append((xs[0], ys[0], xs[1], ys[1]))
        segments.append((xs[1], ys[1], xs[2], ys[2]))
        segments.append((xs[2], ys[2], xs[3], ys[3]))

    return pd.DataFrame(segments, columns=["x", "y", "xend", "yend"])


# Create long-form data for heatmap
heatmap_rows = []
for i, gene in enumerate(reordered_genes):
    for j, sample in enumerate(reordered_samples):
        heatmap_rows.append(
            {"Gene": gene, "Sample": sample, "Expression": reordered_data[i, j], "gene_idx": i, "sample_idx": j}
        )

heatmap_df = pd.DataFrame(heatmap_rows)

# Set category order for proper display
heatmap_df["Gene"] = pd.Categorical(heatmap_df["Gene"], categories=reordered_genes[::-1], ordered=True)
heatmap_df["Sample"] = pd.Categorical(heatmap_df["Sample"], categories=reordered_samples, ordered=True)

# Get dendrogram segments
col_seg_df = get_dendrogram_segments(col_dendro)
row_seg_df = get_dendrogram_segments(row_dendro)

# Scale dendrogram coordinates to match heatmap
# Column dendrogram: x spans samples (0 to n_samples), y is height
col_seg_df["x"] = (col_seg_df["x"] / 10) - 0.5  # scipy uses 10*i spacing
col_seg_df["xend"] = (col_seg_df["xend"] / 10) - 0.5
# Normalize y to a reasonable range
max_col_height = max(col_seg_df["y"].max(), col_seg_df["yend"].max())
col_seg_df["y"] = col_seg_df["y"] / max_col_height * 4
col_seg_df["yend"] = col_seg_df["yend"] / max_col_height * 4

# Row dendrogram: swap x and y for horizontal orientation
row_seg_df_rotated = pd.DataFrame(
    {
        "x": row_seg_df["y"],
        "y": (row_seg_df["x"] / 10) - 0.5,
        "xend": row_seg_df["yend"],
        "yend": (row_seg_df["xend"] / 10) - 0.5,
    }
)
max_row_height = max(row_seg_df_rotated["x"].max(), row_seg_df_rotated["xend"].max())
row_seg_df_rotated["x"] = row_seg_df_rotated["x"] / max_row_height * 4
row_seg_df_rotated["xend"] = row_seg_df_rotated["xend"] / max_row_height * 4

# Create heatmap plot
heatmap_plot = (
    ggplot(heatmap_df, aes(x="Sample", y="Gene", fill="Expression"))
    + geom_tile(width=0.95, height=0.95)
    + scale_fill_gradient2(low="#2166AC", mid="#F7F7F7", high="#B2182B", midpoint=0, name="Expression\n(z-score)")
    + labs(x="Samples", y="Genes", title="heatmap-clustered · letsplot · pyplots.ai")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title_x=element_text(size=18),
        axis_title_y=element_text(size=18),
        axis_text_x=element_text(size=11, angle=45, hjust=1),
        axis_text_y=element_text(size=10),
        legend_title=element_text(size=14),
        legend_text=element_text(size=12),
        panel_grid=element_blank(),
    )
)

# Create column dendrogram (top)
col_dendro_plot = (
    ggplot(col_seg_df)
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), size=1.2, color="#306998")
    + scale_x_continuous(limits=[-0.5, n_samples - 0.5], expand=[0, 0])
    + scale_y_continuous(expand=[0.02, 0])
    + theme_void()
    + theme(plot_margin=[0, 0, 0, 0])
)

# Create row dendrogram (left) - needs to be mirrored
row_seg_df_rotated["x"] = 4 - row_seg_df_rotated["x"]
row_seg_df_rotated["xend"] = 4 - row_seg_df_rotated["xend"]

row_dendro_plot = (
    ggplot(row_seg_df_rotated)
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), size=1.2, color="#306998")
    + scale_x_continuous(expand=[0, 0.02])
    + scale_y_continuous(limits=[-0.5, n_genes - 0.5], expand=[0, 0])
    + theme_void()
    + theme(plot_margin=[0, 0, 0, 0])
)

# Combine plots using ggbunch with relative coordinates
# Layout: row dendrogram (left), column dendrogram (top), heatmap (center)
# Relative coordinates: (x, y, width, height) where (0,0) is top-left, (1,1) is bottom-right

row_dendro_w = 0.12
col_dendro_h = 0.18
heatmap_w = 0.88
heatmap_h = 0.82

bunch = (
    ggbunch(
        [row_dendro_plot, col_dendro_plot, heatmap_plot],
        [
            # Row dendrogram: left side, below the column dendrogram
            (0, col_dendro_h, row_dendro_w, heatmap_h),
            # Column dendrogram: top, to the right of row dendrogram
            (row_dendro_w, 0, heatmap_w, col_dendro_h),
            # Heatmap: main area
            (row_dendro_w, col_dendro_h, heatmap_w, heatmap_h),
        ],
    )
    + ggsize(1600, 900)  # 4800x2700 when scaled 3x
)

# Save as PNG (scale 3x for 4800x2700)
ggsave(bunch, "plot.png", path=".", scale=3)

# Save interactive HTML
ggsave(bunch, "plot.html", path=".")
