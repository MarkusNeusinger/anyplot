""" anyplot.ai
roc-curve: ROC Curve with AUC
Library: altair 6.1.0 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-09
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


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito palette
BRAND = "#009E73"  # Position 1
SECONDARY = "#C475FD"  # Position 2
NEUTRAL = INK_MUTED  # Diagonal reference line

# Data - Generate synthetic classification scores and compute ROC curve
np.random.seed(42)
n_samples = 500
n_thresholds = 200

# Simulate two models with different performance levels
y_true = np.concatenate([np.zeros(n_samples // 2), np.ones(n_samples // 2)])
scores_model1 = np.where(y_true == 1, np.random.beta(5, 2, n_samples), np.random.beta(2, 5, n_samples))
scores_model2 = np.where(y_true == 1, np.random.beta(3, 2, n_samples), np.random.beta(2, 3, n_samples))

# Compute ROC curve for Model 1
thresholds = np.linspace(0, 1, n_thresholds)
tpr1_list, fpr1_list = [], []
for thresh in thresholds:
    y_pred = (scores_model1 >= thresh).astype(int)
    tp = np.sum((y_pred == 1) & (y_true == 1))
    fp = np.sum((y_pred == 1) & (y_true == 0))
    fn = np.sum((y_pred == 0) & (y_true == 1))
    tn = np.sum((y_pred == 0) & (y_true == 0))
    tpr1_list.append(tp / (tp + fn) if (tp + fn) > 0 else 0)
    fpr1_list.append(fp / (fp + tn) if (fp + tn) > 0 else 0)
fpr1 = np.array(fpr1_list)
tpr1 = np.array(tpr1_list)

# Compute ROC curve for Model 2
tpr2_list, fpr2_list = [], []
for thresh in thresholds:
    y_pred = (scores_model2 >= thresh).astype(int)
    tp = np.sum((y_pred == 1) & (y_true == 1))
    fp = np.sum((y_pred == 1) & (y_true == 0))
    fn = np.sum((y_pred == 0) & (y_true == 1))
    tn = np.sum((y_pred == 0) & (y_true == 0))
    tpr2_list.append(tp / (tp + fn) if (tp + fn) > 0 else 0)
    fpr2_list.append(fp / (fp + tn) if (fp + tn) > 0 else 0)
fpr2 = np.array(fpr2_list)
tpr2 = np.array(tpr2_list)

# Compute AUC using trapezoidal rule
auc1 = -np.trapezoid(tpr1, fpr1)
auc2 = -np.trapezoid(tpr2, fpr2)

# Create labels for legend
label1 = f"Strong Model (AUC = {auc1:.2f})"
label2 = f"Weak Model (AUC = {auc2:.2f})"
label_random = "Random (AUC = 0.50)"

# Create DataFrames for Altair
df_model1 = pd.DataFrame({"fpr": fpr1, "tpr": tpr1, "Model": label1})
df_model2 = pd.DataFrame({"fpr": fpr2, "tpr": tpr2, "Model": label2})
df_roc = pd.concat([df_model1, df_model2], ignore_index=True)
df_diagonal = pd.DataFrame({"fpr": [0, 1], "tpr": [0, 1], "Model": label_random})

# ROC curves with interactivity
roc_lines = (
    alt.Chart(df_roc)
    .mark_line(strokeWidth=4)
    .encode(
        x=alt.X("fpr:Q", title="False Positive Rate", scale=alt.Scale(domain=[0, 1])),
        y=alt.Y("tpr:Q", title="True Positive Rate", scale=alt.Scale(domain=[0, 1])),
        color=alt.Color("Model:N", scale=alt.Scale(domain=[label1, label2], range=[BRAND, SECONDARY])),
        tooltip=["fpr:Q", "tpr:Q", "Model:N"],
    )
)

# Diagonal reference line
diagonal_line = (
    alt.Chart(df_diagonal)
    .mark_line(strokeWidth=3, strokeDash=[8, 6])
    .encode(x="fpr:Q", y="tpr:Q", color=alt.value(NEUTRAL), tooltip=alt.value(None))
)

# Combine and style
chart = (
    (roc_lines + diagonal_line)
    .properties(
        width=1400, height=1400, background=PAGE_BG, title=alt.Title("roc-curve · altair · anyplot.ai", fontSize=28)
    )
    .configure_title(color=INK, anchor="middle", fontWeight="normal")
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=18,
        titleFontSize=22,
        titlePadding=15,
        labelPadding=10,
    )
    .configure_legend(
        fillColor="#FFFDF6" if THEME == "light" else "#242420",
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        titleFontSize=18,
        labelFontSize=16,
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
    .interactive()
)

# Save outputs
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
