"""anyplot.ai
line-loss-training: Training Loss Curve
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-14
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

# Imprint palette: all eight positions, one per series in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
EPOCH = "Epoch"  # role: epoch
TRAIN_LOSS = "Training Loss"  # role: train_loss
VAL_LOSS = "Validation Loss"  # role: val_loss
LOSS = "Cross-Entropy Loss"  # y axis title: the loss function used
SPLIT = "Split"  # legend title key for the long table built below

# Data: replace this block with your own table, for example df = pd.read_csv("history.csv")
# (one row per epoch and split: epoch, loss value, and "Training"/"Validation")
np.random.seed(42)
epochs = np.arange(1, 101)

# Training loss: exponential decay with some noise
train_loss = 2.5 * np.exp(-0.04 * epochs) + 0.15 + np.random.normal(0, 0.03, len(epochs))
train_loss = np.clip(train_loss, 0.1, 3.0)

# Validation loss: similar decay but plateaus earlier and shows slight overfitting after epoch 70
val_loss = 2.5 * np.exp(-0.035 * epochs) + 0.25 + np.random.normal(0, 0.04, len(epochs))
val_loss[69:] = val_loss[69:] + 0.002 * (epochs[69:] - 70)
val_loss = np.clip(val_loss, 0.15, 3.0)

df = pd.DataFrame({EPOCH: epochs, TRAIN_LOSS: train_loss, VAL_LOSS: val_loss})

# Plot: reads only df and the constants above
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

long_df = df.melt(id_vars=EPOCH, value_vars=[TRAIN_LOSS, VAL_LOSS], var_name=SPLIT, value_name=LOSS)
splits = long_df[SPLIT].unique()
best = df.loc[df[VAL_LOSS].idxmin()]
best_epoch, best_loss = best[EPOCH], best[VAL_LOSS]

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)

sns.lineplot(
    data=long_df,
    x=EPOCH,
    y=LOSS,
    hue=SPLIT,
    palette=IMPRINT_PALETTE[: len(splits)],
    linewidth=1.8,
    errorbar=None,
    ax=ax,
)

# Mark the epoch of minimum validation loss
ax.axvline(x=best_epoch, color=INK_SOFT, linestyle="--", linewidth=1.2, alpha=0.5)
ax.scatter([best_epoch], [best_loss], s=80, color=IMPRINT_PALETTE[1], zorder=5, edgecolor=INK_SOFT, linewidth=1.2)
ax.annotate(
    f"Optimal: Epoch {best_epoch:.0f}",
    xy=(best_epoch, best_loss),
    xytext=(-40, 60),
    textcoords="offset points",
    ha="right",
    fontsize=9,
    color=INK,
    arrowprops={"arrowstyle": "->", "color": INK_SOFT, "lw": 1.2},
)

# Style
ax.set_xlabel(EPOCH, fontsize=10)
ax.set_ylabel(LOSS, fontsize=10)
ax.set_title("line-loss-training · python · seaborn · anyplot.ai", fontsize=12, color=INK)
ax.tick_params(axis="both", labelsize=8)
ax.set_xlim(df[EPOCH].min(), df[EPOCH].max())
ax.set_ylim(0, long_df[LOSS].max() * 1.08)
sns.despine(ax=ax)
ax.yaxis.grid(True, linewidth=0.6)
ax.xaxis.grid(False)
ax.legend(title=None, fontsize=8, loc="upper right", framealpha=0.95)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
