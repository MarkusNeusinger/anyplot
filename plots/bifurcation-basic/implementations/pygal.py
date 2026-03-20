"""pyplots.ai
bifurcation-basic: Bifurcation Diagram for Dynamical Systems
Library: pygal | Python 3.13
Quality: pending | Created: 2026-03-20
"""

import numpy as np
import pygal
from pygal.style import Style


# Data — logistic map x(n+1) = r * x(n) * (1 - x(n))
np.random.seed(42)
r_values = np.linspace(2.5, 4.0, 1000)
transient = 200
iterations = 100
x0 = 0.1 + np.random.uniform(-0.01, 0.01)

r_all = []
x_all = []

for r in r_values:
    x = x0
    for _ in range(transient):
        x = r * x * (1.0 - x)
    for _ in range(iterations):
        x = r * x * (1.0 - x)
        r_all.append(r)
        x_all.append(x)

r_all = np.array(r_all)
x_all = np.array(x_all)

# Downsample for pygal performance — keep ~20k points via stratified sampling
max_points = 20000
if len(r_all) > max_points:
    indices = np.random.choice(len(r_all), max_points, replace=False)
    indices.sort()
    r_all = r_all[indices]
    x_all = x_all[indices]

# Style
font = "DejaVu Sans, Helvetica, Arial, sans-serif"
custom_style = Style(
    background="white",
    plot_background="#fafafa",
    foreground="#2a2a2a",
    foreground_strong="#2a2a2a",
    foreground_subtle="#e0e0e0",
    guide_stroke_color="#e0e0e0",
    guide_stroke_dasharray="4, 4",
    colors=("#306998",),
    font_family=font,
    title_font_family=font,
    title_font_size=56,
    label_font_size=42,
    major_label_font_size=38,
    legend_font_size=34,
    legend_font_family=font,
    value_font_size=28,
    tooltip_font_size=28,
    tooltip_font_family=font,
    opacity=0.25,
    opacity_hover=0.8,
)

# Chart
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="bifurcation-basic \u00b7 pygal \u00b7 pyplots.ai",
    x_title="Growth Rate Parameter (r)",
    y_title="Steady-State Population (x)",
    show_legend=False,
    stroke=False,
    dots_size=1.5,
    show_x_guides=True,
    show_y_guides=True,
    x_value_formatter=lambda v: f"{v:.2f}",
    value_formatter=lambda v: f"{v:.3f}",
    margin_bottom=80,
    margin_left=60,
    margin_right=40,
    margin_top=50,
    xrange=(2.5, 4.0),
    range=(0.0, 1.0),
    x_labels_major_count=7,
    y_labels_major_count=6,
    print_values=False,
    print_zeroes=False,
    js=[],
)

# Add bifurcation data as XY scatter points
points = [(float(r), float(x)) for r, x in zip(r_all, x_all, strict=True)]
chart.add("Logistic Map", points, stroke=False)

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
