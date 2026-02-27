""" pyplots.ai
mohr-circle: Mohr's Circle for Stress Analysis
Library: pygal 3.1.0 | Python 3.14.3
Quality: 79/100 | Created: 2026-02-27
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

# 2θp angle arc (from horizontal axis to line from center to point A)
arc_r = radius * 0.22
arc_angles = np.linspace(0, np.radians(theta_p2), 30)
arc_pts = [(float(center + arc_r * np.cos(a)), float(arc_r * np.sin(a))) for a in arc_angles]

# Style
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#cccccc",
    colors=("#306998", "#E74C3C", "#2ECC71", "#F39C12", "#8E44AD", "#999999"),
    title_font_size=52,
    label_font_size=36,
    major_label_font_size=32,
    legend_font_size=28,
    value_font_size=24,
    tooltip_font_size=24,
    stroke_width=3,
    opacity=0.85,
    opacity_hover=1.0,
)

# Axis ranges for approximately equal aspect ratio on 4800x2700
padding = 25
y_min = -(radius + padding)
y_max = radius + padding
y_span = y_max - y_min
x_span = y_span * 1.65
x_min = center - x_span / 2
x_max = center + x_span / 2

# Chart
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="mohr-circle · pygal · pyplots.ai",
    x_title="Normal Stress σ (MPa)",
    y_title="Shear Stress τ (MPa)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=5,
    dots_size=6,
    stroke=True,
    show_x_guides=True,
    show_y_guides=True,
    truncate_legend=-1,
    range=(y_min, y_max),
    xrange=(x_min, x_max),
)

# Mohr's Circle outline
chart.add("Mohr's Circle", circle_pts, stroke=True, dots_size=0, stroke_style={"width": 5})

# Stress points A and B with diameter line
chart.add(
    f"A({sigma_x}, {tau_xy})  B({sigma_y}, {-tau_xy})",
    [
        {"value": point_a, "label": f"A(σx={sigma_x}, τxy={tau_xy})"},
        {"value": point_b, "label": f"B(σy={sigma_y}, τxy={-tau_xy})"},
    ],
    stroke=True,
    dots_size=14,
    stroke_style={"width": 3, "dasharray": "8, 4"},
)

# Principal stresses on horizontal axis
chart.add(
    f"σ₁ = {sigma_1:.1f}, σ₂ = {sigma_2:.1f} MPa",
    [
        {"value": (float(sigma_1), 0.0), "label": f"σ₁ = {sigma_1:.1f} MPa"},
        {"value": (float(sigma_2), 0.0), "label": f"σ₂ = {sigma_2:.1f} MPa"},
    ],
    stroke=False,
    dots_size=16,
)

# Max shear stress at top and bottom of circle
chart.add(
    f"τ_max = ±{tau_max:.1f} MPa",
    [
        {"value": (float(center), float(tau_max)), "label": f"τ_max = +{tau_max:.1f} MPa"},
        {"value": (float(center), float(-tau_max)), "label": f"τ_max = −{tau_max:.1f} MPa"},
    ],
    stroke=False,
    dots_size=16,
)

# 2θp angle arc
chart.add(f"2θp = {theta_p2:.1f}°", arc_pts, stroke=True, dots_size=0, stroke_style={"width": 4})

# Save
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
