""" pyplots.ai
lift-curve: Model Lift Chart
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-27
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - Simulated customer response prediction
np.random.seed(42)
n_samples = 1000

# Generate realistic model scores and true outcomes
# Good model: positive correlation between score and actual response
y_score = np.random.beta(2, 5, n_samples)  # Model predictions (0-1)
# True labels influenced by score (better score = higher chance of response)
response_prob = 0.1 + 0.6 * y_score  # Base rate ~10%, top scores ~70%
y_true = (np.random.random(n_samples) < response_prob).astype(int)

# Calculate lift curve data
# Sort by score descending
sorted_indices = np.argsort(y_score)[::-1]
y_true_sorted = y_true[sorted_indices]

# Calculate cumulative metrics
n_total = len(y_true)
n_positive = y_true.sum()
baseline_rate = n_positive / n_total

# Calculate lift at decile intervals (10%, 20%, ..., 100%)
deciles = list(range(10, 101, 10))
lift_values = []

for pct in deciles:
    n_targeted = int(n_total * pct / 100)
    positives_captured = y_true_sorted[:n_targeted].sum()
    model_rate = positives_captured / n_targeted
    lift = model_rate / baseline_rate if baseline_rate > 0 else 1
    lift_values.append(round(lift, 2))

# Create custom style for pyplots
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998", "#FFD43B"),
    title_font_size=56,
    label_font_size=36,
    major_label_font_size=32,
    legend_font_size=32,
    value_font_size=24,
    stroke_width=5,
    opacity=0.9,
    opacity_hover=1.0,
)

# Create line chart
chart = pygal.Line(
    width=4800,
    height=2700,
    style=custom_style,
    title="lift-curve · pygal · pyplots.ai",
    x_title="Population Targeted (%)",
    y_title="Lift (Model Rate / Baseline Rate)",
    show_dots=True,
    dots_size=8,
    stroke_style={"width": 6},
    fill=False,
    show_x_guides=False,
    show_y_guides=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=2,
    truncate_legend=-1,
    range=(0.9, 2.2),
    margin=50,
)

# X-axis labels at deciles
chart.x_labels = [f"{d}%" for d in deciles]

# Add lift curve
chart.add("Model Lift", lift_values)

# Add baseline reference line at y=1
baseline = [1.0] * len(deciles)
chart.add("Random (No Lift)", baseline)

# Save as PNG and HTML
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
