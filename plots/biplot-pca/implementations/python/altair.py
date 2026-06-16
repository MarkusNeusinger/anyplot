""" anyplot.ai
biplot-pca: PCA Biplot with Scores and Loading Vectors
Library: altair 6.1.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-17
"""

import os
import sys


# Remove the script directory from sys.path to avoid importing this file as the altair module
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != script_dir]

import altair as alt  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.datasets import load_iris  # noqa: E402
from sklearn.decomposition import PCA  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data - using Iris dataset for multivariate analysis
iris = load_iris()
X = iris.data
y = iris.target
feature_names = ["Sepal Length", "Sepal Width", "Petal Length", "Petal Width"]
target_names = iris.target_names

# Standardize features for PCA
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Perform PCA with random_state for reproducibility
pca = PCA(n_components=2, random_state=42)
scores = pca.fit_transform(X_scaled)
loadings = pca.components_.T

# Variance explained
var_explained = pca.explained_variance_ratio_ * 100

# Create DataFrame for observation scores
scores_df = pd.DataFrame({"PC1": scores[:, 0], "PC2": scores[:, 1], "Species": [target_names[i] for i in y]})

# Create DataFrame for loading arrows
loading_scale = 2.5
loadings_df = pd.DataFrame(
    {"feature": feature_names, "PC1": loadings[:, 0] * loading_scale, "PC2": loadings[:, 1] * loading_scale}
)

# Prepare arrow line data (from origin to loading point)
arrow_lines = []
for _, row in loadings_df.iterrows():
    arrow_lines.append({"x": 0, "y": 0, "feature": row["feature"], "order": 0})
    arrow_lines.append({"x": row["PC1"], "y": row["PC2"], "feature": row["feature"], "order": 1})
arrow_df = pd.DataFrame(arrow_lines)

# Create scatter plot for observation scores
scatter = (
    alt.Chart(scores_df)
    .mark_point(size=120, opacity=0.8, filled=True)
    .encode(
        x=alt.X("PC1:Q", title=f"PC1 ({var_explained[0]:.1f}%)", scale=alt.Scale(domain=[-4, 4])),
        y=alt.Y("PC2:Q", title=f"PC2 ({var_explained[1]:.1f}%)", scale=alt.Scale(domain=[-3, 3])),
        color=alt.Color(
            "Species:N",
            scale=alt.Scale(range=IMPRINT),
            legend=alt.Legend(title="Species", titleFontSize=18, labelFontSize=16, symbolSize=200, orient="right"),
        ),
        tooltip=["Species:N", alt.Tooltip("PC1:Q", format=".2f"), alt.Tooltip("PC2:Q", format=".2f")],
    )
)

# Create loading arrows as lines
arrows = (
    alt.Chart(arrow_df)
    .mark_line(color=INK_SOFT, strokeWidth=2.5, opacity=0.9)
    .encode(x=alt.X("x:Q"), y=alt.Y("y:Q"), detail="feature:N", order="order:O")
)

# Create arrowheads at the end of loading vectors
arrowheads = (
    alt.Chart(loadings_df)
    .mark_point(shape="triangle", size=150, color=INK_SOFT, opacity=0.9, filled=True)
    .encode(x=alt.X("PC1:Q"), y=alt.Y("PC2:Q"))
    .transform_calculate(angle="atan2(datum.PC2, datum.PC1) * 180 / PI + 90")
    .encode(angle="angle:Q")
)

# Create labels for loading vectors
label_offset = 1.15
loading_labels_df = loadings_df.copy()
loading_labels_df["label_x"] = loading_labels_df["PC1"] * label_offset
loading_labels_df["label_y"] = loading_labels_df["PC2"] * label_offset

# Add manual y-offsets to separate "Petal Length" and "Petal Width" labels
y_adjustments = [0, 0, -0.15, 0.15]
loading_labels_df["label_y"] = loading_labels_df["label_y"] + y_adjustments

loading_labels = (
    alt.Chart(loading_labels_df)
    .mark_text(fontSize=14, fontWeight="bold", color=INK, align="left", dx=10)
    .encode(x=alt.X("label_x:Q"), y=alt.Y("label_y:Q"), text="feature:N")
)

# Create origin marker
origin_df = pd.DataFrame({"x": [0], "y": [0]})
origin = alt.Chart(origin_df).mark_point(size=80, color=INK_SOFT, shape="cross", strokeWidth=2).encode(x="x:Q", y="y:Q")

# Combine all layers with theme-adaptive configuration
chart = (
    alt.layer(scatter, arrows, arrowheads, loading_labels, origin)
    .properties(
        width=1600,
        height=900,
        background=PAGE_BG,
        title=alt.Title(text="biplot-pca · altair · anyplot.ai", fontSize=28, anchor="middle", color=INK),
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
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
        titleFontSize=18,
        labelFontSize=16,
    )
    .interactive()
)

# Save outputs
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
