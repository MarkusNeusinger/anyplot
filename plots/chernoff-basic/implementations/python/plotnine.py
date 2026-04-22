""" pyplots.ai
chernoff-basic: Chernoff Faces for Multivariate Data
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_text,
    facet_wrap,
    geom_path,
    geom_point,
    geom_polygon,
    ggplot,
    labs,
    scale_fill_manual,
    theme,
    theme_void,
)


np.random.seed(42)

# Data: Car performance metrics (6 cars with 4 metrics each)
# Metrics: Engine Power, Fuel Efficiency, Safety Rating, Comfort Score
car_data = {
    "observation_id": ["Compact A", "Compact B", "Sedan A", "Sedan B", "SUV A", "SUV B"],
    "category": ["Compact", "Compact", "Sedan", "Sedan", "SUV", "SUV"],
    "engine_power": [120, 140, 180, 200, 250, 280],  # HP
    "fuel_efficiency": [35, 32, 28, 25, 22, 18],  # MPG
    "safety_rating": [4.2, 4.5, 4.8, 4.6, 4.4, 4.7],  # 1-5 scale
    "comfort_score": [3.5, 3.8, 4.2, 4.5, 4.0, 4.3],  # 1-5 scale
}
sample_df = pd.DataFrame(car_data)


# Normalize data to 0-1 range for facial feature mapping
def normalize_column(col):
    return (col - col.min()) / (col.max() - col.min() + 1e-10)


normalized = sample_df[["engine_power", "fuel_efficiency", "safety_rating", "comfort_score"]].apply(normalize_column)

# Feature mappings:
# engine_power -> face width (0.6 to 1.0)
# fuel_efficiency -> face height (0.8 to 1.2)
# safety_rating -> eye size (0.08 to 0.18)
# comfort_score -> mouth curvature (-0.3 to 0.3)

face_widths = 0.6 + normalized["engine_power"] * 0.4
face_heights = 0.8 + normalized["fuel_efficiency"] * 0.4
eye_sizes = 0.08 + normalized["safety_rating"] * 0.1
mouth_curvatures = -0.3 + normalized["comfort_score"] * 0.6


# Generate face polygon vertices (ellipse approximation)
def make_ellipse(cx, cy, rx, ry, n_points=50):
    theta = np.linspace(0, 2 * np.pi, n_points)
    x = cx + rx * np.cos(theta)
    y = cy + ry * np.sin(theta)
    return x, y


# Generate eye vertices
def make_eye(cx, cy, r, n_points=20):
    theta = np.linspace(0, 2 * np.pi, n_points)
    x = cx + r * np.cos(theta)
    y = cy + r * np.sin(theta)
    return x, y


# Generate mouth curve
def make_mouth(cx, cy, width, curvature, n_points=20):
    x = np.linspace(cx - width / 2, cx + width / 2, n_points)
    y = cy + curvature * (((x - cx) / (width / 2)) ** 2 - 1)
    return x, y


# Generate eyebrow
def make_eyebrow(cx, cy, width, slant, n_points=10):
    x = np.linspace(cx - width / 2, cx + width / 2, n_points)
    y = cy + slant * (x - cx) / (width / 2)
    return x, y


# Build data for all faces
all_data = []

for idx in range(len(sample_df)):
    obs_id = sample_df["observation_id"].iloc[idx]
    category = sample_df["category"].iloc[idx]

    fw = face_widths.iloc[idx]
    fh = face_heights.iloc[idx]
    es = eye_sizes.iloc[idx]
    mc = mouth_curvatures.iloc[idx]

    # Face outline
    fx, fy = make_ellipse(0, 0, fw, fh)
    for i in range(len(fx)):
        all_data.append(
            {"observation_id": obs_id, "category": category, "part": "face", "x": fx[i], "y": fy[i], "order": i}
        )

    # Left eye
    ex, ey = make_eye(-fw * 0.35, fh * 0.25, es)
    for i in range(len(ex)):
        all_data.append(
            {"observation_id": obs_id, "category": category, "part": "left_eye", "x": ex[i], "y": ey[i], "order": i}
        )

    # Right eye
    ex, ey = make_eye(fw * 0.35, fh * 0.25, es)
    for i in range(len(ex)):
        all_data.append(
            {"observation_id": obs_id, "category": category, "part": "right_eye", "x": ex[i], "y": ey[i], "order": i}
        )

    # Left pupil (point)
    all_data.append(
        {
            "observation_id": obs_id,
            "category": category,
            "part": "left_pupil",
            "x": -fw * 0.35,
            "y": fh * 0.25,
            "order": 0,
        }
    )

    # Right pupil (point)
    all_data.append(
        {
            "observation_id": obs_id,
            "category": category,
            "part": "right_pupil",
            "x": fw * 0.35,
            "y": fh * 0.25,
            "order": 0,
        }
    )

    # Mouth
    mx, my = make_mouth(0, -fh * 0.35, fw * 0.5, mc)
    for i in range(len(mx)):
        all_data.append(
            {"observation_id": obs_id, "category": category, "part": "mouth", "x": mx[i], "y": my[i], "order": i}
        )

    # Nose (simple vertical line)
    all_data.append({"observation_id": obs_id, "category": category, "part": "nose", "x": 0, "y": fh * 0.1, "order": 0})
    all_data.append(
        {"observation_id": obs_id, "category": category, "part": "nose", "x": 0, "y": -fh * 0.1, "order": 1}
    )

    # Left eyebrow
    bx, by = make_eyebrow(-fw * 0.35, fh * 0.45, es * 2.5, 0.05)
    for i in range(len(bx)):
        all_data.append(
            {"observation_id": obs_id, "category": category, "part": "left_eyebrow", "x": bx[i], "y": by[i], "order": i}
        )

    # Right eyebrow
    bx, by = make_eyebrow(fw * 0.35, fh * 0.45, es * 2.5, -0.05)
    for i in range(len(bx)):
        all_data.append(
            {
                "observation_id": obs_id,
                "category": category,
                "part": "right_eyebrow",
                "x": bx[i],
                "y": by[i],
                "order": i,
            }
        )

plot_df = pd.DataFrame(all_data)

# Separate dataframes for different geoms
face_df = plot_df[plot_df["part"] == "face"].copy()
left_eye_df = plot_df[plot_df["part"] == "left_eye"].copy()
right_eye_df = plot_df[plot_df["part"] == "right_eye"].copy()
left_pupil_df = plot_df[plot_df["part"] == "left_pupil"].copy()
right_pupil_df = plot_df[plot_df["part"] == "right_pupil"].copy()
mouth_df = plot_df[plot_df["part"] == "mouth"].copy()
nose_df = plot_df[plot_df["part"] == "nose"].copy()
left_eyebrow_df = plot_df[plot_df["part"] == "left_eyebrow"].copy()
right_eyebrow_df = plot_df[plot_df["part"] == "right_eyebrow"].copy()

# Category colors
category_colors = {"Compact": "#306998", "Sedan": "#FFD43B", "SUV": "#4B8BBE"}

# Create the plot using native plotnine geoms
plot = (
    ggplot()
    # Face outline (filled polygon)
    + geom_polygon(
        data=face_df, mapping=aes(x="x", y="y", group="observation_id", fill="category"), color="#333333", size=1.5
    )
    # Eyes (white filled)
    + geom_polygon(
        data=left_eye_df, mapping=aes(x="x", y="y", group="observation_id"), fill="white", color="#333333", size=0.8
    )
    + geom_polygon(
        data=right_eye_df, mapping=aes(x="x", y="y", group="observation_id"), fill="white", color="#333333", size=0.8
    )
    # Pupils
    + geom_point(data=left_pupil_df, mapping=aes(x="x", y="y"), color="#333333", size=3)
    + geom_point(data=right_pupil_df, mapping=aes(x="x", y="y"), color="#333333", size=3)
    # Mouth
    + geom_path(data=mouth_df, mapping=aes(x="x", y="y", group="observation_id"), color="#333333", size=1.2)
    # Nose
    + geom_path(data=nose_df, mapping=aes(x="x", y="y", group="observation_id"), color="#333333", size=1)
    # Eyebrows
    + geom_path(data=left_eyebrow_df, mapping=aes(x="x", y="y", group="observation_id"), color="#333333", size=1.2)
    + geom_path(data=right_eyebrow_df, mapping=aes(x="x", y="y", group="observation_id"), color="#333333", size=1.2)
    # Facet by observation
    + facet_wrap("~observation_id", ncol=3)
    # Colors
    + scale_fill_manual(values=category_colors)
    # Labels
    + labs(
        title="chernoff-basic · plotnine · pyplots.ai",
        subtitle="Car Performance: Power/Efficiency/Safety/Comfort mapped to facial features",
        fill="Category",
    )
    # Theme
    + theme_void()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, ha="center", weight="bold"),
        plot_subtitle=element_text(size=16, ha="center"),
        legend_title=element_text(size=16),
        legend_text=element_text(size=14),
        strip_text=element_text(size=14, weight="bold"),
        legend_position="bottom",
    )
    + coord_fixed(ratio=1)
)

plot.save("plot.png", dpi=300, width=16, height=9)
