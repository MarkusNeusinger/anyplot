""" anyplot.ai
chernoff-basic: Chernoff Faces for Multivariate Data
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 80/100 | Updated: 2026-05-15
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_rect,
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

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - Iris dataset
np.random.seed(42)
iris = load_iris()
df = pd.DataFrame(iris.data, columns=["sepal_length", "sepal_width", "petal_length", "petal_width"])
df["species"] = [iris.target_names[i] for i in iris.target]

# Sample 12 flowers (4 per species)
sample_idx = []
for species in range(3):
    species_idx = np.where(iris.target == species)[0]
    sample_idx.extend(np.random.choice(species_idx, 4, replace=False))
df_sample = df.iloc[sample_idx].reset_index(drop=True)

# Normalize data to 0-1 range
features = ["sepal_length", "sepal_width", "petal_length", "petal_width"]
for col in features:
    min_val = df_sample[col].min()
    max_val = df_sample[col].max()
    df_sample[col + "_norm"] = (df_sample[col] - min_val) / (max_val - min_val)

# Generate faces in a grid
grid_rows = 3
grid_cols = 4
all_face_data = []
label_data = []
species_colors = {"setosa": "#009E73", "versicolor": "#C475FD", "virginica": "#4467A3"}

for idx, row in df_sample.iterrows():
    col = idx % grid_cols
    row_pos = idx // grid_cols
    center_x = col + 0.5
    center_y = (grid_rows - 1 - row_pos) + 0.5

    sepal_len = row["sepal_length_norm"]
    sepal_wid = row["sepal_width_norm"]
    petal_len = row["petal_length_norm"]
    petal_wid = row["petal_width_norm"]

    scale = 0.42
    face_data = []

    # Face outline (ellipse)
    face_width = 0.35 + 0.2 * sepal_len
    face_height = 0.45
    theta = np.linspace(0, 2 * np.pi, 50)
    face_x = center_x + scale * face_width * np.cos(theta)
    face_y = center_y + scale * face_height * np.sin(theta)
    for i in range(len(theta)):
        face_data.append({"x": face_x[i], "y": face_y[i], "part": "face", "order": i})

    # Eyes
    eye_size = 0.03 + 0.04 * sepal_wid
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

    # Mouth
    mouth_y = center_y - scale * 0.15
    mouth_width = 0.12
    curvature = -0.08 + 0.16 * petal_len
    mouth_x = np.linspace(-mouth_width, mouth_width, 20)
    mouth_curve_y = mouth_y + scale * curvature * (1 - (mouth_x / mouth_width) ** 2)
    mouth_curve_x = center_x + scale * mouth_x
    for i in range(len(mouth_x)):
        face_data.append({"x": mouth_curve_x[i], "y": mouth_curve_y[i], "part": "mouth", "order": i})

    # Eyebrows
    brow_y = center_y + scale * 0.22
    brow_slant = -0.03 + 0.06 * petal_wid
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

    # Nose
    nose_top = center_y + scale * 0.02
    nose_bottom = center_y - scale * 0.08
    face_data.append({"x": center_x, "y": nose_top, "part": "nose", "order": 0})
    face_data.append({"x": center_x, "y": nose_bottom, "part": "nose", "order": 1})

    # Convert to DataFrame and add metadata
    face_df = pd.DataFrame(face_data)
    face_df["face_id"] = idx
    face_df["species"] = row["species"]
    all_face_data.append(face_df)

    # Add species label
    label_data.append({"x": center_x, "y": center_y - 0.45, "label": row["species"].title(), "species": row["species"]})

# Combine all face data
faces_df = pd.concat(all_face_data, ignore_index=True)
labels_df = pd.DataFrame(label_data)

# Separate face parts for layering
face_outline = faces_df[faces_df["part"] == "face"]
eyes = faces_df[faces_df["part"].isin(["left_eye", "right_eye"])]
pupils = faces_df[faces_df["part"].isin(["left_pupil", "right_pupil"])]
mouth = faces_df[faces_df["part"] == "mouth"]
brows = faces_df[faces_df["part"].isin(["left_brow", "right_brow"])]
nose = faces_df[faces_df["part"] == "nose"]

# Create plot with theme-adaptive styling
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_grid=element_blank(),
    axis_title=element_blank(),
    axis_text=element_blank(),
    axis_ticks=element_blank(),
    plot_title=element_text(size=24, face="bold", color=INK),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_title=element_text(size=18, color=INK),
    legend_text=element_text(size=16, color=INK_SOFT),
    legend_position="right",
    plot_margin=[40, 20, 20, 20],
)

plot = (
    ggplot()
    + geom_polygon(
        aes(x="x", y="y", group="face_id", fill="species"), data=face_outline, color=INK_SOFT, size=1.5, alpha=0.3
    )
    + geom_polygon(aes(x="x", y="y", group=["face_id", "part"]), data=eyes, fill="white", color=INK_SOFT, size=1.0)
    + geom_polygon(aes(x="x", y="y", group=["face_id", "part"]), data=pupils, fill=INK, color=INK, size=0.5)
    + geom_path(aes(x="x", y="y", group="face_id"), data=mouth, color=INK, size=2.0)
    + geom_path(aes(x="x", y="y", group=["face_id", "part"]), data=brows, color=INK, size=2.5)
    + geom_path(aes(x="x", y="y", group="face_id"), data=nose, color=INK, size=1.5)
    + geom_text(aes(x="x", y="y", label="label"), data=labels_df, color=INK_SOFT, size=12, fontface="bold")
    + scale_fill_manual(values=species_colors)
    + labs(title="chernoff-basic · letsplot · anyplot.ai", fill="Species")
    + anyplot_theme
    + ggsize(1600, 900)
)

# Save outputs
ggsave(plot, f"plot-{THEME}.png", scale=3, path=".")
ggsave(plot, f"plot-{THEME}.html", path=".")
