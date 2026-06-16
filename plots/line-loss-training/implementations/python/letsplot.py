""" anyplot.ai
line-loss-training: Training Loss Curve
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-14
"""

import os
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
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

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
BRAND = "#009E73"  # Training loss (first series)
ACCENT = "#C475FD"  # Validation loss (second series)
OPTIMAL = "#DC2626"  # Optimal epoch marker

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

# Custom theme
custom_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_border=element_blank(),
    panel_grid_major=element_line(color=INK_SOFT, size=0.3, linetype="solid"),
    panel_grid_minor=element_blank(),
    axis_line_x=element_line(color=INK_SOFT, size=0.5),
    axis_line_y=element_line(color=INK_SOFT, size=0.5),
    axis_title=element_text(size=20, color=INK),
    axis_text=element_text(size=16, color=INK_SOFT),
    plot_title=element_text(size=24, color=INK),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(size=16, color=INK_SOFT),
    legend_title=element_text(size=16, color=INK),
    legend_position="top",
)

# Create plot
plot = (
    ggplot(df, aes(x="Epoch", y="Loss", color="Type"))
    + geom_line(size=1.5, alpha=0.9)
    + geom_point(data=optimal_df, mapping=aes(x="Epoch", y="Loss"), color=OPTIMAL, size=6, shape=18, inherit_aes=False)
    + geom_vline(xintercept=optimal_epoch, color=OPTIMAL, size=0.8, linetype="dashed", alpha=0.7)
    + scale_color_manual(values=[BRAND, ACCENT])
    + labs(title="line-loss-training · letsplot · anyplot.ai", x="Epoch", y="Cross-Entropy Loss", color="")
    + theme_minimal()
    + custom_theme
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800x2700)
ggsave(plot, f"plot-{THEME}.png", scale=3)
ggsave(plot, f"plot-{THEME}.html")

# Move files from lets-plot-images directory to current directory
images_dir = Path("lets-plot-images")
if images_dir.exists():
    for file in images_dir.glob(f"plot-{THEME}.*"):
        shutil.move(str(file), str(file.name))
