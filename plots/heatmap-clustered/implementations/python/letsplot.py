"""anyplot.ai
heatmap-clustered: Clustered Heatmap
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-09
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave
from scipy.cluster.hierarchy import dendrogram, linkage


LetsPlot.setup_html()  # noqa: F405

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: diverging map from the negative to the positive anchor, midpoint follows the page
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
IMPRINT_DIV = (IMPRINT_PALETTE[4], PAGE_BG, IMPRINT_PALETTE[2])

# Columns: set these to your table's labels
GENE = "Genes"  # role: row_labels
SAMPLE = "Samples"  # role: column_labels
EXPRESSION = "Expression (z-score)"  # role: matrix

# Data: replace this block with your own labeled matrix, for example df = pd.read_csv("expression.csv", index_col=0)
rng = np.random.default_rng(42)
n_genes, n_samples = 20, 15
values = rng.standard_normal((n_genes, n_samples))
values[0:7, 0:5] += 2.5
values[0:7, 10:15] -= 1.5
values[7:14, 5:10] += 2.5
values[7:14, 0:5] -= 1.0
values[14:20, 10:15] += 2.5
values[14:20, 5:10] -= 1.5
values += rng.standard_normal((n_genes, n_samples)) * 0.3
df = pd.DataFrame(
    values,
    index=[f"Gene_{i + 1:02d}" for i in range(n_genes)],
    columns=[f"Sample_{chr(65 + i)}" for i in range(n_samples)],
)

# Plot: reads only df and the constants above
row_dendro = dendrogram(linkage(df.to_numpy(), method="ward"), no_plot=True)
col_dendro = dendrogram(linkage(df.to_numpy().T, method="ward"), no_plot=True)
clustered = df.iloc[row_dendro["leaves"], col_dendro["leaves"]]
n_rows, n_cols = clustered.shape

# One shared coordinate system keeps every dendrogram leaf on its own row or column of cells
tiles = clustered.reset_index(names=GENE).melt(id_vars=GENE, var_name=SAMPLE, value_name=EXPRESSION)
tiles["x"] = tiles[SAMPLE].map({name: i for i, name in enumerate(clustered.columns)})
tiles["y"] = tiles[GENE].map({name: n_rows - 1 - i for i, name in enumerate(clustered.index)})


def dendro_segments(tree):
    """Return the U-shaped links as segments: leaf positions 0..n-1, heights as merge distance."""
    xs = [(np.array(x) - 5) / 10 for x in tree["icoord"]]
    ys = [np.array(d) for d in tree["dcoord"]]
    rows = [(x[k], y[k], x[k + 1], y[k + 1]) for x, y in zip(xs, ys, strict=True) for k in range(3)]
    return pd.DataFrame(rows, columns=["pos", "height", "pos_end", "height_end"])


gap, share = 0.4, 0.22  # space between matrix and tree, tree depth as a share of the matrix side
col_seg = dendro_segments(col_dendro)
row_seg = dendro_segments(row_dendro)
col_scale = share * n_rows / col_seg[["height", "height_end"]].to_numpy().max()
row_scale = share * n_cols / row_seg[["height", "height_end"]].to_numpy().max()
# Column tree grows upward from the top edge of the matrix
col_seg = pd.DataFrame(
    {
        "x": col_seg["pos"],
        "y": n_rows - 0.5 + gap + col_seg["height"] * col_scale,
        "xend": col_seg["pos_end"],
        "yend": n_rows - 0.5 + gap + col_seg["height_end"] * col_scale,
    }
)
# Row tree grows to the left of the matrix; genes run top to bottom, so leaf positions are flipped
row_seg = pd.DataFrame(
    {
        "x": -0.5 - gap - row_seg["height"] * row_scale,
        "y": n_rows - 1 - row_seg["pos"],
        "xend": -0.5 - gap - row_seg["height_end"] * row_scale,
        "yend": n_rows - 1 - row_seg["pos_end"],
    }
)
x_min = min(row_seg["x"].min(), row_seg["xend"].min())
y_max = max(col_seg["y"].max(), col_seg["yend"].max())

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid=element_blank(),
    axis_title=element_text(color=INK, size=12),
    axis_text=element_text(color=INK_SOFT, size=10),
    axis_line=element_blank(),
    axis_ticks=element_blank(),
    plot_title=element_text(color=INK, size=16, face="bold"),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=10),
    legend_title=element_text(color=INK, size=11),
)

plot = (
    ggplot()
    + geom_tile(aes(x="x", y="y", fill=EXPRESSION), data=tiles, width=0.96, height=0.96)
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=col_seg, size=0.8, color=INK_SOFT)
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=row_seg, size=0.8, color=INK_SOFT)
    + scale_fill_gradient2(low=IMPRINT_DIV[0], mid=IMPRINT_DIV[1], high=IMPRINT_DIV[2], midpoint=0)
    + scale_x_continuous(
        breaks=list(range(n_cols)), labels=list(clustered.columns), limits=[x_min, n_cols - 0.5], expand=[0, 0.01]
    )
    + scale_y_continuous(
        breaks=list(range(n_rows)),
        labels=list(clustered.index[::-1]),
        limits=[-0.5, y_max],
        position="right",
        expand=[0, 0.01],
    )
    + labs(title="heatmap-clustered · python · letsplot · anyplot.ai", x=SAMPLE, y=GENE)
    + theme_minimal()
    + theme(axis_text_x=element_text(angle=45, hjust=1))
    + anyplot_theme
    + ggsize(800, 450)
)

ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
