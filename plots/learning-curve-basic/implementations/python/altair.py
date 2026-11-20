"""anyplot.ai
learning-curve-basic: Model Learning Curve
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-10
"""

import os
import sys


saved_path = sys.path[:]
sys.path = [p for p in sys.path if p not in ("", ".", os.getcwd())]

import altair as alt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import Image  # noqa: E402


sys.path = saved_path

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per curve in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
TRAIN_SIZE = "Training set size (samples)"  # role: train_sizes
CURVE = "Curve"  # role: extra
MEAN_SCORE = "Accuracy (mean of 5 folds)"  # role: validation_scores
STD_SCORE = "Std across folds"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("learning_curve.csv")
# One row per curve and training size: mean and standard deviation of the fold scores.
np.random.seed(42)
train_sizes = np.linspace(100, 1000, 10).astype(int)
n_folds = 5

train_scores = np.zeros((n_folds, len(train_sizes)))
val_scores = np.zeros((n_folds, len(train_sizes)))
for i, size in enumerate(train_sizes):
    base_train = 0.98 - 0.02 * (size / 1000)
    train_scores[:, i] = np.clip(base_train + np.random.normal(0, 0.01, n_folds), 0.85, 1.0)
for i, size in enumerate(train_sizes):
    base_val = 0.70 + 0.18 * (1 - np.exp(-size / 400))
    val_scores[:, i] = np.clip(base_val + np.random.normal(0, 0.025 * np.exp(-size / 500), n_folds), 0.6, 0.95)

df = pd.DataFrame(
    {
        TRAIN_SIZE: np.tile(train_sizes, 2),
        CURVE: ["Training"] * len(train_sizes) + ["Validation"] * len(train_sizes),
        MEAN_SCORE: np.concatenate([train_scores.mean(axis=0), val_scores.mean(axis=0)]),
        STD_SCORE: np.concatenate([train_scores.std(axis=0), val_scores.std(axis=0)]),
    }
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
LOWER, UPPER = "lower", "upper"
plot_df = df.copy()
plot_df[LOWER] = df[MEAN_SCORE] - df[STD_SCORE]
plot_df[UPPER] = df[MEAN_SCORE] + df[STD_SCORE]

x_field = TRAIN_SIZE.translate(ESCAPE)
curves = list(plot_df[CURVE].unique())
color_scale = alt.Scale(domain=curves, range=IMPRINT_PALETTE)
y_scale = alt.Scale(
    domain=[float(np.floor(plot_df[LOWER].min() * 20) / 20), float(np.ceil(plot_df[UPPER].max() * 20) / 20)]
)
x_enc = alt.X(
    x_field, type="quantitative", title=TRAIN_SIZE, axis=alt.Axis(values=sorted(plot_df[TRAIN_SIZE].unique().tolist()))
)

band = (
    alt.Chart(plot_df)
    .mark_area(opacity=0.2)
    .encode(
        x=x_enc,
        y=alt.Y(LOWER, type="quantitative", scale=y_scale, title=MEAN_SCORE),
        y2=UPPER,
        color=alt.Color(CURVE, type="nominal", scale=color_scale, title=CURVE, sort=None),
    )
)

line = (
    alt.Chart(plot_df)
    .mark_line(strokeWidth=2.5, point=alt.OverlayMarkDef(size=60, filled=True))
    .encode(
        x=x_enc,
        y=alt.Y(MEAN_SCORE.translate(ESCAPE), type="quantitative", scale=y_scale, title=MEAN_SCORE),
        color=alt.Color(CURVE, type="nominal", scale=color_scale, title=CURVE, sort=None),
        tooltip=[
            alt.Tooltip(x_field, type="quantitative", title=TRAIN_SIZE),
            alt.Tooltip(CURVE, type="nominal", title=CURVE),
            alt.Tooltip(MEAN_SCORE.translate(ESCAPE), type="quantitative", format=".3f", title=MEAN_SCORE),
            alt.Tooltip(STD_SCORE, type="quantitative", format=".3f", title=STD_SCORE),
        ],
    )
)

chart = (
    alt.layer(band, line)
    .properties(
        width=620,
        height=320,
        title=alt.Title("learning-curve-basic · python · altair · anyplot.ai", fontSize=16, anchor="middle", color=INK),
        background=PAGE_BG,
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, continuousWidth=620, continuousHeight=320)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.1,
        labelColor=INK_SOFT,
        labelFontSize=10,
        titleColor=INK,
        titleFontSize=12,
    )
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        labelFontSize=10,
        titleColor=INK,
        titleFontSize=10,
        symbolOpacity=1,
        symbolType="stroke",
        padding=6,
        cornerRadius=4,
    )
    .interactive()
)

# Save: pad (never crop) to the 3200 x 1800 target
TW, TH = 3200, 1800
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TW or img.height > TH:
    raise SystemExit(f"altair produced {img.width}x{img.height}, exceeds {TW}x{TH}; shrink width/height")
canvas = Image.new("RGB", (TW, TH), PAGE_BG)
canvas.paste(img, ((TW - img.width) // 2, (TH - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
chart.save(f"plot-{THEME}.html")
