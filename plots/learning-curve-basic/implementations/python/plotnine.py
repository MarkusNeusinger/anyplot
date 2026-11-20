"""anyplot.ai
learning-curve-basic: Model Learning Curve
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-05-10
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_ribbon,
    ggplot,
    ggsave,
    labs,
    scale_color_manual,
    scale_fill_manual,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns
SIZE = "Training Set Size"  # role: train_sizes
TRAIN = "Training Score"  # role: train_scores
VALIDATION = "Validation Score"  # role: validation_scores
FOLD = "Fold"  # role: extra

# Data
# Underfitting scenario: both curves plateau low with a small gap. One row per
# (training size, cross-validation fold); fold scores sit symmetrically around the mean.
train_sizes = np.linspace(20, 500, 12).astype(int)
train_mean = 0.72 + 0.12 * np.tanh((train_sizes - 150) / 100)
train_std = 0.04 * np.exp(-train_sizes / 300) + 0.02
val_mean = 0.70 + 0.10 * np.tanh((train_sizes - 150) / 100)
val_std = 0.05 * np.exp(-train_sizes / 250) + 0.025
fold_offsets = np.array([-1.5, -0.5, 0.0, 0.5, 1.5])
fold_offsets = fold_offsets / fold_offsets.std()

df = pd.DataFrame(
    {
        SIZE: np.repeat(train_sizes, len(fold_offsets)),
        FOLD: np.tile(np.arange(1, len(fold_offsets) + 1), len(train_sizes)),
        TRAIN: np.repeat(train_mean, len(fold_offsets))
        + np.repeat(train_std, len(fold_offsets)) * np.tile(fold_offsets, len(train_sizes)),
        VALIDATION: np.repeat(val_mean, len(fold_offsets))
        + np.repeat(val_std, len(fold_offsets)) * np.tile(fold_offsets, len(train_sizes)),
    }
)

# Plot
# Mean and one standard deviation across folds, per training size, in long form
SCORE = "Accuracy Score"
CURVE = "Curve"
SCORE_LOW = "Score low"
SCORE_HIGH = "Score high"
curves = []
for column in (TRAIN, VALIDATION):
    stats = df.groupby(SIZE, sort=True)[column].agg(mean="mean", std=lambda v: v.std(ddof=0)).reset_index()
    curves.append(
        pd.DataFrame(
            {
                SIZE: stats[SIZE],
                SCORE: stats["mean"],
                SCORE_LOW: np.maximum(0, stats["mean"] - stats["std"]),
                SCORE_HIGH: np.minimum(1, stats["mean"] + stats["std"]),
                CURVE: column,
            }
        )
    )
curve_df = pd.concat(curves, ignore_index=True)

# Style
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
    panel_border=element_rect(color=INK_SOFT, fill=None),
    axis_title=element_text(color=INK, size=10),
    axis_text=element_text(color=INK_SOFT, size=8),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK, size=12),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=8),
    legend_title=element_text(color=INK),
    figure_size=(8, 4.5),
    legend_position=(0.75, 0.25),
)

groups = curve_df[CURVE].unique().tolist()
plot = (
    ggplot(curve_df, aes(x=SIZE, y=SCORE, color=CURVE, fill=CURVE))
    + geom_ribbon(aes(ymin=SCORE_LOW, ymax=SCORE_HIGH), alpha=0.25, color="none")
    + geom_line(size=1.0)
    + scale_color_manual(values=IMPRINT_PALETTE, limits=groups)
    + scale_fill_manual(values=IMPRINT_PALETTE, limits=groups)
    + labs(title="learning-curve-basic · python · plotnine · anyplot.ai", color="", fill="")
    + theme_minimal()
    + anyplot_theme
)

# Save
ggsave(plot, f"plot-{THEME}.png", dpi=400, width=8, height=4.5)
