""" anyplot.ai
scatter-matrix: Scatter Plot Matrix
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-09
"""

import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (3 colors for 3 species)
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data: Iris-like flower measurements (4 variables, 3 species)
np.random.seed(42)

species_params = {
    "Setosa": {"sl": (5.0, 0.35), "sw": (3.4, 0.38), "pl": (1.5, 0.17), "pw": (0.2, 0.1)},
    "Versicolor": {"sl": (5.9, 0.52), "sw": (2.8, 0.31), "pl": (4.3, 0.47), "pw": (1.3, 0.2)},
    "Virginica": {"sl": (6.6, 0.64), "sw": (3.0, 0.32), "pl": (5.5, 0.55), "pw": (2.0, 0.27)},
}

n_per_species = 50
data = {var: [] for var in ["Sepal Length (cm)", "Sepal Width (cm)", "Petal Length (cm)", "Petal Width (cm)"]}
species_labels = []
var_keys = ["sl", "sw", "pl", "pw"]
var_names = ["Sepal Length (cm)", "Sepal Width (cm)", "Petal Length (cm)", "Petal Width (cm)"]

for idx, (_species, params) in enumerate(species_params.items()):
    for key, name in zip(var_keys, var_names, strict=True):
        mean, std = params[key]
        data[name].extend(np.random.normal(mean, std, n_per_species))
    species_labels.extend([idx] * n_per_species)

# Convert to arrays
data_arrays = [np.array(data[name]) for name in var_names]
species_names = list(species_params.keys())
species_indices = np.array(species_labels)
n_vars = len(var_names)

# Create figure with extra space for legend
fig = plt.figure(figsize=(16, 9), facecolor=PAGE_BG)
gs = GridSpec(n_vars, n_vars, figure=fig, left=0.08, right=0.88, wspace=0.15, hspace=0.15)
axes = [[fig.add_subplot(gs[i, j]) for j in range(n_vars)] for i in range(n_vars)]

# Plot each cell
for i in range(n_vars):
    for j in range(n_vars):
        ax = axes[i][j]
        ax.set_facecolor(PAGE_BG)

        if i == j:
            # Diagonal: histograms with enhanced visual hierarchy
            for species_idx, (_species, color) in enumerate(zip(species_names, IMPRINT, strict=True)):
                mask = species_indices == species_idx
                species_data = data_arrays[i][mask]
                ax.hist(species_data, bins=12, alpha=0.85, color=color, edgecolor=INK_SOFT, linewidth=1.0)
        else:
            # Off-diagonal: scatter plots with enhanced marker definition
            for species_idx, (_species, color) in enumerate(zip(species_names, IMPRINT, strict=True)):
                mask = species_indices == species_idx
                ax.scatter(
                    data_arrays[j][mask],
                    data_arrays[i][mask],
                    c=color,
                    s=140,
                    alpha=0.8,
                    edgecolors=INK_SOFT,
                    linewidth=0.8,
                )

        # Grid styling
        ax.grid(True, alpha=0.12, linestyle="-", color=INK_SOFT, linewidth=0.6)
        ax.tick_params(axis="both", labelsize=14, colors=INK_SOFT)

        # Remove top and right spines for refined look
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color(INK_SOFT)
        ax.spines["left"].set_linewidth(0.8)
        ax.spines["bottom"].set_color(INK_SOFT)
        ax.spines["bottom"].set_linewidth(0.8)

        # Visual distinction: subtle background for diagonal (histogram) cells
        if i == j:
            ax.set_facecolor(ELEVATED_BG)
        else:
            ax.set_facecolor(PAGE_BG)

        # Axis labels only on edges
        if i == n_vars - 1:
            ax.set_xlabel(var_names[j], fontsize=18, color=INK)
        else:
            ax.set_xticklabels([])

        if j == 0:
            ax.set_ylabel(var_names[i], fontsize=18, color=INK)
        else:
            ax.set_yticklabels([])

# Legend outside matrix (right side)
legend_elements = [
    plt.Line2D(
        [0],
        [0],
        marker="o",
        color="w",
        markerfacecolor=color,
        markersize=12,
        label=species,
        markeredgecolor=PAGE_BG,
        markeredgewidth=0.5,
    )
    for species, color in zip(species_names, IMPRINT, strict=True)
]
leg = fig.legend(
    handles=legend_elements, loc="center right", fontsize=16, frameon=True, fancybox=False, edgecolor=INK_SOFT
)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
for text in leg.get_texts():
    text.set_color(INK)

# Title
fig.suptitle("scatter-matrix · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK, y=0.98)

plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
