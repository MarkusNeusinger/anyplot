""" pyplots.ai
mohr-circle: Mohr's Circle for Stress Analysis
Library: pygal 3.1.0 | Python 3.14.3
Quality: 85/100 | Created: 2026-02-27
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

# 2θp angle arc (large radius for clear visibility)
arc_r = radius * 0.45
arc_angles = np.linspace(0, np.radians(theta_p2), 40)
arc_pts = [(float(center + arc_r * np.cos(a)), float(arc_r * np.sin(a))) for a in arc_angles]

# Axis ranges - tight around circle with balanced padding
padding = 20
y_min = -(radius + padding)
y_max = radius + padding
x_min = float(sigma_2 - padding)
x_max = float(sigma_1 + padding)

# Reference lines through center (combined into one series)
ref_lines = [
    (float(x_min), 0.0),
    (float(x_max), 0.0),
    None,
    (float(center), float(y_min)),
    (float(center), float(y_max)),
]

# Refined colorblind-safe palette with strong contrast
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#2B2B2B",
    foreground_strong="#1A1A1A",
    foreground_subtle="#D8D8D8",
    colors=("#B0B0B0", "#1B6692", "#D4761C", "#0E7C6B", "#4A3D8F", "#B5342B"),
    title_font_size=48,
    label_font_size=34,
    major_label_font_size=30,
    legend_font_size=26,
    value_font_size=22,
    tooltip_font_size=22,
    stroke_width=3,
    opacity=0.92,
    opacity_hover=1.0,
)

# Square canvas (3600×3600) for guaranteed equal aspect ratio — circle appears as true circle
chart = pygal.XY(
    width=3600,
    height=3600,
    style=custom_style,
    title="mohr-circle · pygal · pyplots.ai",
    x_title="Normal Stress σ (MPa)",
    y_title="Shear Stress τ (MPa)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
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
    f"Reference axes (σ={center:.0f} MPa)",
    ref_lines,
    stroke=True,
    dots_size=0,
    stroke_style={"width": 2, "dasharray": "12, 6"},
    show_dots=False,
    allow_interruptions=True,
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

# 2θp angle arc with bold stroke for clear visibility
chart.add(f"2θp = {theta_p2:.1f}°", arc_pts, stroke=True, dots_size=0, stroke_style={"width": 8})

# Save
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
