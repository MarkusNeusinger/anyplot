""" pyplots.ai
contour-decision-boundary: Decision Boundary Classifier Visualization
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_text,
    geom_point,
    geom_tile,
    ggplot,
    guide_legend,
    guides,
    labs,
    scale_color_manual,
    scale_fill_manual,
    theme,
    theme_minimal,
)
from sklearn.datasets import make_moons
from sklearn.svm import SVC


# Data - Generate synthetic classification data
np.random.seed(42)
X, y = make_moons(n_samples=200, noise=0.25, random_state=42)

# Train classifier
clf = SVC(kernel="rbf", C=1.0, gamma=0.5)
clf.fit(X, y)

# Create mesh grid for decision boundary
x_min, x_max = X[:, 0].min() - 0.5, X[:, 0].max() + 0.5
y_min, y_max = X[:, 1].min() - 0.5, X[:, 1].max() + 0.5
h = 0.02  # Step size

xx, yy = np.meshgrid(np.arange(x_min, x_max, h), np.arange(y_min, y_max, h))

# Predict on mesh grid
Z = clf.predict(np.c_[xx.ravel(), yy.ravel()])
Z = Z.reshape(xx.shape)

# Create DataFrame for mesh grid (decision regions)
mesh_df = pd.DataFrame({"X1": xx.ravel(), "X2": yy.ravel(), "Prediction": Z.ravel().astype(str)})

# Create DataFrame for training points
points_df = pd.DataFrame({"X1": X[:, 0], "X2": X[:, 1], "Class": y.astype(str)})

# Identify misclassified points
predictions = clf.predict(X)
points_df["Correct"] = predictions == y
points_df["Status"] = points_df.apply(
    lambda row: f"Class {row['Class']}" if row["Correct"] else f"Class {row['Class']} (misclassified)", axis=1
)

# Color scheme
region_colors = {"0": "#306998", "1": "#FFD43B"}
point_colors = {
    "Class 0": "#1a3a5c",
    "Class 1": "#b8960a",
    "Class 0 (misclassified)": "#1a3a5c",
    "Class 1 (misclassified)": "#b8960a",
}

# Create plot
plot = (
    ggplot()
    + geom_tile(data=mesh_df, mapping=aes(x="X1", y="X2", fill="Prediction"), alpha=0.6)
    + geom_point(data=points_df[points_df["Correct"]], mapping=aes(x="X1", y="X2", color="Status"), size=4, stroke=0.8)
    + geom_point(
        data=points_df[~points_df["Correct"]],
        mapping=aes(x="X1", y="X2", color="Status"),
        size=5,
        stroke=1.5,
        shape="X",
    )
    + scale_fill_manual(values=region_colors, name="Predicted Region")
    + scale_color_manual(values=point_colors, name="Training Points")
    + labs(x="Feature X1", y="Feature X2", title="contour-decision-boundary · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, ha="center"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_title=element_text(size=18),
        legend_text=element_text(size=14),
        legend_position="right",
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
    )
    + guides(fill=guide_legend(override_aes={"alpha": 0.8}))
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
