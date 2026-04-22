""" pyplots.ai
chernoff-basic: Chernoff Faces for Multivariate Data
Library: altair 6.0.0 | Python 3.13.11
Quality: 87/100 | Created: 2025-12-31
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Iris dataset features for 12 representative flowers
np.random.seed(42)
# Diverse samples from iris-like measurements (normalized 0-1)
data = pd.DataFrame(
    {
        "observation": [f"Sample {i + 1}" for i in range(12)],
        "sepal_length": [0.22, 0.83, 0.45, 0.12, 0.91, 0.67, 0.33, 0.78, 0.55, 0.95, 0.28, 0.61],
        "sepal_width": [0.63, 0.45, 0.78, 0.89, 0.32, 0.56, 0.71, 0.41, 0.65, 0.25, 0.82, 0.48],
        "petal_length": [0.07, 0.69, 0.42, 0.05, 0.83, 0.55, 0.18, 0.76, 0.38, 0.95, 0.11, 0.62],
        "petal_width": [0.04, 0.54, 0.33, 0.02, 0.79, 0.48, 0.12, 0.67, 0.29, 0.88, 0.08, 0.52],
        "species": [
            "setosa",
            "virginica",
            "versicolor",
            "setosa",
            "virginica",
            "versicolor",
            "setosa",
            "virginica",
            "versicolor",
            "virginica",
            "setosa",
            "versicolor",
        ],
    }
)

# Map species to colors
species_colors = {"setosa": "#306998", "versicolor": "#FFD43B", "virginica": "#4B8BBE"}
data["color"] = data["species"].map(species_colors)

# Create descriptive labels including species name
data["label"] = [f"{obs} ({sp})" for obs, sp in zip(data["observation"], data["species"], strict=True)]

# Grid positions for 12 faces (4 columns x 3 rows for better canvas utilization)
data["col"] = [i % 4 for i in range(12)]
data["row"] = [i // 4 for i in range(12)]
data["x_center"] = data["col"] * 200 + 130
data["y_center"] = (2 - data["row"]) * 240 + 160

# Calculate face feature dimensions based on variables with more pronounced variation
# face_width: sepal_length, face_height: sepal_width
# eye_size: petal_length, mouth_width: petal_width
# eyebrow_slant: derived from petal_length (maps to eyebrow angle)
data["face_width"] = 40 + data["sepal_length"] * 70  # 40-110
data["face_height"] = 50 + data["sepal_width"] * 80  # 50-130
data["eye_size"] = 6 + data["petal_length"] * 22  # 6-28
data["mouth_width"] = 15 + data["petal_width"] * 35  # 15-50
data["eyebrow_slant"] = -15 + data["petal_length"] * 30  # -15 to 15

# Build face components using layered shapes
face_records = []

for _, r in data.iterrows():
    xc, yc = r["x_center"], r["y_center"]
    fw, fh = r["face_width"], r["face_height"]
    es = r["eye_size"]
    mw = r["mouth_width"]
    eb_slant = r["eyebrow_slant"]

    # Face outline - single smooth ellipse using many small points on perimeter
    # This creates a clean ellipse shape instead of blobby overlapping circles
    for angle in np.linspace(0, 2 * np.pi, 48, endpoint=False):
        px = xc + (fw * 0.9) * np.cos(angle)
        py = yc + (fh * 0.75) * np.sin(angle)
        face_records.append(
            {
                "x": px,
                "y": py,
                "size": 350,
                "color": r["color"],
                "part": "outline",
                "observation": r["observation"],
                "species": r["species"],
                "opacity": 0.7,
            }
        )

    # Face fill - concentric rings of points to fill the ellipse smoothly
    for scale in [0.8, 0.6, 0.4, 0.2]:
        for angle in np.linspace(0, 2 * np.pi, int(36 * scale) + 8, endpoint=False):
            px = xc + (fw * 0.9 * scale) * np.cos(angle)
            py = yc + (fh * 0.75 * scale) * np.sin(angle)
            face_records.append(
                {
                    "x": px,
                    "y": py,
                    "size": 400,
                    "color": r["color"],
                    "part": "face_fill",
                    "observation": r["observation"],
                    "species": r["species"],
                    "opacity": 0.5,
                }
            )

    # Center fill point
    face_records.append(
        {
            "x": xc,
            "y": yc,
            "size": 600,
            "color": r["color"],
            "part": "face_fill",
            "observation": r["observation"],
            "species": r["species"],
            "opacity": 0.5,
        }
    )

    # Left eyebrow (line represented by two points)
    face_records.append(
        {
            "x": xc - fw * 0.38,
            "y": yc + fh * 0.32 + eb_slant * 0.3,
            "size": 120,
            "color": "#2C3E50",
            "part": "eyebrow",
            "observation": r["observation"],
            "species": r["species"],
            "opacity": 0.9,
        }
    )
    face_records.append(
        {
            "x": xc - fw * 0.22,
            "y": yc + fh * 0.32 - eb_slant * 0.3,
            "size": 120,
            "color": "#2C3E50",
            "part": "eyebrow",
            "observation": r["observation"],
            "species": r["species"],
            "opacity": 0.9,
        }
    )
    # Right eyebrow
    face_records.append(
        {
            "x": xc + fw * 0.22,
            "y": yc + fh * 0.32 - eb_slant * 0.3,
            "size": 120,
            "color": "#2C3E50",
            "part": "eyebrow",
            "observation": r["observation"],
            "species": r["species"],
            "opacity": 0.9,
        }
    )
    face_records.append(
        {
            "x": xc + fw * 0.38,
            "y": yc + fh * 0.32 + eb_slant * 0.3,
            "size": 120,
            "color": "#2C3E50",
            "part": "eyebrow",
            "observation": r["observation"],
            "species": r["species"],
            "opacity": 0.9,
        }
    )
    # Left eye
    face_records.append(
        {
            "x": xc - fw * 0.30,
            "y": yc + fh * 0.15,
            "size": es * 45,
            "color": "#1A252F",
            "part": "eye",
            "observation": r["observation"],
            "species": r["species"],
            "opacity": 1.0,
        }
    )
    # Right eye
    face_records.append(
        {
            "x": xc + fw * 0.30,
            "y": yc + fh * 0.15,
            "size": es * 45,
            "color": "#1A252F",
            "part": "eye",
            "observation": r["observation"],
            "species": r["species"],
            "opacity": 1.0,
        }
    )
    # Left pupil (white highlight)
    face_records.append(
        {
            "x": xc - fw * 0.30 + 3,
            "y": yc + fh * 0.15 + 3,
            "size": es * 12,
            "color": "#FFFFFF",
            "part": "pupil",
            "observation": r["observation"],
            "species": r["species"],
            "opacity": 0.95,
        }
    )
    # Right pupil (white highlight)
    face_records.append(
        {
            "x": xc + fw * 0.30 + 3,
            "y": yc + fh * 0.15 + 3,
            "size": es * 12,
            "color": "#FFFFFF",
            "part": "pupil",
            "observation": r["observation"],
            "species": r["species"],
            "opacity": 0.95,
        }
    )
    # Nose
    face_records.append(
        {
            "x": xc,
            "y": yc - fh * 0.05,
            "size": 90,
            "color": "#5D6D7E",
            "part": "nose",
            "observation": r["observation"],
            "species": r["species"],
            "opacity": 0.7,
        }
    )
    # Mouth - using horizontal ellipse shape for better representation
    mouth_y = yc - fh * 0.30
    for dx in np.linspace(-mw * 0.4, mw * 0.4, 7):
        # Parabolic curve for mouth (smiling effect based on width)
        dy = -(dx**2) / (mw * 1.2) + mw * 0.08
        face_records.append(
            {
                "x": xc + dx,
                "y": mouth_y + dy,
                "size": 80 if abs(dx) < mw * 0.3 else 50,
                "color": "#C0392B",
                "part": "mouth",
                "observation": r["observation"],
                "species": r["species"],
                "opacity": 0.9,
            }
        )

face_df = pd.DataFrame(face_records)

# Reorder facial features drawing order
part_order = {"outline": 0, "face_fill": 1, "eyebrow": 2, "nose": 3, "mouth": 4, "eye": 5, "pupil": 6}
face_df["order"] = face_df["part"].map(part_order)
face_df = face_df.sort_values("order")

# Create labels for each face - positioned below faces with descriptive text
label_df = data[["x_center", "y_center", "label", "face_height"]].copy()
label_df["y_label"] = label_df["y_center"] - label_df["face_height"] * 0.7 - 35

# Face features chart (includes outline, fill, and features)
features = (
    alt.Chart(face_df)
    .mark_point(filled=True)
    .encode(
        x=alt.X("x:Q", axis=None, scale=alt.Scale(domain=[0, 900])),
        y=alt.Y("y:Q", axis=None, scale=alt.Scale(domain=[0, 800])),
        size=alt.Size("size:Q", legend=None, scale=alt.Scale(range=[40, 1600])),
        color=alt.Color("color:N", legend=None, scale=None),
        opacity=alt.Opacity("opacity:Q", legend=None),
        order="order:O",
    )
)

# Labels with species info
labels = (
    alt.Chart(label_df)
    .mark_text(fontSize=13, fontWeight="bold", color="#2C3E50")
    .encode(x=alt.X("x_center:Q", axis=None), y=alt.Y("y_label:Q", axis=None), text="label:N")
)

# Legend for species (positioned on right side, higher up to avoid overlap)
legend_data = pd.DataFrame(
    {
        "species": ["setosa", "versicolor", "virginica"],
        "x": [850, 850, 850],
        "y": [780, 730, 680],
        "color": ["#306998", "#FFD43B", "#4B8BBE"],
    }
)

legend_points = (
    alt.Chart(legend_data)
    .mark_point(filled=True, size=600, opacity=0.5)
    .encode(x=alt.X("x:Q", axis=None), y=alt.Y("y:Q", axis=None), color=alt.Color("color:N", scale=None, legend=None))
)

legend_text = (
    alt.Chart(legend_data)
    .mark_text(align="right", fontSize=14, dx=-25, fontWeight="bold")
    .encode(x="x:Q", y="y:Q", text="species:N")
)

# Feature mapping explanation - positioned at top left to avoid overlap with faces
mapping_data = pd.DataFrame(
    {
        "text": [
            "Feature Mapping:",
            "Face width ← sepal length",
            "Face height ← sepal width",
            "Eye size ← petal length",
            "Mouth width ← petal width",
            "Eyebrow slant ← petal length",
        ],
        "x": [30, 30, 30, 30, 30, 30],
        "y": [785, 760, 735, 710, 685, 660],
    }
)

mapping_text = (
    alt.Chart(mapping_data)
    .mark_text(align="left", fontSize=12, color="#34495E")
    .encode(x="x:Q", y="y:Q", text="text:N")
)

# Combine all layers
chart = (
    (features + labels + legend_points + legend_text + mapping_text)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "chernoff-basic · altair · pyplots.ai",
            fontSize=28,
            anchor="middle",
            subtitle="Iris Dataset: Each face represents a flower sample with features encoding measurements",
            subtitleFontSize=16,
        ),
    )
    .configure_view(strokeWidth=0)
)

# Save as PNG and HTML
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
