""" pyplots.ai
mohr-circle: Mohr's Circle for Stress Analysis
Library: pygal 3.1.0 | Python 3.14.3
Quality: 84/100 | Created: 2026-02-27
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - 2D stress state for a steel beam under combined loading
sigma_x = 80  # Normal stress in x-direction (MPa)
sigma_y = -30  # Normal stress in y-direction (MPa)
tau_xy = 40  # Shear stress on xy-plane (MPa)

# Mohr's Circle parameters
center = (sigma_x + sigma_y) / 2
radius = np.sqrt(((sigma_x - sigma_y) / 2) ** 2 + tau_xy**2)
sigma_1 = center + radius
sigma_2 = center - radius
tau_max = radius
theta_p2 = np.degrees(np.arctan2(tau_xy, (sigma_x - sigma_y) / 2))

# Circle points (200 points for smooth curve)
theta = np.linspace(0, 2 * np.pi, 200)
circle_pts = [(float(center + radius * np.cos(t)), float(radius * np.sin(t))) for t in theta]

# Reference stress points
point_a = (float(sigma_x), float(tau_xy))
point_b = (float(sigma_y), float(-tau_xy))

# 2θp angle arc (larger radius for clear visibility)
arc_r = radius * 0.38
arc_angles = np.linspace(0, np.radians(theta_p2), 40)
arc_pts = [(float(center + arc_r * np.cos(a)), float(arc_r * np.sin(a))) for a in arc_angles]

# Reference lines through center (horizontal and vertical)
padding = 25
y_min = -(radius + padding)
y_max = radius + padding
y_span = y_max - y_min
x_span = y_span * 1.65
x_min = center - x_span / 2
x_max = center + x_span / 2

center_h_line = [(float(x_min), 0.0), (float(x_max), 0.0)]
center_v_line = [(float(center), float(y_min)), (float(center), float(y_max))]

# Colorblind-safe palette: grays for ref lines, then steel blue, orange, teal, indigo, coral
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#2B2B2B",
    foreground_strong="#1A1A1A",
    foreground_subtle="#D0D0D0",
    colors=("#AAAAAA", "#AAAAAA", "#2C5F8A", "#D4761C", "#1A8A7A", "#5B4FA0", "#C44E52"),
    title_font_size=52,
    label_font_size=36,
    major_label_font_size=32,
    legend_font_size=28,
    value_font_size=24,
    tooltip_font_size=24,
    stroke_width=3,
    opacity=0.9,
    opacity_hover=1.0,
)

# Chart with value formatters for engineering notation
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="mohr-circle · pygal · pyplots.ai",
    x_title="Normal Stress σ (MPa)",
    y_title="Shear Stress τ (MPa)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=7,
    dots_size=6,
    stroke=True,
    show_x_guides=True,
    show_y_guides=True,
    truncate_legend=-1,
    range=(y_min, y_max),
    xrange=(x_min, x_max),
    x_value_formatter=lambda x: f"{x:.0f} MPa",
    y_value_formatter=lambda y: f"{y:.0f} MPa",
    print_values=False,
    js=[],
)

# Reference lines through center (plotted first, behind data)
chart.add(
    "σ axis", center_h_line, stroke=True, dots_size=0, stroke_style={"width": 2, "dasharray": "12, 6"}, show_dots=False
)
chart.add(
    f"Center (σ={center:.0f})",
    center_v_line,
    stroke=True,
    dots_size=0,
    stroke_style={"width": 2, "dasharray": "12, 6"},
    show_dots=False,
)

# Mohr's Circle outline
chart.add("Mohr's Circle", circle_pts, stroke=True, dots_size=0, stroke_style={"width": 5}, fill=False)

# Stress points A and B with diameter line
chart.add(
    f"A({sigma_x}, {tau_xy})  B({sigma_y}, {int(-tau_xy)})",
    [
        {"value": point_a, "label": f"A: σx={sigma_x}, τxy={tau_xy} MPa"},
        {"value": point_b, "label": f"B: σy={sigma_y}, τxy={int(-tau_xy)} MPa"},
    ],
    stroke=True,
    dots_size=16,
    stroke_style={"width": 3, "dasharray": "10, 5"},
)

# Principal stresses on horizontal axis
chart.add(
    f"σ₁={sigma_1:.1f}, σ₂={sigma_2:.1f} MPa",
    [
        {"value": (float(sigma_1), 0.0), "label": f"σ₁ = {sigma_1:.1f} MPa (max normal)"},
        {"value": (float(sigma_2), 0.0), "label": f"σ₂ = {sigma_2:.1f} MPa (min normal)"},
    ],
    stroke=False,
    dots_size=18,
)

# Max shear stress at top and bottom of circle
chart.add(
    f"τ_max = ±{tau_max:.1f} MPa",
    [
        {"value": (float(center), float(tau_max)), "label": f"τ_max = +{tau_max:.1f} MPa"},
        {"value": (float(center), float(-tau_max)), "label": f"τ_max = −{tau_max:.1f} MPa"},
    ],
    stroke=False,
    dots_size=18,
)

# 2θp angle arc with increased visibility
chart.add(f"2θp = {theta_p2:.1f}°", arc_pts, stroke=True, dots_size=0, stroke_style={"width": 5})

# Save
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
