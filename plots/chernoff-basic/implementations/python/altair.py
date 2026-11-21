"""anyplot.ai
chernoff-basic: Chernoff Faces for Multivariate Data
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-15
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
FEATURES = ["Face width", "Face height", "Eye size", "Mouth width"]  # facial features, driven by the variables in order
GRID_ROWS = 3  # faces are laid out in this many rows
CANVAS = (3200, 1800)  # landscape target in pixels
VIEW = (780, 380)  # inner view in view units; scale factor 4 plus title padding lands on the canvas
KEY_WIDTH = 170  # width of the key panel on the right, in view units

# Columns: set these to your table's column names
OBSERVATION = "Observation"  # role: observation_id
VARIABLES = ["Sepal length", "Sepal width", "Petal length", "Petal width"]  # role: variable_
SPECIES = "Species"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("iris.csv")
df = pd.DataFrame(
    {
        OBSERVATION: [f"Sample {i + 1}" for i in range(12)],
        VARIABLES[0]: [0.22, 0.83, 0.45, 0.12, 0.91, 0.67, 0.33, 0.78, 0.55, 0.95, 0.28, 0.61],
        VARIABLES[1]: [0.63, 0.45, 0.78, 0.89, 0.32, 0.56, 0.71, 0.41, 0.65, 0.25, 0.82, 0.48],
        VARIABLES[2]: [0.07, 0.69, 0.42, 0.05, 0.83, 0.55, 0.18, 0.76, 0.38, 0.95, 0.11, 0.62],
        VARIABLES[3]: [0.04, 0.54, 0.33, 0.02, 0.79, 0.48, 0.12, 0.67, 0.29, 0.88, 0.08, 0.52],
        SPECIES: ["setosa", "virginica", "versicolor", "setosa", "virginica", "versicolor"]
        + ["setosa", "virginica", "versicolor", "virginica", "setosa", "versicolor"],
    }
)

# Plot: reads only df and the constants above
view_w, view_h = VIEW
grid_w = view_w - KEY_WIDTH
n_faces = len(df)
n_cols = int(np.ceil(n_faces / GRID_ROWS))
n_rows = int(np.ceil(n_faces / n_cols))
cell_w, cell_h = grid_w / n_cols, view_h / n_rows

# Normalize every variable to 0-1 so each feature spans its full range
values = df[VARIABLES]
norm = (values - values.min()) / (values.max() - values.min()).replace(0, 1)
norm = norm.fillna(0.5)

groups = sorted(df[SPECIES].dropna().unique())
group_color = {g: IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i, g in enumerate(groups)}

theta = np.linspace(0, 2 * np.pi, 72, endpoint=False)
outline_rows, line_rows, point_rows, label_rows = [], [], [], []
for i, (_, rec) in enumerate(df.iterrows()):
    n = norm.iloc[i]
    col, row = i % n_cols, i // n_cols
    cx = (col + 0.5) * cell_w
    cy = view_h - (row + 0.5) * cell_h + 0.06 * cell_h
    color = group_color.get(rec[SPECIES], INK_SOFT)

    # Variables drive feature sizes; the eyebrow slant follows the third variable
    a = cell_w * (0.14 + 0.14 * n[VARIABLES[0]])  # face half-width
    b = cell_h * (0.17 + 0.10 * n[VARIABLES[1]])  # face half-height
    eye_r = min(cell_w, cell_h) * (0.022 + 0.025 * n[VARIABLES[2]])
    mouth_half = a * (0.2 + 0.4 * n[VARIABLES[3]])
    slant = (n[VARIABLES[2]] - 0.5) * 0.16 * b
    eye_x, eye_y = 0.42 * a, 0.22 * b
    face = i

    for k, t in enumerate(theta):
        outline_rows.append({"face": face, "seq": k, "x": cx + a * np.cos(t), "y": cy + b * np.sin(t), "color": color})

    brow_y = eye_y + eye_r + 0.1 * b
    for sign in (-1, 1):
        for end, (dx, dy) in enumerate([(0.30, -slant), (-0.30, slant)]):
            line_rows.append(
                {
                    "face": f"{face}-brow{sign}",
                    "seq": end,
                    "x": cx + sign * eye_x + sign * dx * a,
                    "y": cy + brow_y + dy,
                }
            )
    mx = np.linspace(-mouth_half, mouth_half, 15)
    for k, dx in enumerate(mx):
        line_rows.append(
            {
                "face": f"{face}-mouth",
                "seq": k,
                "x": cx + dx,
                "y": cy - 0.45 * b + 0.22 * b * ((dx / mouth_half) ** 2 - 1),
            }
        )

    for sign in (-1, 1):
        point_rows.append({"x": cx + sign * eye_x, "y": cy + eye_y, "size": np.pi * eye_r**2, "part": "eye"})
        point_rows.append(
            {"x": cx + sign * eye_x, "y": cy + eye_y, "size": np.pi * (0.45 * eye_r) ** 2, "part": "pupil"}
        )
    point_rows.append({"x": cx, "y": cy - 0.12 * b, "size": np.pi * (0.4 * eye_r) ** 2, "part": "nose"})

    label_rows.append(
        {"x": cx, "y": view_h - (row + 1) * cell_h + 0.06 * cell_h, "label": f"{rec[OBSERVATION]} ({rec[SPECIES]})"}
    )

outline_df, line_df = pd.DataFrame(outline_rows), pd.DataFrame(line_rows)
point_df, label_df = pd.DataFrame(point_rows), pd.DataFrame(label_rows)

x_enc = alt.X("x:Q", axis=None, scale=alt.Scale(domain=[0, view_w], nice=False))
y_enc = alt.Y("y:Q", axis=None, scale=alt.Scale(domain=[0, view_h], nice=False))

faces = (
    alt.Chart(outline_df)
    .mark_line(interpolate="linear-closed", fillOpacity=0.55, strokeWidth=1.5)
    .encode(
        x=x_enc,
        y=y_enc,
        order="seq:Q",
        detail="face:N",
        stroke=alt.Stroke("color:N", scale=None, legend=None),
        fill=alt.Fill("color:N", scale=None, legend=None),
    )
)
strokes = (
    alt.Chart(line_df)
    .mark_line(color=INK, strokeWidth=1.8, strokeCap="round")
    .encode(x=x_enc, y=y_enc, order="seq:Q", detail="face:N")
)
part_color = alt.Color(
    "part:N", legend=None, scale=alt.Scale(domain=["eye", "pupil", "nose"], range=[INK, PAGE_BG, INK_SOFT])
)
points = (
    alt.Chart(point_df)
    .mark_point(filled=True, opacity=1)
    .encode(x=x_enc, y=y_enc, size=alt.Size("size:Q", legend=None, scale=None), color=part_color)
)
labels = (
    alt.Chart(label_df)
    .mark_text(fontSize=10, color=INK_SOFT, baseline="top", dy=3)
    .encode(x=x_enc, y=y_enc, text="label:N")
)

# Key: which variable drives which facial feature, and the species colors
key_x = grid_w + 12
key_rows = [f"{feat} ← {var}" for feat, var in zip(FEATURES, VARIABLES, strict=True)]
key_rows += [f"Eyebrow slant ← {VARIABLES[2]}"]
key_df = pd.DataFrame({"x": key_x, "y": [view_h - 40 - 17 * j for j in range(len(key_rows))], "text": key_rows})
key_text = (
    alt.Chart(key_df)
    .mark_text(align="left", baseline="middle", fontSize=10, color=INK_SOFT)
    .encode(x=x_enc, y=y_enc, text="text:N")
)
key_head = (
    alt.Chart(pd.DataFrame({"x": [key_x], "y": [view_h - 22], "text": ["Key"]}))
    .mark_text(align="left", baseline="middle", fontSize=11, fontWeight="bold", color=INK)
    .encode(x=x_enc, y=y_enc, text="text:N")
)
swatch_y0 = key_df["y"].min() - 34
swatch_step = min(17, (swatch_y0 - 6) / max(len(groups) - 1, 1))
swatch_df = pd.DataFrame(
    [
        {"x": key_x + 5, "y": swatch_y0 - swatch_step * j, "species": g, "color": group_color[g]}
        for j, g in enumerate(groups)
    ]
)
swatches = (
    alt.Chart(swatch_df)
    .mark_point(filled=True, size=110, opacity=0.8)
    .encode(x=x_enc, y=y_enc, color=alt.Color("color:N", scale=None, legend=None))
)
swatch_text = (
    alt.Chart(swatch_df)
    .mark_text(align="left", baseline="middle", fontSize=10, dx=12, color=INK_SOFT)
    .encode(x=x_enc, y=y_enc, text="species:N")
)

chart = (
    alt.layer(faces, strokes, points, labels, key_head, key_text, swatches, swatch_text)
    .properties(
        width=view_w,
        height=view_h,
        background=PAGE_BG,
        title=alt.Title(
            "chernoff-basic · python · altair · anyplot.ai",
            fontSize=16,
            anchor="middle",
            color=INK,
            subtitle=f"Each face is one {SPECIES.lower()} sample; variables normalized to 0-1 drive its features",
            subtitleFontSize=11,
            subtitleColor=INK_SOFT,
        ),
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad (never crop) the PNG to the exact canvas
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > CANVAS[0] or img.height > CANVAS[1]:
    raise SystemExit(f"altair rendered {img.size}, larger than the {CANVAS} canvas; shrink VIEW")
if img.size != CANVAS:
    canvas = Image.new("RGB", CANVAS, PAGE_BG)
    canvas.paste(img, ((CANVAS[0] - img.width) // 2, (CANVAS[1] - img.height) // 2))
    canvas.save(f"plot-{THEME}.png")
