"""anyplot.ai
biplot-pca: PCA Biplot with Scores and Loading Vectors
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 83/100 | Updated: 2026-05-17
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.datasets import load_wine


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

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

# Columns: set these to your table's column names
WINE_CLASS = "Wine class"  # role: labels

# Data: replace this block with your own table, for example df = pd.read_csv("wine.csv")
# (every column except the class column is a numeric feature)
wine = load_wine()
feature_names = [
    "Alcohol",
    "Malic acid",
    "Ash",
    "Alkalinity of ash",
    "Magnesium",
    "Total phenols",
    "Flavanoids",
    "Nonflavanoid phenols",
    "Proanthocyanins",
    "Color intensity",
    "Hue",
    "OD280/OD315",
    "Proline",
]
df = pd.DataFrame(wine.data, columns=feature_names)
df[WINE_CLASS] = [f"Class {t}" for t in wine.target]

# Plot: reads only df and the constants above
df = df.dropna()
FEATURES = list(df.columns.drop(WINE_CLASS))
X = df[FEATURES].to_numpy()
X_scaled = (X - X.mean(axis=0)) / X.std(axis=0)

# PCA by eigendecomposition of the covariance matrix of the standardized features
eigenvalues, eigenvectors = np.linalg.eigh(np.cov(X_scaled.T))
order = np.argsort(eigenvalues)[::-1]
eigenvalues, eigenvectors = eigenvalues[order], eigenvectors[:, order]
loadings = eigenvectors[:, :2]
var_explained = eigenvalues[:2] / eigenvalues.sum() * 100

pc1 = f"PC1 ({var_explained[0]:.1f}% variance)"
pc2 = f"PC2 ({var_explained[1]:.1f}% variance)"
scores = pd.DataFrame(X_scaled @ loadings, columns=[pc1, pc2])
scores[WINE_CLASS] = df[WINE_CLASS]

fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)

n_classes = df[WINE_CLASS].nunique()
sns.scatterplot(
    data=scores,
    x=pc1,
    y=pc2,
    hue=WINE_CLASS,
    palette=IMPRINT_PALETTE[:n_classes],
    s=38,
    alpha=0.75,
    edgecolor=PAGE_BG,
    linewidth=0.5,
    ax=ax,
)

# One common factor scales every loading arrow to the spread of the scores
score_max = np.abs(scores[[pc1, pc2]].to_numpy()).max()
loading_scale = 0.8 * score_max / np.linalg.norm(loadings, axis=1).max()
tips = loadings * loading_scale

# Labels on the same side whose tips sit closer than a text line are spread apart vertically
# (labels move, arrows and points never do)
label_shift = dict.fromkeys(FEATURES, 0.0)
min_gap = 0.07 * np.abs(tips).max()
for side in (tips[:, 0] < 0, tips[:, 0] >= 0):
    members = sorted(np.flatnonzero(side), key=lambda k: -tips[k, 1])
    for prev, cur in zip(members, members[1:], strict=False):
        gap = tips[prev, 1] - tips[cur, 1]
        if gap < min_gap and abs(tips[cur, 0] - tips[prev, 0]) < 0.35 * np.abs(tips).max():
            label_shift[FEATURES[cur]] = label_shift[FEATURES[prev]] - 7.5

for (x_tip, y_tip), name in zip(tips, FEATURES, strict=True):
    ax.annotate(
        "",
        xy=(x_tip, y_tip),
        xytext=(0, 0),
        arrowprops={"arrowstyle": "-|>", "color": INK_SOFT, "lw": 1.1, "mutation_scale": 8, "shrinkA": 0, "shrinkB": 0},
    )
    # Label sits just past the tip, pushed outward along the arrow's own direction
    angle = np.arctan2(y_tip, x_tip)
    ax.annotate(
        name,
        xy=(x_tip, y_tip),
        xytext=(4 * np.cos(angle), 4 * np.sin(angle) + label_shift[name]),
        textcoords="offset points",
        ha="left" if np.cos(angle) > 0.3 else "right" if np.cos(angle) < -0.3 else "center",
        va="bottom" if np.sin(angle) > 0.3 else "top" if np.sin(angle) < -0.3 else "center",
        fontsize=6.5,
        fontweight="bold",
        color=INK,
        bbox={"boxstyle": "round,pad=0.15", "facecolor": ELEVATED_BG, "alpha": 0.8, "edgecolor": "none"},
    )

ax.axhline(0, color=INK_SOFT, linestyle="--", linewidth=0.7, alpha=0.4)
ax.axvline(0, color=INK_SOFT, linestyle="--", linewidth=0.7, alpha=0.4)

# Style
limit = max(score_max, np.abs(tips).max()) * 1.3
ax.set_xlim(-limit, limit)
ax.set_ylim(-limit, limit)
ax.set_aspect("equal")
ax.set_title("biplot-pca · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(pc1, fontsize=10)
ax.set_ylabel(pc2, fontsize=10)
ax.tick_params(axis="both", labelsize=8)
ax.yaxis.grid(True, linewidth=0.6)
sns.despine(ax=ax)

legend = ax.legend(title=WINE_CLASS, fontsize=8, title_fontsize=9, loc="lower right")
legend.get_frame().set_alpha(0.95)

fig.subplots_adjust(left=0.12, right=0.97, top=0.93, bottom=0.09)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
