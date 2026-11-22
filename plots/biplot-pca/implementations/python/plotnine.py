"""anyplot.ai
biplot-pca: PCA Biplot with Scores and Loading Vectors
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-17
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    arrow,
    coord_fixed,
    element_line,
    element_rect,
    element_text,
    geom_path,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    scale_color_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from sklearn.datasets import load_iris
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
SEPAL_LENGTH = "Sepal length (cm)"  # role: features
SEPAL_WIDTH = "Sepal width (cm)"  # role: extra
PETAL_LENGTH = "Petal length (cm)"  # role: extra
PETAL_WIDTH = "Petal width (cm)"  # role: extra
SPECIES = "Species"  # role: labels

# Data: replace this block with your own table, for example df = pd.read_csv("measurements.csv")
iris = load_iris()
df = pd.DataFrame(iris.data, columns=[SEPAL_LENGTH, SEPAL_WIDTH, PETAL_LENGTH, PETAL_WIDTH])
df[SPECIES] = pd.Categorical.from_codes(iris.target, iris.target_names)

# Plot: reads only df and the constants above
FEATURES = [c for c in df.columns if c != SPECIES]
df = df.dropna(subset=FEATURES)
groups = df[SPECIES].astype(str).unique().tolist()
pca = PCA(n_components=2)
scores = pca.fit_transform(StandardScaler().fit_transform(df[FEATURES]))
loadings = pca.components_.T  # shape: (n_features, 2)
var_explained = pca.explained_variance_ratio_ * 100

df_scores = pd.DataFrame({"PC1": scores[:, 0], "PC2": scores[:, 1], SPECIES: df[SPECIES].astype(str).to_numpy()})

# One common factor scales every loading arrow so it sits alongside the scores
scale_factor = 0.8 * np.max(np.abs(scores)) / np.max(np.abs(loadings))
xend = loadings[:, 0] * scale_factor
yend = loadings[:, 1] * scale_factor
names = [f.replace(" (cm)", "") for f in FEATURES]
df_loadings = pd.DataFrame({"x": 0.0, "y": 0.0, "xend": xend, "yend": yend, "variable": names})

# Labels sit just beyond each arrow tip; a vertical pass keeps neighbouring labels apart
label_offset = 0.04 * scale_factor
norm = np.hypot(xend, yend)
lx = xend + xend / norm * label_offset
ly = yend + yend / norm * label_offset
min_gap = 0.14 * scale_factor
for same_side in (lx >= 0, lx < 0):
    idx = np.where(same_side)[0]
    idx = idx[np.argsort(ly[idx])]
    for prev, cur in zip(idx[:-1], idx[1:], strict=True):
        if ly[cur] - ly[prev] < min_gap:
            ly[cur] = ly[prev] + min_gap
df_labels = pd.DataFrame({"x": lx, "y": ly, "variable": names})
right_side = lx >= 0

# Unit circle: loading magnitude 1 in the arrows' scale, round thanks to the fixed aspect
theta = np.linspace(0, 2 * np.pi, 200)
df_circle = pd.DataFrame({"x": np.cos(theta) * scale_factor, "y": np.sin(theta) * scale_factor})

limit = max(scale_factor * 1.1, np.max(np.abs(scores)) * 1.1)
text_size = 5.5  # geom_text size is in mm

anyplot_theme = theme(
    figure_size=(6, 6),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
    panel_border=element_rect(color=INK_SOFT, fill=None),
    axis_title=element_text(size=10, color=INK),
    axis_text=element_text(size=8, color=INK_SOFT),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(size=12, color=INK),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(size=8, color=INK_SOFT),
    legend_title=element_text(size=10, color=INK),
    legend_position="bottom",
    text=element_text(size=7),
)

plot = (
    ggplot()
    + geom_path(df_circle, aes(x="x", y="y"), color=INK_SOFT, linetype="dashed", size=0.5, alpha=0.6)
    + geom_point(df_scores, aes(x="PC1", y="PC2", color=SPECIES), size=2.2, alpha=0.7)
    + geom_segment(
        df_loadings,
        aes(x="x", y="y", xend="xend", yend="yend"),
        color=INK,
        size=0.8,
        arrow=arrow(length=0.08, type="closed"),
    )
    + geom_text(
        df_labels[right_side],
        aes(x="x", y="y", label="variable"),
        size=text_size,
        color=INK,
        fontweight="bold",
        ha="left",
    )
    + geom_text(
        df_labels[~right_side],
        aes(x="x", y="y", label="variable"),
        size=text_size,
        color=INK,
        fontweight="bold",
        ha="right",
    )
    + labs(
        x=f"PC1 ({var_explained[0]:.1f}% of variance)",
        y=f"PC2 ({var_explained[1]:.1f}% of variance)",
        title="biplot-pca · python · plotnine · anyplot.ai",
        color=SPECIES,
    )
    + scale_color_manual(values=IMPRINT_PALETTE, limits=groups)
    + scale_x_continuous(limits=(-limit, limit))
    + scale_y_continuous(limits=(-limit, limit))
    + coord_fixed(ratio=1)
    + theme_minimal()
    + anyplot_theme
)

plot.save(f"plot-{THEME}.png", dpi=400, width=6, height=6, units="in", verbose=False)
