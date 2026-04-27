""" anyplot.ai
qq-basic: Basic Q-Q Plot
Library: pygal 3.1.0 | Python 3.14.4
Quality: 78/100 | Updated: 2026-04-27
"""

import sys


sys.path.pop(0)  # prevent this file from shadowing the installed pygal package

import os
from statistics import NormalDist

import numpy as np
import pygal
from pygal.style import Style


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

OKABE_ITO = ("#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442")

# Data - sample with slight right skew to show deviation from normality
np.random.seed(42)
sample = np.concatenate(
    [
        np.random.normal(0, 1, 80),
        np.random.exponential(0.5, 20),  # Adds some right skew
    ]
)
sample = np.sort(sample)
n = len(sample)

# Calculate theoretical quantiles using standard library
_nd = NormalDist()
probabilities = (np.arange(1, n + 1) - 0.5) / n
theoretical_quantiles = np.array([_nd.inv_cdf(float(p)) for p in probabilities])

# Determine axis range for reference line
min_val = min(theoretical_quantiles.min(), sample.min())
max_val = max(theoretical_quantiles.max(), sample.max())
margin = (max_val - min_val) * 0.1
line_min = min_val - margin
line_max = max_val + margin

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=OKABE_ITO,
    title_font_size=28,
    label_font_size=18,
    major_label_font_size=16,
    legend_font_size=16,
    value_font_size=14,
    stroke_width=3,
)

chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="qq-basic · pygal · anyplot.ai",
    x_title="Theoretical Quantiles",
    y_title="Sample Quantiles",
    show_legend=True,
    legend_at_bottom=True,
    dots_size=12,
    stroke=False,
    show_x_guides=True,
    show_y_guides=True,
)

qq_points = list(zip(theoretical_quantiles, sample, strict=True))
chart.add("Sample Data", qq_points)

reference_line = [(line_min, line_min), (line_max, line_max)]
chart.add("Reference (y=x)", reference_line, stroke=True, show_dots=False, dots_size=0)

chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
