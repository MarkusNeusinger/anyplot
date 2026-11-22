""" anyplot.ai
biplot-pca: PCA Biplot with Scores and Loading Vectors
Library: altair 6.3.0 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-22
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image
from sklearn.datasets import load_iris
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
LOADING_SCALE = 2.5  # one common factor that brings the arrows to the scale of the scores
LABEL_PUSH = 1.15  # variable names sit slightly beyond the arrow tips
WIDTH, HEIGHT = 620, 320  # inner view size; the saved PNG is padded to 3200 x 1800
TARGET = (3200, 1800)

# Columns: set these to your table's column names
SEPAL_LENGTH = "Sepal Length"  # role: features
SEPAL_WIDTH = "Sepal Width"  # role: features
PETAL_LENGTH = "Petal Length"  # role: features
PETAL_WIDTH = "Petal Width"  # role: features
SPECIES = "Species"  # role: labels
FEATURES = [SEPAL_LENGTH, SEPAL_WIDTH, PETAL_LENGTH, PETAL_WIDTH]

# Data: replace this block with your own table, for example df = pd.read_csv("measurements.csv")
iris = load_iris()
df = pd.DataFrame(iris.data, columns=FEATURES)
df[SPECIES] = iris.target_names[iris.target]

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
PC1, PC2 = "PC1", "PC2"
VARIABLE = "Variable"

# PCA on standardized features
pca = PCA(n_components=2, random_state=42)
df = df.dropna(subset=FEATURES)  # PCA needs complete rows
scores = pca.fit_transform(StandardScaler().fit_transform(df[FEATURES]))
var_explained = pca.explained_variance_ratio_ * 100

scores_df = pd.DataFrame({PC1: scores[:, 0], PC2: scores[:, 1], SPECIES: df[SPECIES]})
loadings_df = pd.DataFrame(
    {VARIABLE: FEATURES, PC1: pca.components_[0] * LOADING_SCALE, PC2: pca.components_[1] * LOADING_SCALE}
)

# Symmetric axis limits derived from everything that is drawn
x_lim = float(np.ceil(max(scores_df[PC1].abs().max(), loadings_df[PC1].abs().max() * LABEL_PUSH) + 0.3))
y_lim = float(np.ceil(max(scores_df[PC2].abs().max(), loadings_df[PC2].abs().max() * LABEL_PUSH) + 0.3))

# Arrow shafts: origin -> loading tip, one line per variable
arrow_df = pd.concat(
    [
        pd.DataFrame({"x": 0.0, "y": 0.0, VARIABLE: FEATURES, "order": 0}),
        pd.DataFrame({"x": loadings_df[PC1], "y": loadings_df[PC2], VARIABLE: FEATURES, "order": 1}),
    ],
    ignore_index=True,
)

# Arrowhead rotation in pixel space (clockwise from "up"), so heads follow the drawn shaft
loadings_df["angle"] = np.degrees(np.arctan2(loadings_df[PC1] / x_lim * WIDTH, loadings_df[PC2] / y_lim * HEIGHT))
loadings_df["label_x"] = loadings_df[PC1] * LABEL_PUSH
loadings_df["label_y"] = loadings_df[PC2] * LABEL_PUSH

x_axis = alt.X(
    f"{PC1}:Q", title=f"{PC1} ({var_explained[0]:.1f}% of variance)", scale=alt.Scale(domain=[-x_lim, x_lim])
)
y_axis = alt.Y(
    f"{PC2}:Q", title=f"{PC2} ({var_explained[1]:.1f}% of variance)", scale=alt.Scale(domain=[-y_lim, y_lim])
)

scatter = (
    alt.Chart(scores_df)
    .mark_point(size=28, opacity=0.8, filled=True)
    .encode(
        x=x_axis,
        y=y_axis,
        color=alt.Color(
            SPECIES.translate(ESCAPE),
            type="nominal",
            title=SPECIES,
            scale=alt.Scale(range=IMPRINT_PALETTE),
            legend=alt.Legend(symbolSize=90, orient="right", padding=8, labelLimit=200),
        ),
        tooltip=[
            alt.Tooltip(SPECIES.translate(ESCAPE), title=SPECIES),
            alt.Tooltip(f"{PC1}:Q", format=".2f"),
            alt.Tooltip(f"{PC2}:Q", format=".2f"),
        ],
    )
)

arrows = (
    alt.Chart(arrow_df)
    .mark_line(color=INK_SOFT, strokeWidth=1.4, opacity=0.9)
    .encode(x="x:Q", y="y:Q", detail=f"{VARIABLE}:N", order="order:O")
)

arrowheads = (
    alt.Chart(loadings_df)
    .mark_point(shape="triangle", size=60, color=INK_SOFT, opacity=0.9, filled=True)
    .encode(x=f"{PC1}:Q", y=f"{PC2}:Q", angle=alt.Angle("angle:Q", scale=None))
)

# Push the name of an arrow whose tip sits close to another tip up or down, so neighbours stay legible
tip_px = np.column_stack([loadings_df[PC1] / x_lim * WIDTH, loadings_df[PC2] / y_lim * HEIGHT])
gaps = np.linalg.norm(tip_px[:, None] - tip_px[None], axis=2) + np.eye(len(tip_px)) * 1e9
nearest = gaps.argmin(axis=1)
close = gaps.min(axis=1) < 40
push_px = np.where(close, np.where(loadings_df[PC2] >= loadings_df[PC2].to_numpy()[nearest], 7, -7), 0)
loadings_df["label_y"] = loadings_df["label_y"] + push_px / HEIGHT * 2 * y_lim

label_base = alt.Chart(loadings_df).encode(x="label_x:Q", y="label_y:Q", text=f"{VARIABLE}:N")
label_parts = []
for side, dx, cond in (("left", 4, f"datum['{PC1}'] >= 0"), ("right", -4, f"datum['{PC1}'] < 0")):
    # a page-colored halo under the ink text keeps names readable over score points
    halo = label_base.mark_text(
        fontSize=10, fontWeight="bold", color=PAGE_BG, stroke=PAGE_BG, strokeWidth=3, align=side, dx=dx
    )
    text = label_base.mark_text(fontSize=10, fontWeight="bold", color=INK, align=side, dx=dx)
    label_parts += [halo.transform_filter(cond), text.transform_filter(cond)]
loading_labels = alt.layer(*label_parts)

origin = (
    alt.Chart(pd.DataFrame({"x": [0.0], "y": [0.0]}))
    .mark_point(size=40, color=INK_SOFT, shape="cross", strokeWidth=1.2)
    .encode(x="x:Q", y="y:Q")
)

chart = (
    alt.layer(scatter, arrows, arrowheads, loading_labels, origin)
    .properties(
        width=WIDTH,
        height=HEIGHT,
        background=PAGE_BG,
        title=alt.Title("biplot-pca · python · altair · anyplot.ai", fontSize=16, anchor="middle", color=INK),
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=10,
        titleFontSize=12,
    )
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        titleFontSize=12,
        labelFontSize=10,
    )
    .interactive()
)

# Output: pad (never crop) the rendered PNG up to the exact target canvas
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET[0] or img.height > TARGET[1]:
    # long column names or many rows add padding: scale the whole render down instead of cropping it
    fit = min(TARGET[0] / img.width, TARGET[1] / img.height)
    img = img.resize((int(img.width * fit), int(img.height * fit)), Image.LANCZOS)
canvas = Image.new("RGB", TARGET, PAGE_BG)
canvas.paste(img, ((TARGET[0] - img.width) // 2, (TARGET[1] - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
