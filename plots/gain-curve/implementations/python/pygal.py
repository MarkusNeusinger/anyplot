""" anyplot.ai
gain-curve: Cumulative Gains Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-11
"""

import os

import numpy as np
import pygal
from pygal.style import Style
from sklearn.datasets import make_classification


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito palette: first series is brand green
IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477")

# Generate sample data for classification model evaluation
np.random.seed(42)
X, y_true = make_classification(
    n_samples=1000, n_features=10, n_informative=5, n_redundant=2, n_classes=2, weights=[0.7, 0.3], random_state=42
)

# Simulate model predictions (logistic-like scores)
np.random.seed(42)
y_score = 1 / (1 + np.exp(-(X[:, 0] * 0.8 + X[:, 1] * 0.5 + np.random.randn(1000) * 0.3)))

# Calculate cumulative gains curve
sorted_indices = np.argsort(y_score)[::-1]
y_true_sorted = y_true[sorted_indices]

# Calculate cumulative gains
total_positives = y_true.sum()
cumulative_positives = np.cumsum(y_true_sorted)
gains = cumulative_positives / total_positives * 100

# Calculate percentage of population
population_pct = np.arange(1, len(y_true) + 1) / len(y_true) * 100

# Sample points for smoother pygal rendering (every 2%)
sample_indices = [0] + list(range(19, len(population_pct), 20)) + [len(population_pct) - 1]
pop_sampled = [population_pct[i] for i in sample_indices]
gains_sampled = [gains[i] for i in sample_indices]

# Perfect model line: vertical at positive rate, then horizontal at 100%
positive_rate = (y_true.sum() / len(y_true)) * 100
perfect_model = [(0, 0), (positive_rate, 100), (100, 100)]

# Create custom style for theme-adaptive rendering
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
    stroke_width=3,
)

# Create XY chart
chart = pygal.XY(
    width=4800,
    height=2700,
    title="gain-curve · pygal · anyplot.ai",
    x_title="Population Targeted (%)",
    y_title="Cumulative Gains (%)",
    style=custom_style,
    show_dots=False,
    stroke_style={"width": 5},
    range=(0, 100),
    xrange=(0, 100),
    show_x_guides=True,
    show_y_guides=True,
    legend_at_bottom=True,
    truncate_legend=-1,
)

# Add perfect model reference line
chart.add("Perfect Model", perfect_model)

# Add model gain curve
model_data = [(pop_sampled[i], gains_sampled[i]) for i in range(len(pop_sampled))]
chart.add("Model Gains", model_data)

# Add random baseline (diagonal line)
baseline_data = [(0, 0), (100, 100)]
chart.add("Random Baseline", baseline_data)

# Save as PNG and HTML with theme suffix
chart.render_to_png(f"plot-{THEME}.png")
chart.render_to_file(f"plot-{THEME}.html")
