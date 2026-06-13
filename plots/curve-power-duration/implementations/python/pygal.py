"""anyplot.ai
curve-power-duration: Mean-Maximal Power Duration Curve
Library: pygal 3.1.0 | Python 3.13.13
"""

import os
import sys


# Script filename shadows the installed `pygal` package when run as `python pygal.py`;
# dropping the script directory from sys.path lets the real package resolve.
sys.path.pop(0)

import numpy as np  # noqa: E402
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402
from scipy.interpolate import PchipInterpolator  # noqa: E402


# Theme tokens (Imprint palette — theme-adaptive chrome)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Critical power model — well-trained road cyclist
CP = 280  # W, critical power (aerobic asymptote)
W_PRIME = 20000  # J, finite anaerobic work capacity

# X-axis: 15 log-spaced durations as categorical positions (simulates log x-axis)
DURATIONS_S = [1, 2, 5, 10, 20, 30, 60, 120, 300, 600, 1200, 1800, 3600, 7200, 18000]
X_LABELS_ALL = [
    "1s",
    "2s",
    "5s",
    "10s",
    "20s",
    "30s",
    "1min",
    "2min",
    "5min",
    "10min",
    "20min",
    "30min",
    "1h",
    "2h",
    "5h",
]
# Key reference durations shown as major axis tick labels
X_LABELS_MAJOR = ["1s", "5s", "30s", "1min", "5min", "20min", "1h", "5h"]

# Reference duration indices in DURATIONS_S: 5s=2, 1min=6, 5min=8, 20min=10
REF_IDX = {2, 6, 8, 10}

# Data
# Empirical reference points (physiology-informed, CP≈280 W, P_max≈1100 W at 1 s)
_ref_dur = np.array([1, 5, 15, 30, 60, 180, 300, 600, 1200, 1800, 3600, 7200, 18000])
_ref_pow = np.array([1100, 940, 800, 720, 600, 450, 390, 345, 310, 298, 285, 278, 274])

# Monotone cubic interpolation — preserves non-increasing shape of the curve
_pchip = PchipInterpolator(np.log10(_ref_dur), _ref_pow)
_log_dur = np.log10(np.array(DURATIONS_S, dtype=float))
empirical_power = [round(float(_pchip(ld)), 1) for ld in _log_dur]

# CP model: P(t) = CP + W'/t — only plotted for t ≥ 30 s (where the model is valid)
model_power = [round(CP + W_PRIME / d, 1) if d >= 30 else None for d in DURATIONS_S]

# Horizontal CP asymptote at critical power
cp_line = [float(CP)] * len(DURATIONS_S)

# Reference duration markers: isolated dots at y_max simulate vertical guide marks.
# With allow_interruptions=True, each isolated non-None value renders as a lone dot.
Y_MAX = 1150
ref_markers = [Y_MAX if i in REF_IDX else None for i in range(len(DURATIONS_S))]

# Plot
title_str = "curve-power-duration · python · pygal · anyplot.ai"
n_chars = len(title_str)
title_fs = max(44, round(66 * (67 / n_chars if n_chars > 67 else 1.0)))

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=title_fs,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=2.5,
)

chart = pygal.Line(
    width=3200,
    height=1800,
    style=custom_style,
    title=title_str,
    x_title="Duration",
    y_title="Power (W)",
    show_dots=True,
    dots_size=10,
    stroke=True,
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=30,
    x_labels_major=X_LABELS_MAJOR,
    show_minor_x_labels=False,
    show_y_guides=True,
    show_x_guides=False,
    range=(240, 1150),
    allow_interruptions=True,
)
chart.x_labels = X_LABELS_ALL

# Empirical mean-maximal curve — Imprint brand green, primary series with dots
chart.add("Mean-Maximal Power", empirical_power)

# CP model overlay — Imprint lavender, dashed, starts at 30 s
chart.add("CP Model (P = CP + W’/t)", model_power, stroke_style={"width": 4, "dasharray": "14, 7"}, show_dots=False)

# Critical power asymptote — Imprint blue, dotted horizontal reference
chart.add(f"Critical Power: CP = {CP} W", cp_line, stroke_style={"width": 3, "dasharray": "5, 12"}, show_dots=False)

# Reference duration markers — Imprint amber (#BD8233), large dots at y_max
# Positioned at 5s (sprint), 1min, 5min, 20min (FTP proxy) per spec requirement
chart.add("Reference Durations (5 s · 1 min · 5 min · 20 min)", ref_markers, show_dots=True, dots_size=18)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
