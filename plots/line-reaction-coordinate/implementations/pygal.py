""" pyplots.ai
line-reaction-coordinate: Reaction Coordinate Energy Diagram
Library: pygal 3.1.0 | Python 3.14.3
Quality: 82/100 | Created: 2026-03-21
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - Single-step exothermic reaction
reactant_energy = 50.0  # kJ/mol
transition_energy = 120.0  # kJ/mol
product_energy = 20.0  # kJ/mol
activation_energy = transition_energy - reactant_energy  # Ea = 70 kJ/mol
enthalpy_change = product_energy - reactant_energy  # ΔH = -30 kJ/mol

# Generate smooth energy profile
n_points = 300
reaction_coord = np.linspace(0, 10, n_points)

# Gaussian barrier centered at transition state
sigma = 1.2
peak_pos = 5.0
base_curve = reactant_energy + (transition_energy - reactant_energy) * np.exp(
    -0.5 * ((reaction_coord - peak_pos) / sigma) ** 2
)

# Vectorized Hermite smoothstep transition to product energy
t_raw = np.clip((reaction_coord - 6.5) / 2.0, 0.0, 1.0)
smooth_t = t_raw * t_raw * (3 - 2 * t_raw)
base_curve = base_curve * (1 - smooth_t) + product_energy * smooth_t

# Vectorized tail flattening
base_curve = np.where(reaction_coord < 1.5, reactant_energy, base_curve)
base_curve = np.where(reaction_coord > 8.5, product_energy, base_curve)

# Smooth join regions with repeated convolution
kernel = np.ones(17) / 17
energy_curve = base_curve.copy()
for _ in range(3):
    padded = np.pad(energy_curve, 17, mode="edge")
    energy_curve = np.convolve(padded, kernel, mode="same")[17:-17]

curve_points = list(zip(reaction_coord.tolist(), energy_curve.tolist(), strict=True))

# Colorblind-safe palette
BLUE = "#306998"
DARK_BLUE = "#1A4971"
TEAL = "#2980B9"
ORANGE = "#E67E22"
GRAY = "#AAAAAA"

# Style — y-guides at key energies serve as reference lines
custom_style = Style(
    background="white",
    plot_background="#FAFBFC",
    foreground="#2C3E50",
    foreground_strong="#2C3E50",
    foreground_subtle="#CCCCCC",
    colors=(BLUE, GRAY, GRAY, TEAL, ORANGE, DARK_BLUE, BLUE, BLUE),
    title_font_size=60,
    label_font_size=40,
    major_label_font_size=36,
    legend_font_size=32,
    value_font_size=28,
    stroke_width=5,
)

# Chart
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="line-reaction-coordinate \u00b7 pygal \u00b7 pyplots.ai",
    x_title="Reaction Coordinate",
    y_title="Potential Energy (kJ/mol)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=6,
    show_x_guides=False,
    show_y_guides=True,
    show_x_labels=False,
    dots_size=0,
    stroke=True,
    margin=80,
    margin_left=260,
    margin_right=160,
    margin_bottom=200,
    margin_top=120,
    range=(0, 145),
    xrange=(-0.2, 10.2),
    truncate_legend=-1,
    tooltip_border_radius=8,
)

# Main energy curve
chart.add("Energy Profile", curve_points, stroke_style={"width": 6}, show_dots=False, fill=False)

# Horizontal reference lines at reactant and product energy levels
chart.add(
    None,
    [(0.0, reactant_energy), (10.0, reactant_energy)],
    stroke_style={"width": 3, "dasharray": "16, 8"},
    show_dots=False,
)
chart.add(
    None,
    [(0.0, product_energy), (10.0, product_energy)],
    stroke_style={"width": 3, "dasharray": "16, 8"},
    show_dots=False,
)

# Ea vertical indicator (teal — colorblind-safe)
ea_x = 2.8
chart.add(
    f"Ea = {activation_energy:.0f} kJ/mol",
    [{"value": (ea_x, reactant_energy), "node": {"r": 14}}, {"value": (ea_x, transition_energy), "node": {"r": 14}}],
    stroke_style={"width": 5, "dasharray": "8, 5"},
)

# ΔH vertical indicator (orange — colorblind-safe)
dh_x = 8.5
chart.add(
    f"\u0394H = {enthalpy_change:.0f} kJ/mol",
    [{"value": (dh_x, reactant_energy), "node": {"r": 14}}, {"value": (dh_x, product_energy), "node": {"r": 14}}],
    stroke_style={"width": 5, "dasharray": "8, 5"},
)

# Transition state marker (larger, dark blue)
chart.add(
    "Transition State (\u2021)",
    [{"value": (peak_pos, transition_energy), "node": {"r": 22}}],
    stroke_style={"width": 0},
    dots_size=22,
)

# Reactant marker
chart.add(
    f"Reactants ({reactant_energy:.0f} kJ/mol)",
    [{"value": (1.0, reactant_energy), "node": {"r": 16}}],
    stroke_style={"width": 0},
    dots_size=16,
)

# Product marker
chart.add(
    f"Products ({product_energy:.0f} kJ/mol)",
    [{"value": (9.5, product_energy), "node": {"r": 16}}],
    stroke_style={"width": 0},
    dots_size=16,
)

# Custom y-axis labels at chemically meaningful values
chart.y_labels = [
    {"label": "0", "value": 0},
    {"label": f"{product_energy:.0f}", "value": product_energy},
    {"label": f"{reactant_energy:.0f}", "value": reactant_energy},
    {"label": "80", "value": 80},
    {"label": "100", "value": 100},
    {"label": f"{transition_energy:.0f}", "value": transition_energy},
    {"label": "140", "value": 140},
]

# Save
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
