""" pyplots.ai
contour-decision-boundary: Decision Boundary Classifier Visualization
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import altair as alt
import numpy as np
import pandas as pd
from sklearn.datasets import make_moons
from sklearn.neighbors import KNeighborsClassifier


# Data - generate two-moon classification dataset
np.random.seed(42)
X, y = make_moons(n_samples=150, noise=0.25, random_state=42)

# Train a KNN classifier
clf = KNeighborsClassifier(n_neighbors=5)
clf.fit(X, y)

# Create mesh grid for decision boundary
x_min, x_max = X[:, 0].min() - 0.5, X[:, 0].max() + 0.5
y_min, y_max = X[:, 1].min() - 0.5, X[:, 1].max() + 0.5
xx, yy = np.meshgrid(np.linspace(x_min, x_max, 150), np.linspace(y_min, y_max, 150))

# Predict on mesh grid
Z = clf.predict(np.c_[xx.ravel(), yy.ravel()])
Z = Z.reshape(xx.shape)

# Create DataFrame for background regions (decision boundary)
mesh_df = pd.DataFrame(
    {"X1": xx.ravel(), "X2": yy.ravel(), "Class": ["Class A" if z == 0 else "Class B" for z in Z.ravel()]}
)

# Create DataFrame for training points
train_df = pd.DataFrame(
    {"X1": X[:, 0], "X2": X[:, 1], "Class": ["Class A" if label == 0 else "Class B" for label in y]}
)

# Add prediction for training points to show misclassified
train_predictions = clf.predict(X)
train_df["Classification"] = ["Correct" if p == t else "Incorrect" for p, t in zip(train_predictions, y, strict=True)]

# Decision boundary background using rect marks
background = (
    alt.Chart(mesh_df)
    .mark_rect(opacity=0.4)
    .encode(
        x=alt.X("X1:Q", bin=alt.Bin(maxbins=150), title="Feature X1"),
        y=alt.Y("X2:Q", bin=alt.Bin(maxbins=150), title="Feature X2"),
        color=alt.Color(
            "Class:N",
            scale=alt.Scale(domain=["Class A", "Class B"], range=["#306998", "#FFD43B"]),
            legend=alt.Legend(title="Class", titleFontSize=18, labelFontSize=16, orient="right"),
        ),
    )
)

# Correctly classified points (circles)
correct_points = (
    alt.Chart(train_df[train_df["Classification"] == "Correct"])
    .mark_circle(size=250, strokeWidth=2)
    .encode(
        x=alt.X("X1:Q"),
        y=alt.Y("X2:Q"),
        fill=alt.Color(
            "Class:N", scale=alt.Scale(domain=["Class A", "Class B"], range=["#306998", "#FFD43B"]), legend=None
        ),
        stroke=alt.value("#333333"),
        tooltip=["X1:Q", "X2:Q", "Class:N", "Classification:N"],
    )
)

# Incorrectly classified points (triangles with red stroke)
incorrect_points = (
    alt.Chart(train_df[train_df["Classification"] == "Incorrect"])
    .mark_point(shape="triangle", size=350, strokeWidth=3, filled=True)
    .encode(
        x=alt.X("X1:Q"),
        y=alt.Y("X2:Q"),
        fill=alt.Color(
            "Class:N", scale=alt.Scale(domain=["Class A", "Class B"], range=["#306998", "#FFD43B"]), legend=None
        ),
        stroke=alt.value("#E63946"),
        tooltip=["X1:Q", "X2:Q", "Class:N", "Classification:N"],
    )
)

# Create a separate legend for shapes (classification status)
shape_legend_df = pd.DataFrame({"Classification": ["Correct (●)", "Incorrect (▲)"], "x": [0, 0], "y": [0, 1]})
shape_legend = (
    alt.Chart(shape_legend_df)
    .mark_point(size=0, opacity=0)
    .encode(
        x=alt.X("x:Q"),
        y=alt.Y("y:Q"),
        shape=alt.Shape(
            "Classification:N",
            scale=alt.Scale(domain=["Correct (●)", "Incorrect (▲)"], range=["circle", "triangle"]),
            legend=alt.Legend(title="Classification", titleFontSize=18, labelFontSize=16, orient="right"),
        ),
    )
)

# Combine layers
chart = (
    alt.layer(background, correct_points, incorrect_points, shape_legend)
    .properties(
        width=1600,
        height=900,
        title=alt.Title("contour-decision-boundary \u00b7 altair \u00b7 pyplots.ai", fontSize=28, anchor="middle"),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, gridOpacity=0.3)
    .configure_view(strokeWidth=0)
)

# Save outputs
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
