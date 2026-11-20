""" anyplot.ai
precision-recall: Precision-Recall Curve
Library: altair 6.3.0 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-20
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image
from sklearn.metrics import average_precision_score, precision_recall_curve


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
LABEL = "Actual class"  # role: y_true
SCORES = ["Logistic Regression", "Random Forest"]  # role: y_scores

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
rng = np.random.default_rng(42)
n_samples = 2000
y_true = (rng.random(n_samples) < 0.30).astype(int)
lr_score = np.clip(0.30 + 0.22 * y_true + rng.normal(0, 0.20, n_samples), 0, 1)
rf_score = np.clip(0.28 + 0.34 * y_true + rng.normal(0, 0.20, n_samples), 0, 1)
df = pd.DataFrame({LABEL: y_true, SCORES[0]: lr_score, SCORES[1]: rf_score})

# Plot: reads only df and the constants above
RECALL = "Recall (true positive rate)"
PRECISION = "Precision (positive predictive value)"
MODEL = "Model"
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})

# Positive class = anything above the lowest label value; rows with a missing label or score are skipped
positive = (df[LABEL] > df[LABEL].min()).astype(int).where(df[LABEL].notna())
positive_rate = positive.mean()
baseline_name = f"Random classifier (baseline = {positive_rate:.2f})"

curves = []
names = []
for model in SCORES:
    valid = positive.notna() & df[model].notna()
    precision, recall, _ = precision_recall_curve(positive[valid], df[model][valid])
    ap = average_precision_score(positive[valid], df[model][valid])
    name = f"{model} (AP = {ap:.3f})"
    names.append(name)
    curves.append(pd.DataFrame({RECALL: recall, PRECISION: precision, MODEL: name}))
curves.append(pd.DataFrame({RECALL: [0.0, 1.0], PRECISION: [positive_rate] * 2, MODEL: baseline_name}))
curve_df = pd.concat(curves, ignore_index=True)

legend_names = [*names, baseline_name]
dashes = [[1, 0]] * len(names) + [[8, 5]]
colors = IMPRINT_PALETTE[: len(names)] + [IMPRINT_PALETTE[2]]

title = "precision-recall · python · altair · anyplot.ai"
title_size = round(16 * min(1.0, 67 / len(title)))

chart = (
    alt.Chart(curve_df)
    .mark_line(strokeWidth=3, interpolate="step-after")
    .encode(
        x=alt.X(
            RECALL.translate(ESCAPE), type="quantitative", title=RECALL, scale=alt.Scale(domain=[0, 1], nice=False)
        ),
        y=alt.Y(
            PRECISION.translate(ESCAPE),
            type="quantitative",
            title=PRECISION,
            scale=alt.Scale(domain=[0, 1.02], nice=False),
            axis=alt.Axis(values=[0, 0.2, 0.4, 0.6, 0.8, 1.0]),
        ),
        color=alt.Color(
            MODEL,
            type="nominal",
            title=None,
            sort=None,
            scale=alt.Scale(domain=legend_names, range=colors),
            legend=alt.Legend(
                orient="bottom-left",
                direction="vertical",
                offset=8,
                labelLimit=400,
                symbolStrokeWidth=3,
                symbolType="stroke",
                symbolSize=500,
            ),
        ),
        strokeDash=alt.StrokeDash(MODEL, type="nominal", sort=None, scale=alt.Scale(domain=legend_names, range=dashes)),
    )
    .properties(
        width=620,
        height=320,
        background=PAGE_BG,
        title=alt.Title(title, fontSize=title_size, anchor="middle", color=INK),
    )
    .configure_axis(
        labelFontSize=10,
        titleFontSize=12,
        labelColor=INK_SOFT,
        titleColor=INK,
        gridColor=INK,
        gridOpacity=0.10,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, strokeWidth=0)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        labelFontSize=10,
        padding=6,
        symbolStrokeWidth=3,
    )
)

# Output
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad (never crop) to the canonical landscape canvas
TARGET_W, TARGET_H = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET_W or img.height > TARGET_H:
    raise SystemExit(f"altair produced {img.width}x{img.height}, exceeds {TARGET_W}x{TARGET_H}; shrink width/height")
if img.size != (TARGET_W, TARGET_H):
    canvas = Image.new("RGB", (TARGET_W, TARGET_H), PAGE_BG)
    canvas.paste(img, ((TARGET_W - img.width) // 2, (TARGET_H - img.height) // 2))
    canvas.save(f"plot-{THEME}.png")
