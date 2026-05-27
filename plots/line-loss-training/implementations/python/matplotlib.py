""" anyplot.ai
line-loss-training: Training Loss Curve
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-14
"""

import os

import matplotlib.pyplot as plt
import numpy as np


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito colors
TRAINING_COLOR = "#009E73"
VALIDATION_COLOR = "#C475FD"

# Data
np.random.seed(42)
epochs = np.arange(1, 151)

# Training loss: sigmoid saturation pattern (different from exponential)
# Starts high (~2.2) and rapidly decays, then plateaus
train_loss = 2.2 / (1 + np.exp((epochs - 25) / 8)) + 0.12 + np.random.randn(150) * 0.012

# Validation loss: similar initial decay but with step-function overfitting
# Decays to minimum around epoch 65, then increases due to overfitting
val_base = 2.1 / (1 + np.exp((epochs - 30) / 9)) + 0.18
val_loss = np.copy(val_base) + np.random.randn(150) * 0.015

# Add step-function overfitting: sharp increase after epoch 65
overfitting_start = 65
val_loss[overfitting_start:] += (
    np.linspace(0, 0.5, 150 - overfitting_start) + np.random.randn(150 - overfitting_start) * 0.012
)

# Find minimum validation loss epoch
min_val_epoch = np.argmin(val_loss) + 1
min_val_loss = val_loss[min_val_epoch - 1]

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.plot(epochs, train_loss, linewidth=3, color=TRAINING_COLOR, label="Training Loss", marker="o", markersize=4)
ax.plot(epochs, val_loss, linewidth=3, color=VALIDATION_COLOR, label="Validation Loss", marker="s", markersize=4)

# Mark minimum validation loss (optimal early stopping)
ax.scatter([min_val_epoch], [min_val_loss], s=250, color=TRAINING_COLOR, zorder=5, edgecolors=PAGE_BG, linewidth=1.5)
ax.annotate(
    f"Epoch {min_val_epoch}",
    xy=(min_val_epoch, min_val_loss),
    xytext=(min_val_epoch + 20, min_val_loss - 0.25),
    fontsize=14,
    color=INK,
    arrowprops={"arrowstyle": "->", "color": INK_SOFT, "lw": 1.5},
    bbox={"boxstyle": "round,pad=0.4", "facecolor": PAGE_BG, "edgecolor": INK_SOFT, "linewidth": 1},
)

# Style
ax.set_xlabel("Epoch", fontsize=20, color=INK)
ax.set_ylabel("Cross-Entropy Loss", fontsize=20, color=INK)
ax.set_title("line-loss-training · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

# Grid (subtle, y-axis only)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)

# Legend (upper left to avoid overlap)
leg = ax.legend(fontsize=16, loc="upper left", framealpha=0.95)
if leg:
    leg.get_frame().set_facecolor(PAGE_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    leg.get_frame().set_linewidth(0.8)
    for text in leg.get_texts():
        text.set_color(INK_SOFT)

ax.set_xlim(0, 155)
plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
