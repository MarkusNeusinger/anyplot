""" anyplot.ai
scatter-lag: Lag Plot for Time Series Autocorrelation Diagnosis
Library: pygal 3.1.3 | Python 3.13.14
Quality: 86/100 | Updated: 2026-06-24
"""

import os
import sys

import numpy as np


# Avoid name collision: pygal.py filename shadows the pygal package
_cwd = sys.path[0] if sys.path[0] else "."
if _cwd in sys.path:
    sys.path.remove(_cwd)

import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


# Theme tokens — Imprint palette, theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint categorical palette for temporal quartiles + structural reference layers
PALETTE = (
    "#009E73",  # Q1 — brand green (ALWAYS first)
    "#C475FD",  # Q2 — lavender
    "#4467A3",  # Q3 — blue
    "#BD8233",  # Q4 — ochre
    INK_MUTED,  # +1σ envelope (structural, muted)
    INK_MUTED,  # −1σ envelope (structural, muted)
    INK_SOFT,  # y = x reference diagonal
)

# Data — synthetic AR(1) hourly temperature process, moderate positive autocorrelation
np.random.seed(42)
n = 400
phi = 0.78
noise = np.random.normal(0, 1.0, n)
temperature = np.zeros(n)
temperature[0] = 20.0
for i in range(1, n):
    temperature[i] = 20.0 + phi * (temperature[i - 1] - 20.0) + noise[i]

lag = 1
y_t = temperature[:-lag]
y_t_lag = temperature[lag:]

# Temporal quartile masks — color by time to reveal temporal structure
time_idx = np.arange(len(y_t))
q_bounds = np.percentile(time_idx, [25, 50, 75])

early = [
    {"value": (float(y_t[i]), float(y_t_lag[i])), "label": f"Hour {i + 1}"}
    for i in range(len(y_t))
    if time_idx[i] < q_bounds[0]
]
mid_early = [
    {"value": (float(y_t[i]), float(y_t_lag[i])), "label": f"Hour {i + 1}"}
    for i in range(len(y_t))
    if q_bounds[0] <= time_idx[i] < q_bounds[1]
]
mid_late = [
    {"value": (float(y_t[i]), float(y_t_lag[i])), "label": f"Hour {i + 1}"}
    for i in range(len(y_t))
    if q_bounds[1] <= time_idx[i] < q_bounds[2]
]
late = [
    {"value": (float(y_t[i]), float(y_t_lag[i])), "label": f"Hour {i + 1}"}
    for i in range(len(y_t))
    if time_idx[i] >= q_bounds[2]
]

# Correlation coefficient for title annotation
r = np.corrcoef(y_t, y_t_lag)[0, 1]

# Reference geometry — diagonal y = x and ±1σ spread envelope
data_min = float(min(y_t.min(), y_t_lag.min()))
data_max = float(max(y_t.max(), y_t_lag.max()))
pad = (data_max - data_min) * 0.05
ref_start = data_min - pad
ref_end = data_max + pad
ref_line = [(ref_start, ref_start), (ref_end, ref_end)]

sigma = float(np.std(y_t_lag - y_t))
upper_env = [(ref_start, ref_start + sigma), (ref_end, ref_end + sigma)]
lower_env = [(ref_start, ref_start - sigma), (ref_end, ref_end - sigma)]

# Title — length-aware font scaling (baseline 66px for ~67 chars)
title = f"Lag Plot (k={lag}, r={r:.2f}) · scatter-lag · python · pygal · anyplot.ai"
title_len = len(title)
title_font_size = round(66 * 67 / title_len) if title_len > 67 else 66
title_font_size = max(title_font_size, 44)

font = "DejaVu Sans, Helvetica, Arial, sans-serif"
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=PALETTE,
    font_family=font,
    title_font_family=font,
    title_font_size=title_font_size,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    legend_font_family=font,
    value_font_size=36,
    tooltip_font_size=32,
    tooltip_font_family=font,
    opacity=0.65,
    opacity_hover=0.95,
    stroke_width=2.5,
)

# Chart — canvas at 3200×1800 (landscape 16:9, hard contract)
chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title=title,
    x_title="y(t)  — Temperature (°C)",
    y_title=f"y(t+{lag})  — Temperature at lag {lag} (°C)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    legend_box_size=28,
    stroke=False,
    dots_size=8,
    show_x_guides=True,
    show_y_guides=True,
    x_value_formatter=lambda x: f"{x:.1f}",
    value_formatter=lambda y: f"{y:.1f}",
    margin_bottom=100,
    margin_left=80,
    margin_right=30,
    margin_top=40,
    range=(ref_start, ref_end),
    xrange=(ref_start, ref_end),
    x_labels_major_count=8,
    y_labels_major_count=8,
    print_values=False,
    print_zeroes=False,
    truncate_legend=40,
)

# Temporal quartile scatter series
chart.add("Hours 1–100", early, stroke=False, dots_size=9)
chart.add("Hours 101–200", mid_early, stroke=False)
chart.add("Hours 201–300", mid_late, stroke=False)
chart.add("Hours 301–399", late, stroke=False, dots_size=9)

# ±1σ spread envelope (structural layer — no legend entry)
env_style = {"width": 3, "dasharray": "6, 8", "linecap": "round"}
chart.add(None, upper_env, stroke=True, show_dots=False, stroke_style=env_style)
chart.add(None, lower_env, stroke=True, show_dots=False, stroke_style=env_style)

# Diagonal reference line y = x (strong autocorrelation aligns points to this)
chart.add(
    "y = x (±1σ)",
    ref_line,
    stroke=True,
    show_dots=False,
    stroke_style={"width": 6, "dasharray": "24, 12", "linecap": "round"},
)

# Save — PNG + interactive HTML (pygal is interactive)
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
