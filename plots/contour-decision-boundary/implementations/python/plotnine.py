""" anyplot.ai
contour-decision-boundary: Decision Boundary Classifier Visualization
Library: plotnine 0.15.8 | Python 3.14.10
Quality: 87/100 | Updated: 2026-11-09
"""

import os

import contourpy
import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_cartesian,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_point,
    geom_polygon,
    ggplot,
    guide_legend,
    guides,
    labs,
    scale_fill_manual,
    scale_shape_manual,
    scale_size_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from sklearn.datasets import make_moons
from sklearn.dummy import DummyClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per class in data order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
MESH_STEPS = 200  # mesh resolution per axis for the predicted regions
STATUS = "Training point"
CORRECT = "Correctly classified"
MISCLASSIFIED = "Misclassified"
REGION = "region"

# Columns: set these to your table's column names
FEATURE_1 = "Leaf length (cm)"  # role: X1
FEATURE_2 = "Leaf width (cm)"  # role: X2
CLASS = "Cultivar"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("samples.csv")
X, y = make_moons(n_samples=200, noise=0.25, random_state=42)
df = pd.DataFrame(
    {FEATURE_1: 6.0 + 1.5 * X[:, 0], FEATURE_2: 3.0 + 0.8 * X[:, 1], CLASS: np.where(y == 0, "Alba", "Rosea")}
)

# Plot: reads only df and the constants above
train = df.dropna(subset=[FEATURE_1, FEATURE_2, CLASS]).copy()
train[CLASS] = train[CLASS].astype(str)
classes = train[CLASS].unique().tolist()

features = train[[FEATURE_1, FEATURE_2]].to_numpy(dtype=float)
# A single class cannot train an SVM; it then fills the whole plane
if len(classes) > 1:
    clf = make_pipeline(StandardScaler(), SVC(kernel="rbf", C=1.0, gamma=0.5, break_ties=True))
else:
    clf = DummyClassifier(strategy="most_frequent")
clf.fit(features, train[CLASS])

x_pad = 0.1 * np.ptp(features[:, 0])
y_pad = 0.1 * np.ptp(features[:, 1])
x_grid = np.linspace(features[:, 0].min() - x_pad, features[:, 0].max() + x_pad, MESH_STEPS)
y_grid = np.linspace(features[:, 1].min() - y_pad, features[:, 1].max() + y_pad, MESH_STEPS)
xx, yy = np.meshgrid(x_grid, y_grid)
mesh_points = np.column_stack([xx.ravel(), yy.ravel()])

# Continuous per-class score on the mesh; a region is where its class outscores every other class
if len(classes) > 1:
    scores = clf.decision_function(mesh_points)
    scores = np.column_stack([-scores, scores]) if scores.ndim == 1 else scores
else:
    scores = np.ones((len(mesh_points), 1))
fitted_classes = list(clf.classes_)

# Contour each class margin at 0, so region edges follow the boundary between mesh cells
rings = []
for k, label in enumerate(fitted_classes):
    others = np.delete(scores, k, axis=1)
    margin = scores[:, k] - (others.max(axis=1) if others.shape[1] else 0.0)
    generator = contourpy.contour_generator(x_grid, y_grid, margin.reshape(xx.shape), fill_type="OuterOffset")
    polygons, offsets = generator.filled(0.0, np.inf)
    for points, offset in zip(polygons, offsets, strict=True):
        # Outer ring then each hole, bridged back to the outer start, so holes stay unfilled
        outer = points[offset[0] : offset[1]]
        parts = [outer] + [np.vstack([points[a:b], outer[:1]]) for a, b in zip(offset[1:-1], offset[2:], strict=True)]
        ring = np.vstack(parts)
        rings.append(pd.DataFrame({FEATURE_1: ring[:, 0], FEATURE_2: ring[:, 1], CLASS: label, REGION: len(rings)}))
regions = pd.concat(rings, ignore_index=True)

train[STATUS] = np.where(clf.predict(features) == train[CLASS], CORRECT, MISCLASSIFIED)

plot = (
    ggplot(train, aes(x=FEATURE_1, y=FEATURE_2))
    + geom_polygon(data=regions, mapping=aes(fill=CLASS, group=REGION), alpha=0.32, color=None, show_legend=False)
    + geom_point(aes(fill=CLASS, shape=STATUS, size=STATUS), color=INK, stroke=0.6)
    + scale_fill_manual(values=IMPRINT_PALETTE, limits=classes, name=f"{CLASS} (region and point)")
    + scale_shape_manual(values={CORRECT: "o", MISCLASSIFIED: "D"}, limits=[CORRECT, MISCLASSIFIED])
    + scale_size_manual(values={CORRECT: 3.2, MISCLASSIFIED: 4.2}, limits=[CORRECT, MISCLASSIFIED])
    + scale_x_continuous(expand=(0, 0))
    + scale_y_continuous(expand=(0, 0))
    + coord_cartesian(xlim=(x_grid[0], x_grid[-1]), ylim=(y_grid[0], y_grid[-1]))
    + guides(
        fill=guide_legend(override_aes={"shape": "s", "size": 5}),
        shape=guide_legend(override_aes={"fill": INK_SOFT}),
        size=guide_legend(),
    )
    + labs(title="contour-decision-boundary · python · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        text=element_text(size=7, color=INK),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        axis_ticks=element_blank(),
        plot_title=element_text(size=12, color=INK, ha="center", weight="medium"),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        legend_title=element_text(size=8, color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT, size=0.3),
        legend_key=element_rect(fill=ELEVATED_BG, color=ELEVATED_BG),
        legend_position="right",
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
