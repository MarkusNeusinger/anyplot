""" pyplots.ai
phase-diagram-pt: Thermodynamic Phase Diagram (Pressure-Temperature)
Library: pygal 3.1.0 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-14
"""

import xml.etree.ElementTree as ET

import cairosvg
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
sublimation_temps = np.linspace(200, triple_t, 80)
L_sub = 51059  # J/mol (sublimation enthalpy of water)
R = 8.314
sublimation_pressures = triple_p * np.exp((L_sub / R) * (1 / triple_t - 1 / sublimation_temps))

# Liquid-gas boundary (vaporization curve) - from triple point to critical point
vaporization_temps = np.linspace(triple_t, critical_t, 100)
L_vap = 40700  # J/mol (vaporization enthalpy of water)
vaporization_pressures = triple_p * np.exp((L_vap / R) * (1 / triple_t - 1 / vaporization_temps))

# Solid-liquid boundary (melting curve) - water has negative slope
melting_pressures = np.logspace(np.log10(triple_p), np.log10(critical_p * 5), 80)
melting_temps = triple_t - (melting_pressures - triple_p) * 7.5e-8


# Pressure formatter for readable y-axis labels and tooltips
def format_pressure(val):
    if isinstance(val, (list, tuple)):
        t, p = val
        return f"{t:.0f} K, {format_pressure(p)}"
    p = val
    if p >= 1e6:
        v = p / 1e6
        return f"{v:.0f} MPa" if v == int(v) else f"{v:.1f} MPa"
    if p >= 1e3:
        v = p / 1e3
        return f"{v:.0f} kPa" if v == int(v) else f"{v:.1f} kPa"
    if p >= 1:
        return f"{p:.0f} Pa"
    return f"{p:.1f} Pa"


# Style - publication-quality palette with visual hierarchy
custom_style = Style(
    background="white",
    plot_background="#f8f9fb",
    foreground="#16213e",
    foreground_strong="#16213e",
    foreground_subtle="#e2e4e8",
    colors=(
        "#1d4ed8",  # Solid-Gas (sublimation) - Deep Blue
        "#ea580c",  # Liquid-Gas (vaporization) - Burnt Orange
        "#0f766e",  # Solid-Liquid (melting) - Deep Teal
        "#be123c",  # Triple point - Deep Rose
        "#6d28d9",  # Critical point - Deep Violet
    ),
    font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    title_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    title_font_size=58,
    label_font_size=36,
    major_label_font_size=32,
    value_font_size=26,
    legend_font_size=30,
    legend_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    label_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    major_label_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    value_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    stroke_width=5,
    opacity=0.92,
    opacity_hover=1.0,
    guide_stroke_color="#eaedf0",
    guide_stroke_dasharray="6,6",
    tooltip_font_size=26,
    tooltip_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    tooltip_border_radius=8,
)

# Chart configuration leveraging pygal's distinctive features
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="Water Phase Diagram · phase-diagram-pt · pygal · pyplots.ai",
    x_title="Temperature (K)",
    y_title="Pressure (Pa)",
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=22,
    dots_size=2,
    stroke=True,
    show_x_guides=True,
    show_y_guides=True,
    x_label_rotation=0,
    logarithmic=True,
    explicit_size=True,
    truncate_legend=-1,
    spacing=20,
    margin=40,
    margin_bottom=120,
    margin_left=220,
    margin_right=160,
    tooltip_fancy_mode=True,
    tooltip_border_radius=8,
    interpolate="cubic",
    interpolation_precision=200,
    xrange=(180, 670),
    secondary_range=(0.1, critical_p * 20),
    print_values=False,
    human_readable=True,
    x_value_formatter=lambda x: f"{x:.0f} K",
    value_formatter=format_pressure,
    y_labels=[1, 100, 1e4, 1e6, 1e8],
    y_label_rotation=0,
)

# Sublimation curve (Solid-Gas boundary) with pygal metadata dicts
sublimation_points = [
    {"value": (float(t), float(p)), "label": f"Sublimation: {t:.0f} K, {format_pressure(p)}"}
    for t, p in zip(sublimation_temps[::4], sublimation_pressures[::4], strict=True)
]
chart.add(
    "Solid ↔ Gas (Sublimation)",
    sublimation_points,
    show_dots=False,
    stroke_style={"width": 8, "linecap": "round", "linejoin": "round"},
    formatter=format_pressure,
)

# Vaporization curve (Liquid-Gas boundary)
vaporization_points = [
    {"value": (float(t), float(p)), "label": f"Vaporization: {t:.0f} K, {format_pressure(p)}"}
    for t, p in zip(vaporization_temps[::5], vaporization_pressures[::5], strict=True)
]
chart.add(
    "Liquid ↔ Gas (Vaporization)",
    vaporization_points,
    show_dots=False,
    stroke_style={"width": 8, "linecap": "round", "linejoin": "round"},
    formatter=format_pressure,
)

# Melting curve (Solid-Liquid boundary) - nearly vertical, negative slope for water
melting_points = [
    {"value": (float(t), float(p)), "label": f"Melting: {t:.2f} K, {format_pressure(p)}"}
    for t, p in zip(melting_temps[::4], melting_pressures[::4], strict=True)
]
chart.add(
    "Solid ↔ Liquid (Melting)",
    melting_points,
    show_dots=False,
    stroke_style={"width": 8, "linecap": "round", "linejoin": "round"},
    formatter=format_pressure,
)

# Triple point marker with rich metadata
chart.add(
    f"Triple Point ({triple_t} K, {triple_p:.0f} Pa)",
    [
        {
            "value": (float(triple_t), float(triple_p)),
            "label": "Triple Point — all three phases coexist\n273.16 K, 611.73 Pa",
            "color": "#be123c",
        }
    ],
    dots_size=18,
    stroke=False,
    formatter=format_pressure,
)

# Critical point marker with rich metadata
chart.add(
    f"Critical Point ({critical_t} K, {critical_p / 1e6:.1f} MPa)",
    [
        {
            "value": (float(critical_t), float(critical_p)),
            "label": "Critical Point — liquid-gas distinction vanishes\n647.1 K, 22.064 MPa",
            "color": "#6d28d9",
        }
    ],
    dots_size=18,
    stroke=False,
    formatter=format_pressure,
)

# Render SVG and add phase region labels via post-processing
svg_string = chart.render(is_unicode=True)
root = ET.fromstring(svg_string)

# Phase region labels with colors keyed to boundaries for storytelling
phase_labels = [
    {"text": "SOLID", "x": "1050", "y": "580", "size": "78", "color": "#0f766e", "opacity": "0.40"},
    {"text": "LIQUID", "x": "2650", "y": "520", "size": "78", "color": "#ea580c", "opacity": "0.40"},
    {"text": "GAS", "x": "2900", "y": "1850", "size": "78", "color": "#1d4ed8", "opacity": "0.40"},
    {"text": "SUPERCRITICAL", "x": "3800", "y": "350", "size": "52", "color": "#6d28d9", "opacity": "0.35"},
    {"text": "FLUID", "x": "3930", "y": "420", "size": "52", "color": "#6d28d9", "opacity": "0.35"},
]

for label in phase_labels:
    text_elem = ET.SubElement(root, "{http://www.w3.org/2000/svg}text")
    text_elem.set("x", label["x"])
    text_elem.set("y", label["y"])
    text_elem.set(
        "style",
        f"font-family: DejaVu Sans, Helvetica, Arial, sans-serif; "
        f"font-size: {label['size']}px; "
        f"fill: {label['color']}; "
        f"font-weight: 700; "
        f"letter-spacing: 5px; "
        f"opacity: {label['opacity']}; "
        f"text-anchor: middle;",
    )
    text_elem.text = label["text"]

# Write modified SVG and convert to PNG
modified_svg = ET.tostring(root, encoding="unicode")
with open("plot.svg", "w") as f:
    f.write(modified_svg)

cairosvg.svg2png(bytestring=modified_svg.encode("utf-8"), write_to="plot.png", output_width=4800, output_height=2700)

# Interactive HTML with pygal's native tooltip support
chart.render_to_file("plot.html")
