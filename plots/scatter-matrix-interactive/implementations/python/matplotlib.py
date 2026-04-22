""" pyplots.ai
scatter-matrix-interactive: Interactive Scatter Plot Matrix (SPLOM)
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-10
"""

import matplotlib.pyplot as plt
from sklearn.datasets import load_iris


# Data - Iris dataset (4 numeric variables, 150 samples)
iris = load_iris()
data = iris.data
feature_names = ["Sepal Length\n(cm)", "Sepal Width\n(cm)", "Petal Length\n(cm)", "Petal Width\n(cm)"]
species = iris.target
species_names = ["Setosa", "Versicolor", "Virginica"]
colors = ["#306998", "#FFD43B", "#E55B3C"]

n_vars = len(feature_names)

# Create figure - square format for matrix (12x12 inches at 300 dpi = 3600x3600)
fig, axes = plt.subplots(n_vars, n_vars, figsize=(12, 12))

# Plot scatter matrix
for i in range(n_vars):
    for j in range(n_vars):
        ax = axes[i, j]

        if i == j:
            # Diagonal: histograms for each species
            for k, (name, color) in enumerate(zip(species_names, colors, strict=True)):
                mask = species == k
                ax.hist(data[mask, i], bins=12, alpha=0.65, color=color, edgecolor="white", linewidth=0.5, label=name)
        else:
            # Off-diagonal: scatter plots
            for k, (name, color) in enumerate(zip(species_names, colors, strict=True)):
                mask = species == k
                ax.scatter(
                    data[mask, j],
                    data[mask, i],
                    c=color,
                    alpha=0.75,
                    s=80,
                    edgecolors="white",
                    linewidth=0.5,
                    label=name,
                )

        # Labels on edges only
        if i == n_vars - 1:
            ax.set_xlabel(feature_names[j], fontsize=14, fontweight="medium")
        else:
            ax.set_xticklabels([])

        if j == 0:
            ax.set_ylabel(feature_names[i], fontsize=14, fontweight="medium")
        else:
            ax.set_yticklabels([])

        ax.tick_params(axis="both", labelsize=11)
        ax.grid(True, alpha=0.25, linestyle="--")

# Title
fig.suptitle(
    "Iris Dataset · scatter-matrix-interactive · matplotlib · pyplots.ai", fontsize=22, fontweight="bold", y=1.01
)

# Single legend for entire figure (positioned below title)
handles, labels = axes[0, 1].get_legend_handles_labels()
fig.legend(
    handles,
    labels,
    loc="upper center",
    fontsize=15,
    ncol=3,
    bbox_to_anchor=(0.5, 0.99),
    framealpha=0.95,
    markerscale=1.3,
)

# Note about interactivity limitation
fig.text(
    0.5,
    0.005,
    "Note: matplotlib produces static output. Use Plotly/Bokeh/Altair for linked brushing.",
    ha="center",
    fontsize=12,
    style="italic",
    color="#555555",
)

plt.tight_layout(rect=[0, 0.025, 1, 0.97])
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
