"""anyplot.ai
learning-curve-basic: Model Learning Curve
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-05-10
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, first series always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
TRAIN_SIZE = "Training set size (samples)"  # role: train_sizes
TRAIN_SCORE = "Training"  # role: train_scores
VALIDATION_SCORE = "Validation"  # role: validation_scores
FOLD = "CV fold"  # role: extra
SPLIT = "Score type"
SCORE = "RMSE (thousand USD)"

# Data: replace this block with your own table, for example df = pd.read_csv("learning_curve.csv")
# A house-price regressor evaluated with 5-fold cross-validation. The error is an RMSE, so lower is better:
# the validation error is still falling at the largest size, the training error creeps up as data grows.
rng = np.random.default_rng(7)
sizes = np.array([100, 200, 300, 500, 700, 1000, 1400, 1800, 2400, 3000])
n_folds = 5
train_rmse = 14 + 16 * (1 - np.exp(-sizes / 900))
val_rmse = 30 + 105 * (sizes / 100) ** -0.38
df = pd.DataFrame(
    {
        TRAIN_SIZE: np.tile(sizes, n_folds),
        FOLD: np.repeat(np.arange(1, n_folds + 1), len(sizes)),
        TRAIN_SCORE: (train_rmse * (1 + rng.normal(0, 0.04, (n_folds, len(sizes))))).ravel(),
        VALIDATION_SCORE: (val_rmse * (1 + rng.normal(0, 0.06, (n_folds, len(sizes))))).ravel(),
    }
)

# Plot: reads only df and the constants above
long = df.melt(id_vars=[TRAIN_SIZE, FOLD], value_vars=[TRAIN_SCORE, VALIDATION_SCORE], var_name=SPLIT, value_name=SCORE)
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
        "grid.alpha": 0.15,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

n_splits = long[SPLIT].nunique()
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)

# Mean across folds at every size, band = ±1 standard deviation across folds
sns.lineplot(
    data=long,
    x=TRAIN_SIZE,
    y=SCORE,
    hue=SPLIT,
    style=SPLIT,
    markers=True,
    dashes=False,
    estimator="mean",
    errorbar="sd",
    err_kws={"alpha": 0.2, "linewidth": 0},
    palette=IMPRINT_PALETTE[:n_splits],
    linewidth=2.2,
    markersize=7,
    ax=ax,
)

# Style
ax.set_title("learning-curve-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(TRAIN_SIZE, fontsize=10, color=INK)
ax.set_ylabel(SCORE, fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.set_ylim(0, long[SCORE].max() * 1.08)
ax.yaxis.grid(True, linewidth=0.8)
ax.legend(title=SPLIT, fontsize=8, title_fontsize=8, loc="upper right", framealpha=0.95)
sns.despine(ax=ax)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
