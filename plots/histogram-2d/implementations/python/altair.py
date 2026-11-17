"""anyplot.ai
histogram-2d: 2D Histogram Heatmap
Library: altair 6.1.0 | Python 3.13.13
Quality: 82/100 | Updated: 2026-05-08
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: sequential density ramp runs from position 1 to position 3
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
IMPRINT_SEQ = [IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]]

# Constants
MAX_BINS = 24  # bin count per axis: fine enough for the tilt, coarse enough for a density gradient

# Columns: set these to your table's column names
VARIABLE_X = "Variable X"  # role: x
VARIABLE_Y = "Variable Y"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("points.csv")
np.random.seed(42)
n_points = 6000
sample = np.random.multivariate_normal([0, 0], [[1, 0.7], [0.7, 1]], n_points)
df = pd.DataFrame({VARIABLE_X: sample[:, 0], VARIABLE_Y: sample[:, 1]})

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
x_field = VARIABLE_X.translate(ESCAPE)
y_field = VARIABLE_Y.translate(ESCAPE)

chart = (
    alt.Chart(df)
    .mark_rect()
    .encode(
        x=alt.X(x_field, type="quantitative", bin=alt.Bin(maxbins=MAX_BINS), title=VARIABLE_X),
        y=alt.Y(y_field, type="quantitative", bin=alt.Bin(maxbins=MAX_BINS), title=VARIABLE_Y),
        color=alt.Color(
            "count()",
            type="quantitative",
            scale=alt.Scale(range=IMPRINT_SEQ),
            title="Count",
            legend=alt.Legend(
                titleFontSize=12, labelFontSize=11, gradientLength=180, gradientThickness=14, padding=8, offset=12
            ),
        ),
        tooltip=[
            alt.Tooltip(x_field, type="quantitative", bin=alt.Bin(maxbins=MAX_BINS), title=VARIABLE_X),
            alt.Tooltip(y_field, type="quantitative", bin=alt.Bin(maxbins=MAX_BINS), title=VARIABLE_Y),
            alt.Tooltip("count()", type="quantitative", title="Count"),
        ],
    )
    .properties(
        width=620,
        height=320,
        title=alt.Title("histogram-2d · python · altair · anyplot.ai", fontSize=16, anchor="middle"),
        background=PAGE_BG,
    )
    .configure_axis(
        labelFontSize=11,
        titleFontSize=13,
        tickSize=0,
        domainColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        grid=False,
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, strokeWidth=1)
    .configure_title(color=INK)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save: PNG padded (never cropped) to the 3200 x 1800 canvas, plus interactive HTML
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

TARGET_W, TARGET_H = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET_W or img.height > TARGET_H:
    raise SystemExit(f"altair produced {img.width}x{img.height}, exceeds {TARGET_W}x{TARGET_H}; shrink width/height")
canvas = Image.new("RGB", (TARGET_W, TARGET_H), PAGE_BG)
canvas.paste(img, ((TARGET_W - img.width) // 2, (TARGET_H - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
