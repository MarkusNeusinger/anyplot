""" pyplots.ai
logistic-regression: Logistic Regression Curve Plot
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-09
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - Credit approval example based on credit score
np.random.seed(42)
n_samples = 150

# Generate credit scores (300-850 range)
credit_scores = np.concatenate(
    [
        np.random.normal(520, 70, n_samples // 2),  # Lower scores (more rejections)
        np.random.normal(720, 60, n_samples // 2),  # Higher scores (more approvals)
    ]
)
credit_scores = np.clip(credit_scores, 300, 850)

# Generate binary outcomes with logistic probability
true_probs = 1 / (1 + np.exp(-0.015 * (credit_scores - 600)))
y = (np.random.random(n_samples) < true_probs).astype(int)

# Fit logistic regression using gradient descent (numpy only)
X = (credit_scores - credit_scores.mean()) / credit_scores.std()  # Normalize for stability
b0, b1 = 0.0, 0.0
learning_rate = 0.1
for _ in range(1000):
    z = b0 + b1 * X
    p = 1 / (1 + np.exp(-np.clip(z, -500, 500)))
    grad_b0 = np.mean(p - y)
    grad_b1 = np.mean((p - y) * X)
    b0 -= learning_rate * grad_b0
    b1 -= learning_rate * grad_b1

# Generate smooth curve for predictions
x_curve = np.linspace(300, 850, 100)
x_curve_norm = (x_curve - credit_scores.mean()) / credit_scores.std()
y_proba = 1 / (1 + np.exp(-np.clip(b0 + b1 * x_curve_norm, -500, 500)))

# Confidence interval (approximate using binomial SE)
se = np.sqrt(y_proba * (1 - y_proba) / n_samples) * 1.5
ci_lower = np.clip(y_proba - 1.96 * se, 0, 1)
ci_upper = np.clip(y_proba + 1.96 * se, 0, 1)

# Jitter y values for visibility
y_jittered = y + np.random.uniform(-0.025, 0.025, n_samples)

# Custom style for large canvas
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998", "#306998", "#306998", "#888888", "#E74C3C", "#FFD43B"),
    title_font_size=56,
    label_font_size=36,
    major_label_font_size=32,
    legend_font_size=32,
    value_font_size=24,
    stroke_width=4,
    opacity=0.7,
    opacity_hover=0.95,
    font_family="sans-serif",
)

# Create XY chart
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="logistic-regression · pygal · pyplots.ai",
    x_title="Credit Score",
    y_title="Probability of Approval",
    show_dots=True,
    stroke=True,
    show_x_guides=True,
    show_y_guides=True,
    dots_size=10,
    stroke_style={"width": 4},
    range=(0, 1.05),
    xrange=(280, 870),
    explicit_size=True,
    legend_at_bottom=True,
    legend_box_size=28,
    truncate_legend=-1,
    print_values=False,
)

# Add logistic regression curve (main feature)
curve_points = [(float(x_curve[i]), float(y_proba[i])) for i in range(len(x_curve))]
chart.add("Logistic Fit", curve_points, stroke_style={"width": 5}, dots_size=0, show_dots=False)

# Add confidence interval bounds
ci_upper_pts = [(float(x_curve[i]), float(ci_upper[i])) for i in range(0, len(x_curve), 2)]
ci_lower_pts = [(float(x_curve[i]), float(ci_lower[i])) for i in range(0, len(x_curve), 2)]
chart.add("95% CI Upper", ci_upper_pts, stroke_style={"width": 2, "dasharray": "8,4"}, dots_size=0, show_dots=False)
chart.add("95% CI Lower", ci_lower_pts, stroke_style={"width": 2, "dasharray": "8,4"}, dots_size=0, show_dots=False)

# Add decision threshold line (y = 0.5)
threshold_pts = [(300.0, 0.5), (850.0, 0.5)]
chart.add(
    "Threshold (p=0.5)", threshold_pts, stroke_style={"width": 3, "dasharray": "12,6"}, dots_size=0, show_dots=False
)

# Add data points - Rejected (Class 0)
rejected_pts = [(float(credit_scores[i]), float(y_jittered[i])) for i in range(n_samples) if y[i] == 0]
chart.add("Rejected (0)", rejected_pts, stroke=False, dots_size=14)

# Add data points - Approved (Class 1)
approved_pts = [(float(credit_scores[i]), float(y_jittered[i])) for i in range(n_samples) if y[i] == 1]
chart.add("Approved (1)", approved_pts, stroke=False, dots_size=14)

# Save as PNG and HTML
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
