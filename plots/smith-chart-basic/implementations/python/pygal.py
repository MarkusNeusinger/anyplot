"""anyplot.ai
smith-chart-basic: Smith Chart for RF/Impedance
Library: pygal 3.1.3 | Python 3.14
Quality: pending | Updated: 2026-05-20
"""

import os

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: the locus takes position 1, the structural series use theme-adaptive inks
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
SERIES_COLORS = (IMPRINT_PALETTE[0], INK_SOFT, INK_MUTED, *IMPRINT_PALETTE[1:])

# Constants
Z0 = 50  # reference impedance (ohms)
R_CIRCLES = [0, 0.2, 0.5, 1, 2, 5]  # normalized resistance values of the grid
X_ARCS = [0.2, 0.5, 1, 2, 5]  # normalized reactance values of the grid (both signs)

# Columns: set these to your table's column names
FREQUENCY = "Frequency (Hz)"  # role: frequency
Z_REAL = "Resistance (ohm)"  # role: z_real
Z_IMAG = "Reactance (ohm)"  # role: z_imag

# Data: replace this block with your own table, for example df = pd.read_csv("s11.csv")
np.random.seed(42)
n = 50
freqs = np.linspace(1e9, 6e9, n)
r_base = 25 + 50 * np.exp(-freqs / 3e9)
x_base = 30 * np.sin(2 * np.pi * freqs / 2e9) + 20 * np.cos(freqs / 1e9)
df = pd.DataFrame({FREQUENCY: freqs, Z_REAL: r_base + np.random.randn(n) * 3, Z_IMAG: x_base + np.random.randn(n) * 5})

# Plot
gamma = ((df[Z_REAL] + 1j * df[Z_IMAG]) / Z0 - 1) / ((df[Z_REAL] + 1j * df[Z_IMAG]) / Z0 + 1)
gamma = gamma.to_numpy()
limit = 1.15

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=SERIES_COLORS,
    value_colors=(INK,) * len(SERIES_COLORS),  # point labels default to black
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=48,
    value_label_font_size=48,
    stroke_width=3,
)

# Square canvas; truncate_label=-1 prevents pygal from clipping text
chart = pygal.XY(
    width=2400,
    height=2400,
    style=custom_style,
    title="smith-chart-basic · python · pygal · anyplot.ai",
    show_legend=True,
    legend_at_bottom=True,
    show_x_guides=False,
    show_y_guides=False,
    x_title="Reflection Coefficient Real Part",
    y_title="Reflection Coefficient Imaginary Part",
    dots_size=8,
    range=(-limit, limit),
    xrange=(-limit, limit),
    margin=120,
    truncate_label=-1,
    print_labels=True,
    allow_interruptions=True,
    print_values=False,
)
chart.x_labels = [-1.0, -0.5, 0.0, 0.5, 1.0]

# Impedance locus; the first, middle and last points carry frequency labels and larger markers
key_points = {0, len(df) // 2, len(df) - 1}
locus = []
for i, g in enumerate(gamma):
    point = {"value": (float(g.real), float(g.imag))}
    if i in key_points:
        ghz = df[FREQUENCY].iloc[i] / 1e9
        point["label"] = f"{ghz:.1f} GHz"
        point["node"] = {"r": 22}
    locus.append(point)
chart.add("Antenna impedance, 1 to 6 GHz", locus, show_dots=True, stroke_width=5, dots_size=6)

# Chart boundary (|Γ| = 1)
theta = np.linspace(0, 2 * np.pi, 200)
chart.add(
    "Chart boundary |Γ| = 1", [(float(np.cos(t)), float(np.sin(t))) for t in theta], show_dots=False, stroke_width=5
)

# Smith grid: constant resistance circles, constant reactance arcs and the real axis in one series;
# (None, None) breaks the line between segments
grid = []
t = np.linspace(0, 2 * np.pi, 240)
for r in R_CIRCLES:  # circle of constant r: centre (r/(1+r), 0), radius 1/(1+r)
    cx, rad = r / (1 + r), 1 / (1 + r)
    grid += [(float(cx + rad * np.cos(a)), float(rad * np.sin(a))) for a in t] + [(None, None)]
for x in X_ARCS:  # arc of constant x: centre (1, 1/x), radius 1/x, clipped to the unit disc
    for sign in (1, -1):
        cy, rad = sign / x, 1 / x
        pts = [(1 + rad * np.cos(a), cy + rad * np.sin(a)) for a in np.linspace(0, 2 * np.pi, 4000)]
        run = [(float(px), float(py)) for px, py in pts if px * px + py * py <= 1.0000001]
        grid += run + [(None, None)]
grid += [(-1.0, 0.0), (1.0, 0.0), (None, None)]
chart.add("Resistance and reactance grid", grid, show_dots=False, stroke_width=1.5)

# Save
chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
