"""pyplots.ai
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

# Pre-compute labels inline (no helper functions — KISS)
root_labels = []
for k, z in enumerate(roots_of_unity):
    r, i = z.real, z.imag
    if abs(i) < 1e-10:
        val = f"{r:.1f}"
    elif abs(r) < 1e-10:
        val = f"{i:.1f}i"
    else:
        val = f"{r:.1f}{i:+.1f}i"
    root_labels.append(f"ω{k} = {val}")

arb_names = ["z₁", "z₂", "z₃", "z₄", "z₅", "z₆"]
arb_labels = []
for name, z in zip(arb_names, arbitrary, strict=True):
    r, i = z.real, z.imag
    if abs(i) < 1e-10:
        val = f"{r:.1f}"
    elif abs(r) < 1e-10:
        val = f"{i:.1f}i"
    else:
        val = f"{r:.1f}{i:+.1f}i"
    arb_labels.append(f"{name} = {val}")

r_p, i_p = z_product.real, z_product.imag
prod_label = f"z₁·ω₁ = {r_p:.1f}{i_p:+.1f}i"

# Unit circle points (high resolution for smoothness)
theta = np.linspace(0, 2 * np.pi, 180)
unit_circle = [(float(np.cos(t)), float(np.sin(t))) for t in theta]

# Colorblind-safe palette — refined tones for publication quality
BLUE = "#1E5AA8"
ORANGE = "#D4721A"
PURPLE = "#7B3FA0"
GRAY_CIRCLE = "#94A3B8"
DARK = "#0F172A"

# Style — publication-grade refinement
custom_style = Style(
    background="white",
    plot_background="#F8FAFC",
    foreground="#1E293B",
    foreground_strong="#0F172A",
    foreground_subtle="#CBD5E1",
    guide_stroke_color="#E2E8F0",
    guide_stroke_dasharray="3, 6",
    colors=(GRAY_CIRCLE, BLUE, ORANGE, PURPLE, DARK),
    font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    title_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    title_font_size=56,
    label_font_size=34,
    major_label_font_size=32,
    legend_font_size=30,
    legend_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    value_font_size=28,
    tooltip_font_size=24,
    opacity=0.94,
    opacity_hover=1.0,
)

# Chart — square canvas for equal aspect ratio
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
    margin_left=90,
    margin_right=70,
    margin_top=90,
    range=(-3.5, 3.5),
    xrange=(-3.5, 3.5),
    print_values=True,
    print_values_position="top",
    js=[],
)


# Formatter — inline lambda for a+bi display on values
def complex_formatter(z):
    return (
        ""
        if not isinstance(z, (tuple, list)) or z == (0.0, 0.0)
        else (
            f"{z[0]:.1f}" if abs(z[1]) < 1e-10 else f"{z[1]:.1f}i" if abs(z[0]) < 1e-10 else f"{z[0]:.1f}{z[1]:+.1f}i"
        )
    )


# Unit circle (dashed reference — subtle geometric backdrop)
chart.add(
    "Unit Circle",
    unit_circle,
    stroke=True,
    show_dots=False,
    fill=False,
    stroke_style={"width": 2.5, "dasharray": "6, 6", "opacity": 0.45},
)

# Roots of unity — vectors from origin, prominent as mathematical focal point
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
    dots_size=22,
    stroke_style={"width": 6, "linecap": "round", "opacity": 0.85},
    formatter=complex_formatter,
)

# Arbitrary points — vectors from origin with slightly thinner strokes
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
    dots_size=18,
    stroke_style={"width": 3.5, "linecap": "round", "opacity": 0.7},
    formatter=complex_formatter,
)

# Product z₁·ω₁ — dashed vector highlights complex multiplication result
chart.add(
    "z₁·ω₁ (Product)",
    [
        {"value": (0.0, 0.0), "label": ""},
        {"value": (float(z_product.real), float(z_product.imag)), "label": prod_label},
    ],
    stroke=True,
    show_dots=True,
    dots_size=24,
    stroke_style={"width": 6, "dasharray": "10, 5", "linecap": "round", "opacity": 0.92},
    formatter=complex_formatter,
)

# Origin marker — small, no label to reduce clutter at convergence point
chart.add(
    "Origin",
    [{"value": (0.0, 0.0), "label": "O"}],
    stroke=False,
    dots_size=8,
    print_values=False,
    formatter=lambda x: "",
)

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
