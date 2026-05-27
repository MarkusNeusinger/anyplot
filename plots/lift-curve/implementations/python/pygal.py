""" anyplot.ai
lift-curve: Model Lift Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: 84/100 | Updated: 2026-05-10
"""

import os

import numpy as np
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477")

# Data - Simulated customer response prediction
np.random.seed(42)
n_samples = 1000

# Generate realistic model scores and true outcomes
y_score = np.random.beta(2, 5, n_samples)
response_prob = 0.1 + 0.6 * y_score
y_true = (np.random.random(n_samples) < response_prob).astype(int)

# Calculate lift curve data
sorted_indices = np.argsort(y_score)[::-1]
y_true_sorted = y_true[sorted_indices]

# Calculate cumulative metrics
n_total = len(y_true)
n_positive = y_true.sum()
baseline_rate = n_positive / n_total

# Calculate lift at decile intervals
deciles = list(range(10, 101, 10))
lift_values = []

for pct in deciles:
    n_targeted = int(n_total * pct / 100)
    positives_captured = y_true_sorted[:n_targeted].sum()
    model_rate = positives_captured / n_targeted
    lift = model_rate / baseline_rate if baseline_rate > 0 else 1
    lift_values.append(lift)

# Create custom style
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_SOFT,
    colors=IMPRINT,
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=18,
    value_font_size=16,
    stroke_width=4,
)

# Create line chart
chart = pygal.Line(
    width=4800,
    height=2700,
    style=custom_style,
    title="lift-curve · pygal · anyplot.ai",
    x_title="Population Targeted (%)",
    y_title="Lift (Model Rate / Baseline Rate)",
    show_dots=True,
    dots_size=10,
    stroke_style={"width": 5},
    fill=False,
    show_x_guides=False,
    show_y_guides=True,
    legend_at_bottom=False,
    range=(0.9, max(lift_values) * 1.1),
    margin=100,
)

# X-axis labels at deciles
chart.x_labels = [f"{d}%" for d in deciles]

# Add lift curve with tooltip-friendly data
chart.add("Model Lift", [{"value": v, "label": f"{v:.2f}"} for v in lift_values])

# Add baseline reference line at y=1
baseline = [1.0] * len(deciles)
chart.add("Random (No Lift)", baseline)

# Save as PNG and HTML
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
