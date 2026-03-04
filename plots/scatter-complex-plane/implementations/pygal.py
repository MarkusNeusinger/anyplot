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


# Reusable label formatter for complex numbers (a+bi format)
def format_complex(z):
    """Format a complex number tuple (real, imag) as a+bi string."""
    if not isinstance(z, (tuple, list)) or z == (0.0, 0.0):
        return ""
    r, i = z[0], z[1]
    if abs(i) < 1e-10:
        return f"{r:.1f}"
    if abs(r) < 1e-10:
        return f"{i:.1f}i"
    return f"{r:.1f}{i:+.1f}i"


def make_label(z, prefix=""):
    """Generate a display label for a complex number."""
    txt = format_complex((z.real, z.imag))
    return f"{prefix} = {txt}" if prefix else txt


# Pre-compute labels
root_labels = [make_label(z, f"ω{k}") for k, z in enumerate(roots_of_unity)]
arb_names = ["z₁", "z₂", "z₃", "z₄", "z₅", "z₆"]
arb_labels = [make_label(z, name) for name, z in zip(arb_names, arbitrary, strict=True)]
prod_label = make_label(z_product, "z₁·ω₁")

# Unit circle points
theta = np.linspace(0, 2 * np.pi, 120)
unit_circle = [(float(np.cos(t)), float(np.sin(t))) for t in theta]

# Colorblind-safe palette (blue, orange, purple — no red-green pair)
BLUE = "#2B6CB0"
ORANGE = "#DD6B20"
PURPLE = "#805AD5"
GRAY_CIRCLE = "#A0AEC0"
DARK = "#1A202C"

# Style — refined for publication quality
custom_style = Style(
    background="white",
    plot_background="#F7FAFC",
    foreground="#2D3748",
    foreground_strong="#1A202C",
    foreground_subtle="#E2E8F0",
    guide_stroke_color="#E2E8F0",
    guide_stroke_dasharray="4, 4",
    colors=(GRAY_CIRCLE, BLUE, ORANGE, PURPLE, DARK),
    font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    title_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    title_font_size=58,
    label_font_size=36,
    major_label_font_size=34,
    legend_font_size=32,
    legend_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    value_font_size=30,
    tooltip_font_size=24,
    opacity=0.92,
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
    legend_box_size=26,
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

# Unit circle (dashed reference — subtle backdrop)
chart.add(
    "Unit Circle",
    unit_circle,
    stroke=True,
    show_dots=False,
    fill=False,
    stroke_style={"width": 3, "dasharray": "8, 5", "opacity": 0.5},
)

# Roots of unity - vectors from origin, prominent as mathematical focal point
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
    dots_size=20,
    stroke_style={"width": 7, "linecap": "round", "opacity": 0.9},
    formatter=format_complex,
)

# Arbitrary points - vectors from origin, slightly less prominent
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
    stroke_style={"width": 4, "linecap": "round", "opacity": 0.7},
    formatter=format_complex,
)

# Product z1 * omega1 with dashed vector — highlighted as demonstration of multiplication
chart.add(
    "z₁·ω₁ (Product)",
    [
        {"value": (0.0, 0.0), "label": ""},
        {"value": (float(z_product.real), float(z_product.imag)), "label": prod_label},
    ],
    stroke=True,
    show_dots=True,
    dots_size=22,
    stroke_style={"width": 7, "dasharray": "12, 5", "linecap": "round", "opacity": 0.95},
    formatter=format_complex,
)

# Origin marker — no value label to avoid clutter at (0,0)
chart.add(
    "Origin",
    [{"value": (0.0, 0.0), "label": "0"}],
    stroke=False,
    dots_size=10,
    print_values=False,
    formatter=lambda x: "",
)

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
