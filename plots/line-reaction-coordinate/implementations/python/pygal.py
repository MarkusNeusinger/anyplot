""" anyplot.ai
line-reaction-coordinate: Reaction Coordinate Energy Diagram
Library: pygal 3.1.3 | Python 3.13.14
Quality: 84/100 | Updated: 2026-06-24
"""

import os
import sys


# Script filename shadows the installed 'pygal' package when run as 'python pygal.py';
# dropping the script directory from sys.path lets the real package resolve.
sys.path.pop(0)

import numpy as np
import pygal
from pygal.style import Style


# Theme tokens — Imprint palette chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Data — single-step exothermic reaction
reactant_energy = 50.0
transition_energy = 120.0
product_energy = 20.0
activation_energy = transition_energy - reactant_energy  # Ea = 70 kJ/mol
enthalpy_change = product_energy - reactant_energy  # ΔH = -30 kJ/mol

# Generate smooth energy profile
n_points = 300
reaction_coord = np.linspace(0, 10, n_points)

sigma = 1.2
peak_pos = 5.0
base_curve = reactant_energy + (transition_energy - reactant_energy) * np.exp(
    -0.5 * ((reaction_coord - peak_pos) / sigma) ** 2
)

t_raw = np.clip((reaction_coord - 6.5) / 2.0, 0.0, 1.0)
smooth_t = t_raw * t_raw * (3 - 2 * t_raw)
base_curve = base_curve * (1 - smooth_t) + product_energy * smooth_t

base_curve = np.where(reaction_coord < 1.5, reactant_energy, base_curve)
base_curve = np.where(reaction_coord > 8.5, product_energy, base_curve)

kernel = np.ones(17) / 17
energy_curve = base_curve.copy()
for _ in range(3):
    padded = np.pad(energy_curve, 17, mode="edge")
    energy_curve = np.convolve(padded, kernel, mode="same")[17:-17]

curve_points = list(zip(reaction_coord.tolist(), energy_curve.tolist(), strict=True))

# Series colors: Imprint palette positions assigned by role, first = brand green
SERIES_COLORS = (
    "#009E73",  # Energy Profile — Imprint pos 1 (brand green)
    INK_MUTED,  # Reference line at reactant level (theme-adaptive muted)
    INK_MUTED,  # Reference line at product level (theme-adaptive muted)
    "#2ABCCD",  # Ea indicator — Imprint pos 6 (cyan/teal)
    "#BD8233",  # ΔH indicator — Imprint pos 4 (ochre/warm)
    "#C475FD",  # Transition State — Imprint pos 2 (lavender)
    "#4467A3",  # Reactants — Imprint pos 3 (blue)
    "#AE3030",  # Products — Imprint pos 5 (matte red)
)

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=SERIES_COLORS,
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=2.5,
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="line-reaction-coordinate · python · pygal · anyplot.ai",
    x_title="Reaction Coordinate",
    y_title="Potential Energy (kJ/mol)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    show_x_guides=False,
    show_y_guides=True,
    show_x_labels=False,
    dots_size=0,
    stroke=True,
    margin=60,
    margin_left=200,
    margin_right=120,
    margin_bottom=260,
    margin_top=80,
    range=(5, 130),
    xrange=(-0.2, 10.2),
    truncate_legend=-1,
    tooltip_border_radius=8,
)

# Main energy curve — Imprint pos 1 (brand green)
chart.add("Energy Profile", curve_points, stroke_style={"width": 6}, show_dots=False, fill=False)

# Horizontal reference lines at key energy levels (theme-adaptive muted)
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

# Ea vertical indicator — Imprint pos 6 (cyan)
ea_x = peak_pos
chart.add(
    f"Ea = {activation_energy:.0f} kJ/mol",
    [{"value": (ea_x, reactant_energy), "node": {"r": 14}}, {"value": (ea_x, transition_energy), "node": {"r": 14}}],
    stroke_style={"width": 5, "dasharray": "8, 5"},
)

# ΔH vertical indicator — Imprint pos 4 (ochre)
dh_x = 8.5
chart.add(
    f"ΔH = {enthalpy_change:.0f} kJ/mol",
    [{"value": (dh_x, reactant_energy), "node": {"r": 14}}, {"value": (dh_x, product_energy), "node": {"r": 14}}],
    stroke_style={"width": 5, "dasharray": "8, 5"},
)

# Transition state marker — Imprint pos 2 (lavender)
chart.add(
    "Transition State (‡)",
    [{"value": (peak_pos, transition_energy), "node": {"r": 22}}],
    stroke_style={"width": 0},
    dots_size=22,
)

# Reactants marker — Imprint pos 3 (blue)
chart.add(
    f"Reactants ({reactant_energy:.0f} kJ/mol)",
    [{"value": (1.0, reactant_energy), "node": {"r": 16}}],
    stroke_style={"width": 0},
    dots_size=16,
)

# Products marker — Imprint pos 5 (matte red)
chart.add(
    f"Products ({product_energy:.0f} kJ/mol)",
    [{"value": (9.5, product_energy), "node": {"r": 16}}],
    stroke_style={"width": 0},
    dots_size=16,
)

# Custom y-axis labels at chemically meaningful energy values
chart.y_labels = [
    {"label": f"{product_energy:.0f}", "value": product_energy},
    {"label": f"{reactant_energy:.0f}", "value": reactant_energy},
    {"label": "80", "value": 80},
    {"label": "100", "value": 100},
    {"label": f"{transition_energy:.0f}", "value": transition_energy},
]

# Save
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
chart.render_to_png(f"plot-{THEME}.png")
