"""anyplot.ai
heatmap-clustered: Clustered Heatmap
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-11-09
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Patch


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint diverging cmap for z-scores; the annotation strips skip its two end hues
DIV_LOW, DIV_HIGH = "#4467A3", "#AE3030"
imprint_div = LinearSegmentedColormap.from_list("imprint_div", [DIV_LOW, PAGE_BG, DIV_HIGH])
ANNOTATION_COLORS = [c for c in IMPRINT_PALETTE if c not in (DIV_LOW, DIV_HIGH)]

sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.15,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Columns: set these to your matrix's index and column level names and its value label
GENE_GROUP = "Gene group"  # role: extra
GENE = "Genes"  # role: row_labels
CONDITION = "Condition"  # role: extra
SAMPLE = "Samples"  # role: column_labels
EXPRESSION = "Expression (z-score)"  # role: matrix

# Data: replace this block with your own labeled matrix, for example df = pd.read_csv("expr.csv", index_col=0)
np.random.seed(42)
gene_groups = np.repeat(["Immune", "Metabolic", "Signaling"], [10, 10, 10])
sample_groups = np.repeat(["Control", "Treatment"], [10, 10])
expression = np.zeros((30, 20))
# Immune genes: higher in treatment
expression[0:10, 0:10] = np.random.normal(-1, 0.5, (10, 10))
expression[0:10, 10:20] = np.random.normal(1.5, 0.5, (10, 10))
# Metabolic genes: lower in treatment
expression[10:20, 0:10] = np.random.normal(1, 0.5, (10, 10))
expression[10:20, 10:20] = np.random.normal(-1.2, 0.5, (10, 10))
# Signaling genes: mixed response
expression[20:30, 0:10] = np.random.normal(0.3, 0.8, (10, 10))
expression[20:30, 10:20] = np.random.normal(-0.3, 0.8, (10, 10))
gene_labels = [f"{g[0]}{i + 1:02d}" for i, g in enumerate(gene_groups)]
sample_labels = [f"{s[0]}{i + 1:02d}" for i, s in enumerate(sample_groups)]
df = pd.DataFrame(
    expression,
    index=pd.MultiIndex.from_arrays([gene_groups, gene_labels], names=[GENE_GROUP, GENE]),
    columns=pd.MultiIndex.from_arrays([sample_groups, sample_labels], names=[CONDITION, SAMPLE]),
)

# Plot: reads only df and the constants above
matrix = df.copy()
row_colors = col_colors = None
legends = []
used = 0
for axis, title in ((0, GENE_GROUP), (1, CONDITION)):
    index = matrix.axes[axis]
    if index.nlevels < 2:
        continue
    groups = pd.unique(index.get_level_values(0))
    colors = dict(zip(groups, ANNOTATION_COLORS[used:], strict=False))
    used += len(groups)
    strip = pd.Series([colors[g] for g in index.get_level_values(0)], index=index.get_level_values(-1), name="")
    legends.append((title, [Patch(facecolor=colors[g], edgecolor=INK_SOFT, label=g) for g in groups]))
    if axis == 0:
        row_colors = strip
    else:
        col_colors = strip
matrix.index = matrix.index.get_level_values(-1)
matrix.columns = matrix.columns.get_level_values(-1)
limit = np.nanmax(np.abs(matrix.to_numpy()))

g = sns.clustermap(
    matrix,
    method="ward",
    metric="euclidean",
    cmap=imprint_div,
    center=0,
    vmin=-limit,
    vmax=limit,
    row_colors=row_colors,
    col_colors=col_colors,
    dendrogram_ratio=(0.14, 0.14),
    colors_ratio=0.025,
    cbar_pos=(0.03, 0.86, 0.025, 0.1),
    figsize=(6, 6),
    linewidths=0.3,
    linecolor=PAGE_BG,
    xticklabels=True,
    yticklabels=True,
    tree_kws={"linewidths": 0.9, "colors": INK_SOFT},
)
g.figure.subplots_adjust(left=0.02, right=0.88, top=0.9, bottom=0.17)

# Style
g.ax_heatmap.set_xlabel(SAMPLE, fontsize=10, color=INK)
g.ax_heatmap.set_ylabel(GENE, fontsize=10, color=INK)
g.ax_heatmap.tick_params(axis="x", labelsize=6, rotation=90, colors=INK_SOFT, length=2)
g.ax_heatmap.tick_params(axis="y", labelsize=6, rotation=0, colors=INK_SOFT, length=2)
for strip_ax in (g.ax_row_colors, g.ax_col_colors):
    if strip_ax is not None:
        strip_ax.tick_params(labelsize=6, colors=INK_SOFT, length=0)
g.cax.set_title(EXPRESSION, fontsize=7, color=INK, loc="left", pad=4)
g.cax.tick_params(labelsize=6, colors=INK_SOFT, length=2)

g.figure.suptitle(
    "heatmap-clustered · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK, y=0.97
)

for i, (title, handles) in enumerate(legends):
    g.figure.legend(
        handles=handles,
        title=title,
        loc="lower left" if i == 0 else "lower right",
        bbox_to_anchor=(0.02, 0.005) if i == 0 else (0.98, 0.005),
        ncol=len(handles),
        fontsize=7,
        title_fontsize=8,
        frameon=False,
        handlelength=1.2,
        columnspacing=1.0,
    )

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
