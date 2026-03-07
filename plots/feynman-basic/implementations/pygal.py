"""pyplots.ai
feynman-basic: Feynman Diagram for Particle Interactions
Library: pygal | Python 3.13
Quality: pending | Created: 2026-03-07
"""

import numpy as np
import pygal
from pygal.style import Style


# Data — Electron-positron annihilation: e⁻e⁺ → γ → μ⁻μ⁺
# Vertex positions (interaction points)
v1_x, v1_y = 3.0, 3.0
v2_x, v2_y = 7.0, 3.0

# Fermion endpoints
e_minus_in = (0.5, 5.0)
e_plus_in = (0.5, 1.0)
mu_minus_out = (9.5, 5.0)
mu_plus_out = (9.5, 1.0)

# Fermion lines grouped with None breaks between segments
fermion_lines = [
    {"value": e_minus_in, "label": "e⁻ incoming"},
    {"value": (v1_x, v1_y), "label": "vertex"},
    None,
    {"value": e_plus_in, "label": "e⁺ incoming"},
    {"value": (v1_x, v1_y), "label": "vertex"},
    None,
    {"value": (v2_x, v2_y), "label": "vertex"},
    {"value": mu_minus_out, "label": "μ⁻ outgoing"},
    None,
    {"value": (v2_x, v2_y), "label": "vertex"},
    {"value": mu_plus_out, "label": "μ⁺ outgoing"},
]

# Photon propagator — sinusoidal path between v1 and v2 for wavy appearance
n_wave = 200
t = np.linspace(0, 1, n_wave)
photon_x = v1_x + t * (v2_x - v1_x)
photon_y = v1_y + 0.3 * np.sin(t * 14 * np.pi)
photon_line = list(zip(photon_x.tolist(), photon_y.tolist(), strict=True))

# Vertex markers (dots at interaction points)
vertex_points = [
    {"value": (v1_x, v1_y), "label": "Vertex 1 (annihilation)"},
    {"value": (v2_x, v2_y), "label": "Vertex 2 (pair creation)"},
]

# Style
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#1a1a2e",
    foreground_strong="#1a1a2e",
    foreground_subtle="#f0f0f0",
    colors=(
        "#306998",  # fermion lines (Python Blue)
        "#D4493E",  # photon wavy line (red)
        "#1a1a2e",  # vertex dots (dark)
    ),
    opacity=0.90,
    opacity_hover=1.0,
    title_font_size=34,
    label_font_size=22,
    major_label_font_size=20,
    legend_font_size=18,
    value_font_size=16,
    tooltip_font_size=18,
    stroke_width=4,
    title_font_family="Trebuchet MS, Helvetica, sans-serif",
    label_font_family="Trebuchet MS, Helvetica, sans-serif",
    major_label_font_family="Trebuchet MS, Helvetica, sans-serif",
    legend_font_family="Trebuchet MS, Helvetica, sans-serif",
    value_font_family="Trebuchet MS, Helvetica, sans-serif",
)

# Chart
chart = pygal.XY(
    width=4800,
    height=2700,
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
    legend_box_size=20,
    stroke=True,
    show_dots=False,
    margin_top=30,
    margin_bottom=60,
    margin_left=40,
    margin_right=40,
    tooltip_border_radius=8,
    tooltip_fancy_mode=True,
    print_values=False,
    range=(0, 6),
    xrange=(0, 10),
)

# Propagator lines
chart.add("Fermions (e⁻, e⁺, μ⁻, μ⁺)", fermion_lines, stroke_width=4)
chart.add("Photon (γ)", photon_line, stroke_width=2)

# Vertex dots
chart.add("Vertices", vertex_points, stroke=False, show_dots=True, dots_size=18)


# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
