""" pyplots.ai
line-loss-training: Training Loss Curve
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-31
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_text,
    geom_line,
    geom_point,
    geom_vline,
    ggplot,
    ggsize,
    labs,
    scale_color_manual,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Data - Simulated neural network training loss over 100 epochs
np.random.seed(42)
epochs = np.arange(1, 101)

# Training loss: starts high, decreases with noise - continues to decrease throughout
train_loss = 2.5 * np.exp(-0.05 * epochs) + 0.08 + np.random.normal(0, 0.015, len(epochs))

# Validation loss: decreases then increases (overfitting after ~50 epochs)
val_loss_base = 2.5 * np.exp(-0.045 * epochs) + 0.2
noise = np.random.normal(0, 0.02, len(epochs))
val_loss = val_loss_base + noise
# Add overfitting effect - validation loss increases after epoch 50
overfitting_start = 50
val_loss[overfitting_start:] = val_loss[overfitting_start:] + 0.008 * (epochs[overfitting_start:] - overfitting_start)

# Find optimal epoch (minimum validation loss)
optimal_epoch = int(epochs[np.argmin(val_loss)])
optimal_loss = float(val_loss.min())

# Create DataFrame for plotting
df = pd.DataFrame(
    {
        "Epoch": np.tile(epochs, 2),
        "Loss": np.concatenate([train_loss, val_loss]),
        "Type": ["Training Loss"] * len(epochs) + ["Validation Loss"] * len(epochs),
    }
)

# Optimal point marker
optimal_df = pd.DataFrame({"Epoch": [optimal_epoch], "Loss": [optimal_loss]})

# Create plot
plot = (
    ggplot(df, aes(x="Epoch", y="Loss", color="Type"))
    + geom_line(size=1.5, alpha=0.9)
    + geom_point(
        data=optimal_df, mapping=aes(x="Epoch", y="Loss"), color="#DC2626", size=6, shape=18, inherit_aes=False
    )
    + geom_vline(xintercept=optimal_epoch, color="#DC2626", size=0.8, linetype="dashed", alpha=0.7)
    + scale_color_manual(values=["#306998", "#FFD43B"])
    + labs(title="line-loss-training · letsplot · pyplots.ai", x="Epoch", y="Cross-Entropy Loss", color="")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_text=element_text(size=16),
        legend_position="top",
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800x2700)
ggsave(plot, "plot.png", path=".", scale=3)

# Save as HTML for interactive version
ggsave(plot, "plot.html", path=".")
