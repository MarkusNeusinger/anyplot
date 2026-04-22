""" pyplots.ai
contour-decision-boundary: Decision Boundary Classifier Visualization
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-01
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
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

# Data - Create synthetic classification data
np.random.seed(42)
X, y = make_moons(n_samples=200, noise=0.25, random_state=42)

# Train a KNN classifier
classifier = KNeighborsClassifier(n_neighbors=5)
classifier.fit(X, y)

# Create mesh grid for decision boundary
h = 0.02  # Step size
x_min, x_max = X[:, 0].min() - 0.5, X[:, 0].max() + 0.5
y_min, y_max = X[:, 1].min() - 0.5, X[:, 1].max() + 0.5
xx, yy = np.meshgrid(np.arange(x_min, x_max, h), np.arange(y_min, y_max, h))

# Predict class for each point in mesh
Z = classifier.predict(np.c_[xx.ravel(), yy.ravel()])
Z = Z.reshape(xx.shape)

# Create DataFrame for mesh grid
mesh_df = pd.DataFrame({"X1": xx.ravel(), "X2": yy.ravel(), "Predicted": Z.ravel().astype(str)})

# Create DataFrame for training points
train_df = pd.DataFrame({"X1": X[:, 0], "X2": X[:, 1], "Class": y.astype(str)})

# Add classification result (correct/incorrect) for training points
predictions = classifier.predict(X)
train_df["Correct"] = np.where(predictions == y, "Correct", "Incorrect")

# Plot - Decision boundary with training points
plot = (
    ggplot()
    # Decision regions as filled contour using tiles
    + geom_tile(aes(x="X1", y="X2", fill="Predicted"), data=mesh_df, alpha=0.4)
    # Training points
    + geom_point(aes(x="X1", y="X2", color="Class", shape="Correct"), data=train_df, size=5, stroke=1.5)
    # Color scales
    + scale_fill_manual(values=["#306998", "#FFD43B"], name="Predicted Class")
    + scale_color_manual(values=["#306998", "#FFD43B"], name="True Class")
    + scale_shape_manual(values=[16, 4], name="Classification")  # Circle for correct, X for incorrect
    # Labels
    + labs(title="contour-decision-boundary · letsplot · pyplots.ai", x="Feature X1", y="Feature X2")
    # Theme
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_title=element_text(size=18),
        legend_text=element_text(size=14),
        legend_position="right",
    )
    + ggsize(1600, 900)
)

# Save - use path parameter to specify exact location
ggsave(plot, filename="plot.png", path=".", scale=3)

# Save HTML for interactive version
ggsave(plot, filename="plot.html", path=".")
