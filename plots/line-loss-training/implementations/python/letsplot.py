"""anyplot.ai
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
    ggsave,
    ggsize,
    labs,
    scale_color_manual,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
OPTIMAL = "#AE3030"  # Imprint position 5, marks the early-stopping epoch

# Constants
LOSS_FUNCTION = "Cross-Entropy Loss"  # the loss that the y axis reports

# Columns: set these to your table's column names
EPOCH = "Epoch"  # role: epoch
TRAIN_LOSS = "Training loss"  # role: train_loss
VAL_LOSS = "Validation loss"  # role: val_loss

# Data: replace this block with your own table, for example df = pd.read_csv("history.csv")
np.random.seed(42)
epochs = np.arange(1, 101)
# Training loss keeps falling; validation loss falls, then rises after epoch 50 (overfitting)
train_loss = 2.5 * np.exp(-0.05 * epochs) + 0.08 + np.random.normal(0, 0.015, len(epochs))
val_loss = 2.5 * np.exp(-0.045 * epochs) + 0.2 + np.random.normal(0, 0.02, len(epochs))
val_loss[50:] += 0.008 * (epochs[50:] - 50)
df = pd.DataFrame({EPOCH: epochs, TRAIN_LOSS: train_loss, VAL_LOSS: val_loss})

# Plot: reads only df and the constants above
long_df = df.melt(id_vars=EPOCH, value_vars=[TRAIN_LOSS, VAL_LOSS], var_name="Series", value_name=LOSS_FUNCTION)
best = df.loc[df[VAL_LOSS].idxmin()]
optimal_df = pd.DataFrame({EPOCH: [best[EPOCH]], LOSS_FUNCTION: [best[VAL_LOSS]]})

custom_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_border=element_blank(),
    panel_grid_major=element_line(color=INK_SOFT, size=0.3, linetype="solid"),
    panel_grid_minor=element_blank(),
    axis_line_x=element_line(color=INK_SOFT, size=0.5),
    axis_line_y=element_line(color=INK_SOFT, size=0.5),
    axis_title=element_text(size=12, color=INK),
    axis_text=element_text(size=10, color=INK_SOFT),
    plot_title=element_text(size=16, color=INK),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(size=10, color=INK_SOFT),
    legend_title=element_blank(),
    legend_position="top",
)

plot = (
    ggplot(long_df, aes(x=EPOCH, y=LOSS_FUNCTION, color="Series"))
    + geom_line(size=1.2, alpha=0.9)
    + geom_vline(xintercept=float(best[EPOCH]), color=OPTIMAL, size=0.6, linetype="dashed", alpha=0.7)
    + geom_point(
        data=optimal_df, mapping=aes(x=EPOCH, y=LOSS_FUNCTION), color=OPTIMAL, size=5, shape=18, inherit_aes=False
    )
    + scale_color_manual(values=IMPRINT_PALETTE)
    + labs(title="line-loss-training · python · letsplot · anyplot.ai", x=EPOCH, y=LOSS_FUNCTION, color="")
    + theme_minimal()
    + custom_theme
    + ggsize(800, 450)
)

# Save: PNG at 3200 x 1800 and interactive HTML
ggsave(plot, f"plot-{THEME}.png", scale=4)
ggsave(plot, f"plot-{THEME}.html")

# Move files from lets-plot-images directory to current directory
images_dir = Path("lets-plot-images")
if images_dir.exists():
    for file in images_dir.glob(f"plot-{THEME}.*"):
        shutil.move(str(file), str(file.name))
