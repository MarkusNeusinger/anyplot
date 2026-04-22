""" pyplots.ai
nyquist-basic: Nyquist Plot for Control Systems
Library: pygal 3.1.0 | Python 3.14.3
Quality: 76/100 | Created: 2026-03-20
"""

import math

import numpy as np
import pygal
from pygal.style import Style


# Data — Transfer function G(s) = 2 / [s(s+1)(s+2)]
omega = np.logspace(-2, 2, 800)
s = 1j * omega
G = 2.0 / (s * (s + 1) * (s + 2))

real_part = G.real
imag_part = G.imag

# Mirror for negative frequencies (Nyquist contour reflection)
real_mirror = real_part[::-1]
imag_mirror = -imag_part[::-1]

# Custom style
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#cccccc",
    colors=(
        "#306998",  # Nyquist curve (positive freq)
        "#7BA1C7",  # Nyquist curve (negative freq)
        "#E74C3C",  # Critical point
        "#AAAAAA",  # Unit circle
        "#306998",  # Frequency annotations (same as positive curve)
    ),
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=42,
    legend_font_size=42,
    tooltip_font_size=36,
    stroke_width=4,
    opacity=0.9,
    opacity_hover=0.95,
)

# Chart
chart = pygal.XY(
    width=4800,
    height=4800,
    style=custom_style,
    title="nyquist-basic · pygal · pyplots.ai",
    x_title="Real",
    y_title="Imaginary",
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=36,
    dots_size=3,
    stroke=True,
    show_x_guides=True,
    show_y_guides=True,
    explicit_size=True,
    range=(-2.5, 2.5),
    xrange=(-2.5, 2.5),
    value_formatter=lambda x: f"{x:.3f}",
)

# Positive frequency curve with tooltips showing frequency values
step = 4
nyquist_positive = [
    {"value": (float(real_part[i]), float(imag_part[i])), "label": f"ω = {omega[i]:.3f} rad/s"}
    for i in range(0, len(omega), step)
]
chart.add("G(jω), ω ≥ 0", nyquist_positive, show_dots=False, stroke_style={"width": 5})

# Negative frequency curve (mirror) with tooltips
nyquist_negative = [
    {"value": (float(real_mirror[i]), float(imag_mirror[i])), "label": f"ω = -{omega[len(omega) - 1 - i]:.3f} rad/s"}
    for i in range(0, len(omega), step)
]
chart.add("G(jω), ω < 0", nyquist_negative, show_dots=False, stroke_style={"width": 4, "dasharray": "12,6"})

# Critical point (-1, 0)
chart.add(
    "Critical Point (-1, 0)", [{"value": (-1.0, 0.0), "label": "Critical Point: (-1, 0)"}], stroke=False, dots_size=24
)

# Unit circle
circle_points = [
    {"value": (math.cos(math.radians(a)), math.sin(math.radians(a))), "label": f"{a}°"} for a in range(0, 361, 3)
]
chart.add("Unit Circle", circle_points, stroke=True, show_dots=False, stroke_style={"width": 3, "dasharray": "8,6"})

# Frequency annotations at key points along the curve (▶ markers with labels)
freq_targets = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
freq_annotations = []
for ft in freq_targets:
    idx = int(np.argmin(np.abs(omega - ft)))
    freq_annotations.append({"value": (float(real_part[idx]), float(imag_part[idx])), "label": f"ω = {ft} rad/s"})
chart.add("Frequency ω (rad/s)", freq_annotations, stroke=False, dots_size=12)

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
