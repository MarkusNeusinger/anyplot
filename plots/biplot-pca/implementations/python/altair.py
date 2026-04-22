""" pyplots.ai
biplot-pca: PCA Biplot with Scores and Loading Vectors
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-09
"""

import altair as alt
import pandas as pd
from sklearn.datasets import load_iris
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


# Data - using Iris dataset for multivariate analysis
iris = load_iris()
X = iris.data
y = iris.target
# Simplify feature names for cleaner display
feature_names = ["Sepal Length", "Sepal Width", "Petal Length", "Petal Width"]
target_names = iris.target_names

# Standardize features for PCA
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Perform PCA
pca = PCA(n_components=2)
scores = pca.fit_transform(X_scaled)
loadings = pca.components_.T  # Shape: (n_features, n_components)

# Variance explained
var_explained = pca.explained_variance_ratio_ * 100

# Create DataFrame for observation scores
scores_df = pd.DataFrame({"PC1": scores[:, 0], "PC2": scores[:, 1], "Species": [target_names[i] for i in y]})

# Create DataFrame for loading arrows (origin + endpoint)
# Scale loadings to be visible alongside scores (within axis bounds)
loading_scale = 2.5  # Scale factor for visibility
loadings_df = pd.DataFrame(
    {
        "feature": feature_names,
        "PC1": loadings[:, 0] * loading_scale,
        "PC2": loadings[:, 1] * loading_scale,
        "x0": [0] * len(feature_names),
        "y0": [0] * len(feature_names),
    }
)

# Prepare arrow line data (from origin to loading point)
arrow_lines = []
for _, row in loadings_df.iterrows():
    arrow_lines.append({"x": 0, "y": 0, "feature": row["feature"], "order": 0})
    arrow_lines.append({"x": row["PC1"], "y": row["PC2"], "feature": row["feature"], "order": 1})
arrow_df = pd.DataFrame(arrow_lines)

# Define colors (Python Blue, Python Yellow, plus one more for 3 species)
species_colors = ["#306998", "#FFD43B", "#6A5ACD"]

# Create scatter plot for observation scores
scatter = (
    alt.Chart(scores_df)
    .mark_point(size=120, opacity=0.8, filled=True)
    .encode(
        x=alt.X("PC1:Q", title=f"PC1 ({var_explained[0]:.1f}%)", scale=alt.Scale(domain=[-4, 4])),
        y=alt.Y("PC2:Q", title=f"PC2 ({var_explained[1]:.1f}%)", scale=alt.Scale(domain=[-3, 3])),
        color=alt.Color(
            "Species:N",
            scale=alt.Scale(range=species_colors),
            legend=alt.Legend(title="Species", titleFontSize=18, labelFontSize=16, symbolSize=200, orient="right"),
        ),
        tooltip=["Species:N", alt.Tooltip("PC1:Q", format=".2f"), alt.Tooltip("PC2:Q", format=".2f")],
    )
)

# Create loading arrows as lines
arrows = (
    alt.Chart(arrow_df)
    .mark_line(color="#333333", strokeWidth=2.5, opacity=0.9)
    .encode(x=alt.X("x:Q"), y=alt.Y("y:Q"), detail="feature:N", order="order:O")
)

# Create arrowheads at the end of loading vectors
arrowheads = (
    alt.Chart(loadings_df)
    .mark_point(shape="triangle", size=150, color="#333333", opacity=0.9, filled=True)
    .encode(
        x=alt.X("PC1:Q"),
        y=alt.Y("PC2:Q"),
        angle=alt.value(0),  # Will be rotated based on direction
    )
    .transform_calculate(angle="atan2(datum.PC2, datum.PC1) * 180 / PI + 90")
    .encode(angle="angle:Q")
)

# Create labels for loading vectors (positioned beyond arrow endpoints)
# Add offsets to separate overlapping labels
label_offset = 1.15
loading_labels_df = loadings_df.copy()
loading_labels_df["label_x"] = loading_labels_df["PC1"] * label_offset
loading_labels_df["label_y"] = loading_labels_df["PC2"] * label_offset

# Add manual y-offsets to separate "Petal Length" and "Petal Width" labels
# These have very similar directions in the Iris PCA
y_adjustments = [0, 0, -0.15, 0.15]  # Order: Sepal Length, Sepal Width, Petal Length, Petal Width
loading_labels_df["label_y"] = loading_labels_df["label_y"] + y_adjustments

loading_labels = (
    alt.Chart(loading_labels_df)
    .mark_text(fontSize=14, fontWeight="bold", color="#333333", align="left", dx=10)
    .encode(x=alt.X("label_x:Q"), y=alt.Y("label_y:Q"), text="feature:N")
)

# Create origin marker
origin_df = pd.DataFrame({"x": [0], "y": [0]})
origin = (
    alt.Chart(origin_df).mark_point(size=80, color="#333333", shape="cross", strokeWidth=2).encode(x="x:Q", y="y:Q")
)

# Combine all layers
chart = (
    alt.layer(scatter, arrows, arrowheads, loading_labels, origin)
    .properties(
        width=1600, height=900, title=alt.Title(text="biplot-pca · altair · pyplots.ai", fontSize=28, anchor="middle")
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, gridOpacity=0.3, gridDash=[3, 3])
    .configure_view(strokeWidth=0)
    .configure_legend(titleFontSize=18, labelFontSize=16)
)

# Save outputs
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
