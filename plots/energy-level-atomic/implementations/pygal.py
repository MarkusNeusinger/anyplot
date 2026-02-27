"""pyplots.ai
energy-level-atomic: Atomic Energy Level Diagram
Library: pygal 3.1.0 | Python 3.14.3
Quality: 87/100 | Created: 2026-02-27
"""

import pygal
from pygal.style import Style


# Data - Hydrogen atom energy levels (En = -13.6/n² eV)
energy_values = {n: -13.6 / n**2 for n in range(1, 7)}

# Evenly-spaced visual positions (nonlinear scale for converging upper levels)
visual_y = {1: 1.0, 2: 2.5, 3: 4.0, 4: 5.5, 5: 7.0, 6: 8.5}
ionization_y = 10.0

# Spectral series transitions: (upper_n, lower_n, label)
lyman_transitions = [(2, 1, "Ly-\u03b1 122 nm"), (3, 1, "Ly-\u03b2 103 nm"), (4, 1, "Ly-\u03b3 97 nm")]
balmer_transitions = [
    (3, 2, "H\u03b1 656 nm"),
    (4, 2, "H\u03b2 486 nm"),
    (5, 2, "H\u03b3 434 nm"),
    (6, 2, "H\u03b4 410 nm"),
]
paschen_transitions = [(4, 3, "Pa-\u03b1 1875 nm"), (5, 3, "Pa-\u03b2 1282 nm"), (6, 3, "Pa-\u03b3 1094 nm")]

# Layout x-positions (spaced by series for clear grouping)
level_x_start = 1.0
level_x_end = 9.2
lyman_x_positions = [2.0, 2.7, 3.4]
balmer_x_positions = [4.5, 5.2, 5.9, 6.6]
paschen_x_positions = [7.5, 8.1, 8.7]

# Colors by series order:
# 6 hidden levels + ionization + 3 Lyman (wide UV spread) + 4 Balmer (visible) + 3 Paschen (IR warm)
level_color = "#4A5568"
all_colors = (
    (level_color,) * 6
    + ("#CC3333",)
    + ("#2D006E", "#7B2FBE", "#CC44AA")  # Lyman: deep indigo, violet, magenta-pink
    + ("#E01030", "#00B8D4", "#2244EE", "#6A0DAD")  # Balmer: red, teal, blue, deep violet
    + ("#D95F02", "#E6A800", "#8B6914")  # Paschen: burnt orange, gold, bronze
)

custom_style = Style(
    background="white",
    plot_background="#F4F5FB",
    foreground="#2A2A3A",
    foreground_strong="#1A1A2A",
    foreground_subtle="#DDDDE8",
    colors=all_colors,
    title_font_size=48,
    label_font_size=24,
    major_label_font_size=24,
    legend_font_size=28,
    value_font_size=20,
    stroke_width=4,
)

# Custom value formatter showing energy in eV for tooltips
energy_lookup = {visual_y[n]: energy_values[n] for n in range(1, 7)}
energy_lookup[ionization_y] = 0.0


def format_energy(val):
    """Format tooltip values as energy in eV."""
    if isinstance(val, tuple):
        y = val[1]
    else:
        y = val
    ev = energy_lookup.get(y, y)
    return f"{ev:+.2f} eV"


# Plot
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="Hydrogen Atom \u00b7 energy-level-atomic \u00b7 pygal \u00b7 pyplots.ai",
    y_title="Energy (eV)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    show_x_guides=False,
    show_y_guides=False,
    show_x_labels=False,
    dots_size=16,
    stroke=True,
    margin=80,
    margin_left=240,
    margin_right=100,
    margin_bottom=200,
    margin_top=100,
    range=(0, 11),
    xrange=(0, 10.0),
    truncate_legend=-1,
    tooltip_border_radius=8,
    value_formatter=format_energy,
    print_values=False,
    print_labels=False,
    legend_box_size=20,
)

# Y-axis labels showing actual energy values at evenly-spaced positions
chart.y_labels = [
    {"label": "n=1:  \u221213.60 eV", "value": visual_y[1]},
    {"label": "n=2:  \u22123.40 eV", "value": visual_y[2]},
    {"label": "n=3:  \u22121.51 eV", "value": visual_y[3]},
    {"label": "n=4:  \u22120.85 eV", "value": visual_y[4]},
    {"label": "n=5:  \u22120.54 eV", "value": visual_y[5]},
    {"label": "n=6:  \u22120.38 eV", "value": visual_y[6]},
    {"label": "Ionization:  0.00 eV", "value": ionization_y},
]

# Energy level horizontal lines (hidden from legend with None title)
for n in range(1, 7):
    chart.add(
        None,
        [
            {"value": (level_x_start, visual_y[n]), "node": {"r": 0}},
            {"value": (level_x_end, visual_y[n]), "node": {"r": 0}},
        ],
        stroke_style={"width": 3},
    )

# Ionization limit (dashed, prominent)
chart.add(
    "Ionization (0 eV)",
    [
        {"value": (level_x_start - 0.3, ionization_y), "node": {"r": 0}},
        {"value": (level_x_end + 0.3, ionization_y), "node": {"r": 0}},
    ],
    stroke_style={"width": 4, "dasharray": "18, 10"},
)

# Emission transitions: large dot at lower level (destination), small dot at upper (origin)
# The asymmetric node sizes indicate downward direction of emission

# Lyman series (UV transitions to n=1)
lyman_widths = [14, 12, 10]
lyman_lower_nodes = [26, 22, 18]
lyman_upper_nodes = [14, 12, 11]
for i, (upper, lower, label) in enumerate(lyman_transitions):
    x = lyman_x_positions[i]
    chart.add(
        label,
        [
            {"value": (x, visual_y[upper]), "node": {"r": lyman_upper_nodes[i]}},
            {"value": (x, visual_y[lower]), "node": {"r": lyman_lower_nodes[i]}},
        ],
        stroke_style={"width": lyman_widths[i]},
    )

# Balmer series (visible transitions to n=2) — H-alpha is the focal point
balmer_widths = [16, 13, 11, 10]
balmer_lower_nodes = [30, 22, 18, 16]
balmer_upper_nodes = [14, 12, 10, 9]
for i, (upper, lower, label) in enumerate(balmer_transitions):
    x = balmer_x_positions[i]
    chart.add(
        label,
        [
            {"value": (x, visual_y[upper]), "node": {"r": balmer_upper_nodes[i]}},
            {"value": (x, visual_y[lower]), "node": {"r": balmer_lower_nodes[i]}},
        ],
        stroke_style={"width": balmer_widths[i]},
    )

# Paschen series (IR transitions to n=3) — warm colors for infrared
paschen_widths = [13, 11, 10]
paschen_lower_nodes = [24, 20, 16]
paschen_upper_nodes = [13, 11, 10]
for i, (upper, lower, label) in enumerate(paschen_transitions):
    x = paschen_x_positions[i]
    chart.add(
        label,
        [
            {"value": (x, visual_y[upper]), "node": {"r": paschen_upper_nodes[i]}},
            {"value": (x, visual_y[lower]), "node": {"r": paschen_lower_nodes[i]}},
        ],
        stroke_style={"width": paschen_widths[i]},
    )

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
