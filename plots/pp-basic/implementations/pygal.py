"""pyplots.ai
pp-basic: Probability-Probability (P-P) Plot
Library: pygal 3.1.0 | Python 3.14.3
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

# Deviation from perfect fit
deviation = empirical_cdf - theoretical_cdf

# Three-tier classification for visual hierarchy
close_points = []
mild_points = []
strong_points = []
for i in range(n):
    t_cdf = float(theoretical_cdf[i])
    e_cdf = float(empirical_cdf[i])
    d = deviation[i]
    tooltip = "Sample #{}: {:.0f} MPa, Δ={:+.3f}".format(i + 1, observed[i], d)
    point = {"value": (t_cdf, e_cdf), "label": tooltip}
    if abs(d) <= 0.015:
        close_points.append(point)
    elif abs(d) <= 0.04:
        mild_points.append(point)
    else:
        strong_points.append(point)

# Refined style — colorblind-safe palette with blue-orange-teal triad
custom_style = Style(
    background="#f7f9fb",
    plot_background="#ffffff",
    foreground="#3a3a3a",
    foreground_strong="#1a1a1a",
    foreground_subtle="#d8dde3",
    opacity=".8",
    opacity_hover="1",
    colors=("#a0b4c4", "#306998", "#e69f00", "#009e73"),
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=42,
    legend_font_size=36,
    value_font_size=32,
    stroke_width=2,
    title_font_family="Trebuchet MS, Helvetica, sans-serif",
    label_font_family="Trebuchet MS, Helvetica, sans-serif",
    major_label_font_family="Trebuchet MS, Helvetica, sans-serif",
    legend_font_family="Trebuchet MS, Helvetica, sans-serif",
    value_font_family="Trebuchet MS, Helvetica, sans-serif",
    tooltip_font_size=28,
    tooltip_font_family="Trebuchet MS, Helvetica, sans-serif",
    transition="200ms ease-in",
    value_colors=(),
    guide_stroke_color="#e8ecf0",
    major_guide_stroke_color="#d0d6dc",
)

# Square XY chart
chart = pygal.XY(
    width=3600,
    height=3600,
    style=custom_style,
    title="pp-basic · pygal · pyplots.ai",
    x_title="Theoretical CDF (Normal Distribution)",
    y_title="Empirical CDF (Steel Rod Tensile Strength)",
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=26,
    dots_size=9,
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
    tooltip_border_radius=10,
    explicit_size=True,
    spacing=35,
    margin_bottom=130,
    margin_top=80,
    margin_left=80,
    truncate_legend=-1,
    dynamic_print_values=True,
    js=[],
)

# 45° reference line — drawn first to sit behind data
chart.add(
    "Perfect Normal Fit",
    [(0, 0), (0.2, 0.2), (0.4, 0.4), (0.6, 0.6), (0.8, 0.8), (1, 1)],
    stroke=True,
    show_dots=False,
    dots_size=0,
    stroke_dasharray="16, 10",
    stroke_style={"width": 3, "linecap": "round"},
)

# Close-to-diagonal points (good fit region)
chart.add("Good Fit (|Δ| ≤ 0.015)", close_points, dots_size=7)

# Mild deviation
chart.add("Mild Deviation (0.015 < |Δ| ≤ 0.04)", mild_points, dots_size=10)

# Strong deviation — highlighted in teal for maximum accessibility
chart.add("Strong Deviation (|Δ| > 0.04)", strong_points, dots_size=14)

# Save outputs
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
