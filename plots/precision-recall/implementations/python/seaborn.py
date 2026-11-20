"""anyplot.ai
precision-recall: Precision-Recall Curve
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-10
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import average_precision_score, precision_recall_curve


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per model in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Columns: set these to your table's column names
Y_TRUE = "Fraud (1 = fraudulent)"  # role: y_true
SCORES = ["Model A", "Model B", "Model C"]  # role: y_scores

# Data: replace this block with your own table, for example df = pd.read_csv("predictions.csv")
rng = np.random.RandomState(42)
n_samples = 1000
n_positive = 100  # 10% positive class (imbalanced fraud detection)
labels = np.zeros(n_samples, dtype=int)
labels[:n_positive] = 1
rng.shuffle(labels)
is_positive = labels == 1
df = pd.DataFrame(
    {
        Y_TRUE: labels,
        # Good separation, moderate separation, and no separation between the classes
        SCORES[0]: np.where(is_positive, rng.beta(5, 2, n_samples), rng.beta(2, 5, n_samples)),
        SCORES[1]: np.where(is_positive, rng.beta(3, 2, n_samples), rng.beta(2, 3, n_samples)),
        SCORES[2]: np.where(is_positive, rng.beta(2, 2, n_samples), rng.beta(2, 2, n_samples)),
    }
)

# Plot: reads only df and the constants above
labelled = df.dropna(subset=[Y_TRUE])
is_fraud = labelled[Y_TRUE] == labelled[Y_TRUE].max()  # the highest label value is the positive class
baseline = is_fraud.mean()

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)

for i, model in enumerate(SCORES):
    scored = labelled[model].notna()  # a missing score drops that row for this model only
    precision, recall, _ = precision_recall_curve(is_fraud[scored], labelled.loc[scored, model])
    ap = average_precision_score(is_fraud[scored], labelled.loc[scored, model])
    ax.step(recall, precision, where="post", linewidth=2.0, color=IMPRINT_PALETTE[i], label=f"{model} (AP = {ap:.2f})")
    ax.fill_between(recall, precision, step="post", alpha=0.2, color=IMPRINT_PALETTE[i])

# Baseline: random classifier at the positive class ratio
ax.axhline(baseline, linestyle="--", linewidth=1.5, color=INK_SOFT, label=f"Random classifier (P = {baseline:.2f})")

# Style
ax.set_title("precision-recall · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium")
ax.set_xlabel("Recall (sensitivity)", fontsize=10)
ax.set_ylabel("Precision (positive predictive value)", fontsize=10)
ax.tick_params(axis="both", labelsize=8)
ax.set_xlim(0, 1)
ax.set_ylim(0, 1.05)
ax.legend(loc="upper right", fontsize=8, frameon=True, framealpha=0.9)
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8)
sns.despine(ax=ax)

fig.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
