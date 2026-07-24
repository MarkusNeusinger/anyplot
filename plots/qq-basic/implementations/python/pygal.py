""" anyplot.ai
qq-basic: Basic Q-Q Plot
Library: pygal 3.1.3 | Python 3.13.14
Quality: 88/100 | Updated: 2026-07-24
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

BRAND = "#009E73"  # Imprint palette position 1 — always first series
AMBER = "#DDCC77"  # Imprint semantic anchor — warning / caution, flags the slow-response tail

# Data - API response times (ms): a fast, tightly-clustered core plus an
# occasional slow request, producing the right-skewed tail that QQ plots
# are commonly used to surface before assuming normality in latency analysis.
np.random.seed(42)
baseline = np.random.normal(150, 18, 80)
slow_tail = 150 + np.random.exponential(35, 20)
sample = np.sort(np.concatenate([baseline, slow_tail]))
n = len(sample)

# Calculate theoretical quantiles using standard library
_nd = NormalDist()
probabilities = (np.arange(1, n + 1) - 0.5) / n
theoretical_quantiles = np.array([_nd.inv_cdf(float(p)) for p in probabilities])

# Theoretical quantiles are unitless z-scores while the sample is in ms, so
# the fitted reference line uses the sample's own mean/std (y = mean + std*x)
# rather than y=x — the standard QQ convention when axes are in different units.
theo_margin = (theoretical_quantiles.max() - theoretical_quantiles.min()) * 0.1
line_x_min = theoretical_quantiles.min() - theo_margin
line_x_max = theoretical_quantiles.max() + theo_margin

sample_mean = sample.mean()
sample_std = sample.std()

# Flag the slow-response tail (>2 std above the mean) so the deviation this
# QQ plot exists to reveal is visually called out, not just implied by shape.
outlier_threshold = sample_mean + 2 * sample_std

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=(BRAND, INK),  # series 1 = brand green, series 2 (reference line) = neutral ink
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
    title="qq-basic · python · pygal · anyplot.ai",
    x_title="Theoretical Quantiles",
    y_title="Sample Quantiles (Response Time, ms)",
    show_legend=True,
    legend_at_bottom=True,
    dots_size=13,
    stroke=False,
    show_x_guides=True,
    show_y_guides=True,
)

qq_points = [
    {"value": (tq, s), "color": AMBER, "tooltip": "Slow response outlier"} if s > outlier_threshold else (tq, s)
    for tq, s in zip(theoretical_quantiles, sample, strict=True)
]
chart.add("API Response Time", qq_points)

reference_line = [
    (line_x_min, sample_mean + sample_std * line_x_min),
    (line_x_max, sample_mean + sample_std * line_x_max),
]
chart.add("Reference (Normal)", reference_line, stroke=True, show_dots=False, dots_size=0)

chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
