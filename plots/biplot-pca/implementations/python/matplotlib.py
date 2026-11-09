"""anyplot.ai
biplot-pca: PCA Biplot with Scores and Loading Vectors
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-09
"""

import os

import matplotlib.patheffects as patheffects
import matplotlib.pyplot as plt
import numpy as np
from sklearn.datasets import load_iris
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
ARROW_REACH = 0.85  # longest loading arrow spans this share of the largest score distance from the origin
NEAR_ANGLE = np.deg2rad(12)  # arrows closer than this in direction get their labels split above and below
LABEL_LIFT = 5  # extra vertical clearance (points) for split labels, keeping them off points and the PC2 = 0 line

# Columns: set these to your table's column names
MEASUREMENTS = ["Sepal length (cm)", "Sepal width (cm)", "Petal length (cm)", "Petal width (cm)"]  # role: features
SPECIES = "Species"  # role: labels

# Data: replace this block with your own table, for example df = pd.read_csv("flowers.csv")
iris = load_iris(as_frame=True)
df = iris.data.set_axis(MEASUREMENTS, axis=1)
df[SPECIES] = [iris.target_names[code].capitalize() for code in iris.target]

# Plot: reads only df and the constants above
observations = df.dropna(subset=MEASUREMENTS).reset_index(drop=True)
table = observations[MEASUREMENTS]
pca = PCA(n_components=2)
scores = pca.fit_transform(StandardScaler().fit_transform(table))
loadings = pca.components_.T
explained = pca.explained_variance_ratio_ * 100

# One common factor for every arrow, so relative lengths follow the loadings
scale = ARROW_REACH * np.hypot(scores[:, 0], scores[:, 1]).max() / np.hypot(loadings[:, 0], loadings[:, 1]).max()
tips = loadings * scale
angles = np.arctan2(tips[:, 1], tips[:, 0])

fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.axhline(0, color=INK_MUTED, linewidth=0.8, alpha=0.6, zorder=1)
ax.axvline(0, color=INK_MUTED, linewidth=0.8, alpha=0.6, zorder=1)

for i, (species, rows) in enumerate(observations.groupby(SPECIES, sort=False)):
    ax.scatter(
        scores[rows.index, 0],
        scores[rows.index, 1],
        s=60,
        alpha=0.75,
        color=IMPRINT_PALETTE[i],
        edgecolors=PAGE_BG,
        linewidth=0.6,
        label=species,
        zorder=2,
    )

for i, measurement in enumerate(table.columns):
    ax.annotate(
        "",
        xy=tips[i],
        xytext=(0, 0),
        arrowprops={"arrowstyle": "-|>", "color": INK, "lw": 1.6, "mutation_scale": 12, "shrinkA": 0, "shrinkB": 0},
        zorder=3,
    )
    gaps = angles[i] - np.delete(angles, i)
    near = np.abs(gaps) < NEAR_ANGLE
    va = "center" if not near.any() else ("bottom" if (gaps[near] > 0).all() else "top")
    direction = tips[i] / np.hypot(*tips[i])
    lift = {"center": 0, "bottom": LABEL_LIFT, "top": -LABEL_LIFT}[va]
    ax.annotate(
        measurement,
        xy=tips[i],
        xytext=direction * 6 + np.array([0, lift]),
        textcoords="offset points",
        ha="left" if direction[0] >= 0 else "right",
        va=va,
        fontsize=8,
        color=INK,
        path_effects=[patheffects.withStroke(linewidth=2.5, foreground=PAGE_BG)],
        bbox={"boxstyle": "round,pad=0.25", "facecolor": PAGE_BG, "edgecolor": "none", "alpha": 0.85},
        zorder=4,
    )

# Style
ax.set_aspect("equal", adjustable="datalim")
ax.margins(0.12)
ax.set_xlabel(f"PC1 ({explained[0]:.1f}% of variance)", fontsize=10, color=INK)
ax.set_ylabel(f"PC2 ({explained[1]:.1f}% of variance)", fontsize=10, color=INK)
ax.set_title("biplot-pca · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=12)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, length=0)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for side in ("left", "bottom"):
    ax.spines[side].set_color(INK_SOFT)
ax.grid(True, alpha=0.12, linewidth=0.6, color=INK)
ax.set_axisbelow(True)

if observations[SPECIES].nunique() > 1:
    leg = ax.legend(title=SPECIES, fontsize=8, title_fontsize=8, loc="best", frameon=True)
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    plt.setp(leg.get_texts(), color=INK_SOFT)
    leg.get_title().set_color(INK)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
