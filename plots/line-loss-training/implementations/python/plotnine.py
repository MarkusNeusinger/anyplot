""" pyplots.ai
line-loss-training: Training Loss Curve
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_line,
    element_text,
    geom_line,
    geom_point,
    geom_vline,
    ggplot,
    labs,
    scale_color_manual,
    theme,
    theme_minimal,
)


# Data - Simulated training history with typical loss curve behavior
np.random.seed(42)
epochs = np.arange(1, 51)

# Training loss: starts high, decreases with diminishing returns
train_loss = 2.5 * np.exp(-0.08 * epochs) + 0.15 + np.random.normal(0, 0.02, len(epochs))

# Validation loss: follows training initially, then diverges (overfitting)
val_loss = 2.5 * np.exp(-0.06 * epochs) + 0.25 + np.random.normal(0, 0.03, len(epochs))
# Add uptick after epoch 30 to show clear overfitting
val_loss[30:] += np.linspace(0, 0.25, 20)

# Find optimal stopping point (minimum validation loss)
optimal_epoch = epochs[np.argmin(val_loss)]

# Create long-format DataFrame for plotnine
df = pd.DataFrame(
    {
        "Epoch": np.concatenate([epochs, epochs]),
        "Loss": np.concatenate([train_loss, val_loss]),
        "Type": ["Training Loss"] * len(epochs) + ["Validation Loss"] * len(epochs),
    }
)

# Plot
plot = (
    ggplot(df, aes(x="Epoch", y="Loss", color="Type"))
    + geom_line(size=1.5, alpha=0.9)
    + geom_point(size=3, alpha=0.7)
    + geom_vline(xintercept=optimal_epoch, linetype="dashed", color="#555555", size=0.8, alpha=0.7)
    + annotate(
        "text",
        x=optimal_epoch + 1,
        y=max(val_loss) * 0.85,
        label=f"Best: {optimal_epoch}",
        size=12,
        ha="left",
        color="#555555",
    )
    + scale_color_manual(values={"Training Loss": "#306998", "Validation Loss": "#FFD43B"})
    + labs(title="line-loss-training · plotnine · pyplots.ai", x="Epoch", y="Cross-Entropy Loss", color="")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24, weight="bold"),
        legend_text=element_text(size=16),
        legend_position="top",
        legend_direction="horizontal",
        panel_grid_major=element_line(color="#cccccc", size=0.5, alpha=0.3),
        panel_grid_minor=element_line(color="#eeeeee", size=0.3, alpha=0.2),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
