""" pyplots.ai
pp-basic: Probability-Probability (P-P) Plot
Library: pygal 3.1.0 | Python 3.14.3
Quality: 83/100 | Created: 2026-03-15
"""

import math

import numpy as np
import pygal
from pygal.style import Style


# Data - 200 samples with slight skew to show deviation from normality
np.random.seed(42)
observed = np.concatenate([np.random.normal(50, 10, 160), np.random.exponential(8, 40) + 45])
observed = np.sort(observed)
n = len(observed)

# Fit normal parameters from the data
mu = np.mean(observed)
sigma = np.std(observed, ddof=1)

# Compute empirical CDF using plotting position i/(n+1)
empirical_cdf = np.arange(1, n + 1) / (n + 1)

# Compute theoretical CDF using normal distribution: Phi((x - mu) / sigma)
theoretical_cdf = np.array([0.5 * (1.0 + math.erf((x - mu) / (sigma * math.sqrt(2)))) for x in observed])

# Compute deviation from perfect fit for storytelling
deviation = empirical_cdf - theoretical_cdf

# Split points into close-to-fit and deviating groups for visual emphasis
threshold = 0.02
close_points = []
deviate_points = []
for i in range(n):
    tooltip = "Obs #{}: Δ={:+.3f}".format(i + 1, deviation[i])
    point = {"value": (float(theoretical_cdf[i]), float(empirical_cdf[i])), "label": tooltip}
    if abs(deviation[i]) > threshold:
        deviate_points.append(point)
    else:
        close_points.append(point)

# Custom style with refined palette and typography
custom_style = Style(
    background="#fafafa",
    plot_background="#ffffff",
    foreground="#2d2d2d",
    foreground_strong="#1a1a1a",
    foreground_subtle="#e0e0e0",
    opacity=".75",
    opacity_hover="1",
    colors=("#8faabe", "#306998", "#e74c3c"),
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=42,
    legend_font_size=38,
    value_font_size=32,
    stroke_width=3,
    title_font_family="sans-serif",
    label_font_family="sans-serif",
    major_label_font_family="sans-serif",
    legend_font_family="sans-serif",
    value_font_family="sans-serif",
    tooltip_font_size=28,
    tooltip_font_family="sans-serif",
)

# Create XY chart with square dimensions
chart = pygal.XY(
    width=3600,
    height=3600,
    style=custom_style,
    title="pp-basic · pygal · pyplots.ai",
    x_title="Theoretical CDF (Normal Distribution)",
    y_title="Empirical CDF",
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=28,
    dots_size=9,
    stroke=False,
    show_x_guides=True,
    show_y_guides=True,
    xrange=(0, 1),
    range=(0, 1),
    x_label_rotation=-15,
    x_labels=[0, 0.2, 0.4, 0.6, 0.8, 1.0],
    y_labels=[0, 0.2, 0.4, 0.6, 0.8, 1.0],
    print_values=False,
    tooltip_border_radius=8,
    inner_radius=0,
    explicit_size=True,
    spacing=30,
    margin_bottom=120,
)

# 45-degree reference line (perfect fit) — drawn first so it sits behind dots
chart.add(
    "Perfect Normal Fit",
    [(0, 0), (0.25, 0.25), (0.5, 0.5), (0.75, 0.75), (1, 1)],
    stroke=True,
    show_dots=False,
    dots_size=0,
    stroke_dasharray="12, 8",
    stroke_style={"width": 4},
)

# Points near the reference line (good fit)
chart.add("Near Diagonal (|Δ| ≤ 0.02)", close_points, dots_size=8)

# Points deviating from the reference line (skew region) — highlighted in red
chart.add("Deviating (|Δ| > 0.02)", deviate_points, dots_size=12)

# Save outputs
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
