"""anyplot.ai
line-loss-training: Training Loss Curve
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-14
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
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
    scale_x_continuous,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
EPOCH = "Epoch"  # role: epoch
TRAIN_LOSS = "Training Loss"  # role: train_loss
VAL_LOSS = "Validation Loss"  # role: val_loss

# Data: replace this block with your own table, for example df = pd.read_csv("history.csv")
np.random.seed(42)
n_epochs = 50
epochs = np.arange(1, n_epochs + 1)
# Training loss: starts high, decreases with diminishing returns
train_loss = 2.5 * np.exp(-0.08 * epochs) + 0.15 + np.random.normal(0, 0.02, n_epochs)
# Validation loss: follows training at first, then turns upward (overfitting)
val_loss = 2.5 * np.exp(-0.06 * epochs) + 0.25 + np.random.normal(0, 0.03, n_epochs)
val_loss[30:] += np.linspace(0, 0.25, n_epochs - 30)
df = pd.DataFrame({EPOCH: epochs, TRAIN_LOSS: train_loss, VAL_LOSS: val_loss})

# Plot: reads only df and the constants above
series = [TRAIN_LOSS, VAL_LOSS]
long_df = df.melt(id_vars=EPOCH, value_vars=series, var_name="Series", value_name="Loss")

best_row = df.loc[df[VAL_LOSS].idxmin()]
best_epoch = best_row[EPOCH]
loss_span = df[series].max().max() - df[series].min().min()
x_span = df[EPOCH].max() - df[EPOCH].min()

plot = (
    ggplot(long_df, aes(x=EPOCH, y="Loss", color="Series"))
    + geom_line(size=1.0, alpha=0.9)
    + geom_point(size=2.0, alpha=0.7)
    + geom_vline(xintercept=best_epoch, linetype="dashed", color=INK_SOFT, size=0.5, alpha=0.7)
    + annotate(
        "text",
        x=best_epoch - x_span * 0.015,
        y=best_row[VAL_LOSS] + loss_span * 0.10,
        label=f"Best: epoch {int(best_epoch)}",
        size=9,
        ha="right",
        color=INK_SOFT,
    )
    + scale_x_continuous(limits=(df[EPOCH].min(), df[EPOCH].max()), expand=(0.02, 0))
    + scale_color_manual(values=IMPRINT_PALETTE, limits=series)
    + labs(title="line-loss-training · python · plotnine · anyplot.ai", y="Cross-Entropy Loss", color="")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.15),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
        panel_border=element_rect(color=INK_SOFT, fill=None),
        text=element_text(size=7, color=INK),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(size=12, weight="bold", color=INK),
        legend_position="top",
        legend_direction="horizontal",
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_key=element_rect(fill=ELEVATED_BG, color=ELEVATED_BG),
        legend_text=element_text(size=8, color=INK_SOFT),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
