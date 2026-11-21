"""anyplot.ai
line-loss-training: Training Loss Curve
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-14
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per series in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
LOSS_LABEL = "Cross-Entropy Loss"  # the loss function the y axis reports

# Columns: set these to your table's column names
EPOCH = "Epoch"  # role: epoch
TRAIN_LOSS = "Training Loss"  # role: train_loss
VAL_LOSS = "Validation Loss"  # role: val_loss

# Data: replace this block with your own table, for example df = pd.read_csv("history.csv")
np.random.seed(42)
n_epochs = 150
epochs = np.arange(1, n_epochs + 1)

# Training loss: sigmoid saturation, starts near 2.3 and plateaus
train_loss = 2.2 / (1 + np.exp((epochs - 25) / 8)) + 0.12 + np.random.randn(n_epochs) * 0.012

# Validation loss: similar decay, then a drift upward (overfitting) after epoch 65
val_loss = 2.1 / (1 + np.exp((epochs - 30) / 9)) + 0.18 + np.random.randn(n_epochs) * 0.015
overfit_start = 65
n_over = n_epochs - overfit_start
val_loss[overfit_start:] += np.linspace(0, 0.5, n_over) + np.random.randn(n_over) * 0.012

df = pd.DataFrame({EPOCH: epochs, TRAIN_LOSS: train_loss, VAL_LOSS: val_loss})

# Plot: reads only df and the constants above
best = df[VAL_LOSS].idxmin()
best_epoch = df.loc[best, EPOCH]
best_loss = df.loc[best, VAL_LOSS]

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.plot(df[EPOCH], df[TRAIN_LOSS], linewidth=2.5, color=IMPRINT_PALETTE[0], label=TRAIN_LOSS)
ax.plot(df[EPOCH], df[VAL_LOSS], linewidth=2.5, color=IMPRINT_PALETTE[1], label=VAL_LOSS)

# Mark the minimum validation loss (optimal early-stopping epoch)
ax.scatter([best_epoch], [best_loss], s=110, color=IMPRINT_PALETTE[0], zorder=5, edgecolors=PAGE_BG, linewidth=1.2)
ax.annotate(
    f"Min validation loss\nEpoch {best_epoch}: {best_loss:.2f}",
    xy=(best_epoch, best_loss),
    xytext=(40, 90),
    textcoords="offset points",
    fontsize=9,
    color=INK,
    arrowprops={"arrowstyle": "->", "color": INK_SOFT, "lw": 1.2},
    bbox={"boxstyle": "round,pad=0.4", "facecolor": PAGE_BG, "edgecolor": INK_SOFT, "linewidth": 0.8},
)

# Style
ax.set_title("line-loss-training · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(EPOCH, fontsize=10, color=INK)
ax.set_ylabel(LOSS_LABEL, fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.set_xlim(df[EPOCH].min(), df[EPOCH].max())

for side in ("top", "right"):
    ax.spines[side].set_visible(False)
for side in ("left", "bottom"):
    ax.spines[side].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)

leg = ax.legend(fontsize=8, loc="upper right")
leg.get_frame().set_facecolor(PAGE_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
leg.get_frame().set_linewidth(0.8)
plt.setp(leg.get_texts(), color=INK_SOFT)

fig.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
