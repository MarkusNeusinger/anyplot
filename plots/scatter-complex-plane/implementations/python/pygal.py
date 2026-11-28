"""anyplot.ai
scatter-complex-plane: Complex Plane Visualization (Argand Diagram)
Library: pygal 3.1.3 | Python 3.14.10
Quality: pending | Updated: 2026-11-28
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
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
UNIT_RADIUS = 1.0  # the reference circle of the complex plane
ARROW_LENGTH = 0.28  # arrowhead barb length in data units (capped at 40% of a short vector)
ARROW_SPREAD = np.radians(24)  # angle between the shaft and each barb
VECTOR_DOTS = [20, 16, 22]  # dot size of the tip, per category in order
VECTOR_STROKES = [  # stroke per category in order; a dashed stroke marks a computed result
    {"width": 5, "linecap": "round", "opacity": 0.88},
    {"width": 3.5, "linecap": "round", "opacity": 0.75},
    {"width": 6, "dasharray": "26, 16", "linecap": "round", "opacity": 0.92},
]

# Columns: set these to your table's column names
REAL = "Real Axis"  # role: real
IMAGINARY = "Imaginary Axis"  # role: imaginary
LABEL = "Annotation"  # role: label
CATEGORY = "Category"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("complex_numbers.csv")
roots = [np.exp(1j * (np.radians(15) + 2 * np.pi * k / 3)) for k in range(3)]
samples = [2.5 + 1.0j, -1.5 + 0.2j, 1.0 - 2.0j, -2.0 - 1.0j]
numbers = roots + samples + [samples[0] + samples[1]]  # the last one is the vector sum z1 + z2
names = [f"ω{k}" for k in range(len(roots))] + [f"z{k + 1}" for k in range(len(samples))] + ["z1+z2"]
categories = ["Roots of Unity (3rd)"] * len(roots) + ["Sample Points"] * len(samples) + ["z1+z2 (Vector Sum)"]
df = pd.DataFrame(
    {
        REAL: [z.real for z in numbers],
        IMAGINARY: [z.imag for z in numbers],
        LABEL: [f"{n}={z.real:.1f}{z.imag:+.1f}i" for n, z in zip(names, numbers, strict=True)],
        CATEGORY: categories,
    }
)

# Plot: reads only df and the constants above
extent = np.ceil(max(df[REAL].abs().max(), df[IMAGINARY].abs().max())) + 0.3

title = "scatter-complex-plane · python · pygal · anyplot.ai"
title_fs = max(44, round(66 * 67 / max(len(title), 67)))

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    colors=IMPRINT_PALETTE,
    value_colors=[INK] * len(IMPRINT_PALETTE),
    font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    title_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    title_font_size=title_fs,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    value_label_font_size=36,
    stroke_width=6,
    opacity=0.94,
    opacity_hover=1.0,
)

# Square canvas keeps the aspect ratio equal so the unit circle looks circular
chart = pygal.XY(
    width=2400,
    height=2400,
    style=custom_style,
    title=title,
    x_title=REAL,
    y_title=IMAGINARY,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    legend_box_size=24,
    stroke=False,
    dots_size=12,
    show_x_guides=True,
    show_y_guides=True,
    truncate_legend=-1,
    margin_bottom=140,
    margin_left=100,
    margin_right=253,
    margin_top=100,
    range=(-extent, extent),
    xrange=(-extent, extent),
    print_values=False,
    print_labels=True,
    js=[],
)

# One vector series per category: origin -> tip, then two barbs forming the arrowhead
no_dot = {"r": 0}
for i, (category, rows) in enumerate(df.groupby(CATEGORY, sort=False)):
    points = []
    for re, im, label in zip(rows[REAL], rows[IMAGINARY], rows[LABEL], strict=True):
        tip = complex(re, im)
        head = min(ARROW_LENGTH, 0.4 * abs(tip))
        barbs = [tip - head * np.exp(1j * (np.angle(tip) + sign * ARROW_SPREAD)) for sign in (1, -1)]
        # pygal joins every point of a series into one path (None does not break it), so the
        # path retraces its own steps: origin, tip, barb, tip, barb, tip, back to the origin
        tip_point = {"value": (re, im), "label": "", "node": no_dot}
        points += [
            {"value": (0.0, 0.0), "label": "", "node": no_dot},
            {"value": (re, im), "label": label},
            {"value": (barbs[0].real, barbs[0].imag), "label": "", "node": no_dot},
            tip_point,
            {"value": (barbs[1].real, barbs[1].imag), "label": "", "node": no_dot},
            tip_point,
        ]
    chart.add(
        category,
        points,
        stroke=True,
        show_dots=True,
        dots_size=VECTOR_DOTS[i % len(VECTOR_DOTS)],
        stroke_style=VECTOR_STROKES[i % len(VECTOR_STROKES)],
    )

# Unit circle: subtle dashed reference
angles = np.linspace(0, 2 * np.pi, 180)
chart.add(
    "Unit Circle",
    [(float(UNIT_RADIUS * np.cos(t)), float(UNIT_RADIUS * np.sin(t))) for t in angles],
    stroke=True,
    show_dots=False,
    fill=False,
    stroke_style={"width": 2.5, "dasharray": "10, 14", "opacity": 0.6},
)

# Origin: drawn last so it sits on top of all vectors
chart.add("Origin", [{"value": (0.0, 0.0), "label": ""}], stroke=False, dots_size=20)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
