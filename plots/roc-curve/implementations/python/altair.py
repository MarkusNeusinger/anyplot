""" anyplot.ai
roc-curve: ROC Curve with AUC
Library: altair 6.3.0 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-21
"""

import os
import sys


current_dir = sys.path[0] if sys.path and sys.path[0] else "."
if current_dir in sys.path:
    sys.path.remove(current_dir)
sys.path.insert(0, "/dev/null")

import altair as alt  # noqa: E402


sys.path = [p for p in sys.path if p != "/dev/null"]
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import Image  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
N_THRESHOLDS = 200  # score thresholds swept for each curve

# Columns: set these to your table's column names
FPR = "False positive rate"  # role: fpr
TPR = "True positive rate"  # role: tpr
AUC = "AUC"  # role: auc
MODEL = "Model"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("roc_points.csv")
np.random.seed(42)
n_samples = 500
y_true = np.concatenate([np.zeros(n_samples // 2), np.ones(n_samples // 2)])
scores = {
    "Strong Model": np.where(y_true == 1, np.random.beta(5, 2, n_samples), np.random.beta(2, 5, n_samples)),
    "Weak Model": np.where(y_true == 1, np.random.beta(3, 2, n_samples), np.random.beta(2, 3, n_samples)),
}
frames = []
for name, score in scores.items():
    predicted = score[None, :] >= np.linspace(0, 1, N_THRESHOLDS)[:, None]
    positives = y_true == 1
    fpr = (predicted & ~positives).sum(axis=1) / (~positives).sum()
    tpr = (predicted & positives).sum(axis=1) / positives.sum()
    # Trapezoidal AUC; thresholds ascend, so FPR descends along the curve
    frames.append(pd.DataFrame({FPR: fpr, TPR: tpr, AUC: -np.trapezoid(tpr, fpr), MODEL: name}))
df = pd.concat(frames, ignore_index=True)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
models = list(df[MODEL].unique())

labels = {name: f"{name} (AUC = {df.loc[df[MODEL] == name, AUC].iloc[0]:.2f})" for name in models}
label_random = "Random (AUC = 0.50)"
df_plot = df.copy()
df_plot[MODEL] = df[MODEL].map(labels)
df_diagonal = pd.DataFrame({FPR: [0, 1], TPR: [0, 1], MODEL: label_random})
df_plot = pd.concat([df_plot, df_diagonal], ignore_index=True)

domain = [*labels.values(), label_random]
colors = [*IMPRINT_PALETTE[: len(models)], INK_MUTED]
dashes = [*[[1, 0]] * len(models), [8, 6]]

chart = (
    alt.Chart(df_plot)
    .mark_line(strokeWidth=4, strokeJoin="round")
    .encode(
        x=alt.X(FPR.translate(ESCAPE), type="quantitative", title=FPR, scale=alt.Scale(domain=[0, 1])),
        y=alt.Y(TPR.translate(ESCAPE), type="quantitative", title=TPR, scale=alt.Scale(domain=[0, 1])),
        color=alt.Color(
            MODEL.translate(ESCAPE), type="nominal", title=None, sort=None, scale=alt.Scale(domain=domain, range=colors)
        ),
        strokeDash=alt.StrokeDash(
            MODEL.translate(ESCAPE), type="nominal", title=None, sort=None, scale=alt.Scale(domain=domain, range=dashes)
        ),
        tooltip=[
            alt.Tooltip(FPR.translate(ESCAPE), type="quantitative", title=FPR, format=".3f"),
            alt.Tooltip(TPR.translate(ESCAPE), type="quantitative", title=TPR, format=".3f"),
            alt.Tooltip(MODEL.translate(ESCAPE), type="nominal", title=MODEL),
        ],
    )
    .properties(
        width=470,
        height=470,
        background=PAGE_BG,
        title=alt.Title("roc-curve · python · altair · anyplot.ai", fontSize=18),
    )
    .configure_title(color=INK, anchor="middle", fontWeight="normal")
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=12,
        titleFontSize=14,
        titlePadding=10,
        labelPadding=6,
    )
    .configure_legend(
        orient="bottom-right",
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        labelFontSize=12,
        symbolStrokeWidth=4,
        symbolSize=500,
        padding=8,
        offset=12,
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
    .interactive()
)

# Save outputs
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad (never crop) to the square target canvas
TW, TH = 2400, 2400
img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TW or h > TH:
    raise SystemExit(f"altair vl-convert produced {w}x{h}, exceeds target {TW}x{TH}; shrink width/height")
if (w, h) != (TW, TH):
    canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    canvas.paste(img, ((TW - w) // 2, (TH - h) // 2))
    canvas.save(f"plot-{THEME}.png")
