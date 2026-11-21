"""anyplot.ai
andrews-curves: Andrews Curves for Multivariate Data
Library: altair 6.1.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-15
"""

import os
import sys


# Remove script directory from sys.path to avoid importing local altair.py
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir in sys.path:
    sys.path.remove(script_dir)

import altair as alt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import Image  # noqa: E402
from sklearn.datasets import load_iris  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
N_POINTS = 200  # evaluation points of t over one full period, dense enough for smooth curves

# Columns: set these to your table's column names
VARIABLES = ["Sepal length (cm)", "Sepal width (cm)", "Petal length (cm)", "Petal width (cm)"]  # role: variable_
SPECIES = "Species"  # role: category

# Data: replace this block with your own table, for example df = pd.read_csv("measurements.csv")
iris = load_iris()
df = pd.DataFrame(iris.data, columns=VARIABLES)
df[SPECIES] = pd.Categorical.from_codes(iris.target, ["Setosa", "Versicolor", "Virginica"]).astype(str)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
OBSERVATION = "Observation"
VALUE = "Andrews curve value"
T = "t (radians)"

# Normalize variables to similar scales so no single variable dominates
values = df[VARIABLES].to_numpy(dtype=float)
scaled = (values - np.nanmean(values, axis=0)) / np.nanstd(values, axis=0)

# Andrews transformation: f(t) = x1/sqrt(2) + x2 sin(t) + x3 cos(t) + x4 sin(2t) + x5 cos(2t) + ...
t = np.linspace(-np.pi, np.pi, N_POINTS)
curves = np.tile(scaled[:, [0]] / np.sqrt(2), (1, N_POINTS))
for i in range(1, scaled.shape[1]):
    freq = (i + 1) // 2
    basis = np.sin(freq * t) if i % 2 == 1 else np.cos(freq * t)
    curves = curves + scaled[:, [i]] * basis

curve_df = pd.DataFrame(
    {
        T: np.tile(t, len(df)),
        VALUE: curves.ravel(),
        OBSERVATION: np.repeat(np.arange(len(df)), N_POINTS),
        SPECIES: np.repeat(df[SPECIES].to_numpy(), N_POINTS),
    }
)
groups = list(dict.fromkeys(df[SPECIES]))

title = "andrews-curves · python · altair · anyplot.ai"
chart = (
    alt.Chart(curve_df)
    .mark_line(opacity=0.4, strokeWidth=1.2)
    .encode(
        x=alt.X(T.translate(ESCAPE), type="quantitative", title=T, scale=alt.Scale(domain=[-np.pi, np.pi], nice=False)),
        y=alt.Y(VALUE.translate(ESCAPE), type="quantitative", title=VALUE),
        color=alt.Color(
            SPECIES.translate(ESCAPE),
            type="nominal",
            title=SPECIES,
            sort=None,
            scale=alt.Scale(domain=groups, range=IMPRINT_PALETTE),
            legend=alt.Legend(symbolOpacity=1, symbolStrokeWidth=3),
        ),
        detail=alt.Detail(OBSERVATION, type="nominal"),
    )
    .properties(
        width=620,
        height=320,
        padding={"left": 0, "right": 0, "top": 0, "bottom": 0},
        background=PAGE_BG,
        title=alt.Title(title, fontSize=16),
    )
    .configure_view(fill=PAGE_BG, stroke=None, continuousWidth=620, continuousHeight=320)
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
    .configure_title(color=INK)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=10,
        titleFontSize=10,
        padding=6,
    )
)

# Save as PNG and HTML
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad (never crop) the PNG to the canonical 3200 x 1800 canvas
TW, TH = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TW or h > TH:
    raise SystemExit(f"altair vl-convert produced {w}x{h}, exceeds target {TW}x{TH}. Shrink width/height.")
if w < TW or h < TH:
    canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    canvas.paste(img, ((TW - w) // 2, (TH - h) // 2))
    canvas.save(f"plot-{THEME}.png")
