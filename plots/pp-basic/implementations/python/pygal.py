""" pyplots.ai
pp-basic: Probability-Probability (P-P) Plot
Library: pygal 3.1.0 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-15
"""

import math

import numpy as np
import pygal
from pygal.style import Style


# Quality-control scenario: 200 tensile strength measurements (MPa) from steel rods
# Mix of compliant samples (normal) and heat-treatment anomalies (skewed batch)
np.random.seed(42)
compliant = np.random.normal(520, 35, 160)  # Standard production run
anomalous = np.random.exponential(30, 40) + 480  # Heat-treatment drift batch
observed = np.sort(np.concatenate([compliant, anomalous]))
n = len(observed)

# Fit normal parameters from full sample
mu = np.mean(observed)
sigma = np.std(observed, ddof=1)

# Empirical CDF using plotting position i/(n+1)
empirical_cdf = np.arange(1, n + 1) / (n + 1)

# Theoretical CDF: Phi((x - mu) / sigma)
sqrt2 = math.sqrt(2)
theoretical_cdf = np.array([0.5 * (1.0 + math.erf((x - mu) / (sigma * sqrt2))) for x in observed])

# Deviation from perfect fit — used for classification and tooltips
deviation = empirical_cdf - theoretical_cdf
max_dev = float(np.max(np.abs(deviation)))

# Classify points into three tiers for visual hierarchy
good_fit = []  # |Δ| ≤ 0.01 — tightly along diagonal
mild_dev = []  # 0.01 < |Δ| ≤ 0.025 — moderate departure
strong_dev = []  # |Δ| > 0.025 — clear distributional mismatch

for i in range(n):
    t = float(theoretical_cdf[i])
    e = float(empirical_cdf[i])
    d = float(deviation[i])
    label = "#{} · {:.0f} MPa · Δ = {:+.3f}".format(i + 1, observed[i], d)
    pt = {"value": (t, e), "label": label}
    if abs(d) <= 0.01:
        good_fit.append(pt)
    elif abs(d) <= 0.025:
        mild_dev.append(pt)
    else:
        strong_dev.append(pt)

# Publication-grade style — Python Blue anchor with warm accent
custom_style = Style(
    background="#ffffff",
    plot_background="#fafbfc",
    foreground="#2d2d2d",
    foreground_strong="#111111",
    foreground_subtle="#e2e6ea",
    opacity=".75",
    opacity_hover="1",
    colors=("#c8d5e0", "#306998", "#e8913a", "#d04a3e"),
    title_font_size=72,
    label_font_size=46,
    major_label_font_size=44,
    legend_font_size=34,
    value_font_size=30,
    stroke_width=2,
    title_font_family="Trebuchet MS, Helvetica Neue, sans-serif",
    label_font_family="Trebuchet MS, Helvetica Neue, sans-serif",
    major_label_font_family="Trebuchet MS, Helvetica Neue, sans-serif",
    legend_font_family="Trebuchet MS, Helvetica Neue, sans-serif",
    value_font_family="Trebuchet MS, Helvetica Neue, sans-serif",
    tooltip_font_size=26,
    tooltip_font_family="Trebuchet MS, Helvetica Neue, sans-serif",
    transition="150ms ease-in",
    value_colors=(),
    guide_stroke_color="#eceef1",
    major_guide_stroke_color="#dde1e6",
)

chart = pygal.XY(
    width=3600,
    height=3600,
    style=custom_style,
    title="pp-basic · pygal · pyplots.ai",
    x_title="Theoretical CDF (Normal Distribution)",
    y_title="Empirical CDF (Steel Rod Tensile Strength)",
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=24,
    dots_size=8,
    stroke=False,
    show_x_guides=True,
    show_y_guides=True,
    xrange=(0, 1),
    range=(0, 1),
    x_label_rotation=0,
    x_labels=[0, 0.2, 0.4, 0.6, 0.8, 1.0],
    y_labels=[0, 0.2, 0.4, 0.6, 0.8, 1.0],
    x_labels_major_every=2,
    y_labels_major_every=2,
    show_minor_x_labels=True,
    show_minor_y_labels=True,
    print_values=False,
    tooltip_border_radius=8,
    tooltip_fancy_mode=True,
    explicit_size=True,
    spacing=30,
    margin_bottom=100,
    margin_top=75,
    margin_left=75,
    margin_right=50,
    truncate_legend=-1,
    dynamic_print_values=True,
    inner_radius=0,
    js=[],
)

# 45° reference line — dashed, drawn first so data sits on top
chart.add(
    "Perfect Normal Fit",
    [(0, 0), (0.25, 0.25), (0.5, 0.5), (0.75, 0.75), (1, 1)],
    stroke=True,
    show_dots=False,
    dots_size=0,
    stroke_dasharray="14, 8",
    stroke_style={"width": 3, "linecap": "round"},
    formatter=lambda x, y: "Reference: y = x",
)

# Good fit band — largest group, subtle Python Blue
chart.add("Good Fit  |Δ| ≤ 0.01  ({} pts)".format(len(good_fit)), good_fit, dots_size=7)

# Mild deviation — medium emphasis
chart.add("Mild Deviation  0.01 < |Δ| ≤ 0.025  ({} pts)".format(len(mild_dev)), mild_dev, dots_size=11)

# Strong deviation — bold accent for maximum visual weight
chart.add("Strong Deviation  |Δ| > 0.025  ({} pts)".format(len(strong_dev)), strong_dev, dots_size=15)

# Dual output: interactive SVG as HTML + static PNG
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
