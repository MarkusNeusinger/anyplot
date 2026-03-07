""" pyplots.ai
feynman-basic: Feynman Diagram for Particle Interactions
Library: pygal 3.1.0 | Python 3.14.3
Quality: 79/100 | Created: 2026-03-07
"""

import numpy as np
import pygal
from pygal.style import Style


# Data — Electron-positron annihilation: e⁻e⁺ → γ → μ⁻μ⁺
# Vertex positions (interaction points) centered in diagram
v1 = (3.0, 5.0)
v2 = (7.0, 5.0)

# External particle endpoints — spread wide to fill canvas
e_minus = (0.2, 8.8)
e_plus = (0.2, 1.2)
mu_minus = (9.8, 8.8)
mu_plus = (9.8, 1.2)

# Each propagator as a named series for clear particle identification
e_minus_line = [{"value": e_minus, "label": "e⁻ incoming fermion"}, {"value": v1, "label": "Vertex 1 — annihilation"}]
e_plus_line = [{"value": e_plus, "label": "e⁺ incoming antifermion"}, {"value": v1, "label": "Vertex 1 — annihilation"}]
mu_minus_line = [
    {"value": v2, "label": "Vertex 2 — pair creation"},
    {"value": mu_minus, "label": "μ⁻ outgoing fermion"},
]
mu_plus_line = [
    {"value": v2, "label": "Vertex 2 — pair creation"},
    {"value": mu_plus, "label": "μ⁺ outgoing antifermion"},
]

# Photon propagator — sinusoidal wavy path between vertices
t = np.linspace(0, 1, 300)
photon_x = v1[0] + t * (v2[0] - v1[0])
photon_y = v1[1] + 0.5 * np.sin(t * 16 * np.pi)
photon_line = [
    {"value": (float(x), float(y)), "label": "γ (virtual photon)"} for x, y in zip(photon_x, photon_y, strict=True)
]

# Vertex markers
vertex_points = [
    {"value": v1, "label": "Vertex 1 — annihilation point"},
    {"value": v2, "label": "Vertex 2 — pair creation point"},
]

# Style — distinct colors per particle type for visual storytelling
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#1a1a2e",
    foreground_strong="#1a1a2e",
    foreground_subtle="#f0f0f0",
    colors=(
        "#1A3F7D",  # e⁻ (dark blue)
        "#4A86C8",  # e⁺ (medium blue — antifermion)
        "#1B6B35",  # μ⁻ (dark green)
        "#3D9B6A",  # μ⁺ (medium green — antifermion)
        "#D4493E",  # photon (red)
        "#1a1a2e",  # vertices (dark)
    ),
    opacity=1.0,
    opacity_hover=1.0,
    title_font_size=36,
    label_font_size=22,
    major_label_font_size=20,
    legend_font_size=24,
    value_font_size=28,
    tooltip_font_size=20,
    stroke_width=5,
    title_font_family="Trebuchet MS, Helvetica, sans-serif",
    label_font_family="Trebuchet MS, Helvetica, sans-serif",
    major_label_font_family="Trebuchet MS, Helvetica, sans-serif",
    legend_font_family="Trebuchet MS, Helvetica, sans-serif",
    value_font_family="Trebuchet MS, Helvetica, sans-serif",
)

# Square canvas for symmetric Feynman diagram layout
chart = pygal.XY(
    width=3600,
    height=3600,
    style=custom_style,
    title="e⁻e⁺ → γ → μ⁻μ⁺ Annihilation · feynman-basic · pygal · pyplots.ai",
    show_x_guides=False,
    show_y_guides=False,
    show_x_labels=False,
    show_y_labels=False,
    x_title="",
    y_title="",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    legend_box_size=24,
    stroke=True,
    show_dots=False,
    print_values=False,
    margin_top=20,
    margin_bottom=60,
    margin_left=30,
    margin_right=30,
    tooltip_border_radius=8,
    tooltip_fancy_mode=True,
    range=(0.0, 10.0),
    xrange=(-0.5, 10.5),
)

# Fermion propagators — each particle as its own named series
chart.add("e⁻ fermion", e_minus_line, stroke_width=6)
chart.add("e⁺ antifermion", e_plus_line, stroke_width=6)
chart.add("μ⁻ fermion", mu_minus_line, stroke_width=6)
chart.add("μ⁺ antifermion", mu_plus_line, stroke_width=6)

# Photon propagator (wavy red line)
chart.add("γ photon", photon_line, stroke_width=4)

# Vertex dots (interaction points)
chart.add("Vertices", vertex_points, stroke=False, show_dots=True, dots_size=24)

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
