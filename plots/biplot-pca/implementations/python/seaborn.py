""" pyplots.ai
biplot-pca: PCA Biplot with Scores and Loading Vectors
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-09
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Load Iris dataset from seaborn
iris = sns.load_dataset("iris")
feature_names = ["sepal_length", "sepal_width", "petal_length", "petal_width"]
X = iris[feature_names].values
species = iris["species"].values

# Standardize features (z-score normalization)
X_mean = X.mean(axis=0)
X_std = X.std(axis=0)
X_scaled = (X - X_mean) / X_std

# Perform PCA using numpy (eigenvalue decomposition of covariance matrix)
cov_matrix = np.cov(X_scaled.T)
eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)

# Sort eigenvectors by eigenvalues in descending order
idx = np.argsort(eigenvalues)[::-1]
eigenvalues = eigenvalues[idx]
eigenvectors = eigenvectors[:, idx]

# Get first 2 principal components
pc_vectors = eigenvectors[:, :2]

# Project data onto principal components (scores)
scores = X_scaled @ pc_vectors

# Loadings are the eigenvectors
loadings = pc_vectors

# Calculate variance explained
var_explained = eigenvalues[:2] / eigenvalues.sum() * 100

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Prepare data for seaborn
score_df = {"PC1": scores[:, 0], "PC2": scores[:, 1], "Species": species}

# Use Python colors as primary palette
palette = {"setosa": "#306998", "versicolor": "#FFD43B", "virginica": "#6B8E23"}

# Plot observation scores with seaborn
sns.scatterplot(
    x="PC1",
    y="PC2",
    hue="Species",
    data=score_df,
    palette=palette,
    s=200,
    alpha=0.7,
    edgecolor="white",
    linewidth=1.5,
    ax=ax,
)

# Scale loadings to be visible but not overwhelming
score_max = np.abs(scores).max()
loading_scale = score_max * 1.2

# Draw loading arrows and labels
arrow_color = "#333333"
feature_labels = ["Sepal Length", "Sepal Width", "Petal Length", "Petal Width"]

# Store arrow endpoints for label positioning
arrow_ends = []
for i, feature in enumerate(feature_labels):
    x_load = loadings[i, 0] * loading_scale
    y_load = loadings[i, 1] * loading_scale
    arrow_ends.append((x_load, y_load, feature))

    # Draw arrow from origin to loading position
    ax.annotate(
        "",
        xy=(x_load, y_load),
        xytext=(0, 0),
        arrowprops={"arrowstyle": "->", "color": arrow_color, "lw": 2.5, "mutation_scale": 20},
    )

# Add labels with smart positioning to avoid overlap
for _i, (x_load, y_load, feature) in enumerate(arrow_ends):
    # Offset text beyond arrow tip
    text_offset = 1.12
    x_text = x_load * text_offset
    y_text = y_load * text_offset

    # Adjust horizontal alignment based on position
    if x_load > 0.3:
        ha = "left"
    elif x_load < -0.3:
        ha = "right"
    else:
        ha = "center"

    # Adjust vertical alignment based on position
    if y_load > 0.5:
        va = "bottom"
    elif y_load < -0.5:
        va = "top"
    else:
        va = "center"

    # Special adjustment for overlapping labels
    if feature == "Petal Width":
        y_text -= 0.35
    elif feature == "Petal Length":
        y_text += 0.35
    elif feature == "Sepal Width":
        # Move label to the left to avoid legend overlap
        x_text -= 0.5

    ax.text(
        x_text,
        y_text,
        feature,
        fontsize=15,
        fontweight="bold",
        ha=ha,
        va=va,
        color=arrow_color,
        bbox={"boxstyle": "round,pad=0.2", "facecolor": "white", "alpha": 0.85, "edgecolor": "none"},
    )

# Draw reference lines at origin
ax.axhline(y=0, color="gray", linestyle="--", linewidth=1, alpha=0.5)
ax.axvline(x=0, color="gray", linestyle="--", linewidth=1, alpha=0.5)

# Styling
ax.set_xlabel(f"PC1 ({var_explained[0]:.1f}%)", fontsize=20)
ax.set_ylabel(f"PC2 ({var_explained[1]:.1f}%)", fontsize=20)
ax.set_title("biplot-pca · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--")

# Legend styling - place in lower right to avoid arrow labels
legend = ax.legend(title="Species", fontsize=14, title_fontsize=16, loc="lower right")
legend.get_frame().set_alpha(0.9)

# Set balanced axis limits
max_range = max(np.abs(scores).max(), loading_scale) * 1.25
ax.set_xlim(-max_range, max_range)
ax.set_ylim(-max_range, max_range)
ax.set_aspect("equal")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
