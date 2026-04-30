""" anyplot.ai
stem-basic: Basic Stem Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: 84/100 | Updated: 2026-04-30
"""

import os
import sys

import numpy as np


# Pop script dir so this file (pygal.py) doesn't shadow the installed pygal package
_script_dir = sys.path.pop(0)
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


sys.path.insert(0, _script_dir)

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

OKABE_ITO = ("#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442")

# Data - discrete impulse response (decaying oscillation)
np.random.seed(42)
n_points = 30
sample_index = np.arange(n_points)
amplitude = np.exp(-sample_index / 8) * np.sin(sample_index * 0.8) * 2 + np.random.randn(n_points) * 0.1

# Build stem data: baseline dot suppressed, marker visible only at data value
stem_data = []
for i in range(n_points):
    xi = float(sample_index[i])
    yi = float(amplitude[i])
    stem_data.append({"value": (xi, 0.0), "node": {"r": 0}})  # baseline anchor, no dot
    stem_data.append({"value": (xi, yi), "node": {"r": 14}, "label": f"n={i}, a={yi:.3f}"})
    stem_data.append(None)  # break between stems

# Custom style
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=OKABE_ITO,
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=44,
    legend_font_size=56,
    value_font_size=40,
    stroke_width=3,
    opacity="0.18",
    opacity_hover="0.9",
)

# Chart
chart = pygal.XY(
    width=4800,
    height=2700,
    title="stem-basic · pygal · anyplot.ai",
    x_title="Sample Index (n)",
    y_title="Amplitude (a.u.)",
    style=custom_style,
    show_dots=True,
    dots_size=14,
    stroke=True,
    stroke_style={"width": 8},
    show_x_guides=False,
    show_y_guides=True,
    show_legend=False,
    margin=120,
)

chart.add("Impulse Response", stem_data)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
