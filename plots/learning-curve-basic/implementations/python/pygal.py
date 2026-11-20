"""anyplot.ai
learning-curve-basic: Model Learning Curve
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-10
"""

import os

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
TRAIN_SIZE = "Training set size (samples)"  # role: train_sizes
FOLD = "Fold"  # role: extra
TRAIN_SCORE = "Training score"  # role: train_scores
VALIDATION_SCORE = "Validation score"  # role: validation_scores

# Data: replace this block with your own table, for example df = pd.read_csv("learning_curve.csv")
rng = np.random.default_rng(42)
sizes = np.arange(100, 1001, 100)
n_folds = 5
df = pd.DataFrame(
    {
        TRAIN_SIZE: np.repeat(sizes, n_folds),
        FOLD: np.tile(np.arange(1, n_folds + 1), len(sizes)),
        TRAIN_SCORE: np.repeat(0.95 - 0.05 * np.exp(-sizes / 200), n_folds)
        + rng.standard_normal(len(sizes) * n_folds) * np.repeat(0.02 * np.exp(-sizes / 300), n_folds),
        VALIDATION_SCORE: np.repeat(0.65 + 0.25 * (1 - np.exp(-sizes / 400)), n_folds)
        + rng.standard_normal(len(sizes) * n_folds) * np.repeat(0.04 * np.exp(-sizes / 500) + 0.01, n_folds),
    }
)

# Plot: mean and ±1 std across folds at every training size
stats = df.groupby(TRAIN_SIZE, sort=True)[[TRAIN_SCORE, VALIDATION_SCORE]].agg(["mean", "std"])
x_values = stats.index.tolist()


def series(column, offset=0.0):
    """(x, y) points of a column's mean, shifted by `offset` standard deviations."""
    y = stats[(column, "mean")] + offset * stats[(column, "std")]
    return list(zip(x_values, y.round(4).tolist(), strict=True))


low = min(df[TRAIN_SCORE].min(), df[VALIDATION_SCORE].min())
high = max(df[TRAIN_SCORE].max(), df[VALIDATION_SCORE].max())
pad = (high - low) * 0.08
x_pad = (max(x_values) - min(x_values)) * 0.06

# Series order: two mean curves, then four dashed ±1 std bounds in their curve's color
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=(
        IMPRINT_PALETTE[0],
        IMPRINT_PALETTE[1],
        IMPRINT_PALETTE[0],
        IMPRINT_PALETTE[0],
        IMPRINT_PALETTE[1],
        IMPRINT_PALETTE[1],
    ),
    title_font_size=60,
    label_font_size=52,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=5,
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="learning-curve-basic · python · pygal · anyplot.ai",
    x_title=TRAIN_SIZE,
    y_title="Accuracy score",
    show_dots=True,
    dots_size=9,
    show_x_guides=False,
    show_y_guides=True,
    legend_at_bottom=True,
    range=(low - pad, min(high + pad, 1.02)),
    xrange=(min(x_values) - x_pad, max(x_values) + x_pad),
    x_labels=x_values,
    margin=50,
)

chart.add(TRAIN_SCORE, series(TRAIN_SCORE), stroke_style={"width": 7})
chart.add(VALIDATION_SCORE, series(VALIDATION_SCORE), stroke_style={"width": 7})

# Variability across folds: ±1 std bounds, dashed, no legend entry
bound_style = {"width": 3, "dasharray": "14, 8"}
for column in (TRAIN_SCORE, VALIDATION_SCORE):
    for sign in (1, -1):
        chart.add(None, series(column, sign), show_dots=False, stroke_style=bound_style)

chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
