""" pyplots.ai
scatter-matrix: Scatter Plot Matrix
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec


# Data: Iris-like flower measurements (4 variables, 3 species)
np.random.seed(42)

# Species parameters (mean, std for each measurement)
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

for species, params in species_params.items():
    for key, name in zip(var_keys, var_names, strict=True):
        mean, std = params[key]
        data[name].extend(np.random.normal(mean, std, n_per_species))
    species_labels.extend([species] * n_per_species)

# Convert to arrays
data_arrays = [np.array(data[name]) for name in var_names]
n_vars = len(var_names)

# Colors for species
colors_map = {"Setosa": "#306998", "Versicolor": "#FFD43B", "Virginica": "#4CAF50"}
colors = [colors_map[s] for s in species_labels]

# Create scatter plot matrix using GridSpec for tighter control (square format)
fig = plt.figure(figsize=(12, 12))
gs = GridSpec(n_vars, n_vars, figure=fig, wspace=0.08, hspace=0.08)
axes = [[fig.add_subplot(gs[i, j]) for j in range(n_vars)] for i in range(n_vars)]

# Plot each cell
for i in range(n_vars):
    for j in range(n_vars):
        ax = axes[i][j]

        if i == j:
            # Diagonal: histograms for each species
            for species, color in colors_map.items():
                mask = [s == species for s in species_labels]
                species_data = data_arrays[i][mask]
                ax.hist(species_data, bins=12, alpha=0.7, color=color, edgecolor="white", linewidth=0.5)
        else:
            # Off-diagonal: scatter plots with increased marker size
            ax.scatter(data_arrays[j], data_arrays[i], c=colors, s=70, alpha=0.6, edgecolors="white", linewidth=0.5)

        # Grid styling
        ax.grid(True, alpha=0.3, linestyle="--")
        ax.tick_params(axis="both", labelsize=16)

        # Axis labels only on edges with proper font sizes
        if i == n_vars - 1:
            ax.set_xlabel(var_names[j], fontsize=20)
        else:
            ax.set_xticklabels([])

        if j == 0:
            ax.set_ylabel(var_names[i], fontsize=20)
        else:
            ax.set_yticklabels([])

# Legend (add to top-right subplot with larger marker size)
legend_elements = [
    plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=color, markersize=14, label=species)
    for species, color in colors_map.items()
]
axes[0][n_vars - 1].legend(handles=legend_elements, loc="upper right", fontsize=16, framealpha=0.9)

# Title with proper font size
fig.suptitle("scatter-matrix · matplotlib · pyplots.ai", fontsize=24, y=0.995)

plt.savefig("plot.png", dpi=300, bbox_inches="tight")
