""" pyplots.ai
learning-curve-basic: Model Learning Curve
Library: pygal 3.1.0 | Python 3.13.11
Quality: 90/100 | Created: 2025-12-26
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - Simulating sklearn's learning_curve output
np.random.seed(42)

# Training set sizes (as percentages converted to actual samples)
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
).T  # Shape: (n_folds, n_sizes)

# Validation scores: start lower, converge towards training (gap shows variance)
val_scores_base = 0.65 + 0.25 * (1 - np.exp(-train_sizes / 400))
val_scores_std_vals = 0.04 * np.exp(-train_sizes / 500) + 0.01
val_scores = np.array(
    [val_scores_base[i] + np.random.randn(n_folds) * val_scores_std_vals[i] for i in range(n_sizes)]
).T  # Shape: (n_folds, n_sizes)

# Calculate means and standard deviations
train_mean = np.mean(train_scores, axis=0)
train_std = np.std(train_scores, axis=0)
val_mean = np.mean(val_scores, axis=0)
val_std = np.std(val_scores, axis=0)

# Custom style for pyplots - scaled for 4800x2700 canvas
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333",
    foreground_strong="#333",
    foreground_subtle="#666",
    colors=("#306998", "#FFD43B", "#306998", "#306998", "#FFD43B", "#FFD43B"),
    title_font_size=56,
    label_font_size=36,
    major_label_font_size=32,
    legend_font_size=36,
    value_font_size=28,
    stroke_width=5,
    opacity=0.9,
    opacity_hover=1.0,
)

# Create XY chart for learning curve
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="learning-curve-basic · pygal · pyplots.ai",
    x_title="Training Set Size (samples)",
    y_title="Accuracy Score",
    show_dots=True,
    dots_size=12,
    stroke_style={"width": 5},
    show_x_guides=False,
    show_y_guides=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=2,
    truncate_legend=-1,
    range=(0.5, 1.02),
    xrange=(50, 1050),
    x_labels=[100, 200, 300, 400, 500, 600, 700, 800, 900, 1000],
    margin=50,
)

# Prepare data points as (x, y) tuples
train_points = [(int(train_sizes[i]), round(train_mean[i], 3)) for i in range(n_sizes)]
val_points = [(int(train_sizes[i]), round(val_mean[i], 3)) for i in range(n_sizes)]

# Add upper/lower bounds for confidence bands (±1 std)
train_upper = [(int(train_sizes[i]), round(train_mean[i] + train_std[i], 3)) for i in range(n_sizes)]
train_lower = [(int(train_sizes[i]), round(train_mean[i] - train_std[i], 3)) for i in range(n_sizes)]
val_upper = [(int(train_sizes[i]), round(val_mean[i] + val_std[i], 3)) for i in range(n_sizes)]
val_lower = [(int(train_sizes[i]), round(val_mean[i] - val_std[i], 3)) for i in range(n_sizes)]

# Add main learning curves with larger markers
chart.add("Training Score (±1σ band)", train_points, stroke_style={"width": 6})
chart.add("Validation Score (±1σ band)", val_points, stroke_style={"width": 6})

# Add confidence bounds as secondary lines (thinner, dashed, no legend)
chart.add(None, train_upper, show_dots=False, stroke_style={"width": 2, "dasharray": "8, 4"})
chart.add(None, train_lower, show_dots=False, stroke_style={"width": 2, "dasharray": "8, 4"})
chart.add(None, val_upper, show_dots=False, stroke_style={"width": 2, "dasharray": "8, 4"})
chart.add(None, val_lower, show_dots=False, stroke_style={"width": 2, "dasharray": "8, 4"})

# Save as HTML (interactive) and PNG
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
