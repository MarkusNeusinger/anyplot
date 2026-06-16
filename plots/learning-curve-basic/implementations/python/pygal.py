""" anyplot.ai
learning-curve-basic: Model Learning Curve
Library: pygal 3.1.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-10
"""

import os

import numpy as np
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477")

# Data - Simulating sklearn's learning_curve output
np.random.seed(42)

# Training set sizes
n_samples_total = 1000
train_sizes_pct = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
train_sizes = (train_sizes_pct * n_samples_total).astype(int)

# Simulate cross-validation folds (5 folds)
n_folds = 5
n_sizes = len(train_sizes)

# Training scores: start high, remain high (slight overfitting pattern)
train_scores_base = 0.95 - 0.05 * np.exp(-train_sizes / 200)
train_scores_std_vals = 0.02 * np.exp(-train_sizes / 300)
train_scores = np.array(
    [train_scores_base[i] + np.random.randn(n_folds) * train_scores_std_vals[i] for i in range(n_sizes)]
).T

# Validation scores: start lower, converge towards training (gap shows variance)
val_scores_base = 0.65 + 0.25 * (1 - np.exp(-train_sizes / 400))
val_scores_std_vals = 0.04 * np.exp(-train_sizes / 500) + 0.01
val_scores = np.array(
    [val_scores_base[i] + np.random.randn(n_folds) * val_scores_std_vals[i] for i in range(n_sizes)]
).T

# Calculate means and standard deviations
train_mean = np.mean(train_scores, axis=0)
train_std = np.std(train_scores, axis=0)
val_mean = np.mean(val_scores, axis=0)
val_std = np.std(val_scores, axis=0)

# Custom style for 4800x2700 canvas with theme-adaptive colors
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT,
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=16,
    value_font_size=14,
    stroke_width=4,
)

# Create XY chart for learning curve
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="learning-curve-basic · pygal · anyplot.ai",
    x_title="Training Set Size (samples)",
    y_title="Accuracy Score",
    show_dots=True,
    dots_size=8,
    stroke_style={"width": 4},
    show_x_guides=False,
    show_y_guides=True,
    legend_at_bottom=False,
    range=(0.6, 1.02),
    xrange=(50, 1050),
    x_labels=[100, 200, 300, 400, 500, 600, 700, 800, 900, 1000],
    margin=80,
)

# Prepare data points as (x, y) tuples
train_points = [(int(train_sizes[i]), round(train_mean[i], 3)) for i in range(n_sizes)]
val_points = [(int(train_sizes[i]), round(val_mean[i], 3)) for i in range(n_sizes)]

# Add upper/lower bounds for confidence bands (±1 std)
train_upper = [(int(train_sizes[i]), round(train_mean[i] + train_std[i], 3)) for i in range(n_sizes)]
train_lower = [(int(train_sizes[i]), round(train_mean[i] - train_std[i], 3)) for i in range(n_sizes)]
val_upper = [(int(train_sizes[i]), round(val_mean[i] + val_std[i], 3)) for i in range(n_sizes)]
val_lower = [(int(train_sizes[i]), round(val_mean[i] - val_std[i], 3)) for i in range(n_sizes)]

# Add main learning curves
chart.add("Training Score", train_points, stroke_style={"width": 5})
chart.add("Validation Score", val_points, stroke_style={"width": 5})

# Add confidence bounds as secondary lines (thinner, dashed, no legend)
chart.add(None, train_upper, show_dots=False, stroke_style={"width": 2, "dasharray": "8, 4"})
chart.add(None, train_lower, show_dots=False, stroke_style={"width": 2, "dasharray": "8, 4"})
chart.add(None, val_upper, show_dots=False, stroke_style={"width": 2, "dasharray": "8, 4"})
chart.add(None, val_lower, show_dots=False, stroke_style={"width": 2, "dasharray": "8, 4"})

# Save as HTML (interactive) and PNG
chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
