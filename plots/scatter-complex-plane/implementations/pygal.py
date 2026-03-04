""" pyplots.ai
scatter-complex-plane: Complex Plane Visualization (Argand Diagram)
Library: pygal 3.1.0 | Python 3.14.3
Quality: 76/100 | Created: 2026-03-04
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - complex numbers: 3rd roots of unity, arbitrary points, and a product
np.random.seed(42)

roots_of_unity = [np.exp(2j * np.pi * k / 3) for k in range(3)]
arbitrary = [2.5 + 1.5j, -1.8 + 2.2j, 1.0 - 2.0j, -0.5 - 1.5j, 3.0 + 0j, 0 + 2.8j]
z_product = arbitrary[0] * roots_of_unity[1]

# Unit circle
theta = np.linspace(0, 2 * np.pi, 120)
unit_circle = [(float(np.cos(t)), float(np.sin(t))) for t in theta]

# Style
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#dddddd",
    guide_stroke_color="#dddddd",
    guide_stroke_dasharray="4, 4",
    colors=(
        "#AAAAAA",  # Unit circle
        "#306998",  # Roots of unity
        "#E74C3C",  # Arbitrary points
        "#2ECC71",  # Product
        "#1A1A1A",  # Origin
    ),
    font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    title_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    title_font_size=56,
    label_font_size=36,
    major_label_font_size=32,
    legend_font_size=30,
    legend_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    value_font_size=24,
    tooltip_font_size=24,
    opacity=0.85,
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


# Format complex number as a+bi string
def fmt(z):
    return (
        f"{z.real:.1f}"
        if abs(z.imag) < 1e-10
        else f"{z.imag:.1f}i"
        if abs(z.real) < 1e-10
        else f"{z.real:.1f}{z.imag:+.1f}i"
    )


# Unit circle (dashed reference)
chart.add(
    "Unit Circle",
    unit_circle,
    stroke=True,
    show_dots=False,
    fill=False,
    stroke_style={"width": 3, "dasharray": "12, 8", "opacity": 0.6},
)

# Roots of unity - vectors from origin with labeled endpoints
roots_series = []
for z in roots_of_unity:
    roots_series.append((0.0, 0.0))
    roots_series.append({"value": (float(z.real), float(z.imag)), "label": f"ω = {fmt(z)}"})
    roots_series.append(None)

chart.add(
    "Roots of Unity (3rd)",
    roots_series,
    stroke=True,
    show_dots=True,
    dots_size=16,
    stroke_style={"width": 4, "linecap": "round"},
    formatter=lambda x: fmt(complex(x[0], x[1])) if isinstance(x, (tuple, list)) and x != (0.0, 0.0) else "",
)

# Arbitrary points - vectors from origin
arb_series = []
labels = ["z₁", "z₂", "z₃", "z₄", "z₅", "z₆"]
for i, z in enumerate(arbitrary):
    arb_series.append((0.0, 0.0))
    arb_series.append({"value": (float(z.real), float(z.imag)), "label": f"{labels[i]} = {fmt(z)}"})
    arb_series.append(None)

chart.add(
    "Arbitrary Points",
    arb_series,
    stroke=True,
    show_dots=True,
    dots_size=14,
    stroke_style={"width": 3, "linecap": "round"},
    formatter=lambda x: fmt(complex(x[0], x[1])) if isinstance(x, (tuple, list)) and x != (0.0, 0.0) else "",
)

# Product z1 * omega1 with dashed vector
chart.add(
    "z₁·ω₁ (Product)",
    [(0.0, 0.0), {"value": (float(z_product.real), float(z_product.imag)), "label": f"z₁·ω₁ = {fmt(z_product)}"}],
    stroke=True,
    show_dots=True,
    dots_size=18,
    stroke_style={"width": 4, "dasharray": "8, 6", "linecap": "round"},
    formatter=lambda x: fmt(complex(x[0], x[1])) if isinstance(x, (tuple, list)) and x != (0.0, 0.0) else "",
)

# Origin marker
chart.add("Origin", [{"value": (0.0, 0.0), "label": "0+0i"}], stroke=False, dots_size=10, formatter=lambda x: "0")

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
