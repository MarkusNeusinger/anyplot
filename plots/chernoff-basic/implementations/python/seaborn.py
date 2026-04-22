""" pyplots.ai
chernoff-basic: Chernoff Faces for Multivariate Data
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 82/100 | Created: 2025-12-31
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Load and prepare data (Iris dataset - 4 measurements per flower)
iris_df = sns.load_dataset("iris")
feature_cols = ["sepal_length", "sepal_width", "petal_length", "petal_width"]
data = iris_df[feature_cols].values
species_map = {"setosa": 0, "versicolor": 1, "virginica": 2}
target = iris_df["species"].map(species_map).values

# Select subset of samples with maximum variation within each species (5 per species = 15 total)
np.random.seed(42)
indices = []
for species in range(3):
    species_indices = np.where(target == species)[0]
    species_data = data[species_indices]
    # For each feature, find samples with min and max values to maximize visible variation
    # Then add centroid sample
    selected = set()
    for feat_idx in range(4):
        feat_values = species_data[:, feat_idx]
        min_idx = species_indices[np.argmin(feat_values)]
        max_idx = species_indices[np.argmax(feat_values)]
        selected.add(min_idx)
        selected.add(max_idx)
    # Add sample closest to mean
    mean_vals = species_data.mean(axis=0)
    distances = np.sum((species_data - mean_vals) ** 2, axis=1)
    selected.add(species_indices[np.argmin(distances)])
    # Convert to list and take first 5
    selected = list(selected)[:5]
    while len(selected) < 5:
        for idx in species_indices:
            if idx not in selected:
                selected.append(idx)
                break
    indices.extend(selected[:5])
indices = np.array(indices)

subset_data = data[indices]
subset_target = target[indices]
species_names = ["Setosa", "Versicolor", "Virginica"]

# Global normalization for heatmap (shows species differences)
data_min = data.min(axis=0)
data_max = data.max(axis=0)
heatmap_normalized = (subset_data - data_min) / (data_max - data_min + 1e-8)

# WITHIN-species normalization for faces (maximizes visible variation within each species)
# This ensures each species shows its full range of variation in facial features
normalized_data = np.zeros_like(subset_data)
for species in range(3):
    species_mask = subset_target == species
    species_subset = subset_data[species_mask]
    for feat_idx in range(4):
        feat_min = species_subset[:, feat_idx].min()
        feat_max = species_subset[:, feat_idx].max()
        feat_range = feat_max - feat_min if feat_max > feat_min else 1.0
        normalized_data[species_mask, feat_idx] = (species_subset[:, feat_idx] - feat_min) / feat_range

# Set seaborn style
sns.set_style("white")
sns.set_context("poster", font_scale=1.0)

# Color palette for species (using seaborn palette)
palette = sns.color_palette("Set2", 3)
face_colors = [palette[t] for t in subset_target]

# Create figure - 16:9 aspect ratio for 4800x2700 at 300dpi
fig = plt.figure(figsize=(16, 9))

# Create grid layout: heatmap on left, faces on right
gs = fig.add_gridspec(3, 7, width_ratios=[1.5, 1, 1, 1, 1, 1, 0.1], hspace=0.25, wspace=0.15)

# Add heatmap showing feature values on left side using seaborn (global normalization)
ax_heatmap = fig.add_subplot(gs[:, 0])
sns.heatmap(
    heatmap_normalized,
    ax=ax_heatmap,
    cmap="YlOrRd",
    cbar=False,
    xticklabels=["Sepal\nLength", "Sepal\nWidth", "Petal\nLength", "Petal\nWidth"],
    yticklabels=[f"{species_names[subset_target[i]][0]}{(i % 5) + 1}" for i in range(15)],
    linewidths=1,
    linecolor="white",
    annot=True,
    fmt=".2f",
    annot_kws={"size": 9},
)
ax_heatmap.set_title("Feature Values\n(Normalized)", fontsize=16, fontweight="bold", pad=10)
ax_heatmap.tick_params(axis="x", labelsize=12, rotation=0)
ax_heatmap.tick_params(axis="y", labelsize=11)

# Draw Chernoff faces in grid (3 rows x 5 cols on the right side)
for idx in range(15):
    row = idx // 5  # Rows 0, 1, 2
    col = idx % 5 + 1  # Columns 1-5 (column 0 is heatmap)
    ax = fig.add_subplot(gs[row, col])

    features = normalized_data[idx]
    color = face_colors[idx]

    # Map features to facial characteristics with WIDER ranges for visible variation
    # Feature 0: sepal_length -> face width (0.45 to 1.0)
    # Feature 1: sepal_width -> face height (0.55 to 1.1)
    # Feature 2: petal_length -> eye size (0.04 to 0.16)
    # Feature 3: petal_width -> mouth curvature (-0.35 to 0.35)

    face_width = 0.45 + features[0] * 0.55
    face_height = 0.55 + features[1] * 0.55
    eye_size = 0.04 + features[2] * 0.12
    mouth_curve = -0.35 + features[3] * 0.7

    # Draw face outline (ellipse)
    face = mpatches.Ellipse((0.5, 0.5), face_width, face_height, facecolor=color, edgecolor="black", linewidth=2.5)
    ax.add_patch(face)

    # Draw eyes
    eye_y = 0.58
    eye_spacing = 0.11 + features[1] * 0.05

    # Left eye
    left_eye = mpatches.Ellipse(
        (0.5 - eye_spacing, eye_y), eye_size * 1.6, eye_size, facecolor="white", edgecolor="black", linewidth=2
    )
    ax.add_patch(left_eye)
    left_pupil = mpatches.Circle((0.5 - eye_spacing, eye_y), eye_size * 0.35, facecolor="black")
    ax.add_patch(left_pupil)

    # Right eye
    right_eye = mpatches.Ellipse(
        (0.5 + eye_spacing, eye_y), eye_size * 1.6, eye_size, facecolor="white", edgecolor="black", linewidth=2
    )
    ax.add_patch(right_eye)
    right_pupil = mpatches.Circle((0.5 + eye_spacing, eye_y), eye_size * 0.35, facecolor="black")
    ax.add_patch(right_pupil)

    # Draw eyebrows
    eyebrow_angle = -0.12 + features[2] * 0.24
    eyebrow_y = eye_y + eye_size + 0.05

    ax.plot(
        [0.5 - eye_spacing - 0.05, 0.5 - eye_spacing + 0.05],
        [eyebrow_y + eyebrow_angle, eyebrow_y - eyebrow_angle],
        color="black",
        linewidth=3.5,
        solid_capstyle="round",
    )
    ax.plot(
        [0.5 + eye_spacing - 0.05, 0.5 + eye_spacing + 0.05],
        [eyebrow_y - eyebrow_angle, eyebrow_y + eyebrow_angle],
        color="black",
        linewidth=3.5,
        solid_capstyle="round",
    )

    # Draw nose
    nose_size = 0.03 + features[0] * 0.025
    nose = mpatches.Polygon(
        [[0.5, 0.50], [0.5 - nose_size, 0.40], [0.5 + nose_size, 0.40]],
        facecolor=tuple(c * 0.85 for c in color[:3]),
        edgecolor="black",
        linewidth=1.5,
    )
    ax.add_patch(nose)

    # Draw mouth
    mouth_width = 0.08 + features[0] * 0.05
    mouth_x = np.linspace(0.5 - mouth_width, 0.5 + mouth_width, 25)
    mouth_y = 0.30 + mouth_curve * ((mouth_x - 0.5) ** 2) * 18
    ax.plot(mouth_x, mouth_y, color="#8B0000", linewidth=3.5, solid_capstyle="round")

    # Set axis properties
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    ax.axis("off")

    # Add label below face
    species_idx = subset_target[idx]
    sample_num = (idx % 5) + 1
    ax.text(
        0.5, -0.02, f"{species_names[species_idx]} #{sample_num}", ha="center", va="top", fontsize=11, fontweight="bold"
    )

# Add overall title
fig.suptitle("chernoff-basic · seaborn · pyplots.ai", fontsize=24, fontweight="bold", y=0.98)

# Add legend for species (positioned to the right)
legend_handles = [mpatches.Patch(color=palette[i], label=species_names[i], ec="black", lw=1.5) for i in range(3)]
fig.legend(
    handles=legend_handles, loc="center right", fontsize=14, frameon=True, bbox_to_anchor=(0.99, 0.5), title="Species"
)

# Add feature mapping explanation at bottom
feature_text = (
    "Face Width ← Sepal Length  |  Face Height ← Sepal Width  |  Eye Size ← Petal Length  |  Mouth Curve ← Petal Width"
)
fig.text(0.55, 0.02, feature_text, ha="center", fontsize=12, style="italic")

plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
