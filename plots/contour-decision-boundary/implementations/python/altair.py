""" anyplot.ai
contour-decision-boundary: Decision Boundary Classifier Visualization
Library: altair 6.1.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-16
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from sklearn.datasets import make_moons
from sklearn.neighbors import KNeighborsClassifier


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

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
            scale=alt.Scale(domain=["Class A", "Class B"], range=[IMPRINT[0], IMPRINT[1]]),
            legend=alt.Legend(title="Decision Region", titleFontSize=18, labelFontSize=16, orient="right"),
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
            "Class:N", scale=alt.Scale(domain=["Class A", "Class B"], range=[IMPRINT[0], IMPRINT[1]]), legend=None
        ),
        stroke=alt.value(INK_SOFT),
        tooltip=["X1:Q", "X2:Q", "Class:N", "Classification:N"],
    )
)

# Incorrectly classified points (triangles with orange stroke)
incorrect_points = (
    alt.Chart(train_df[train_df["Classification"] == "Incorrect"])
    .mark_point(shape="triangle", size=350, strokeWidth=3, filled=True)
    .encode(
        x=alt.X("X1:Q"),
        y=alt.Y("X2:Q"),
        fill=alt.Color(
            "Class:N", scale=alt.Scale(domain=["Class A", "Class B"], range=[IMPRINT[0], IMPRINT[1]]), legend=None
        ),
        stroke=alt.value(IMPRINT[1]),
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
        background=PAGE_BG,
        title=alt.Title("contour-decision-boundary · altair · anyplot.ai", fontSize=28, anchor="middle", color=INK),
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, strokeWidth=0)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=18,
        titleFontSize=22,
    )
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=16,
        titleFontSize=18,
    )
)

# Save outputs
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
