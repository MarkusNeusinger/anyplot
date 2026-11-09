""" anyplot.ai
heatmap-clustered: Clustered Heatmap
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 86/100 | Updated: 2026-11-09
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from scipy.cluster.hierarchy import dendrogram, linkage


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint diverging colormap: matte red ↔ theme surface ↔ blue
imprint_div = LinearSegmentedColormap.from_list("imprint_div", ["#AE3030", PAGE_BG, "#4467A3"])

# Columns: set this to the label of your matrix values
EXPRESSION = "Expression (z-score)"  # role: matrix

# Data: replace this block with your own matrix, for example df = pd.read_csv("expression.csv", index_col=0)
np.random.seed(42)
genes = [
    "CDK1",
    "CCNB1",
    "PLK1",
    "AURKA",
    "BUB1",  # Cell cycle genes
    "GAPDH",
    "LDHA",
    "PKM",
    "HK2",
    "ENO1",  # Metabolism genes
    "IL6",
    "TNF",
    "IFNG",
    "IL1B",
    "CXCL8",  # Immune response genes
]
samples = ["T1_A", "T1_B", "T1_C", "T2_A", "T2_B", "T2_C", "N1_A", "N1_B", "N1_C", "N2_A", "N2_B", "N2_C"]
values = np.random.randn(len(genes), len(samples)) * 0.5
values[0:5, 0:6] += 2.0  # Cell cycle genes upregulated in tumors
values[0:5, 6:12] -= 1.5
values[5:10, 0:6] += 1.0  # Metabolism genes moderately upregulated in tumors
values[5:10, 6:12] -= 0.5
values[10:15, 0:3] += 1.5  # Immune genes show a mixed pattern
values[10:15, 3:6] -= 0.5
values[10:15, 6:9] += 0.8
values[10:15, 9:12] -= 1.0
df = pd.DataFrame(values, index=genes, columns=samples)

# Plot: Ward linkage on Euclidean distances, rows and columns reordered by the dendrograms
matrix = df.to_numpy(dtype=float)
filled = np.where(np.isnan(matrix), np.nanmean(matrix), matrix)
row_linkage = linkage(filled, method="ward", metric="euclidean")
col_linkage = linkage(filled.T, method="ward", metric="euclidean")
row_order = dendrogram(row_linkage, no_plot=True)["leaves"]
col_order = dendrogram(col_linkage, no_plot=True)["leaves"]
clustered = df.iloc[row_order, col_order]
vmax = np.nanmax(np.abs(clustered.to_numpy(dtype=float)))

fig = plt.figure(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
gs = fig.add_gridspec(
    2,
    2,
    width_ratios=[0.18, 1],
    height_ratios=[0.18, 1],
    wspace=0.01,
    hspace=0.01,
    left=0.04,
    right=0.78,
    top=0.92,
    bottom=0.11,
)

# Column dendrogram (top) — dendrogram leaves sit at 5, 15, 25, … in its own units
ax_col = fig.add_subplot(gs[0, 1])
dendrogram(col_linkage, ax=ax_col, color_threshold=0, above_threshold_color=INK_SOFT)
ax_col.set_xlim(0, 10 * len(col_order))

# Row dendrogram (left) — leaf order flipped so it reads top-down like the heatmap rows
ax_row = fig.add_subplot(gs[1, 0])
dendrogram(row_linkage, ax=ax_row, orientation="left", color_threshold=0, above_threshold_color=INK_SOFT)
ax_row.set_ylim(10 * len(row_order), 0)

for ax in (ax_col, ax_row):
    ax.set_facecolor(PAGE_BG)
    ax.set_xticks([])
    ax.set_yticks([])
    for line in ax.collections:
        line.set_linewidth(1.4)
    for spine in ax.spines.values():
        spine.set_visible(False)

# Heatmap (center)
ax_heat = fig.add_subplot(gs[1, 1])
ax_heat.set_facecolor(PAGE_BG)
im = ax_heat.imshow(clustered.to_numpy(dtype=float), cmap=imprint_div, aspect="auto", vmin=-vmax, vmax=vmax)
ax_heat.set_xticks(np.arange(clustered.shape[1]), clustered.columns, rotation=45, ha="right")
ax_heat.set_yticks(np.arange(clustered.shape[0]), clustered.index)
ax_heat.yaxis.tick_right()
ax_heat.tick_params(axis="both", length=0, labelsize=8, colors=INK_SOFT, pad=3)
ax_heat.set_xticks(np.arange(clustered.shape[1] + 1) - 0.5, minor=True)
ax_heat.set_yticks(np.arange(clustered.shape[0] + 1) - 0.5, minor=True)
ax_heat.grid(which="minor", color=PAGE_BG, linewidth=1.0)
ax_heat.tick_params(which="minor", length=0)
for spine in ax_heat.spines.values():
    spine.set_visible(False)

# Colorbar — placed right of the gene labels, spanning the heatmap height
heat_box = ax_heat.get_position()
ax_cbar = fig.add_axes([0.89, heat_box.y0, 0.025, heat_box.height])
cbar = fig.colorbar(im, cax=ax_cbar)
cbar.set_label(EXPRESSION, fontsize=10, color=INK)
cbar.ax.tick_params(labelsize=8, colors=INK_SOFT, length=0)
cbar.outline.set_visible(False)

# Title
fig.suptitle(
    "heatmap-clustered · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK, y=0.97
)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
