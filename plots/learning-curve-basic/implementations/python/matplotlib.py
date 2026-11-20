""" anyplot.ai
learning-curve-basic: Model Learning Curve
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-20
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
TRAIN_SIZE = "Training set size (samples)"  # role: train_sizes
TRAIN_ERROR = "Training error (MSE)"  # role: train_scores
VALIDATION_ERROR = "Validation error (MSE)"  # role: validation_scores

# Data: replace this block with your own table, for example df = pd.read_csv("learning_curve.csv")
# Scenario: a high-variance (overfitting) regressor, 5-fold cross-validated mean squared error
rng = np.random.default_rng(7)
sizes = np.array([100, 200, 400, 700, 1000, 1500, 2000, 2500, 3000, 4000])
n_folds = 5
train_mean = 0.02 + 0.04 * (1 - np.exp(-sizes / 900))
validation_mean = 0.30 + 0.55 * np.exp(-sizes / 1100)
df = pd.DataFrame(
    {
        TRAIN_SIZE: np.repeat(sizes, n_folds),
        TRAIN_ERROR: np.repeat(train_mean, n_folds) * (1 + rng.normal(0, 0.12, sizes.size * n_folds)),
        VALIDATION_ERROR: np.repeat(validation_mean, n_folds) * (1 + rng.normal(0, 0.09, sizes.size * n_folds)),
    }
)

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

curves = [(TRAIN_ERROR, "Training error", "o"), (VALIDATION_ERROR, "Validation error", "s")]
for color, (column, label, marker) in zip(IMPRINT_PALETTE, curves, strict=False):
    stats = df.groupby(TRAIN_SIZE)[column].agg(["mean", "std"])
    ax.fill_between(
        stats.index, stats["mean"] - stats["std"], stats["mean"] + stats["std"], color=color, alpha=0.2, lw=0
    )
    ax.plot(stats.index, stats["mean"], marker=marker, color=color, linewidth=2.5, markersize=6, label=label)

ax.set_xlabel(TRAIN_SIZE, fontsize=10, color=INK)
ax.set_ylabel("Mean squared error (5-fold CV)", fontsize=10, color=INK)
ax.set_title("learning-curve-basic · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.set_ylim(0, df[VALIDATION_ERROR].max() * 1.08)
ax.set_xlim(0, df[TRAIN_SIZE].max() * 1.03)

for side in ("top", "right"):
    ax.spines[side].set_visible(False)
for side in ("left", "bottom"):
    ax.spines[side].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8, color=INK)
ax.set_axisbelow(True)

leg = ax.legend(fontsize=8, loc="upper right")
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

fig.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
