""" pyplots.ai
scatter-complex-plane: Complex Plane Visualization (Argand Diagram)
Library: pygal 3.1.0 | Python 3.14.3
Quality: 79/100 | Created: 2026-03-04
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - complex numbers: 3rd roots of unity, arbitrary points, and a product
np.random.seed(42)

roots_of_unity = [np.exp(2j * np.pi * k / 3) for k in range(3)]
arbitrary = [2.5 + 1.5j, -1.8 + 2.2j, 1.0 - 2.0j, -0.5 - 1.5j, 3.0 + 0j, 0 + 2.8j]
z_product = arbitrary[0] * roots_of_unity[1]

# Pre-compute labels (a+bi format) for all complex numbers
root_labels = []
for z in roots_of_unity:
    if abs(z.imag) < 1e-10:
        root_labels.append(f"ω = {z.real:.1f}")
    elif abs(z.real) < 1e-10:
        root_labels.append(f"ω = {z.imag:.1f}i")
    else:
        root_labels.append(f"ω = {z.real:.1f}{z.imag:+.1f}i")

arb_names = ["z₁", "z₂", "z₃", "z₄", "z₅", "z₆"]
arb_labels = []
for name, z in zip(arb_names, arbitrary, strict=True):
    if abs(z.imag) < 1e-10:
        arb_labels.append(f"{name} = {z.real:.1f}")
    elif abs(z.real) < 1e-10:
        arb_labels.append(f"{name} = {z.imag:.1f}i")
    else:
        arb_labels.append(f"{name} = {z.real:.1f}{z.imag:+.1f}i")

if abs(z_product.imag) < 1e-10:
    prod_label = f"z₁·ω₁ = {z_product.real:.1f}"
elif abs(z_product.real) < 1e-10:
    prod_label = f"z₁·ω₁ = {z_product.imag:.1f}i"
else:
    prod_label = f"z₁·ω₁ = {z_product.real:.1f}{z_product.imag:+.1f}i"

# Unit circle points
theta = np.linspace(0, 2 * np.pi, 120)
unit_circle = [(float(np.cos(t)), float(np.sin(t))) for t in theta]

# Colorblind-safe palette (blue, orange, purple — no red-green pair)
BLUE = "#306998"
ORANGE = "#E67E22"
PURPLE = "#8E44AD"
GRAY_CIRCLE = "#888888"
DARK = "#1A1A1A"

# Style
custom_style = Style(
    background="white",
    plot_background="#FAFAFA",
    foreground="#2C3E50",
    foreground_strong="#2C3E50",
    foreground_subtle="#E0E0E0",
    guide_stroke_color="#E0E0E0",
    guide_stroke_dasharray="3, 3",
    colors=(GRAY_CIRCLE, BLUE, ORANGE, PURPLE, DARK),
    font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    title_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    title_font_size=56,
    label_font_size=36,
    major_label_font_size=32,
    legend_font_size=30,
    legend_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    value_font_size=28,
    tooltip_font_size=24,
    opacity=0.9,
    opacity_hover=1.0,
)

# Chart - square for equal aspect ratio
chart = pygal.XY(
    width=3600,
    height=3600,
    style=custom_style,
    title="scatter-complex-plane · pygal · pyplots.ai",
    x_title="Real Axis",
    y_title="Imaginary Axis",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=5,
    legend_box_size=24,
    stroke=False,
    dots_size=14,
    show_x_guides=True,
    show_y_guides=True,
    truncate_legend=-1,
    margin_bottom=120,
    margin_left=80,
    margin_right=60,
    margin_top=80,
    range=(-3.5, 3.5),
    xrange=(-3.5, 3.5),
    print_values=True,
    print_values_position="top",
    js=[],
)

# Unit circle (dashed reference)
chart.add(
    "Unit Circle",
    unit_circle,
    stroke=True,
    show_dots=False,
    fill=False,
    stroke_style={"width": 4, "dasharray": "10, 6", "opacity": 0.7},
)

# Roots of unity - vectors from origin with labeled endpoints
roots_series = []
for i, z in enumerate(roots_of_unity):
    roots_series.append({"value": (0.0, 0.0), "label": ""})
    roots_series.append({"value": (float(z.real), float(z.imag)), "label": root_labels[i]})
    roots_series.append(None)

chart.add(
    "Roots of Unity (3rd)",
    roots_series,
    stroke=True,
    show_dots=True,
    dots_size=18,
    stroke_style={"width": 6, "linecap": "round", "opacity": 0.85},
    formatter=lambda x: (
        ""
        if not isinstance(x, (tuple, list)) or x == (0.0, 0.0)
        else f"{x[0]:.1f}"
        if abs(x[1]) < 1e-10
        else f"{x[1]:.1f}i"
        if abs(x[0]) < 1e-10
        else f"{x[0]:.1f}{x[1]:+.1f}i"
    ),
)

# Arbitrary points - vectors from origin
arb_series = []
for i, z in enumerate(arbitrary):
    arb_series.append({"value": (0.0, 0.0), "label": ""})
    arb_series.append({"value": (float(z.real), float(z.imag)), "label": arb_labels[i]})
    arb_series.append(None)

chart.add(
    "Arbitrary Points",
    arb_series,
    stroke=True,
    show_dots=True,
    dots_size=16,
    stroke_style={"width": 5, "linecap": "round", "opacity": 0.8},
    formatter=lambda x: (
        ""
        if not isinstance(x, (tuple, list)) or x == (0.0, 0.0)
        else f"{x[0]:.1f}"
        if abs(x[1]) < 1e-10
        else f"{x[1]:.1f}i"
        if abs(x[0]) < 1e-10
        else f"{x[0]:.1f}{x[1]:+.1f}i"
    ),
)

# Product z1 * omega1 with dashed vector
chart.add(
    "z₁·ω₁ (Product)",
    [
        {"value": (0.0, 0.0), "label": ""},
        {"value": (float(z_product.real), float(z_product.imag)), "label": prod_label},
    ],
    stroke=True,
    show_dots=True,
    dots_size=20,
    stroke_style={"width": 6, "dasharray": "10, 6", "linecap": "round", "opacity": 0.9},
    formatter=lambda x: (
        ""
        if not isinstance(x, (tuple, list)) or x == (0.0, 0.0)
        else f"{x[0]:.1f}"
        if abs(x[1]) < 1e-10
        else f"{x[1]:.1f}i"
        if abs(x[0]) < 1e-10
        else f"{x[0]:.1f}{x[1]:+.1f}i"
    ),
)

# Origin marker
chart.add("Origin", [{"value": (0.0, 0.0), "label": "0"}], stroke=False, dots_size=10, formatter=lambda x: "")

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
