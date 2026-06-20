""" anyplot.ai
line-parametric: Parametric Curve Plot
Library: pygal 3.1.3 | Python 3.13.14
Quality: 83/100 | Updated: 2026-06-20
"""

import os

import numpy as np
import pygal
from pygal.style import Style


THEME = os.getenv("ANYPLOT_THEME", "light")

# Theme-adaptive chrome tokens
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint categorical palette — 8 hues, canonical order
# 4 Lissajous segments (positions 1-4) + 4 Rose curve segments (positions 5-8)
IMPRINT_PALETTE = (
    "#009E73",  # 1 brand green
    "#C475FD",  # 2 lavender
    "#4467A3",  # 3 blue
    "#BD8233",  # 4 ochre
    "#AE3030",  # 5 matte red
    "#2ABCCD",  # 6 cyan
    "#954477",  # 7 rose
    "#99B314",  # 8 lime
)

# Data — two parametric curves, both bounded in [-1, 1] × [-1, 1]
n_points = 800
n_segs = 4
seg_size = n_points // n_segs

# Curve 1: Lissajous (3, 2) — x = sin(3t), y = sin(2t), t ∈ [0, 2π]
t_liss = np.linspace(0, 2 * np.pi, n_points)
liss_x = np.sin(3 * t_liss)
liss_y = np.sin(2 * t_liss)

# Curve 2: Four-petal rose (rhodonea) — x = cos(2t)·cos(t), y = cos(2t)·sin(t)
# Distinct from normalized spiral: petals expand and retract, traversal is visible via color
t_rose = np.linspace(0, 2 * np.pi, n_points)
rose_x = np.cos(2 * t_rose) * np.cos(t_rose)
rose_y = np.cos(2 * t_rose) * np.sin(t_rose)

font = "DejaVu Sans, Helvetica, Arial, sans-serif"

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT_PALETTE,
    font_family=font,
    title_font_family=font,
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    tooltip_font_size=36,
    tooltip_font_family=font,
    opacity=1.0,
    stroke_opacity=1.0,
    stroke_width=10,
)

chart = pygal.XY(
    width=2400,
    height=2400,
    style=custom_style,
    title="line-parametric · python · pygal · anyplot.ai",
    x_title="Horizontal Position  x(t)",
    y_title="Vertical Position  y(t)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=2,
    legend_box_size=24,
    stroke=True,
    show_dots=False,
    show_x_guides=True,
    show_y_guides=True,
    x_value_formatter=lambda v: f"{v:.1f}",
    value_formatter=lambda v: f"{v:.1f}",
    js=[],
    xrange=(-1.2, 1.2),
    range=(-1.2, 1.2),
    print_values=False,
    margin_bottom=340,
    margin_left=80,
    margin_right=60,
    margin_top=60,
    truncate_legend=-1,
)

# Segment labels — short form so legend fits in 2 columns
liss_labels = ["Lissajous  0 to pi/2", "Lissajous  pi/2 to pi", "Lissajous  pi to 3pi/2", "Lissajous  3pi/2 to 2pi"]
rose_labels = ["Rose Curve  0 to pi/2", "Rose Curve  pi/2 to pi", "Rose Curve  pi to 3pi/2", "Rose Curve  3pi/2 to 2pi"]

# Lissajous (3,2) — 4 segments, Imprint positions 1–4, reveal traversal via color gradient
for k in range(n_segs):
    start = k * seg_size
    end = min((k + 1) * seg_size + 1, n_points)
    seg_data = [{"value": (float(liss_x[i]), float(liss_y[i]))} for i in range(start, end)]
    chart.add(
        liss_labels[k], seg_data, stroke_style={"width": 10, "linecap": "round", "linejoin": "round"}, show_dots=False
    )

# Four-petal rose — 4 segments, Imprint positions 5–8, reveal petal traversal via color
for k in range(n_segs):
    start = k * seg_size
    end = min((k + 1) * seg_size + 1, n_points)
    seg_data = [{"value": (float(rose_x[i]), float(rose_y[i]))} for i in range(start, end)]
    chart.add(
        rose_labels[k], seg_data, stroke_style={"width": 10, "linecap": "round", "linejoin": "round"}, show_dots=False
    )

# Save — PNG + interactive HTML, both theme-suffixed
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
