""" pyplots.ai
line-loss-training: Training Loss Curve
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-31
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


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

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Use seaborn lineplot with hue for dual curves
sns.lineplot(data=df, x="Epoch", y="Loss", hue="Type", palette=["#306998", "#FFD43B"], linewidth=3, ax=ax)

# Mark optimal stopping point
ax.axvline(x=optimal_epoch, color="#E74C3C", linestyle="--", linewidth=2, alpha=0.7)
ax.scatter([optimal_epoch], [optimal_val_loss], s=200, color="#E74C3C", zorder=5, edgecolor="white", linewidth=2)
ax.annotate(
    f"Optimal: Epoch {optimal_epoch}",
    xy=(optimal_epoch, optimal_val_loss),
    xytext=(optimal_epoch + 8, optimal_val_loss + 0.15),
    fontsize=16,
    color="#E74C3C",
    arrowprops={"arrowstyle": "->", "color": "#E74C3C", "lw": 2},
)

# Labels and styling
ax.set_xlabel("Epoch", fontsize=20)
ax.set_ylabel("Cross-Entropy Loss", fontsize=20)
ax.set_title("line-loss-training · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--")

# Customize legend
ax.legend(fontsize=16, loc="upper right", framealpha=0.9)

# Set axis limits
ax.set_xlim(0, 105)
ax.set_ylim(0, 2.8)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
