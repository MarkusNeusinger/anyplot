""" anyplot.ai
learning-curve-basic: Model Learning Curve
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 80/100 | Updated: 2026-11-20
"""

import os

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
    geom_ribbon,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_color_manual,
    scale_fill_manual,
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

# Imprint palette: all eight positions, first series is always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
TRAIN_SIZE = "Training set size (samples)"  # role: train_sizes
TRAIN_SCORE = "Training score"  # role: train_scores
VALIDATION_SCORE = "Validation score"  # role: validation_scores
METRIC = "Accuracy (0-1)"  # label of the metric the scores measure

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
# One row per cross-validation fold and training size (scikit-learn's learning_curve output, flattened)
np.random.seed(42)
train_sizes = np.array([50, 100, 200, 400, 600, 800, 1000, 1200, 1400, 1600])
n_folds = 5

train_mean = 0.99 - 0.15 * np.exp(-train_sizes / 200)
train_scores = np.array([train_mean + np.random.randn(len(train_sizes)) * 0.01 for _ in range(n_folds)])

validation_mean = 0.65 + 0.20 * (1 - np.exp(-train_sizes / 500))
validation_scores = np.array([validation_mean + np.random.randn(len(train_sizes)) * 0.02 for _ in range(n_folds)])

df = pd.DataFrame(
    {
        TRAIN_SIZE: np.tile(train_sizes, n_folds),
        TRAIN_SCORE: train_scores.ravel(),
        VALIDATION_SCORE: validation_scores.ravel(),
    }
)

# Plot: reads only df and the constants above
curves = [TRAIN_SCORE, VALIDATION_SCORE]
long = df.melt(id_vars=TRAIN_SIZE, value_vars=curves, var_name="curve", value_name="score")
summary = (
    long.groupby(["curve", TRAIN_SIZE], sort=False)["score"]
    .agg(mean="mean", std=lambda s: s.std(ddof=0))
    .reset_index()
    .assign(lower=lambda t: t["mean"] - t["std"], upper=lambda t: t["mean"] + t["std"])
)

plot = (
    ggplot(summary, aes(x=TRAIN_SIZE, y="mean", color="curve", fill="curve"))
    + geom_ribbon(aes(ymin="lower", ymax="upper"), alpha=0.2, color="rgba(0,0,0,0)")
    + geom_line(size=1.0)
    + geom_point(size=2.5)
    + scale_color_manual(values=IMPRINT_PALETTE)
    + scale_fill_manual(values=IMPRINT_PALETTE)
    + labs(x=TRAIN_SIZE, y=METRIC, title="learning-curve-basic · python · letsplot · anyplot.ai", color="", fill="")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK_SOFT, size=0.3),
        panel_grid_minor=element_blank(),
        axis_title=element_text(color=INK, size=12),
        axis_text=element_text(color=INK_SOFT, size=10),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(color=INK, size=16),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(color=INK_SOFT, size=10),
        legend_title=element_text(color=INK),
        legend_position="bottom",
    )
    + ggsize(800, 450)
)

# Save as PNG (scale 4x = 3200 x 1800 px) and HTML
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
