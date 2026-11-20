"""anyplot.ai
roc-curve: ROC Curve with AUC
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-09
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import auc, roc_curve


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Column constants
MODEL = "Model"  # role: extra
FPR = "False Positive Rate"  # role: fpr
TPR = "True Positive Rate"  # role: tpr
AUC = "AUC"  # role: auc

# Data: replace this block with your own table, for example df = pd.read_csv("roc.csv")
# One row per ROC operating point: model name, FPR, TPR and the model's AUC.
rng = np.random.default_rng(42)
n_samples = 1000
y_true = rng.binomial(1, 0.5, n_samples)
scores = {
    "Random Forest": y_true * rng.beta(5, 2, n_samples) + (1 - y_true) * rng.beta(2, 6, n_samples),
    "Logistic Regression": y_true * rng.beta(4, 2, n_samples) + (1 - y_true) * rng.beta(2, 4, n_samples),
    "Decision Tree": y_true * rng.beta(2.5, 2, n_samples) + (1 - y_true) * rng.beta(2, 2.5, n_samples),
}
frames = []
for name, score in scores.items():
    fpr, tpr, _ = roc_curve(y_true, score)
    frames.append(pd.DataFrame({MODEL: name, FPR: fpr, TPR: tpr, AUC: auc(fpr, tpr)}))
df = pd.concat(frames, ignore_index=True)

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.set_prop_cycle(color=IMPRINT_PALETTE)
for i, (model, rows) in enumerate(df.groupby(MODEL, sort=False)):
    label = f"{model} (AUC = {rows[AUC].iloc[0]:.2f})"
    (line,) = ax.plot(rows[FPR], rows[TPR], linewidth=2.5, label=label)
    if i < 2:
        ax.fill_between(rows[FPR], rows[TPR], alpha=0.12 - 0.04 * i, color=line.get_color())

ax.plot([0, 1], [0, 1], color=INK_SOFT, linewidth=1.8, linestyle="--", label="Random Classifier (AUC = 0.50)")

# Style
ax.set_xlabel(FPR, fontsize=10, color=INK)
ax.set_ylabel(TPR, fontsize=10, color=INK)
ax.set_title("roc-curve · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.set_xlim(-0.02, 1.0)
ax.set_ylim(0.0, 1.02)

for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

ax.grid(True, alpha=0.15, linewidth=0.8, color=INK, axis="y")

leg = ax.legend(loc="lower right", fontsize=8)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
leg.get_frame().set_linewidth(0.8)
plt.setp(leg.get_texts(), color=INK_SOFT)

fig.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
