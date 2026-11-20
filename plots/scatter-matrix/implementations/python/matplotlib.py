"""anyplot.ai
scatter-matrix: Scatter Plot Matrix
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-09
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import MaxNLocator


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette, canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns
VARIABLES = ["Sepal Length (cm)", "Sepal Width (cm)", "Petal Length (cm)", "Petal Width (cm)"]  # role: variables
SPECIES = "Species"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("flowers.csv")
rng = np.random.default_rng(42)
species_params = {
    "Setosa": [(5.0, 0.35), (3.4, 0.38), (1.5, 0.17), (0.2, 0.1)],
    "Versicolor": [(5.9, 0.52), (2.8, 0.31), (4.3, 0.47), (1.3, 0.2)],
    "Virginica": [(6.6, 0.64), (3.0, 0.32), (5.5, 0.55), (2.0, 0.27)],
}
frames = []
for name, params in species_params.items():
    block = {var: rng.normal(mean, std, 50) for var, (mean, std) in zip(VARIABLES, params, strict=True)}
    block[SPECIES] = name
    frames.append(pd.DataFrame(block))
df = pd.concat(frames, ignore_index=True)

# Plot
groups = list(df[SPECIES].unique())
colors = {g: IMPRINT_PALETTE[k % len(IMPRINT_PALETTE)] for k, g in enumerate(groups)}
n_vars = len(VARIABLES)
limits = {}
for var in VARIABLES:
    pad = (df[var].max() - df[var].min()) * 0.06
    limits[var] = (df[var].min() - pad, df[var].max() + pad)

fig, axes = plt.subplots(n_vars, n_vars, figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
fig.subplots_adjust(left=0.12, right=0.97, bottom=0.09, top=0.84, wspace=0.08, hspace=0.08)

for i, row_var in enumerate(VARIABLES):
    for j, col_var in enumerate(VARIABLES):
        ax = axes[i, j]
        ax.set_facecolor(ELEVATED_BG if i == j else PAGE_BG)
        ax.set_xlim(*limits[col_var])
        bins = np.histogram_bin_edges(df[col_var], bins=14, range=limits[col_var])
        for group in groups:
            rows = df[df[SPECIES] == group]
            if i == j:
                ax.hist(rows[col_var], bins=bins, color=colors[group], alpha=0.65, edgecolor=INK_SOFT, linewidth=0.3)
            else:
                ax.scatter(rows[col_var], rows[row_var], s=9, color=colors[group], alpha=0.6, edgecolors="none")
        if i != j:
            ax.set_ylim(*limits[row_var])

        ax.grid(True, alpha=0.15, color=INK_SOFT, linewidth=0.4)
        ax.set_axisbelow(True)
        ax.xaxis.set_major_locator(MaxNLocator(nbins=3, prune="both"))
        ax.yaxis.set_major_locator(MaxNLocator(nbins=3, prune="both"))
        ax.tick_params(axis="both", labelsize=6, colors=INK_SOFT, length=2, width=0.5)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(INK_SOFT)
            ax.spines[side].set_linewidth(0.5)

        if i == n_vars - 1:
            ax.set_xlabel(col_var, fontsize=8, color=INK)
        else:
            ax.tick_params(axis="x", labelbottom=False)
        if j == 0:
            ax.set_ylabel(row_var, fontsize=8, color=INK)
        if j != 0 or i == 0:
            ax.tick_params(axis="y", labelleft=False)

handles = [
    plt.Line2D(
        [0],
        [0],
        marker="o",
        linestyle="",
        markersize=5,
        markerfacecolor=colors[group],
        markeredgecolor="none",
        label=group,
    )
    for k, group in enumerate(groups)
]
leg = fig.legend(
    handles=handles,
    title=SPECIES,
    loc="upper center",
    bbox_to_anchor=(0.545, 0.95),
    ncol=len(groups),
    fontsize=8,
    title_fontsize=8,
    frameon=True,
)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
leg.get_title().set_color(INK)
for text in leg.get_texts():
    text.set_color(INK)

fig.suptitle("scatter-matrix · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK, y=0.985)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
