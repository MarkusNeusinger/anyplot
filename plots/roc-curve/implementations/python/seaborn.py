"""anyplot.ai
roc-curve: ROC Curve with AUC
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-05-09
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import auc, roc_curve


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per curve in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
MARKER = "Diagnostic marker"  # role: extra
FPR = "False positive rate (FPR)"  # role: fpr
TPR = "True positive rate (TPR)"  # role: tpr
AUC = "AUC"  # role: auc

# Data: replace this block with your own table, for example df = pd.read_csv("roc_points.csv")
rng = np.random.default_rng(42)
n_patients = 400
had_attack = (rng.random(n_patients) < 0.4).astype(int)
separation = {"Troponin I": 1.9, "CK-MB": 1.0, "Myoglobin": 0.45}  # how far attack patients sit above the rest
rows = []
for marker, shift in separation.items():
    score = rng.normal(0, 1, n_patients) + shift * had_attack
    fpr, tpr, _ = roc_curve(had_attack, score)
    rows.append(pd.DataFrame({MARKER: marker, FPR: fpr, TPR: tpr, AUC: auc(fpr, tpr)}))
df = pd.concat(rows, ignore_index=True)

# Plot: reads only df and the constants above
df["curve"] = df[MARKER] + " (AUC = " + df[AUC].round(3).astype(str) + ")"
n_curves = df[MARKER].nunique()

sns.set_theme(
    style="whitegrid",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.1,
        "grid.linewidth": 0.8,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_axisbelow(True)

sns.lineplot(
    data=df,
    x=FPR,
    y=TPR,
    hue="curve",
    palette=IMPRINT_PALETTE[:n_curves],
    estimator=None,
    sort=False,
    drawstyle="steps-post",
    linewidth=2.2,
    ax=ax,
)

# Random-classifier reference, dashed so it reads apart from the model curves
ax.plot([0, 1], [0, 1], linestyle="--", linewidth=1.6, color=INK_SOFT, label="Random guess (AUC = 0.500)")

ax.set_title("roc-curve · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(FPR, fontsize=10)
ax.set_ylabel(TPR, fontsize=10)
ax.tick_params(axis="both", labelsize=8)
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.set_aspect("equal", adjustable="box")
sns.despine(ax=ax)
ax.legend(loc="lower right", fontsize=8, title=MARKER, title_fontsize=9, fancybox=False)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
