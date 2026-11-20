"""anyplot.ai
calibration-curve: Calibration Curve
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-10
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

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
N_BINS = 10  # equal-width probability bins, as the spec asks

Y_TRUE = "Actual outcome (0 or 1)"  # role: y_true
Y_PROBS = ["Predicted probability"]  # role: y_prob

# Data: replace this block with your own table, for example df = pd.read_csv("predictions.csv")
rng = np.random.default_rng(42)
n_samples = 2000
# A slightly overconfident classifier: scores follow the label, plus noise
labels = rng.binomial(1, 0.4, n_samples)
scores = np.clip(labels * 0.6 + (1 - labels) * 0.3 + rng.normal(0, 0.15, n_samples), 0.01, 0.99)
df = pd.DataFrame({Y_TRUE: labels, Y_PROBS[0]: scores})

# Plot
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
MEAN_PRED = "Mean predicted probability"
FRAC_POS = "Fraction of positives"
COUNT = "Samples"

Y_PROB = Y_PROBS[0]  # one classifier is drawn; further columns would add curves

# Calibration points: mean prediction vs. observed positive rate per equal-width bin
valid = df.dropna(subset=[Y_PROB, Y_TRUE])
top = max(1.0, valid[Y_PROB].max())  # probabilities stay in 0-1; wider only if the data is
bin_idx = np.minimum((valid[Y_PROB] / top * N_BINS).astype(int), N_BINS - 1)
calib = valid.groupby(bin_idx).agg({Y_PROB: "mean", Y_TRUE: "mean"}).reset_index(drop=True)
calib.columns = [MEAN_PRED, FRAC_POS]
brier = ((valid[Y_PROB] - valid[Y_TRUE]) ** 2).mean()

# Histogram of predicted probabilities (twice as many bins, same x scale)
counts, edges = np.histogram(valid[Y_PROB], bins=2 * N_BINS, range=(0, top))
hist = pd.DataFrame({"start": edges[:-1], "end": edges[1:], COUNT: counts})

prob_scale = alt.Scale(domain=[0, 1], nice=False)
x_scale = alt.Scale(domain=[0, top], nice=False)
diagonal = pd.DataFrame({MEAN_PRED: [0, top], FRAC_POS: [0, 1]})

x_calib = alt.X(MEAN_PRED.translate(ESCAPE), type="quantitative", title=MEAN_PRED, scale=x_scale)
y_calib = alt.Y(FRAC_POS.translate(ESCAPE), type="quantitative", title=FRAC_POS, scale=prob_scale)

perfect_line = (
    alt.Chart(diagonal)
    .mark_line(color=IMPRINT_PALETTE[1], strokeWidth=2, strokeDash=[6, 4], clip=True)
    .encode(x=x_calib, y=y_calib)
)
curve = alt.Chart(calib).mark_line(color=IMPRINT_PALETTE[0], strokeWidth=3, clip=True).encode(x=x_calib, y=y_calib)
points = (
    alt.Chart(calib)
    .mark_point(color=IMPRINT_PALETTE[0], size=110, filled=True, opacity=1, clip=True)
    .encode(
        x=x_calib,
        y=y_calib,
        tooltip=[
            alt.Tooltip(MEAN_PRED.translate(ESCAPE), format=".3f"),
            alt.Tooltip(FRAC_POS.translate(ESCAPE), format=".3f"),
        ],
    )
)

title = "calibration-curve · python · altair · anyplot.ai"
calibration_panel = alt.layer(perfect_line, curve, points).properties(
    width=620,
    height=215,
    title=alt.Title(
        title,
        subtitle=f"Classifier A · Brier score {brier:.3f} · dashed line = perfect calibration",
        fontSize=17,
        subtitleFontSize=12,
        subtitleColor=INK_SOFT,
    ),
)

histogram_panel = (
    alt.Chart(hist)
    .mark_bar(color=IMPRINT_PALETTE[0], opacity=0.75, stroke=PAGE_BG, strokeWidth=0.5)
    .encode(
        x=alt.X("start:Q", title=Y_PROB, scale=x_scale),
        x2="end:Q",
        y2=alt.Y2(datum=0),
        y=alt.Y(COUNT.translate(ESCAPE), type="quantitative", title=COUNT),
    )
    .properties(width=620, height=60)
)

chart = (
    alt.vconcat(calibration_panel, histogram_panel, spacing=8)
    .properties(background=PAGE_BG, padding={"left": 5, "right": 10, "top": 5, "bottom": 5})
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_axis(
        labelFontSize=11,
        titleFontSize=13,
        labelColor=INK_SOFT,
        titleColor=INK,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.15,
    )
    .configure_axisX(grid=False)
    .configure_title(color=INK)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad (never crop) to the exact canvas
TW, TH = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TW or h > TH:
    raise SystemExit(f"altair vl-convert produced {w}×{h}, exceeds target {TW}×{TH}. Shrink width/height.")
if w < TW or h < TH:
    canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    canvas.paste(img, ((TW - w) // 2, (TH - h) // 2))
    canvas.save(f"plot-{THEME}.png")
