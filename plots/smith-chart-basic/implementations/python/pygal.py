""" anyplot.ai
smith-chart-basic: Smith Chart for RF/Impedance
Library: pygal 3.1.0 | Python 3.13.13
Quality: 79/100 | Updated: 2026-05-20
"""

import os

import numpy as np
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# In pygal, series colors always come from the `colors` tuple in order of add() calls.
# 4 structural (empty-label) series consume positions 1-4 before the data series.
# Palette positions 1-4: structural chart elements (Smith chart grid infrastructure)
# Palette positions 5-8: data series in canonical Okabe-Ito order 1→4
CHART_COLORS = (
    "#E69F00",  # pos 1: unit circle boundary (Okabe-Ito amber — warm, distinct)
    "#56B4E9",  # pos 2: resistance circles (Okabe-Ito sky blue)
    INK_MUTED,  # pos 3: reactance arcs (theme-adaptive muted)
    INK_SOFT,  # pos 4: real axis (theme-adaptive subtle)
    "#009E73",  # pos 5: "Antenna Z(f)" ← brand green — first data series
    "#D55E00",  # pos 6: "1 GHz" (Okabe-Ito 2 = vermillion)
    "#0072B2",  # pos 7: "3.5 GHz" (Okabe-Ito 3 = blue)
    "#CC79A7",  # pos 8: "6 GHz" (Okabe-Ito 4 = pink/purple)
)

Z0 = 50  # reference impedance (ohms)
R_CIRCLES = [0, 0.2, 0.5, 1, 2, 5]
X_ARCS = [0.2, 0.5, 1, 2, 5]

# Style
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=CHART_COLORS,
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=3,
)

# Chart — square format; right-side legend avoids bottom truncation
chart = pygal.XY(
    width=2400,
    height=2400,
    style=custom_style,
    title="smith-chart-basic · python · pygal · anyplot.ai",
    show_legend=True,
    legend_at_bottom=False,
    show_x_guides=False,
    show_y_guides=False,
    x_title="Reflection Coefficient Real Part",
    y_title="Reflection Coefficient Imaginary Part",
    dots_size=8,
    range=(-1.15, 1.15),
    xrange=(-1.15, 1.15),
    margin=80,
)

# Structural series — empty label keeps them out of the legend
# Unit circle boundary (|Γ| = 1): pos 1 = #E69F00 amber
theta = np.linspace(0, 2 * np.pi, 200)
unit_circle = [(float(np.cos(t)), float(np.sin(t))) for t in theta]
chart.add("", unit_circle, show_dots=False, stroke_width=5)

# Constant resistance circles: pos 2 = #56B4E9 sky blue
r_grid = []
for r in R_CIRCLES:
    x_vals = np.concatenate([np.linspace(-50, -0.01, 100), np.linspace(0.01, 50, 100)])
    for x in x_vals:
        z_n = complex(r, x)
        g = (z_n - 1) / (z_n + 1)
        if abs(g) <= 1.001:
            r_grid.append((float(g.real), float(g.imag)))
    r_grid.append((None, None))
chart.add("", r_grid, show_dots=False, stroke_width=1.5)

# Constant reactance arcs: pos 3 = INK_MUTED gray
x_grid = []
for x in X_ARCS:
    for r in np.linspace(0.001, 50, 100):
        z_n = complex(r, x)
        g = (z_n - 1) / (z_n + 1)
        if abs(g) <= 1.001:
            x_grid.append((float(g.real), float(g.imag)))
    x_grid.append((None, None))
    for r in np.linspace(0.001, 50, 100):
        z_n = complex(r, -x)
        g = (z_n - 1) / (z_n + 1)
        if abs(g) <= 1.001:
            x_grid.append((float(g.real), float(g.imag)))
    x_grid.append((None, None))
chart.add("", x_grid, show_dots=False, stroke_width=1.5)

# Real axis: pos 4 = INK_SOFT gray
chart.add("", [(-1.0, 0.0), (1.0, 0.0)], show_dots=False, stroke_width=2)

# Data — antenna impedance sweep 1–6 GHz
np.random.seed(42)
n = 50
freqs = np.linspace(1e9, 6e9, n)

r_base = 25 + 50 * np.exp(-freqs / 3e9)
x_base = 30 * np.sin(2 * np.pi * freqs / 2e9) + 20 * np.cos(freqs / 1e9)
z_r = r_base + np.random.randn(n) * 3
z_i = x_base + np.random.randn(n) * 5

z_c = z_r + 1j * z_i
z_norm = z_c / Z0
gamma = (z_norm - 1) / (z_norm + 1)

# Impedance locus: pos 5 = #009E73 brand green
locus = [(float(g.real), float(g.imag)) for g in gamma]
chart.add("Antenna Z(f)", locus, show_dots=True, stroke_width=5, dots_size=6)

# Frequency markers (stroke=False = dots only, no connecting line)
chart.add("1 GHz", [(float(gamma[0].real), float(gamma[0].imag))], show_dots=True, dots_size=22, stroke=False)
chart.add(
    "3.5 GHz", [(float(gamma[n // 2].real), float(gamma[n // 2].imag))], show_dots=True, dots_size=22, stroke=False
)
chart.add("6 GHz", [(float(gamma[-1].real), float(gamma[-1].imag))], show_dots=True, dots_size=22, stroke=False)

# Save
chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
