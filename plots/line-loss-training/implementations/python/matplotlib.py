""" pyplots.ai
line-loss-training: Training Loss Curve
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 94/100 | Created: 2025-12-31
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Simulate training and validation loss over epochs
np.random.seed(42)
epochs = np.arange(1, 51)

# Training loss: exponential decay with small noise
train_loss = 2.5 * np.exp(-0.08 * epochs) + 0.15 + np.random.randn(50) * 0.015

# Validation loss: decays similarly but starts overfitting after epoch 28
val_base = 2.5 * np.exp(-0.065 * epochs) + 0.30
noise = np.random.randn(50) * 0.02
val_loss = val_base + noise
# Clear overfitting after epoch 28: validation loss increases while training keeps dropping
val_loss[28:] = val_loss[28] + np.linspace(0, 0.35, 22) + np.random.randn(22) * 0.015

# Find minimum validation loss epoch for annotation
min_val_epoch = np.argmin(val_loss) + 1
min_val_loss = val_loss[min_val_epoch - 1]

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Plot training and validation loss curves
ax.plot(epochs, train_loss, linewidth=3, color="#306998", label="Training Loss", marker="o", markersize=6)
ax.plot(epochs, val_loss, linewidth=3, color="#FFD43B", label="Validation Loss", marker="s", markersize=6)

# Mark minimum validation loss point (optimal early stopping)
ax.scatter([min_val_epoch], [min_val_loss], s=300, color="#E74C3C", zorder=5, edgecolors="black", linewidth=2)
ax.annotate(
    f"Best: Epoch {min_val_epoch}",
    xy=(min_val_epoch, min_val_loss),
    xytext=(min_val_epoch - 12, min_val_loss + 0.35),
    fontsize=16,
    arrowprops={"arrowstyle": "->", "color": "black", "lw": 2},
    bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "black"},
)

# Labels and styling
ax.set_xlabel("Epoch", fontsize=20)
ax.set_ylabel("Cross-Entropy Loss", fontsize=20)
ax.set_title("line-loss-training · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.legend(fontsize=16, loc="upper right")
ax.grid(True, alpha=0.3, linestyle="--")

# Set axis limits
ax.set_xlim(0, 52)
ax.set_ylim(0, 2.8)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
