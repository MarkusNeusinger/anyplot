""" pyplots.ai
gain-curve: Cumulative Gains Chart
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-29
"""

import numpy as np
import pygal
from pygal.style import Style
from sklearn.datasets import make_classification


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

# Create custom style for large canvas
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998", "#999999"),
    title_font_size=48,
    label_font_size=32,
    major_label_font_size=28,
    legend_font_size=28,
    value_font_size=24,
    stroke_width=4,
    opacity=0.9,
    opacity_hover=1.0,
)

# Create XY chart
chart = pygal.XY(
    width=4800,
    height=2700,
    title="gain-curve · pygal · pyplots.ai",
    x_title="Population Targeted (%)",
    y_title="Cumulative Gains (%)",
    style=custom_style,
    show_dots=False,
    stroke_style={"width": 5},
    range=(0, 100),
    xrange=(0, 100),
    show_x_guides=True,
    show_y_guides=True,
    legend_at_bottom=False,
    truncate_legend=-1,
)

# Add model gain curve
model_data = [(pop_sampled[i], gains_sampled[i]) for i in range(len(pop_sampled))]
chart.add("Model Gains", model_data)

# Add random baseline (diagonal line)
baseline_data = [(0, 0), (100, 100)]
chart.add("Random Baseline", baseline_data)

# Save as PNG and HTML
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
