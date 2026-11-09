""" anyplot.ai
precision-recall: Precision-Recall Curve
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 87/100 | Updated: 2026-11-09
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, precision_recall_curve


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per classifier in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
ISO_F1 = [0.2, 0.4, 0.6, 0.8]  # F1 scores drawn as reference curves

# Columns: set these to your table's column names
IS_SPAM = "Spam (1 = yes)"  # role: y_true
SCORES = ["Spam filter score"]  # role: y_scores

# Data: replace this block with your own table, for example df = pd.read_csv("predictions.csv")
# 500 e-mails, 20 % spam; the filter scores spam higher than regular mail
np.random.seed(42)
df = pd.DataFrame(
    {
        IS_SPAM: np.concatenate([np.ones(100, dtype=int), np.zeros(400, dtype=int)]),
        SCORES[0]: np.concatenate([np.random.beta(5, 2, 100), np.random.beta(2, 5, 400)]),
    }
)

# Plot: reads only df and the constants above
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG, layout="constrained")
ax.set_facecolor(PAGE_BG)

# Iso-F1 reference curves, each starting where it meets precision 1
for f1 in ISO_F1:
    recall_iso = np.linspace(f1 / (2 - f1), 1, 200)
    ax.plot(
        recall_iso,
        f1 * recall_iso / (2 * recall_iso - f1),
        color=INK_MUTED,
        linewidth=0.8,
        linestyle=(0, (1, 2)),
        alpha=0.7,
        zorder=1,
    )
    ax.annotate(
        f"F1 = {f1:.1f}",
        xy=(f1 / (2 - f1), 1),
        xytext=(0, 4),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=7,
        color=INK_MUTED,
    )

actual = df[IS_SPAM].dropna()
positive = actual.max()  # the larger label value is the positive class (1 of 0 and 1)
positive_share = (actual == positive).mean()
ax.axhline(
    positive_share,
    color=INK,
    linewidth=1.2,
    linestyle=(0, (5, 3)),
    label=f"Random classifier (precision = {positive_share:.0%})",
    zorder=2,
)

for i, column in enumerate(SCORES):
    rows = df[[IS_SPAM, column]].dropna()
    truth = rows[IS_SPAM] == positive
    scores = rows[column].astype(float)
    precision, recall, _ = precision_recall_curve(truth, scores)
    ap = average_precision_score(truth, scores)
    ax.fill_between(recall, precision, step="post", color=IMPRINT_PALETTE[i], alpha=0.12, linewidth=0, zorder=2)
    ax.step(
        recall,
        precision,
        where="post",
        color=IMPRINT_PALETTE[i],
        linewidth=2.5,
        label=f"{column} (AP = {ap:.3f})",
        zorder=3,
    )

# Style
ax.set_title("precision-recall · python · matplotlib · anyplot.ai", fontsize=12, fontweight="bold", color=INK)
ax.set_xlabel("Recall (true positive rate)", fontsize=10, color=INK)
ax.set_ylabel("Precision (positive predictive value)", fontsize=10, color=INK)
ax.set_xlim(0, 1.01)  # room for the curve's last step at recall 1
ax.set_ylim(0, 1.08)  # room for the iso-F1 labels above precision 1
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.grid(True, alpha=0.15, color=INK, linewidth=0.6)
ax.set_axisbelow(True)
for side in ("top", "right"):
    ax.spines[side].set_visible(False)
for side in ("left", "bottom"):
    ax.spines[side].set_color(INK_SOFT)
handles, labels = ax.get_legend_handles_labels()
legend = ax.legend(handles[1:] + handles[:1], labels[1:] + labels[:1], fontsize=8, loc="lower left", frameon=True)
legend.get_frame().set_facecolor(ELEVATED_BG)
legend.get_frame().set_edgecolor(INK_SOFT)
legend.get_frame().set_linewidth(0.6)
plt.setp(legend.get_texts(), color=INK_SOFT)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
