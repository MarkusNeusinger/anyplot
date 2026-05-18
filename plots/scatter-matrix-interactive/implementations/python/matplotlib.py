""" anyplot.ai
scatter-matrix-interactive: Interactive Scatter Plot Matrix (SPLOM)
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-18
"""

import os

import matplotlib.pyplot as plt
from sklearn.datasets import load_iris


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito palette (positions 1-3)
COLORS = ["#009E73", "#D55E00", "#0072B2"]

# Data - Iris dataset (4 numeric variables, 150 samples)
iris = load_iris()
data = iris.data
feature_names = ["Sepal Length\n(cm)", "Sepal Width\n(cm)", "Petal Length\n(cm)", "Petal Width\n(cm)"]
species = iris.target
species_names = ["Setosa", "Versicolor", "Virginica"]

n_vars = len(feature_names)

# Create figure - square format for matrix (12x12 inches at 300 dpi = 3600x3600)
fig, axes = plt.subplots(n_vars, n_vars, figsize=(12, 12), facecolor=PAGE_BG)

# Plot scatter matrix
for i in range(n_vars):
    for j in range(n_vars):
        ax = axes[i, j]
        ax.set_facecolor(PAGE_BG)

        if i == j:
            # Diagonal: histograms for each species
            for k, (name, color) in enumerate(zip(species_names, COLORS, strict=True)):
                mask = species == k
                ax.hist(data[mask, i], bins=12, alpha=0.65, color=color, edgecolor="white", linewidth=0.8, label=name)
        else:
            # Off-diagonal: scatter plots
            for k, (name, color) in enumerate(zip(species_names, COLORS, strict=True)):
                mask = species == k
                ax.scatter(
                    data[mask, j],
                    data[mask, i],
                    c=color,
                    alpha=0.7,
                    s=120,
                    edgecolors="white",
                    linewidth=0.8,
                    label=name,
                )

        # Labels on edges only
        if i == n_vars - 1:
            ax.set_xlabel(feature_names[j], fontsize=18, fontweight="medium", color=INK)
        else:
            ax.set_xticklabels([])

        if j == 0:
            ax.set_ylabel(feature_names[i], fontsize=18, fontweight="medium", color=INK)
        else:
            ax.set_yticklabels([])

        ax.tick_params(axis="both", labelsize=14, colors=INK_SOFT)
        ax.grid(True, alpha=0.12, linestyle="-", linewidth=0.6, color=INK)

        # Theme-adaptive spines
        for spine in ax.spines.values():
            spine.set_color(INK_SOFT)
            spine.set_linewidth(0.8)

# Title
fig.suptitle("Iris Dataset · scatter-matrix-interactive", fontsize=26, fontweight="bold", y=0.98, color=INK)

# Single legend for entire figure
handles, labels = axes[0, 1].get_legend_handles_labels()
leg = fig.legend(
    handles,
    labels,
    loc="upper center",
    fontsize=16,
    ncol=3,
    bbox_to_anchor=(0.5, 0.965),
    framealpha=0.95,
    markerscale=1.2,
)
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    leg.get_frame().set_linewidth(0.8)
    for text in leg.get_texts():
        text.set_color(INK_SOFT)

# Note about interactivity limitation (subtle)
fig.text(
    0.5,
    0.005,
    "Note: matplotlib produces static visualization. Use Plotly, Bokeh, or Altair for linked brushing and interaction.",
    ha="center",
    fontsize=12,
    style="italic",
    color=INK_MUTED,
)

plt.tight_layout(rect=[0, 0.03, 1, 0.96])
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
