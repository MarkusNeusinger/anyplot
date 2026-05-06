"""anyplot.ai
ternary-basic: Basic Ternary Plot
Library: pygal 3.1.0 | Python 3.13
Quality: pending | Created: 2025-12-24
"""

import math
import os

import cairosvg
import numpy as np
import pygal
from pygal.style import Style


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"

np.random.seed(42)

H = math.sqrt(3) / 2

compositions = [
    (65, 25, 10),
    (10, 45, 45),
    (30, 35, 35),
    (40, 40, 20),
    (50, 10, 40),
    (20, 65, 15),
    (90, 5, 5),
    (5, 90, 5),
    (5, 5, 90),
    (33, 34, 33),
    (45, 45, 10),
    (55, 35, 10),
    (15, 20, 65),
    (10, 15, 75),
    (50, 30, 20),
]

data_points = [(0.5 * (2 * s[1] + s[0]) / 100, H * s[0] / 100) for s in compositions]

vertex_sand = (0.5, H)
vertex_silt = (1.0, 0.0)
vertex_clay = (0.0, 0.0)

grid_lines = []
for pct in [0.2, 0.4, 0.6, 0.8]:
    p1 = (0.5 * (2 * (1 - pct) + pct), H * pct)
    p2 = (0.5 * pct, H * pct)
    grid_lines.extend([p1, p2, (None, None)])

    p1 = (0.5 * (2 * pct + (1 - pct)), H * (1 - pct))
    p2 = (pct, 0.0)
    grid_lines.extend([p1, p2, (None, None)])

    p1 = (0.5 * (1 - pct), H * (1 - pct))
    p2 = (0.5 * (2 * (1 - pct)), 0.0)
    grid_lines.extend([p1, p2, (None, None)])

tick_marks = []
tick_len = 0.03

for pct in [0.2, 0.4, 0.6, 0.8]:
    x_left = 0.5 * pct
    y_left = H * pct
    tick_marks.extend([(x_left, y_left), (x_left - tick_len, y_left), (None, None)])

    x_right = 0.5 * (2 - pct)
    y_right = H * pct
    tick_marks.extend([(x_right, y_right), (x_right + tick_len, y_right), (None, None)])

    x_base = pct
    y_base = 0.0
    tick_marks.extend([(x_base, y_base), (x_base, y_base - tick_len), (None, None)])

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=(BRAND, INK_MUTED, INK_SOFT, INK),
    title_font_size=80,
    label_font_size=48,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=40,
    opacity=0.85,
)

chart = pygal.XY(
    width=3600,
    height=3600,
    style=custom_style,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    show_x_guides=False,
    show_y_guides=False,
    show_x_labels=False,
    show_y_labels=False,
    x_title="",
    y_title="",
    title="Soil Composition · ternary-basic · pygal · anyplot.ai",
    dots_size=20,
    stroke=False,
    include_x_axis=False,
    xrange=(-0.15, 1.15),
    yrange=(-0.20, 1.05),
    explicit_size=True,
    margin=50,
    margin_bottom=120,
)

chart.add(
    None, [vertex_clay, vertex_silt, vertex_sand, vertex_clay], stroke=True, show_dots=False, stroke_style={"width": 5}
)

chart.add(None, grid_lines, stroke=True, show_dots=False, stroke_style={"width": 2, "dasharray": "8,5"})

chart.add("Soil Samples", data_points, stroke=False, dots_size=22)

chart.add(None, tick_marks, stroke=True, show_dots=False, stroke_style={"width": 3})

svg_content = chart.render().decode("utf-8")

plot_x_start = 150
plot_x_end = 3450
plot_y_start = 250
plot_y_end = 3350
x_range = 1.30
y_range = 1.25

sand_px = plot_x_start + (0.5 + 0.15) / x_range * (plot_x_end - plot_x_start)
sand_py = plot_y_start + (1.05 - (H + 0.06)) / y_range * (plot_y_end - plot_y_start)
silt_px = plot_x_start + (1.07 + 0.15) / x_range * (plot_x_end - plot_x_start)
silt_py = plot_y_start + (1.05 - (-0.03)) / y_range * (plot_y_end - plot_y_start)
clay_px = plot_x_start + (-0.07 + 0.15) / x_range * (plot_x_end - plot_x_start)
clay_py = plot_y_start + (1.05 - (-0.03)) / y_range * (plot_y_end - plot_y_start)

vertex_labels_svg = f"""
  <text x="{sand_px}" y="{sand_py}" text-anchor="middle" font-size="60" font-weight="bold" fill="{INK}" font-family="sans-serif">SAND</text>
  <text x="{silt_px}" y="{silt_py}" text-anchor="start" font-size="60" font-weight="bold" fill="{INK}" font-family="sans-serif">SILT</text>
  <text x="{clay_px}" y="{clay_py}" text-anchor="end" font-size="60" font-weight="bold" fill="{INK}" font-family="sans-serif">CLAY</text>
"""

pct_labels_svg = ""
pct_font_size = 36

for pct in [20, 40, 60, 80]:
    frac = pct / 100.0

    left_x = 0.5 * frac
    left_y = H * frac
    left_px = plot_x_start + (left_x - 0.06 + 0.15) / x_range * (plot_x_end - plot_x_start)
    left_py = plot_y_start + (1.05 - left_y) / y_range * (plot_y_end - plot_y_start)
    pct_labels_svg += f'  <text x="{left_px}" y="{left_py}" text-anchor="end" font-size="{pct_font_size}" fill="{INK_MUTED}" font-family="sans-serif">{pct}</text>\n'

    right_x = 0.5 * (2 - frac)
    right_y = H * frac
    right_px = plot_x_start + (right_x + 0.04 + 0.15) / x_range * (plot_x_end - plot_x_start)
    right_py = plot_y_start + (1.05 - right_y) / y_range * (plot_y_end - plot_y_start)
    pct_labels_svg += f'  <text x="{right_px}" y="{right_py}" text-anchor="start" font-size="{pct_font_size}" fill="{INK_MUTED}" font-family="sans-serif">{pct}</text>\n'

    base_x = frac
    base_y = -0.05
    base_px = plot_x_start + (base_x + 0.15) / x_range * (plot_x_end - plot_x_start)
    base_py = plot_y_start + (1.05 - base_y) / y_range * (plot_y_end - plot_y_start)
    pct_labels_svg += f'  <text x="{base_px}" y="{base_py}" text-anchor="middle" font-size="{pct_font_size}" fill="{INK_MUTED}" font-family="sans-serif">{pct}</text>\n'

all_labels_svg = vertex_labels_svg + pct_labels_svg
svg_content = svg_content.replace("</svg>", all_labels_svg + "</svg>")

with open(f"plot-{THEME}.html", "w") as f:
    f.write(svg_content)

cairosvg.svg2png(bytestring=svg_content.encode("utf-8"), write_to=f"plot-{THEME}.png")
