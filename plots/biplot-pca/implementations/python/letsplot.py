""" anyplot.ai
biplot-pca: PCA Biplot with Scores and Loading Vectors
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-17
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
BRAND = "#009E73"  # Okabe-Ito position 1

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Load Iris dataset
iris = load_iris()
X = iris.data
y = iris.target
feature_names = iris.feature_names
target_names = iris.target_names

# Standardize features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Perform PCA
pca = PCA(n_components=2)
scores = pca.fit_transform(X_scaled)
loadings = pca.components_.T  # Variables x Components

# Variance explained
var_explained = pca.explained_variance_ratio_ * 100

# Create dataframe for scores
scores_df = pd.DataFrame({"PC1": scores[:, 0], "PC2": scores[:, 1], "Species": [target_names[i] for i in y]})

# Scale loadings for visibility alongside scores
score_range = max(np.abs(scores).max(), 1)
loading_scale = score_range * 1.5

# Create dataframe for loading arrows
clean_names = ["Sepal Length", "Sepal Width", "Petal Length", "Petal Width"]
loadings_df = pd.DataFrame(
    {
        "x_start": [0] * len(feature_names),
        "y_start": [0] * len(feature_names),
        "x_end": loadings[:, 0] * loading_scale,
        "y_end": loadings[:, 1] * loading_scale,
        "variable": clean_names,
    }
)

# Label positions with smart offset to avoid overlap
label_offsets = []
for i, name in enumerate(clean_names):
    x_end = loadings_df["x_end"].iloc[i]
    y_end = loadings_df["y_end"].iloc[i]
    if name == "Petal Width":
        label_offsets.append((x_end * 1.15, y_end * 1.15 + 0.4))
    elif name == "Petal Length":
        label_offsets.append((x_end * 1.15, y_end * 1.15 - 0.3))
    else:
        label_offsets.append((x_end * 1.15, y_end * 1.15))

loadings_df["label_x"] = [offset[0] for offset in label_offsets]
loadings_df["label_y"] = [offset[1] for offset in label_offsets]

# Unit circle for reference
circle_theta = np.linspace(0, 2 * np.pi, 100)
circle_df = pd.DataFrame({"x": np.cos(circle_theta), "y": np.sin(circle_theta)})

# Build the plot
plot = (
    ggplot()  # noqa: F405
    + geom_point(  # noqa: F405
        data=scores_df,
        mapping=aes(x="PC1", y="PC2", color="Species"),  # noqa: F405
        size=5,
        alpha=0.8,
    )
    + geom_segment(  # noqa: F405
        data=loadings_df,
        mapping=aes(x="x_start", y="y_start", xend="x_end", yend="y_end"),  # noqa: F405
        color=INK_SOFT,
        size=1.8,
        arrow=arrow(length=15, type="open"),  # noqa: F405
    )
    + geom_text(  # noqa: F405
        data=loadings_df,
        mapping=aes(x="label_x", y="label_y", label="variable"),  # noqa: F405
        size=14,
        color=INK_SOFT,
    )
    + geom_path(  # noqa: F405
        data=circle_df,
        mapping=aes(x="x", y="y"),  # noqa: F405
        color=INK_MUTED,
        size=0.5,
    )
    + geom_hline(yintercept=0, color=INK_MUTED, size=0.5, linetype="dashed")  # noqa: F405
    + geom_vline(xintercept=0, color=INK_MUTED, size=0.5, linetype="dashed")  # noqa: F405
    + labs(  # noqa: F405
        x=f"PC1 ({var_explained[0]:.1f}%)",
        y=f"PC2 ({var_explained[1]:.1f}%)",
        title="biplot-pca · letsplot · anyplot.ai",
        color="Species",
    )
    + scale_color_manual(values=IMPRINT)  # noqa: F405
    + scale_x_continuous(expand=[0.15, 0.15])  # noqa: F405
    + scale_y_continuous(expand=[0.15, 0.15])  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),  # noqa: F405
        panel_background=element_rect(fill=PAGE_BG),  # noqa: F405
        panel_grid_major=element_line(  # noqa: F405
            color=INK, size=0.3
        ),
        panel_grid_minor=element_blank(),  # noqa: F405
        axis_title=element_text(size=20, color=INK),  # noqa: F405
        axis_text=element_text(size=16, color=INK_SOFT),  # noqa: F405
        axis_line=element_line(color=INK_SOFT, size=0.5),  # noqa: F405
        plot_title=element_text(size=24, color=INK),  # noqa: F405
        legend_background=element_rect(  # noqa: F405
            fill=ELEVATED_BG, color=INK_SOFT
        ),
        legend_text=element_text(size=16, color=INK_SOFT),  # noqa: F405
        legend_title=element_text(size=18, color=INK),  # noqa: F405
    )
    + ggsize(1600, 900)  # noqa: F405
)

# Save PNG (scale 3x for 4800x2700)
export_ggsave(plot, filename=f"plot-{THEME}.png", path=".", scale=3)

# Save HTML for interactivity
export_ggsave(plot, filename=f"plot-{THEME}.html", path=".")
