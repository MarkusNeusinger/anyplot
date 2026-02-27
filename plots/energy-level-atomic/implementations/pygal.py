"""pyplots.ai
energy-level-atomic: Atomic Energy Level Diagram
Library: pygal | Python 3.13
Quality: pending | Created: 2026-02-27
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

# Layout x-positions
level_x_start = 1.5
level_x_end = 8.5
lyman_x_positions = [2.8, 3.4, 4.0]
balmer_x_positions = [6.0, 6.6, 7.2, 7.8]

# Colors: 6 levels + ionization + 3 Lyman + 4 Balmer = 14 series
level_gray = "#444444"
all_colors = (
    (level_gray,) * 6 + ("#BB4444",) + ("#7B2FBE", "#9544B0", "#B07CC6") + ("#DC143C", "#00B4D8", "#4361EE", "#7209B7")
)

custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#dddddd",
    colors=all_colors,
    title_font_size=48,
    label_font_size=24,
    major_label_font_size=24,
    legend_font_size=24,
    value_font_size=20,
    stroke_width=5,
)

# Plot
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="Hydrogen Atom \u00b7 energy-level-atomic \u00b7 pygal \u00b7 pyplots.ai",
    y_title="Energy (eV)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=7,
    show_x_guides=False,
    show_y_guides=False,
    show_x_labels=False,
    dots_size=14,
    stroke=True,
    margin=80,
    margin_left=220,
    margin_bottom=200,
    margin_top=100,
    range=(0, 11),
    xrange=(0, 10),
    truncate_legend=-1,
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

# Energy level horizontal lines
for n in range(1, 7):
    chart.add(
        f"n={n} ({energy_values[n]:.2f} eV)",
        [
            {"value": (level_x_start, visual_y[n]), "node": {"r": 0}},
            {"value": (level_x_end, visual_y[n]), "node": {"r": 0}},
        ],
    )

# Ionization limit (dashed)
chart.add(
    "Ionization (0 eV)",
    [
        {"value": (level_x_start - 0.3, ionization_y), "node": {"r": 0}},
        {"value": (level_x_end + 0.3, ionization_y), "node": {"r": 0}},
    ],
    stroke_style={"width": 3, "dasharray": "15, 10"},
)

# Lyman series (UV transitions to n=1)
for i, (upper, lower, label) in enumerate(lyman_transitions):
    x = lyman_x_positions[i]
    chart.add(
        label, [{"value": (x, visual_y[upper]), "node": {"r": 0}}, {"value": (x, visual_y[lower]), "node": {"r": 14}}]
    )

# Balmer series (visible transitions to n=2)
for i, (upper, lower, label) in enumerate(balmer_transitions):
    x = balmer_x_positions[i]
    chart.add(
        label, [{"value": (x, visual_y[upper]), "node": {"r": 0}}, {"value": (x, visual_y[lower]), "node": {"r": 14}}]
    )

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
