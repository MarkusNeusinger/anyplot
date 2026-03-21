""" pyplots.ai
line-reaction-coordinate: Reaction Coordinate Energy Diagram
Library: pygal 3.1.0 | Python 3.14.3
Quality: 76/100 | Created: 2026-03-21
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

# Generate smooth reaction coordinate curve using Gaussian-shaped barrier
n_points = 300
reaction_coord = np.linspace(0, 10, n_points)

# Build energy profile: reactant plateau → barrier → product plateau
sigma = 1.2
peak_pos = 5.0
barrier_height = transition_energy - reactant_energy
base_curve = reactant_energy + barrier_height * np.exp(-0.5 * ((reaction_coord - peak_pos) / sigma) ** 2)

# Smoothly transition to product energy on the right side
transition_start = 6.5
transition_end = 8.5
for i in range(n_points):
    x = reaction_coord[i]
    if x > transition_start:
        t = min((x - transition_start) / (transition_end - transition_start), 1.0)
        smooth_t = t * t * (3 - 2 * t)  # Hermite smoothstep
        base_curve[i] = base_curve[i] * (1 - smooth_t) + product_energy * smooth_t

# Flatten the tails
for i in range(n_points):
    x = reaction_coord[i]
    if x < 1.5:
        base_curve[i] = reactant_energy
    elif x > 8.5:
        base_curve[i] = product_energy

# Smooth the join regions with repeated moving average
kernel_size = 17
kernel = np.ones(kernel_size) / kernel_size
energy_curve = base_curve.copy()
for _ in range(3):
    padded = np.pad(energy_curve, kernel_size, mode="edge")
    energy_curve = np.convolve(padded, kernel, mode="same")[kernel_size:-kernel_size]

# Convert to list of (x, y) tuples for pygal XY
curve_points = [(float(reaction_coord[i]), float(energy_curve[i])) for i in range(n_points)]

# Style
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333",
    foreground_strong="#333",
    foreground_subtle="#ddd",
    colors=(
        "#306998",  # Main curve (Python Blue)
        "#888888",  # Reactant dashed line
        "#888888",  # Product dashed line
        "#C0392B",  # Ea arrow
        "#27AE60",  # ΔH arrow
        "#306998",  # Transition state marker
        "#306998",  # Reactant marker
        "#306998",  # Product marker
    ),
    title_font_size=60,
    label_font_size=40,
    major_label_font_size=36,
    legend_font_size=36,
    value_font_size=28,
    stroke_width=5,
)

# Plot
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="line-reaction-coordinate · pygal · pyplots.ai",
    x_title="Reaction Coordinate",
    y_title="Potential Energy (kJ/mol)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=5,
    show_x_guides=False,
    show_y_guides=True,
    show_x_labels=False,
    dots_size=0,
    stroke=True,
    margin=80,
    margin_left=260,
    margin_right=120,
    margin_bottom=220,
    margin_top=120,
    range=(0, 145),
    xrange=(0, 10),
    truncate_legend=-1,
    tooltip_border_radius=8,
)

# Main energy curve
chart.add("Energy Profile", curve_points, stroke_style={"width": 6}, show_dots=False, fill=False)

# Reactant energy dashed line
chart.add(
    None,
    [{"value": (0.0, reactant_energy), "node": {"r": 0}}, {"value": (10.0, reactant_energy), "node": {"r": 0}}],
    stroke_style={"width": 2, "dasharray": "12, 8"},
    show_dots=False,
)

# Product energy dashed line
chart.add(
    None,
    [{"value": (0.0, product_energy), "node": {"r": 0}}, {"value": (10.0, product_energy), "node": {"r": 0}}],
    stroke_style={"width": 2, "dasharray": "12, 8"},
    show_dots=False,
)

# Ea vertical indicator (reactant level to transition state)
ea_x = 3.2
chart.add(
    f"Ea = {activation_energy:.0f} kJ/mol",
    [{"value": (ea_x, reactant_energy), "node": {"r": 10}}, {"value": (ea_x, transition_energy), "node": {"r": 10}}],
    stroke_style={"width": 4, "dasharray": "6, 4"},
)

# ΔH vertical indicator (reactant level to product level)
dh_x = 9.2
chart.add(
    f"ΔH = {enthalpy_change:.0f} kJ/mol",
    [{"value": (dh_x, reactant_energy), "node": {"r": 10}}, {"value": (dh_x, product_energy), "node": {"r": 10}}],
    stroke_style={"width": 4, "dasharray": "6, 4"},
)

# Key point markers with labels
chart.add(
    "Transition State (‡)",
    [{"value": (peak_pos, transition_energy), "node": {"r": 16}}],
    stroke_style={"width": 0},
    dots_size=16,
)

chart.add(
    f"Reactants ({reactant_energy:.0f} kJ/mol)",
    [{"value": (1.0, reactant_energy), "node": {"r": 14}}],
    stroke_style={"width": 0},
    dots_size=14,
)

chart.add(
    f"Products ({product_energy:.0f} kJ/mol)",
    [{"value": (9.0, product_energy), "node": {"r": 14}}],
    stroke_style={"width": 0},
    dots_size=14,
)

# Custom y-axis labels
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
