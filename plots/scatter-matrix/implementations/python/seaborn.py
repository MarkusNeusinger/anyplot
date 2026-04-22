""" pyplots.ai
scatter-matrix: Scatter Plot Matrix
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data: Simulated iris-like measurements for 4 variables
np.random.seed(42)
n_samples = 150

# Three species with different characteristics
species = np.repeat(["Setosa", "Versicolor", "Virginica"], n_samples // 3)

# Generate realistic measurements for each species
data = {
    "Sepal Length (cm)": np.concatenate(
        [
            np.random.normal(5.0, 0.35, n_samples // 3),
            np.random.normal(5.9, 0.52, n_samples // 3),
            np.random.normal(6.6, 0.64, n_samples // 3),
        ]
    ),
    "Sepal Width (cm)": np.concatenate(
        [
            np.random.normal(3.4, 0.38, n_samples // 3),
            np.random.normal(2.8, 0.31, n_samples // 3),
            np.random.normal(3.0, 0.32, n_samples // 3),
        ]
    ),
    "Petal Length (cm)": np.concatenate(
        [
            np.random.normal(1.5, 0.17, n_samples // 3),
            np.random.normal(4.3, 0.47, n_samples // 3),
            np.random.normal(5.6, 0.55, n_samples // 3),
        ]
    ),
    "Petal Width (cm)": np.concatenate(
        [
            np.random.normal(0.2, 0.1, n_samples // 3),
            np.random.normal(1.3, 0.2, n_samples // 3),
            np.random.normal(2.0, 0.27, n_samples // 3),
        ]
    ),
    "Species": species,
}

df = pd.DataFrame(data)

# Plot: Scatter matrix with pairplot (square format for grid-based plot)
sns.set_context("talk", font_scale=1.4)
sns.set_style("whitegrid")

g = sns.pairplot(
    df,
    hue="Species",
    palette=["#306998", "#FFD43B", "#4B8BBE"],
    diag_kind="kde",
    plot_kws={"s": 80, "alpha": 0.7, "edgecolor": "white", "linewidth": 0.5},
    diag_kws={"linewidth": 2.5, "fill": True, "alpha": 0.4},
    corner=False,
    height=3.0,
    aspect=1.0,
)

# Adjust title
g.figure.suptitle("scatter-matrix \u00b7 seaborn \u00b7 pyplots.ai", fontsize=28, y=1.02, fontweight="bold")

# Adjust legend
g._legend.set_title("Species")
g._legend.get_title().set_fontsize(18)
for text in g._legend.get_texts():
    text.set_fontsize(16)

# Position legend to avoid cutoff
g._legend.set_bbox_to_anchor((0.85, 0.5))

# Increase axis label sizes
for ax in g.axes.flatten():
    if ax is not None:
        ax.tick_params(axis="both", labelsize=14)
        xlabel = ax.get_xlabel()
        ylabel = ax.get_ylabel()
        if xlabel:
            ax.set_xlabel(xlabel, fontsize=16)
        if ylabel:
            ax.set_ylabel(ylabel, fontsize=16)

plt.tight_layout()
g.figure.savefig("plot.png", dpi=300, bbox_inches="tight")
