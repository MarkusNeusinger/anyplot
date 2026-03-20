"""pyplots.ai
line-parametric: Parametric Curve Plot
Library: pygal | Python 3.13
Quality: pending | Created: 2026-03-20
"""

import numpy as np
import pygal
from pygal.style import Style


# Data — parametric curves with parameter t
n_points = 800

# Lissajous figure: x = sin(3t), y = sin(2t), t ∈ [0, 2π]
t_liss = np.linspace(0, 2 * np.pi, n_points)
lissajous_x = np.sin(3 * t_liss)
lissajous_y = np.sin(2 * t_liss)

# Spiral: x = t·cos(t), y = t·sin(t), t ∈ [0, 4π], normalized to [-1,1] range
t_spiral = np.linspace(0, 4 * np.pi, n_points)
raw_spiral_x = t_spiral * np.cos(t_spiral)
raw_spiral_y = t_spiral * np.sin(t_spiral)
spiral_max = max(np.abs(raw_spiral_x).max(), np.abs(raw_spiral_y).max())
spiral_x = raw_spiral_x / spiral_max
spiral_y = raw_spiral_y / spiral_max

# Color gradient — 6 segments per curve for smooth color transition
n_segments = 6
segment_size = n_points // n_segments

# Cool→warm for Lissajous (deep blue → red-orange)
lissajous_colors = ["#084594", "#2171b5", "#4292c6", "#ef6548", "#d7301f", "#990000"]

# Violet→emerald for Spiral
spiral_colors = ["#6a1b9a", "#8e24aa", "#ab47bc", "#26a69a", "#00897b", "#00695c"]

# Style
font = "DejaVu Sans, Helvetica, Arial, sans-serif"
all_colors = tuple(lissajous_colors + spiral_colors + ["#333333"])

custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#dddddd",
    guide_stroke_color="#e8e8e8",
    colors=all_colors,
    font_family=font,
    title_font_family=font,
    title_font_size=56,
    label_font_size=40,
    major_label_font_size=36,
    legend_font_size=32,
    legend_font_family=font,
    value_font_size=24,
    tooltip_font_size=24,
    tooltip_font_family=font,
    opacity=0.85,
    opacity_hover=1.0,
    stroke_opacity=1.0,
    stroke_opacity_hover=1.0,
    stroke_width=12,
)

# Chart — square aspect ratio for geometric accuracy
chart = pygal.XY(
    width=4800,
    height=4800,
    style=custom_style,
    title="line-parametric \u00b7 pygal \u00b7 pyplots.ai",
    x_title="x(t)",
    y_title="y(t)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    legend_box_size=24,
    stroke=True,
    show_dots=False,
    show_x_guides=True,
    show_y_guides=True,
    x_value_formatter=lambda v: f"{v:.1f}",
    value_formatter=lambda v: f"{v:.1f}",
    margin_bottom=140,
    margin_left=80,
    margin_right=60,
    margin_top=60,
    truncate_legend=-1,
    print_values=False,
    xrange=(-1.3, 1.3),
    range=(-1.3, 1.3),
    js=[],
)

# Add Lissajous segments (cool → warm gradient showing t direction)
for i in range(n_segments):
    start = i * segment_size
    end = min((i + 1) * segment_size + 1, n_points)
    seg_x = lissajous_x[start:end]
    seg_y = lissajous_y[start:end]
    points = [(float(x), float(y)) for x, y in zip(seg_x, seg_y, strict=True)]
    t_start = t_liss[start] / np.pi
    t_end = t_liss[min(end - 1, n_points - 1)] / np.pi
    label = f"Lissajous t={t_start:.1f}\u03c0\u2013{t_end:.1f}\u03c0"
    chart.add(label, points, stroke_style={"width": 12, "linecap": "round", "linejoin": "round"}, show_dots=False)

# Add spiral segments (purple → green gradient)
for i in range(n_segments):
    start = i * segment_size
    end = min((i + 1) * segment_size + 1, n_points)
    seg_x = spiral_x[start:end]
    seg_y = spiral_y[start:end]
    points = [(float(x), float(y)) for x, y in zip(seg_x, seg_y, strict=True)]
    t_start = t_spiral[start] / np.pi
    t_end = t_spiral[min(end - 1, n_points - 1)] / np.pi
    label = f"Spiral t={t_start:.1f}\u03c0\u2013{t_end:.1f}\u03c0"
    chart.add(label, points, stroke_style={"width": 10, "linecap": "round", "linejoin": "round"}, show_dots=False)

# Mark start/end points
chart.add(
    "Start / End points",
    [
        {"value": (float(lissajous_x[0]), float(lissajous_y[0])), "label": "Lissajous start (t=0)"},
        {"value": (float(lissajous_x[-1]), float(lissajous_y[-1])), "label": "Lissajous end (t=2\u03c0)"},
        {"value": (float(spiral_x[0]), float(spiral_y[0])), "label": "Spiral start (t=0)"},
        {"value": (float(spiral_x[-1]), float(spiral_y[-1])), "label": "Spiral end (t=4\u03c0)"},
    ],
    stroke=False,
    dots_size=16,
)

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
