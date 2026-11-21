"""anyplot.ai
contour-decision-boundary: Decision Boundary Classifier Visualization
Library: altair 6.1.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-16
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image
from sklearn.datasets import make_moons
from sklearn.neighbors import KNeighborsClassifier


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per class in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
MESH_SIZE = 150  # grid points per axis for the predicted-region background
MARGIN = 0.5  # padding of the feature plane around the training points

# Columns: set these to your table's column names
X1 = "Feature X1"  # role: X1
X2 = "Feature X2"  # role: X2
CLASS = "Class"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("points.csv")
_features, _labels = make_moons(n_samples=150, noise=0.25, random_state=42)
df = pd.DataFrame(
    {X1: _features[:, 0], X2: _features[:, 1], CLASS: ["Class A" if label == 0 else "Class B" for label in _labels]}
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
STATUS = "Classification"
X1_END, X2_END = "x1_end", "x2_end"
train = df.dropna(subset=[X1, X2, CLASS])
classes = list(train[CLASS].astype(str).unique())
class_colors = alt.Scale(domain=classes, range=IMPRINT_PALETTE[: len(classes)])

clf = KNeighborsClassifier(n_neighbors=5).fit(train[[X1, X2]].to_numpy(), train[CLASS].astype(str))

# Predicted class on a regular mesh covering the feature plane
xx, yy = np.meshgrid(
    np.linspace(train[X1].min() - MARGIN, train[X1].max() + MARGIN, MESH_SIZE),
    np.linspace(train[X2].min() - MARGIN, train[X2].max() + MARGIN, MESH_SIZE),
)
mesh = pd.DataFrame({X1: xx.ravel(), X2: yy.ravel()})
mesh[CLASS] = clf.predict(mesh.to_numpy())
half_x, half_y = (xx[0, 1] - xx[0, 0]) / 2, (yy[1, 0] - yy[0, 0]) / 2
mesh[X1_END], mesh[X2_END] = mesh[X1] + half_x, mesh[X2] + half_y
mesh[X1], mesh[X2] = mesh[X1] - half_x, mesh[X2] - half_y
x_domain = [mesh[X1].min(), mesh[X1_END].max()]
y_domain = [mesh[X2].min(), mesh[X2_END].max()]

# Training points: true class as fill, correct vs misclassified as shape
train = train.assign(
    **{STATUS: np.where(clf.predict(train[[X1, X2]].to_numpy()) == train[CLASS].astype(str), "Correct", "Incorrect")}
)

background = (
    alt.Chart(mesh)
    .mark_rect(opacity=0.4, stroke=None)
    .encode(
        x=alt.X(X1.translate(ESCAPE), type="quantitative", title=X1, scale=alt.Scale(domain=x_domain, nice=False)),
        x2=alt.X2(X1_END),
        y=alt.Y(X2.translate(ESCAPE), type="quantitative", title=X2, scale=alt.Scale(domain=y_domain, nice=False)),
        y2=alt.Y2(X2_END),
        color=alt.Color(
            CLASS.translate(ESCAPE),
            type="nominal",
            title="Decision region",
            scale=class_colors,
            legend=alt.Legend(titleFontSize=12, labelFontSize=11, orient="right"),
        ),
    )
)

points = (
    alt.Chart(train)
    .mark_point(filled=True, size=90, strokeWidth=1.2, stroke=INK_SOFT, opacity=1)
    .encode(
        x=alt.X(X1.translate(ESCAPE), type="quantitative", title=X1, scale=alt.Scale(domain=x_domain, nice=False)),
        y=alt.Y(X2.translate(ESCAPE), type="quantitative", title=X2, scale=alt.Scale(domain=y_domain, nice=False)),
        fill=alt.Color(CLASS.translate(ESCAPE), type="nominal", scale=class_colors, legend=None),
        shape=alt.Shape(
            STATUS,
            type="nominal",
            title="Training point",
            scale=alt.Scale(domain=["Correct", "Incorrect"], range=["circle", "triangle-up"]),
            legend=alt.Legend(titleFontSize=12, labelFontSize=11, orient="right", symbolFillColor=INK_SOFT),
        ),
        tooltip=[
            alt.Tooltip(X1.translate(ESCAPE), type="quantitative", title=X1),
            alt.Tooltip(X2.translate(ESCAPE), type="quantitative", title=X2),
            alt.Tooltip(CLASS.translate(ESCAPE), type="nominal", title=CLASS),
            alt.Tooltip(STATUS, type="nominal"),
        ],
    )
)

chart = (
    alt.layer(background, points)
    .resolve_scale(color="independent", shape="independent")
    .properties(
        width=560,
        height=360,
        background=PAGE_BG,
        title=alt.Title("contour-decision-boundary · python · altair · anyplot.ai", fontSize=16, color=INK),
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=12,
        titleFontSize=14,
    )
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK, padding=8)
)

# Save outputs
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad (never crop) to the exact 3200 x 1800 canvas
TW, TH = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TW or img.height > TH:
    raise SystemExit(f"vl-convert produced {img.width}x{img.height}, exceeds {TW}x{TH}; shrink width/height")
canvas = Image.new("RGB", (TW, TH), PAGE_BG)
canvas.paste(img, ((TW - img.width) // 2, (TH - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
