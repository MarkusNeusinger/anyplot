""" pyplots.ai
chernoff-basic: Chernoff Faces for Multivariate Data
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_text,
    geom_path,
    geom_polygon,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_fill_manual,
    theme,
)
from sklearn.datasets import load_iris


LetsPlot.setup_html()

# Data - Iris dataset (4 measurements per flower, 3 species)
np.random.seed(42)
iris = load_iris()
df = pd.DataFrame(iris.data, columns=["sepal_length", "sepal_width", "petal_length", "petal_width"])
df["species"] = [iris.target_names[i] for i in iris.target]

# Sample 12 flowers (4 per species) for clear visualization
sample_idx = []
for species in range(3):
    species_idx = np.where(iris.target == species)[0]
    sample_idx.extend(np.random.choice(species_idx, 4, replace=False))
df_sample = df.iloc[sample_idx].reset_index(drop=True)

# Normalize data to 0-1 range for facial feature mapping
features = ["sepal_length", "sepal_width", "petal_length", "petal_width"]
for col in features:
    min_val = df_sample[col].min()
    max_val = df_sample[col].max()
    df_sample[col + "_norm"] = (df_sample[col] - min_val) / (max_val - min_val)


# Chernoff face generator - maps 4 variables to facial features
def create_face(row_data, center_x, center_y, scale=0.4):
    """Generate face components based on normalized data values."""
    sepal_len = row_data["sepal_length_norm"]  # Face width
    sepal_wid = row_data["sepal_width_norm"]  # Eye size
    petal_len = row_data["petal_length_norm"]  # Mouth curvature
    petal_wid = row_data["petal_width_norm"]  # Eyebrow slant

    face_data = []

    # Face outline (ellipse) - face width controlled by sepal_length
    face_width = 0.35 + 0.2 * sepal_len  # Range: 0.35 to 0.55
    face_height = 0.45
    theta = np.linspace(0, 2 * np.pi, 50)
    face_x = center_x + scale * face_width * np.cos(theta)
    face_y = center_y + scale * face_height * np.sin(theta)
    for i in range(len(theta)):
        face_data.append({"x": face_x[i], "y": face_y[i], "part": "face", "order": i})

    # Eyes - eye size controlled by sepal_width
    eye_size = 0.03 + 0.04 * sepal_wid  # Range: 0.03 to 0.07
    eye_y = center_y + scale * 0.12
    eye_spacing = 0.12

    # Left eye
    theta_eye = np.linspace(0, 2 * np.pi, 20)
    left_eye_x = center_x - scale * eye_spacing + scale * eye_size * np.cos(theta_eye)
    left_eye_y = eye_y + scale * eye_size * np.sin(theta_eye)
    for i in range(len(theta_eye)):
        face_data.append({"x": left_eye_x[i], "y": left_eye_y[i], "part": "left_eye", "order": i})

    # Right eye
    right_eye_x = center_x + scale * eye_spacing + scale * eye_size * np.cos(theta_eye)
    right_eye_y = eye_y + scale * eye_size * np.sin(theta_eye)
    for i in range(len(theta_eye)):
        face_data.append({"x": right_eye_x[i], "y": right_eye_y[i], "part": "right_eye", "order": i})

    # Pupils
    pupil_size = eye_size * 0.4
    left_pupil_x = center_x - scale * eye_spacing + scale * pupil_size * np.cos(theta_eye)
    left_pupil_y = eye_y + scale * pupil_size * np.sin(theta_eye)
    for i in range(len(theta_eye)):
        face_data.append({"x": left_pupil_x[i], "y": left_pupil_y[i], "part": "left_pupil", "order": i})

    right_pupil_x = center_x + scale * eye_spacing + scale * pupil_size * np.cos(theta_eye)
    right_pupil_y = eye_y + scale * pupil_size * np.sin(theta_eye)
    for i in range(len(theta_eye)):
        face_data.append({"x": right_pupil_x[i], "y": right_pupil_y[i], "part": "right_pupil", "order": i})

    # Mouth - curvature controlled by petal_length
    mouth_y = center_y - scale * 0.15
    mouth_width = 0.12
    curvature = -0.08 + 0.16 * petal_len  # Range: -0.08 (sad) to 0.08 (happy)
    mouth_x = np.linspace(-mouth_width, mouth_width, 20)
    mouth_curve_y = mouth_y + scale * curvature * (1 - (mouth_x / mouth_width) ** 2)
    mouth_curve_x = center_x + scale * mouth_x
    for i in range(len(mouth_x)):
        face_data.append({"x": mouth_curve_x[i], "y": mouth_curve_y[i], "part": "mouth", "order": i})

    # Eyebrows - slant controlled by petal_width
    brow_y = center_y + scale * 0.22
    brow_slant = -0.03 + 0.06 * petal_wid  # Range: -0.03 (angry) to 0.03 (surprised)
    brow_length = 0.06

    # Left eyebrow
    face_data.append(
        {
            "x": center_x - scale * (eye_spacing + brow_length),
            "y": brow_y - scale * brow_slant,
            "part": "left_brow",
            "order": 0,
        }
    )
    face_data.append(
        {
            "x": center_x - scale * (eye_spacing - brow_length),
            "y": brow_y + scale * brow_slant,
            "part": "left_brow",
            "order": 1,
        }
    )

    # Right eyebrow
    face_data.append(
        {
            "x": center_x + scale * (eye_spacing - brow_length),
            "y": brow_y + scale * brow_slant,
            "part": "right_brow",
            "order": 0,
        }
    )
    face_data.append(
        {
            "x": center_x + scale * (eye_spacing + brow_length),
            "y": brow_y - scale * brow_slant,
            "part": "right_brow",
            "order": 1,
        }
    )

    # Nose - simple vertical line
    nose_top = center_y + scale * 0.02
    nose_bottom = center_y - scale * 0.08
    face_data.append({"x": center_x, "y": nose_top, "part": "nose", "order": 0})
    face_data.append({"x": center_x, "y": nose_bottom, "part": "nose", "order": 1})

    return pd.DataFrame(face_data)


# Generate faces in a grid (3 rows x 4 columns = 12 faces)
grid_rows = 3
grid_cols = 4
all_face_data = []
label_data = []
species_colors = {"setosa": "#306998", "versicolor": "#FFD43B", "virginica": "#DC2626"}

for idx, row in df_sample.iterrows():
    col = idx % grid_cols
    row_pos = idx // grid_cols
    center_x = col + 0.5
    center_y = (grid_rows - 1 - row_pos) + 0.5  # Flip y so row 0 is at top

    face_df = create_face(row, center_x, center_y, scale=0.42)
    face_df["face_id"] = idx
    face_df["species"] = row["species"]
    all_face_data.append(face_df)

    # Add label
    label_data.append({"x": center_x, "y": center_y - 0.45, "label": row["species"].title(), "species": row["species"]})

faces_df = pd.concat(all_face_data, ignore_index=True)
labels_df = pd.DataFrame(label_data)

# Separate dataframes for different face parts
face_outline = faces_df[faces_df["part"] == "face"]
eyes = faces_df[faces_df["part"].isin(["left_eye", "right_eye"])]
pupils = faces_df[faces_df["part"].isin(["left_pupil", "right_pupil"])]
mouth = faces_df[faces_df["part"] == "mouth"]
brows = faces_df[faces_df["part"].isin(["left_brow", "right_brow"])]
nose = faces_df[faces_df["part"] == "nose"]

# Create the plot
plot = (
    ggplot()
    # Face outlines (colored by species)
    + geom_polygon(
        aes(x="x", y="y", group="face_id", fill="species"), data=face_outline, color="#333333", size=1.5, alpha=0.3
    )
    # Eyes (white fill)
    + geom_polygon(aes(x="x", y="y", group=["face_id", "part"]), data=eyes, fill="white", color="#333333", size=1.0)
    # Pupils (black fill)
    + geom_polygon(aes(x="x", y="y", group=["face_id", "part"]), data=pupils, fill="#333333", color="#333333", size=0.5)
    # Mouth (line)
    + geom_path(aes(x="x", y="y", group="face_id"), data=mouth, color="#333333", size=2.0)
    # Eyebrows (lines)
    + geom_path(aes(x="x", y="y", group=["face_id", "part"]), data=brows, color="#333333", size=2.5)
    # Nose (line)
    + geom_path(aes(x="x", y="y", group="face_id"), data=nose, color="#333333", size=1.5)
    # Species labels (no legend for text color)
    + geom_text(aes(x="x", y="y", label="label"), data=labels_df, color="#333333", size=12, fontface="bold")
    # Color scale
    + scale_fill_manual(values=species_colors)
    # Labels
    + labs(title="Iris Species Comparison · chernoff-basic · lets-plot · pyplots.ai", fill="Species")
    # Theme
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        panel_grid=element_blank(),
        legend_title=element_text(size=16),
        legend_text=element_text(size=14),
        legend_position="right",
        plot_margin=[40, 20, 20, 20],  # top, right, bottom, left
    )
    + ggsize(1600, 900)
)

# Save as PNG (use path parameter to avoid subdirectory creation)
ggsave(plot, "plot.png", scale=3, path=".")

# Save as HTML for interactivity
ggsave(plot, "plot.html", path=".")
