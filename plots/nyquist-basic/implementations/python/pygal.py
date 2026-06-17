""" anyplot.ai
nyquist-basic: Nyquist Plot for Control Systems
Library: pygal 3.1.0 | Python 3.13.14
Quality: 83/100 | Updated: 2026-06-17
"""

import math
import os
import sys


# Script is named pygal.py — remove its directory from sys.path first so
# 'import pygal' resolves to the installed package, not this file.
sys.path = [p for p in sys.path if p != os.path.dirname(os.path.abspath(__file__))]

import numpy as np
import pygal
from pygal.style import Style


# Theme tokens (Imprint palette)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Data — Transfer function G(s) = 2 / [s(s+1)(s+2)]
omega = np.logspace(-2, 2, 800)
s = 1j * omega
G = 2.0 / (s * (s + 1) * (s + 2))

real_part = G.real
imag_part = G.imag

# Mirror for negative frequencies (Nyquist contour reflection)
real_mirror = real_part[::-1]
imag_mirror = -imag_part[::-1]

# Imprint palette — position 1 (green) for main curve, red (semantic) for critical point
IMPRINT_COLORS = (
    "#009E73",  # brand green — positive frequency curve
    "#C475FD",  # lavender — negative frequency mirror
    "#AE3030",  # matte red — critical point (semantic: stability boundary)
    INK_MUTED,  # muted neutral — unit circle reference
    "#BD8233",  # ochre — frequency markers
)

# Title — 44 chars, use default 66 (no shrink needed)
TITLE = "nyquist-basic · python · pygal · anyplot.ai"
title_size = round(66 * min(1.0, 67 / len(TITLE)))

# Custom style using Imprint palette
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT_COLORS,
    title_font_size=title_size,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=2.5,
)

# Chart — square canvas for 1:1 aspect ratio (unit circle must appear circular)
chart = pygal.XY(
    width=2400,
    height=2400,
    style=custom_style,
    title=TITLE,
    x_title="Real",
    y_title="Imaginary",
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=36,
    dots_size=3,
    stroke=True,
    show_x_guides=True,
    show_y_guides=True,
    explicit_size=True,
    range=(-2, 2),
    xrange=(-2, 2),
    value_formatter=lambda x: f"{x:.3f}",
)

# Positive frequency curve with tooltips showing frequency values
step = 4
nyquist_positive = [
    {"value": (float(real_part[i]), float(imag_part[i])), "label": f"ω = {omega[i]:.3f} rad/s"}
    for i in range(0, len(omega), step)
]
chart.add("G(jω), ω ≥ 0", nyquist_positive, show_dots=False, stroke_style={"width": 5})

# Negative frequency mirror with tooltips
nyquist_negative = [
    {"value": (float(real_mirror[i]), float(imag_mirror[i])), "label": f"ω = -{omega[len(omega) - 1 - i]:.3f} rad/s"}
    for i in range(0, len(omega), step)
]
chart.add("G(jω), ω < 0", nyquist_negative, show_dots=False, stroke_style={"width": 4, "dasharray": "12,6"})

# Critical point (−1, 0) — red marker (semantic: boundary of stability region)
chart.add(
    "Critical Point (−1, 0)", [{"value": (-1.0, 0.0), "label": "Critical Point: (−1, 0)"}], stroke=False, dots_size=24
)

# Unit circle reference (dashed, muted)
circle_points = [
    {"value": (math.cos(math.radians(a)), math.sin(math.radians(a))), "label": f"{a}°"} for a in range(0, 361, 3)
]
chart.add("Unit Circle", circle_points, stroke=True, show_dots=False, stroke_style={"width": 2, "dasharray": "8,6"})

# Frequency markers at key points along the curve (visible in both PNG and HTML)
freq_targets = [0.5, 1.0, 2.0, 5.0, 10.0]
freq_annotations = []
for ft in freq_targets:
    idx = int(np.argmin(np.abs(omega - ft)))
    freq_annotations.append({"value": (float(real_part[idx]), float(imag_part[idx])), "label": f"ω = {ft} rad/s"})
chart.add("ω markers (rad/s)", freq_annotations, stroke=False, dots_size=16)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
