"""anyplot.ai
biplot-pca: PCA Biplot with Scores and Loading Vectors
Library: letsplot 4.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-17
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave
from sklearn.datasets import load_iris
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


LetsPlot.setup_html()  # noqa: F405

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

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
df[SPECIES] = [iris.target_names[i] for i in iris.target]

# Plot: reads only df and the constants above
FEATURES = [SEPAL_LENGTH, SEPAL_WIDTH, PETAL_LENGTH, PETAL_WIDTH]
df = df.dropna(subset=[*FEATURES, SPECIES])
X_scaled = StandardScaler().fit_transform(df[FEATURES])
pca = PCA(n_components=2)
scores = pca.fit_transform(X_scaled)
var_explained = pca.explained_variance_ratio_ * 100
pc1, pc2 = f"PC1 ({var_explained[0]:.1f}%)", f"PC2 ({var_explained[1]:.1f}%)"

scores_df = pd.DataFrame({pc1: scores[:, 0], pc2: scores[:, 1], SPECIES: df[SPECIES]})

# One common factor scales every loading arrow; it also sets the radius of the
# reference circle, so an arrow touching the circle has a loading of 1
loading_scale = 0.9 * min(np.abs(scores[:, 0]).max(), np.abs(scores[:, 1]).max())
loadings = pca.components_.T * loading_scale
loadings_df = pd.DataFrame(
    {
        "x0": 0.0,
        "y0": 0.0,
        "x1": loadings[:, 0],
        "y1": loadings[:, 1],
        "lx": loadings[:, 0] * 1.18,
        "ly": loadings[:, 1] * 1.18,
        "variable": [name.rsplit(" (", 1)[0] for name in FEATURES],
    }
)

# Arrows that point almost the same way get their labels pushed apart vertically
angle = np.arctan2(loadings[:, 1], loadings[:, 0])
for lower, upper in zip(np.argsort(angle)[:-1], np.argsort(angle)[1:], strict=False):
    if angle[upper] - angle[lower] < 0.3:
        loadings_df.loc[lower, "ly"] -= 0.1 * loading_scale
        loadings_df.loc[upper, "ly"] += 0.1 * loading_scale

theta = np.linspace(0, 2 * np.pi, 200)
circle_df = pd.DataFrame({"cx": loading_scale * np.cos(theta), "cy": loading_scale * np.sin(theta)})

plot = (
    ggplot()  # noqa: F405
    + geom_hline(yintercept=0, color=INK_MUTED, size=0.3, linetype="dashed")  # noqa: F405
    + geom_vline(xintercept=0, color=INK_MUTED, size=0.3, linetype="dashed")  # noqa: F405
    + geom_path(data=circle_df, mapping=aes(x="cx", y="cy"), color=INK_MUTED, size=0.4)  # noqa: F405
    + geom_point(  # noqa: F405
        data=scores_df,
        mapping=aes(x=pc1, y=pc2, color=SPECIES),  # noqa: F405
        size=2.5,
        alpha=0.8,
    )
    + geom_segment(  # noqa: F405
        data=loadings_df,
        mapping=aes(x="x0", y="y0", xend="x1", yend="y1"),  # noqa: F405
        color=INK,
        size=1.0,
        arrow=arrow(length=12, type="closed"),  # noqa: F405
    )
    + geom_text(  # noqa: F405
        data=loadings_df,
        mapping=aes(x="lx", y="ly", label="variable"),  # noqa: F405
        size=5,
        color=INK,
        fontface="bold",
    )
    + scale_color_manual(values=IMPRINT_PALETTE)  # noqa: F405
    + coord_fixed(ratio=1)  # noqa: F405
    + scale_x_continuous(expand=[0.12, 0])  # noqa: F405
    + scale_y_continuous(expand=[0.12, 0])  # noqa: F405
    + labs(x=pc1, y=pc2, title="biplot-pca · python · letsplot · anyplot.ai")  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),  # noqa: F405
        panel_background=element_rect(fill=PAGE_BG),  # noqa: F405
        panel_grid_major=element_line(color=INK, size=0.15),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        axis_title=element_text(size=12, color=INK),  # noqa: F405
        axis_text=element_text(size=10, color=INK_SOFT),  # noqa: F405
        axis_line=element_line(color=INK_SOFT, size=0.3),  # noqa: F405
        plot_title=element_text(size=16, color=INK),  # noqa: F405
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),  # noqa: F405
        legend_text=element_text(size=10, color=INK_SOFT),  # noqa: F405
        legend_title=element_text(size=12, color=INK),  # noqa: F405
    )
    + ggsize(800, 450)  # noqa: F405
)

export_ggsave(plot, filename=f"plot-{THEME}.png", path=".", scale=4)
export_ggsave(plot, filename=f"plot-{THEME}.html", path=".")
