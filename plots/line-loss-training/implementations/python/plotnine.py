""" anyplot.ai
line-loss-training: Training Loss Curve
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-14
"""

import os
import sys


# Prevent this file from shadowing the plotnine library when run from its own directory
sys.path = [p for p in sys.path if not p or os.path.abspath(p) != os.path.abspath(os.path.dirname(__file__))]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from plotnine import (  # noqa: E402
    aes,
    annotate,
    element_line,
    element_rect,
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


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette
TRAINING_COLOR = "#009E73"  # bluish green
VALIDATION_COLOR = "#C475FD"  # vermillion

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
    + geom_vline(xintercept=optimal_epoch, linetype="dashed", color=INK_SOFT, size=0.8, alpha=0.6)
    + annotate(
        "text",
        x=optimal_epoch + 1.5,
        y=np.min(val_loss) + (np.max(val_loss) - np.min(val_loss)) * 0.1,
        label=f"Best: {int(optimal_epoch)}",
        size=14,
        ha="left",
        color=INK_SOFT,
    )
    + scale_color_manual(values={"Training Loss": TRAINING_COLOR, "Validation Loss": VALIDATION_COLOR})
    + labs(title="line-loss-training · plotnine · anyplot.ai", x="Epoch", y="Cross-Entropy Loss", color="")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
        panel_border=element_rect(color=INK_SOFT, fill=None),
        text=element_text(size=14, color=INK),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(size=24, weight="bold", color=INK),
        legend_position="top",
        legend_direction="horizontal",
        legend_background=element_rect(fill=PAGE_BG, color=INK_SOFT),
        legend_text=element_text(size=16, color=INK_SOFT),
    )
)

# Save
script_dir = os.path.dirname(os.path.abspath(__file__))
plot.save(os.path.join(script_dir, f"plot-{THEME}.png"), dpi=300, verbose=False)
