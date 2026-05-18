""" anyplot.ai
logistic-regression: Logistic Regression Curve Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-18
"""

import os

import numpy as np
import pygal
from pygal.style import Style


# Theme-adaptive colors
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito palette
OKABE_ITO = ("#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442")

# Data - Medical diagnosis based on biomarker level
np.random.seed(42)
n_samples = 150

# Generate biomarker levels (0-100 scale)
biomarker_levels = np.concatenate(
    [
        np.random.normal(30, 15, n_samples // 2),  # Lower levels (mostly negative)
        np.random.normal(70, 15, n_samples // 2),  # Higher levels (mostly positive)
    ]
)
biomarker_levels = np.clip(biomarker_levels, 0, 100)

# Generate binary outcomes with logistic probability
true_probs = 1 / (1 + np.exp(-0.08 * (biomarker_levels - 50)))
y = (np.random.random(n_samples) < true_probs).astype(int)

# Fit logistic regression using gradient descent
X = (biomarker_levels - biomarker_levels.mean()) / biomarker_levels.std()
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
x_curve = np.linspace(0, 100, 100)
x_curve_norm = (x_curve - biomarker_levels.mean()) / biomarker_levels.std()
y_proba = 1 / (1 + np.exp(-np.clip(b0 + b1 * x_curve_norm, -500, 500)))

# Confidence interval (approximate using binomial SE)
se = np.sqrt(y_proba * (1 - y_proba) / n_samples) * 1.5
ci_lower = np.clip(y_proba - 1.96 * se, 0, 1)
ci_upper = np.clip(y_proba + 1.96 * se, 0, 1)

# Jitter y values for visibility
y_jittered = y + np.random.uniform(-0.025, 0.025, n_samples)

# Custom style for large canvas with theme-adaptive colors
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=OKABE_ITO,
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
    style=custom_style,
    title="logistic-regression · pygal · pyplots.ai",
    x_title="Biomarker Level",
    y_title="Probability of Disease",
    show_dots=True,
    stroke=True,
    show_x_guides=True,
    show_y_guides=True,
    dots_size=8,
    stroke_style={"width": 4},
    range=(0, 1.05),
    xrange=(-5, 105),
    explicit_size=True,
    legend_at_bottom=True,
    legend_box_size=28,
    truncate_legend=-1,
    print_values=False,
)

# Add logistic regression curve (main feature) - Okabe-Ito position 1 (green)
curve_points = [(float(x_curve[i]), float(y_proba[i])) for i in range(len(x_curve))]
chart.add("Logistic Fit", curve_points, stroke_style={"width": 5}, dots_size=0, show_dots=False, color=OKABE_ITO[0])

# Add confidence interval bounds - lighter/dashed variations
ci_upper_pts = [(float(x_curve[i]), float(ci_upper[i])) for i in range(0, len(x_curve), 2)]
ci_lower_pts = [(float(x_curve[i]), float(ci_lower[i])) for i in range(0, len(x_curve), 2)]
chart.add(
    "95% CI Upper",
    ci_upper_pts,
    stroke_style={"width": 2, "dasharray": "8,4"},
    dots_size=0,
    show_dots=False,
    color=OKABE_ITO[0],
)
chart.add(
    "95% CI Lower",
    ci_lower_pts,
    stroke_style={"width": 2, "dasharray": "8,4"},
    dots_size=0,
    show_dots=False,
    color=OKABE_ITO[0],
)

# Add decision threshold line (y = 0.5)
threshold_pts = [(0.0, 0.5), (100.0, 0.5)]
chart.add(
    "Threshold (p=0.5)",
    threshold_pts,
    stroke_style={"width": 3, "dasharray": "12,6"},
    dots_size=0,
    show_dots=False,
    color=INK_MUTED,
)

# Add data points - Negative (Class 0) - Okabe-Ito position 2 (vermillion)
negative_pts = [(float(biomarker_levels[i]), float(y_jittered[i])) for i in range(n_samples) if y[i] == 0]
chart.add("Negative (0)", negative_pts, stroke=False, dots_size=12, color=OKABE_ITO[1])

# Add data points - Positive (Class 1) - Okabe-Ito position 3 (blue)
positive_pts = [(float(biomarker_levels[i]), float(y_jittered[i])) for i in range(n_samples) if y[i] == 1]
chart.add("Positive (1)", positive_pts, stroke=False, dots_size=12, color=OKABE_ITO[2])

# Save as PNG and HTML with theme suffix
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
