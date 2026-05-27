""" anyplot.ai
scatter-matrix-interactive: Interactive Scatter Plot Matrix (SPLOM)
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-18
"""

import os
import sys


# Force import from venv, not local matplotlib.py
original_path = sys.path.copy()
sys.path = [
    p for p in sys.path
    if p != "" and p != "." and "/scatter-matrix-interactive/implementations/python" not in p
]

import matplotlib.pyplot as plt  # noqa: E402
import seaborn as sns  # noqa: E402


sys.path = original_path

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette - first series always #009E73
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Load Iris dataset - classic multivariate data for scatter matrices
iris = sns.load_dataset("iris")

# Rename columns for clearer axis labels
df = iris.rename(
    columns={
        "sepal_length": "Sepal Length (cm)",
        "sepal_width": "Sepal Width (cm)",
        "petal_length": "Petal Length (cm)",
        "petal_width": "Petal Width (cm)",
        "species": "Species",
    }
)

# Create color mapping using Okabe-Ito palette
palette = {"setosa": IMPRINT[0], "versicolor": IMPRINT[1], "virginica": IMPRINT[2]}

# Apply theme-adaptive styling
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
        "grid.alpha": 0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Create scatter matrix using PairGrid (square format: 3600x3600 at 300 dpi = 12x12 inches)
g = sns.PairGrid(
    df,
    vars=["Sepal Length (cm)", "Sepal Width (cm)", "Petal Length (cm)", "Petal Width (cm)"],
    hue="Species",
    palette=palette,
    height=2.7,
    aspect=1,
    corner=False,
)

# Off-diagonal: scatter plots with sized markers and transparency
g.map_offdiag(sns.scatterplot, s=80, alpha=0.7, edgecolor=PAGE_BG, linewidth=0.5)

# Diagonal: KDE plots for univariate distributions
g.map_diag(sns.kdeplot, fill=True, alpha=0.5, linewidth=2.5)

# Style axis labels and ticks for large canvas readability
for ax in g.axes.flatten():
    if ax is not None:
        ax.tick_params(axis="both", labelsize=18, colors=INK_SOFT)
        ax.xaxis.label.set_size(20)
        ax.xaxis.label.set_color(INK)
        ax.yaxis.label.set_size(20)
        ax.yaxis.label.set_color(INK)
        ax.grid(True, alpha=0.10, linewidth=0.8)
        for spine in ax.spines.values():
            spine.set_edgecolor(INK_SOFT)

# Add legend with larger fonts
g.add_legend(
    title="Species",
    fontsize=18,
    title_fontsize=20,
    bbox_to_anchor=(1.02, 0.5),
    loc="center left",
    frameon=True,
    fancybox=True,
    markerscale=2.5,
)

# Add title to the figure
g.figure.suptitle(
    "scatter-matrix-interactive · python · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK, y=1.02
)

# Adjust layout and save at 3600x3600 (square format for symmetric grid)
plt.tight_layout()
g.figure.set_size_inches(12, 12)

# Save to the script's directory
script_dir = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(script_dir, f"plot-{THEME}.png")
g.figure.savefig(output_path, dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
