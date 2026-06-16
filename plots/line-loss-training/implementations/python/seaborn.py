""" anyplot.ai
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

# Okabe-Ito palette
BRAND = "#009E73"  # Training loss - first series
ACCENT = "#C475FD"  # Validation loss - second series

# Data - simulate realistic neural network training loss curves
np.random.seed(42)
epochs = np.arange(1, 101)

# Training loss: exponential decay with some noise
train_loss = 2.5 * np.exp(-0.04 * epochs) + 0.15 + np.random.normal(0, 0.03, len(epochs))
train_loss = np.clip(train_loss, 0.1, 3.0)

# Validation loss: similar decay but plateaus earlier and shows slight overfitting
val_loss = 2.5 * np.exp(-0.035 * epochs) + 0.25 + np.random.normal(0, 0.04, len(epochs))
# Add slight overfitting after epoch 70
val_loss[69:] = val_loss[69:] + 0.002 * (epochs[69:] - 70)
val_loss = np.clip(val_loss, 0.15, 3.0)

# Find optimal epoch (minimum validation loss)
optimal_epoch = epochs[np.argmin(val_loss)]
optimal_val_loss = val_loss.min()

# Create DataFrame for seaborn
df = pd.DataFrame(
    {
        "Epoch": np.tile(epochs, 2),
        "Loss": np.concatenate([train_loss, val_loss]),
        "Type": ["Training Loss"] * len(epochs) + ["Validation Loss"] * len(epochs),
    }
)

# Set theme and style
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

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Use seaborn lineplot with hue for dual curves
sns.lineplot(data=df, x="Epoch", y="Loss", hue="Type", palette=[BRAND, ACCENT], linewidth=3, ax=ax)

# Mark optimal stopping point
ax.axvline(x=optimal_epoch, color=INK_SOFT, linestyle="--", linewidth=2, alpha=0.5)
ax.scatter([optimal_epoch], [optimal_val_loss], s=200, color=ACCENT, zorder=5, edgecolor=INK_SOFT, linewidth=2)
ax.annotate(
    f"Optimal: Epoch {optimal_epoch}",
    xy=(optimal_epoch, optimal_val_loss),
    xytext=(optimal_epoch + 8, optimal_val_loss + 0.15),
    fontsize=16,
    color=INK,
    arrowprops={"arrowstyle": "->", "color": INK_SOFT, "lw": 2},
)

# Style
ax.set_xlabel("Epoch", fontsize=20, color=INK)
ax.set_ylabel("Cross-Entropy Loss", fontsize=20, color=INK)
ax.set_title("line-loss-training · seaborn · anyplot.ai", fontsize=24, color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Remove top and right spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)

# Grid - y-axis only
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8)
ax.xaxis.grid(False)

# Customize legend
ax.legend(fontsize=16, loc="upper right", framealpha=0.95)

# Set axis limits
ax.set_xlim(0, 105)
ax.set_ylim(0, 2.8)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
