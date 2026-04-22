""" pyplots.ai
scatter-matrix-interactive: Interactive Scatter Plot Matrix (SPLOM)
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-10
"""

import matplotlib.pyplot as plt
import seaborn as sns


# Note: Seaborn produces static plots. Interactive features like linked
# brushing, cross-subplot selection, zoom/pan are not available.
# This implementation creates a high-quality static scatter matrix using PairGrid.
# For full interactivity, use Plotly, Bokeh, or Altair implementations.

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

# Define color palette - Python Blue first, then complementary colorblind-safe colors
palette = {"setosa": "#306998", "versicolor": "#FFD43B", "virginica": "#4DAF4A"}

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
# 150 data points → use s=80 per quality guidelines (100-300 points → s=50-100)
g.map_offdiag(sns.scatterplot, s=80, alpha=0.7, edgecolor="white", linewidth=0.5)

# Diagonal: KDE plots for univariate distributions
g.map_diag(sns.kdeplot, fill=True, alpha=0.5, linewidth=2.5)

# Style axis labels and ticks for large canvas readability
for ax in g.axes.flatten():
    if ax is not None:
        ax.tick_params(axis="both", labelsize=14)
        ax.xaxis.label.set_size(16)
        ax.yaxis.label.set_size(16)
        ax.grid(True, alpha=0.2, linestyle="--")

# Add legend with larger fonts
g.add_legend(
    title="Species",
    fontsize=16,
    title_fontsize=18,
    bbox_to_anchor=(1.02, 0.5),
    loc="center left",
    frameon=True,
    fancybox=True,
    markerscale=2.0,
)

# Add title to the figure with more space for subtitle
g.figure.suptitle("scatter-matrix-interactive · seaborn · pyplots.ai", fontsize=26, fontweight="bold", y=1.05)

# Subtitle noting static nature - larger font and better spacing from title
g.figure.text(
    0.5,
    1.01,
    "Static visualization (interactive brushing/selection requires Plotly, Bokeh, or Altair)",
    ha="center",
    fontsize=15,
    style="italic",
    color="#555555",
)

# Adjust layout and save at 3600x3600 (square format for symmetric grid)
plt.tight_layout()
g.figure.set_size_inches(12, 12)
g.figure.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white", edgecolor="none")
