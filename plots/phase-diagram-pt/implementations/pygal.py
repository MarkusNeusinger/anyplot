""" pyplots.ai
phase-diagram-pt: Thermodynamic Phase Diagram (Pressure-Temperature)
Library: pygal 3.1.0 | Python 3.14.3
Quality: 77/100 | Created: 2026-03-14
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - Water phase diagram (realistic values)
# Triple point: 273.16 K, 611.73 Pa (0.00604 atm)
# Critical point: 647.1 K, 22.064 MPa (217.7 atm)
triple_t = 273.16
triple_p = 611.73
critical_t = 647.1
critical_p = 22.064e6

# Solid-gas boundary (sublimation curve) - Clausius-Clapeyron approximation
# From ~200 K up to triple point
sublimation_temps = np.linspace(200, triple_t, 80)
L_sub = 51059  # J/mol (sublimation enthalpy of water)
R = 8.314
sublimation_pressures = triple_p * np.exp((L_sub / R) * (1 / triple_t - 1 / sublimation_temps))

# Liquid-gas boundary (vaporization curve) - from triple point to critical point
vaporization_temps = np.linspace(triple_t, critical_t, 100)
L_vap = 40700  # J/mol (vaporization enthalpy of water)
vaporization_pressures = triple_p * np.exp((L_vap / R) * (1 / triple_t - 1 / vaporization_temps))

# Solid-liquid boundary (melting curve) - water has negative slope
# From triple point upward in pressure
melting_pressures = np.logspace(np.log10(triple_p), np.log10(critical_p * 5), 80)
# Water: dT/dP is negative and very small (~-0.0075 K/atm)
# Using simplified Clausius-Clapeyron for solid-liquid
melting_temps = triple_t - (melting_pressures - triple_p) * 7.5e-8

# Style
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#2d2d2d",
    foreground_strong="#2d2d2d",
    foreground_subtle="#e0e0e0",
    colors=(
        "#306998",  # Solid-Gas (sublimation) - Python Blue
        "#c45a00",  # Liquid-Gas (vaporization) - Orange
        "#0e7c6b",  # Solid-Liquid (melting) - Teal
        "#d62728",  # Triple point - Red
        "#7b2d8e",  # Critical point - Purple
    ),
    font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    title_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    title_font_size=56,
    label_font_size=38,
    major_label_font_size=34,
    value_font_size=28,
    legend_font_size=36,
    legend_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    label_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    major_label_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    value_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    stroke_width=5,
    opacity=0.9,
    opacity_hover=1.0,
    guide_stroke_color="#e0e0e0",
    guide_stroke_dasharray="3,3",
    tooltip_font_size=28,
    tooltip_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    tooltip_border_radius=8,
)

# Chart
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="Water Phase Diagram · phase-diagram-pt · pygal · pyplots.ai",
    x_title="Temperature (K)",
    y_title="Pressure (Pa)",
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=28,
    dots_size=4,
    stroke=True,
    show_x_guides=True,
    show_y_guides=True,
    x_label_rotation=0,
    logarithmic=True,
    explicit_size=True,
    truncate_legend=-1,
    spacing=20,
    margin=30,
    margin_bottom=140,
    margin_left=100,
    tooltip_fancy_mode=True,
    interpolate="cubic",
    interpolation_precision=200,
)

# Sublimation curve (Solid-Gas boundary)
sublimation_points = [(float(t), float(p)) for t, p in zip(sublimation_temps, sublimation_pressures, strict=True)]
chart.add("Solid ↔ Gas (Sublimation)", sublimation_points, show_dots=False, stroke_style={"width": 6})

# Vaporization curve (Liquid-Gas boundary)
vaporization_points = [(float(t), float(p)) for t, p in zip(vaporization_temps, vaporization_pressures, strict=True)]
chart.add("Liquid ↔ Gas (Vaporization)", vaporization_points, show_dots=False, stroke_style={"width": 6})

# Melting curve (Solid-Liquid boundary) - nearly vertical, negative slope for water
melting_points = [(float(t), float(p)) for t, p in zip(melting_temps, melting_pressures, strict=True)]
chart.add("Solid ↔ Liquid (Melting)", melting_points, show_dots=False, stroke_style={"width": 6})

# Triple point marker
chart.add(
    f"Triple Point ({triple_t} K, {triple_p:.0f} Pa)",
    [{"value": (float(triple_t), float(triple_p)), "label": "Triple Point: 273.16 K, 611.73 Pa"}],
    dots_size=20,
    stroke=False,
)

# Critical point marker
chart.add(
    f"Critical Point ({critical_t} K, {critical_p / 1e6:.1f} MPa)",
    [{"value": (float(critical_t), float(critical_p)), "label": "Critical Point: 647.1 K, 22.064 MPa"}],
    dots_size=20,
    stroke=False,
)

# Save
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
