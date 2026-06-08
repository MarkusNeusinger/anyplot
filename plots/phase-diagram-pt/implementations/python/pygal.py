"""anyplot.ai
phase-diagram-pt: Thermodynamic Phase Diagram (Pressure-Temperature)
Library: pygal | Python 3.14
Quality: pending | Updated: 2026-06-08
"""

# Ensure we import the installed pygal package, not this file
import importlib.util
import os
import sys
import xml.etree.ElementTree as ET

import cairosvg
import numpy as np


pygal_spec = importlib.util.find_spec("pygal")
if pygal_spec and pygal_spec.origin != __file__:
    import pygal
    from pygal.style import Style
else:
    _cwd = os.getcwd()
    sys.path = [p for p in sys.path if os.path.abspath(p) != _cwd]
    try:
        import pygal
        from pygal.style import Style
    finally:
        sys.path.insert(0, _cwd)

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — theme-independent categorical colors
IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Water phase diagram (physically accurate constants)
triple_t = 273.16  # K
triple_p = 611.73  # Pa
critical_t = 647.1  # K
critical_p = 22.064e6  # Pa
R = 8.314  # J/(mol·K)

# Sublimation curve (Solid-Gas): from 200 K to triple point
sublimation_temps = np.linspace(200, triple_t, 80)
L_sub = 51059  # J/mol — sublimation enthalpy of water
sublimation_pressures = triple_p * np.exp((L_sub / R) * (1 / triple_t - 1 / sublimation_temps))

# Vaporization curve (Liquid-Gas): from triple point to critical point
vaporization_temps = np.linspace(triple_t, critical_t, 100)
L_vap = 40700  # J/mol — vaporization enthalpy of water
vaporization_pressures = triple_p * np.exp((L_vap / R) * (1 / triple_t - 1 / vaporization_temps))

# Melting curve (Solid-Liquid): water has anomalous negative slope
melting_pressures = np.logspace(np.log10(triple_p), np.log10(critical_p * 5), 80)
melting_temps = triple_t - (melting_pressures - triple_p) * 7.5e-8


def format_pressure(val):
    if isinstance(val, (list, tuple)):
        t, p = val
        return f"{t:.0f} K, {format_pressure(p)}"
    p = val
    if p >= 1e6:
        return f"{p / 1e6:.1f} MPa"
    if p >= 1e3:
        return f"{p / 1e3:.1f} kPa"
    return f"{p:.1f} Pa"


# Title: 46 chars < 67 baseline → no scaling needed, use default 66
title = "phase-diagram-pt · python · pygal · anyplot.ai"

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT_PALETTE,
    font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    title_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    value_font_size=36,
    legend_font_size=44,
    legend_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    label_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    major_label_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    value_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    stroke_width=5,
    opacity=0.92,
    opacity_hover=1.0,
    guide_stroke_color=INK_MUTED,
    guide_stroke_dasharray="6,6",
    tooltip_font_size=36,
    tooltip_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    tooltip_border_radius=8,
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title=title,
    x_title="Temperature (K)",
    y_title="Pressure (Pa)",
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=22,
    dots_size=2,
    stroke=True,
    show_x_guides=True,
    show_y_guides=True,
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
    xrange=(180, 720),
    print_values=False,
    human_readable=True,
    x_value_formatter=lambda x: f"{x:.0f} K",
    value_formatter=format_pressure,
    y_labels=[1, 100, 1e4, 1e6, 1e8],
    y_label_rotation=0,
)

# Sublimation curve (Solid-Gas boundary) — Imprint position 1: brand green
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

# Vaporization curve (Liquid-Gas boundary) — Imprint position 2: lavender
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

# Melting curve (Solid-Liquid boundary) — Imprint position 3: blue; water's anomalous negative slope
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

# Triple point — Imprint matte red (#AE3030): distinctive thermodynamic landmark
chart.add(
    f"Triple Point ({triple_t} K, {triple_p:.0f} Pa)",
    [
        {
            "value": (float(triple_t), float(triple_p)),
            "label": "Triple Point — all three phases coexist\n273.16 K, 611.73 Pa",
            "color": "#AE3030",
        }
    ],
    dots_size=18,
    stroke=False,
    formatter=format_pressure,
)

# Critical point — Imprint ochre (#BD8233): secondary landmark
chart.add(
    f"Critical Point ({critical_t} K, {critical_p / 1e6:.1f} MPa)",
    [
        {
            "value": (float(critical_t), float(critical_p)),
            "label": "Critical Point — liquid-gas distinction vanishes\n647.1 K, 22.064 MPa",
            "color": "#BD8233",
        }
    ],
    dots_size=18,
    stroke=False,
    formatter=format_pressure,
)

# Post-process SVG to inject phase region labels
svg_string = chart.render(is_unicode=True)
root = ET.fromstring(svg_string)

# Label positions estimated for 3200×1800 canvas with margin_left=220, margin_right=160
# x-axis: T=180..720 K maps to SVG x=220..3040 (width=2820)
# y-axis: log P mapped to SVG y=80..1530 (height=1450, top=high P)
phase_labels = [
    {"text": "SOLID", "x": "600", "y": "580", "size": "52", "color": IMPRINT_PALETTE[2], "opacity": "0.35"},
    {"text": "LIQUID", "x": "1370", "y": "400", "size": "52", "color": IMPRINT_PALETTE[1], "opacity": "0.35"},
    {"text": "GAS", "x": "1890", "y": "1050", "size": "52", "color": IMPRINT_PALETTE[0], "opacity": "0.35"},
    {"text": "SUPERCRITICAL", "x": "2730", "y": "155", "size": "36", "color": IMPRINT_PALETTE[3], "opacity": "0.30"},
    {"text": "FLUID", "x": "2730", "y": "193", "size": "36", "color": IMPRINT_PALETTE[3], "opacity": "0.30"},
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
        f"letter-spacing: 4px; "
        f"opacity: {label['opacity']}; "
        f"text-anchor: middle;",
    )
    text_elem.text = label["text"]

modified_svg = ET.tostring(root, encoding="unicode")

cairosvg.svg2png(
    bytestring=modified_svg.encode("utf-8"), write_to=f"plot-{THEME}.png", output_width=3200, output_height=1800
)

chart.render_to_file(f"plot-{THEME}.html")
