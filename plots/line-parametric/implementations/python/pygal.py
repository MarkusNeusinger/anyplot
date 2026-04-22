""" pyplots.ai
line-parametric: Parametric Curve Plot
Library: pygal 3.1.0 | Python 3.14.3
Quality: 80/100 | Created: 2026-03-20
"""

import numpy as np
import pygal
from pygal.style import Style


# Data — parametric curves with parameter t
n_points = 1000

# Lissajous figure: x = sin(3t), y = sin(2t), t ∈ [0, 2π]
t_liss = np.linspace(0, 2 * np.pi, n_points)
lissajous_x = np.sin(3 * t_liss)
lissajous_y = np.sin(2 * t_liss)

# Spiral: x = t·cos(t), y = t·sin(t), t ∈ [0, 4π], normalized to [-1,1]
t_spiral = np.linspace(0, 4 * np.pi, n_points)
raw_spiral_x = t_spiral * np.cos(t_spiral)
raw_spiral_y = t_spiral * np.sin(t_spiral)
spiral_max = max(np.abs(raw_spiral_x).max(), np.abs(raw_spiral_y).max())
spiral_x = raw_spiral_x / spiral_max
spiral_y = raw_spiral_y / spiral_max

# Split each curve into 4 segments for smooth color gradient
n_segs = 4
seg_size = n_points // n_segs

# Lissajous gradient: deep blue → steel blue → burnt orange → warm amber
liss_colors = ["#08306b", "#2171b5", "#d94701", "#fd8d3c"]
liss_labels = ["Lissajous  0 → π/2", "Lissajous  π/2 → π", "Lissajous  π → 3π/2", "Lissajous  3π/2 → 2π"]

# Spiral gradient: deep purple → orchid → teal → forest green
spi_colors = ["#4a1486", "#807dba", "#006d5b", "#41ab5d"]
spi_labels = ["Spiral  0 → π", "Spiral  π → 2π", "Spiral  2π → 3π", "Spiral  3π → 4π"]

all_colors = liss_colors + spi_colors + ["#d62728", "#d62728", "#1a1a1a", "#1a1a1a"]

# Style — polished design with explicit font sizing
font = "DejaVu Sans, Helvetica, Arial, sans-serif"

custom_style = Style(
    background="white",
    plot_background="#f7f7f7",
    foreground="#2d2d2d",
    foreground_strong="#1a1a1a",
    foreground_subtle="#d9d9d9",
    guide_stroke_color="#e8e8e8",
    major_guide_stroke_color="#d0d0d0",
    colors=tuple(all_colors),
    font_family=font,
    title_font_family=font,
    title_font_size=52,
    label_font_size=36,
    major_label_font_size=32,
    legend_font_size=30,
    legend_font_family=font,
    value_font_size=28,
    tooltip_font_size=28,
    tooltip_font_family=font,
    opacity=0.95,
    opacity_hover=1.0,
    stroke_opacity=1.0,
    stroke_opacity_hover=1.0,
    stroke_width=8,
)


# Custom tooltip formatter showing parameter value
def fmt_tooltip(x, y, t_val, curve):
    return f"{curve}: t={t_val:.2f}  →  ({x:.3f}, {y:.3f})"


# Chart — square 3600×3600 for geometric accuracy
chart = pygal.XY(
    width=3600,
    height=3600,
    style=custom_style,
    title="line-parametric · pygal · pyplots.ai",
    x_title="Horizontal Position x(t)",
    y_title="Vertical Position y(t)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    legend_box_size=22,
    stroke=True,
    show_dots=False,
    show_x_guides=True,
    show_y_guides=True,
    x_value_formatter=lambda v: f"{v:.1f}",
    value_formatter=lambda v: f"{v:.1f}",
    margin_bottom=200,
    margin_left=100,
    margin_right=80,
    margin_top=80,
    truncate_legend=-1,
    print_values=False,
    xrange=(-1.3, 1.3),
    range=(-1.3, 1.3),
    js=[],
    include_x_axis=True,
    dots_size=0,
)

# Lissajous — 4 segments for smooth cool-to-warm gradient
for k in range(n_segs):
    start = k * seg_size
    end = min((k + 1) * seg_size + 1, n_points)
    seg_data = [
        {
            "value": (float(lissajous_x[i]), float(lissajous_y[i])),
            "label": fmt_tooltip(lissajous_x[i], lissajous_y[i], t_liss[i], "Lissajous"),
        }
        for i in range(start, end)
    ]
    chart.add(
        liss_labels[k], seg_data, stroke_style={"width": 10, "linecap": "round", "linejoin": "round"}, show_dots=False
    )

# Spiral — 4 segments for smooth purple-to-green gradient
for k in range(n_segs):
    start = k * seg_size
    end = min((k + 1) * seg_size + 1, n_points)
    seg_data = [
        {
            "value": (float(spiral_x[i]), float(spiral_y[i])),
            "label": fmt_tooltip(spiral_x[i], spiral_y[i], t_spiral[i], "Spiral"),
        }
        for i in range(start, end)
    ]
    chart.add(
        spi_labels[k], seg_data, stroke_style={"width": 8, "linecap": "round", "linejoin": "round"}, show_dots=False
    )

# Start points — large red dots at t=0, offset slightly so both are visible
# Lissajous starts at (0, 0), Spiral starts at (0, 0) — show side by side
chart.add(
    "▶ Lissajous start",
    [{"value": (float(lissajous_x[0]), float(lissajous_y[0])), "label": "Lissajous t=0"}],
    stroke=False,
    dots_size=30,
    show_dots=True,
)
chart.add(
    "▶ Spiral start",
    [{"value": (float(spiral_x[0]) + 0.03, float(spiral_y[0]) + 0.03), "label": "Spiral t=0 (origin)"}],
    stroke=False,
    dots_size=26,
    show_dots=True,
)

# End points — dark square markers at curve endpoints (distinct positions)
chart.add(
    "◼ Lissajous end",
    [{"value": (float(lissajous_x[-1]), float(lissajous_y[-1])), "label": "Lissajous t=2π"}],
    stroke=False,
    dots_size=26,
    show_dots=True,
)
chart.add(
    "◼ Spiral end",
    [{"value": (float(spiral_x[-1]), float(spiral_y[-1])), "label": "Spiral t=4π"}],
    stroke=False,
    dots_size=26,
    show_dots=True,
)

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
