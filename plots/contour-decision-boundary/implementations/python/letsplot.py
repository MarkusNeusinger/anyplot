"""anyplot.ai
contour-decision-boundary: Decision Boundary Classifier Visualization
Library: letsplot 4.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-16
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_point,
    geom_tile,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_color_manual,
    scale_fill_manual,
    scale_shape_manual,
    theme,
    theme_minimal,
)
from sklearn.datasets import make_moons
from sklearn.neighbors import KNeighborsClassifier


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per class in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
N_NEIGHBORS = 5  # the classifier whose boundary is drawn
MESH_SIZE = 250  # grid cells along each axis of the predicted regions
MESH_MARGIN = 0.1  # how far the regions extend past the training points, as a share of the range

# Columns: set these to your table's column names
X1 = "Feature X1"  # role: X1
X2 = "Feature X2"  # role: X2
CLASS = "Class"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("points.csv")
features, labels = make_moons(n_samples=200, noise=0.25, random_state=42)
df = pd.DataFrame({X1: features[:, 0], X2: features[:, 1], CLASS: [f"Class {label}" for label in labels]})

# Plot: reads only df and the constants above
df = df.dropna(subset=[X1, X2, CLASS]).astype({CLASS: str})
classes = sorted(df[CLASS].unique())
classifier = KNeighborsClassifier(n_neighbors=N_NEIGHBORS).fit(df[[X1, X2]].to_numpy(), df[CLASS])


def mesh_axis(column):
    pad = (df[column].max() - df[column].min()) * MESH_MARGIN
    return np.linspace(df[column].min() - pad, df[column].max() + pad, MESH_SIZE)


# Mesh of predicted regions covering the plotted plane
xx, yy = np.meshgrid(mesh_axis(X1), mesh_axis(X2))
mesh = pd.DataFrame({X1: xx.ravel(), X2: yy.ravel()})
mesh["Predicted"] = classifier.predict(mesh[[X1, X2]].to_numpy())

df["Classification"] = np.where(classifier.predict(df[[X1, X2]].to_numpy()) == df[CLASS], "Correct", "Incorrect")

colors = IMPRINT_PALETTE[: len(classes)]
plot = (
    ggplot()
    + geom_tile(aes(x=X1, y=X2, fill="Predicted"), data=mesh, alpha=0.4)
    + geom_point(aes(x=X1, y=X2, color=CLASS, shape="Classification"), data=df, size=2.5, stroke=1.2)
    + scale_fill_manual(values=colors, name="Predicted class")
    + scale_color_manual(values=colors, name="True class")
    + scale_shape_manual(values=[16, 4], name="Classification")
    + labs(title="contour-decision-boundary · python · letsplot · anyplot.ai")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        plot_title=element_text(size=16, color=INK),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_title=element_text(size=11, color=INK),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_position="right",
    )
    + ggsize(800, 450)
)

# Save
ggsave(plot, filename=f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, filename=f"plot-{THEME}.html", path=".")
