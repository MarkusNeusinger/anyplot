"""anyplot.ai
chernoff-basic: Chernoff Faces for Multivariate Data
Library: letsplot 4.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-15
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

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
GRID_COLS = 4  # faces per row in the grid layout

# Columns: set these to your table's column names
OBSERVATION = "Flower"  # role: observation_id
SPECIES = "Species"  # role: extra
VARIABLES = ["Sepal length (cm)", "Sepal width (cm)", "Petal length (cm)", "Petal width (cm)"]  # role: variable_

# Data: replace this block with your own table, for example df = pd.read_csv("flowers.csv")
np.random.seed(42)
iris = load_iris()
iris_df = pd.DataFrame(iris.data, columns=VARIABLES)
iris_df[SPECIES] = [iris.target_names[i] for i in iris.target]
picked = [np.random.choice(np.flatnonzero(iris.target == k), 4, replace=False) for k in range(len(iris.target_names))]
df = iris_df.iloc[np.concatenate(picked)].reset_index(drop=True)
df[SPECIES] = df[SPECIES].str.title()
df.insert(0, OBSERVATION, [f"Flower {i + 1}" for i in range(len(df))])

# Plot: reads only df and the constants above
features = VARIABLES
span = (df[features].max() - df[features].min()).replace(0, 1)
norm = (df[features] - df[features].min()) / span  # every variable on a common 0-1 scale

groups = list(dict.fromkeys(df[SPECIES]))
species_colors = {g: IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i, g in enumerate(groups)}
grid_rows = int(np.ceil(len(df) / GRID_COLS))
scale = 0.42
theta = np.linspace(0, 2 * np.pi, 50)
theta_eye = np.linspace(0, 2 * np.pi, 20)

LAYER_OF = {"face": "face", "eye": "eyes", "pupil": "pupils", "mouth": "mouth", "brow": "brows", "nose": "nose"}
parts = []
label_rows = []
for idx in range(len(df)):
    cx = idx % GRID_COLS + 0.5
    cy = (grid_rows - 1 - idx // GRID_COLS) + 0.5
    sepal_len, sepal_wid, petal_len, petal_wid = norm.iloc[idx][features].to_numpy()

    def add(part, xs, ys, face_id=idx):
        parts.append(
            pd.DataFrame(
                {
                    "x": xs,
                    "y": ys,
                    "part": part,
                    "layer": LAYER_OF[part.split("_")[-1]],
                    "face_id": face_id,
                    "order": range(len(xs)),
                }
            )
        )

    # Face outline: width follows sepal length
    face_width = 0.35 + 0.2 * sepal_len
    add("face", cx + scale * face_width * np.cos(theta), cy + scale * 0.45 * np.sin(theta))

    # Eyes and pupils: size follows sepal width
    eye_size = 0.03 + 0.04 * sepal_wid
    eye_spacing = 0.12
    eye_y = cy + scale * 0.12
    for side, sign in (("left", -1), ("right", 1)):
        ex = cx + sign * scale * eye_spacing
        add(f"{side}_eye", ex + scale * eye_size * np.cos(theta_eye), eye_y + scale * eye_size * np.sin(theta_eye))
        pupil = eye_size * 0.4
        add(f"{side}_pupil", ex + scale * pupil * np.cos(theta_eye), eye_y + scale * pupil * np.sin(theta_eye))

    # Mouth: curvature follows petal length
    mouth_width = 0.12
    curvature = -0.08 + 0.16 * petal_len
    mx = np.linspace(-mouth_width, mouth_width, 20)
    add("mouth", cx + scale * mx, cy - scale * 0.15 + scale * curvature * (1 - (mx / mouth_width) ** 2))

    # Eyebrows: slant follows petal width
    brow_y = cy + scale * 0.22
    slant = -0.03 + 0.06 * petal_wid
    brow_length = 0.06
    add(
        "left_brow",
        [cx - scale * (eye_spacing + brow_length), cx - scale * (eye_spacing - brow_length)],
        [brow_y - scale * slant, brow_y + scale * slant],
    )
    add(
        "right_brow",
        [cx + scale * (eye_spacing - brow_length), cx + scale * (eye_spacing + brow_length)],
        [brow_y + scale * slant, brow_y - scale * slant],
    )

    # Nose
    add("nose", [cx, cx], [cy + scale * 0.02, cy - scale * 0.08])

    label_rows.append(
        {"x": cx, "y": cy - 0.45, "label": str(df[SPECIES].iloc[idx]).title(), SPECIES: df[SPECIES].iloc[idx]}
    )

faces_df = pd.concat(parts, ignore_index=True)
faces_df = faces_df.merge(
    pd.DataFrame({"face_id": range(len(df)), SPECIES: df[SPECIES].to_numpy()}), on="face_id", how="left"
)
labels_df = pd.DataFrame(label_rows)

layers = dict(list(faces_df.groupby("layer")))
face_outline, eyes, pupils = layers["face"], layers["eyes"], layers["pupils"]
mouth, brows, nose = layers["mouth"], layers["brows"], layers["nose"]

# Key: which variable drives which facial feature
key = (
    f"Face width: {VARIABLES[0]}   ·   Eye size: {VARIABLES[1]}\n"
    f"Mouth curvature: {VARIABLES[2]}   ·   Eyebrow slant: {VARIABLES[3]}"
)

# Style
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_grid=element_blank(),
    axis_title=element_blank(),
    axis_text=element_blank(),
    axis_ticks=element_blank(),
    plot_title=element_text(size=16, face="bold", color=INK),
    plot_caption=element_text(size=11, color=INK_SOFT),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_title=element_text(size=12, color=INK),
    legend_text=element_text(size=11, color=INK_SOFT),
    legend_position="right",
    plot_margin=[20, 10, 10, 10],
)

plot = (
    ggplot()
    + geom_polygon(
        aes(x="x", y="y", group="face_id", fill=SPECIES), data=face_outline, color=INK_SOFT, size=0.8, alpha=0.3
    )
    + geom_polygon(aes(x="x", y="y", group=["face_id", "part"]), data=eyes, fill="white", color=INK_SOFT, size=0.5)
    + geom_polygon(aes(x="x", y="y", group=["face_id", "part"]), data=pupils, fill=INK, color=INK, size=0.3)
    + geom_path(aes(x="x", y="y", group="face_id"), data=mouth, color=INK, size=1.0)
    + geom_path(aes(x="x", y="y", group=["face_id", "part"]), data=brows, color=INK, size=1.2)
    + geom_path(aes(x="x", y="y", group="face_id"), data=nose, color=INK, size=0.8)
    + geom_text(aes(x="x", y="y", label="label"), data=labels_df, color=INK_SOFT, size=4, fontface="bold")
    + scale_fill_manual(values=species_colors)
    + labs(title="chernoff-basic · python · letsplot · anyplot.ai", fill=SPECIES, caption=key)
    + anyplot_theme
    + ggsize(800, 450)
)

# Save outputs
ggsave(plot, f"plot-{THEME}.png", scale=4, path=".")
ggsave(plot, f"plot-{THEME}.html", path=".")
