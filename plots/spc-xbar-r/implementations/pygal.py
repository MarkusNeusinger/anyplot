""" pyplots.ai
spc-xbar-r: Statistical Process Control Chart (X-bar/R)
Library: pygal 3.1.0 | Python 3.14.3
Quality: 83/100 | Created: 2026-03-19
"""

import io

import cairosvg
import numpy as np
import pygal
from PIL import Image, ImageDraw
from pygal.style import Style


# Data — CNC shaft diameter measurements, subgroup size n=5
np.random.seed(42)
n_samples = 30
subgroup_size = 5

# Control chart constants for n=5
A2 = 0.577
D3 = 0.0
D4 = 2.114

# Generate realistic measurements around target 25.00 mm
target = 25.00
process_std = 0.02
measurements = np.random.normal(target, process_std, (n_samples, subgroup_size))

# Inject out-of-control points
measurements[7] += 0.06  # Shift up — tool wear
measurements[18] -= 0.07  # Shift down — recalibration overshoot
measurements[24] += 0.08  # Shift up — material batch change

# Compute X-bar and R for each sample
sample_means = measurements.mean(axis=1)
sample_ranges = measurements.max(axis=1) - measurements.min(axis=1)

# Control limits
x_bar_bar = sample_means.mean()
r_bar = sample_ranges.mean()

xbar_ucl = x_bar_bar + A2 * r_bar
xbar_lcl = x_bar_bar - A2 * r_bar
xbar_uw = x_bar_bar + (2 / 3) * A2 * r_bar  # +2 sigma warning
xbar_lw = x_bar_bar - (2 / 3) * A2 * r_bar  # -2 sigma warning

r_ucl = D4 * r_bar
r_lcl = D3 * r_bar  # 0 for n=5
r_uw = r_bar + (2 / 3) * (r_ucl - r_bar)  # +2 sigma warning

# Identify out-of-control points
xbar_ooc = (sample_means > xbar_ucl) | (sample_means < xbar_lcl)
r_ooc = sample_ranges > r_ucl

# Colors
C_NORMAL = "#306998"
C_OOC = "#C0392B"
C_CL = "#1A1A2E"
C_UCL_LCL = "#E74C3C"
C_WARN = "#D35400"
PLOT_BG = "#F4F3EE"
GRID_COLOR = "#E8E5E0"

custom_style = Style(
    background="white",
    plot_background=PLOT_BG,
    foreground="#333333",
    foreground_strong="#1A1A2E",
    foreground_subtle=GRID_COLOR,
    colors=(C_NORMAL, C_OOC, C_CL, C_UCL_LCL, C_UCL_LCL, C_WARN, C_WARN),
    title_font_size=48,
    label_font_size=28,
    major_label_font_size=28,
    legend_font_size=24,
    value_font_size=18,
    stroke_width=3,
    font_family="sans-serif",
    tooltip_font_size=22,
    opacity=0.9,
    opacity_hover=1.0,
)

sample_ids = list(range(1, n_samples + 1))
x_labels = [str(i) if i % 5 == 0 or i == 1 else "" for i in sample_ids]

# Common chart config
common_config = {
    "width": 4800,
    "height": 1300,
    "style": custom_style,
    "show_y_guides": True,
    "show_x_guides": False,
    "margin": 25,
    "margin_left": 140,
    "margin_right": 100,
    "spacing": 20,
    "truncate_label": -1,
    "truncate_legend": -1,
    "print_values": False,
    "show_minor_x_labels": True,
    "legend_at_bottom": True,
    "legend_at_bottom_columns": 4,
    "legend_box_size": 20,
    "js": [],
    "explicit_size": True,
    "dots_size": 12,
    "stroke_style": {"width": 4, "linecap": "round", "linejoin": "round"},
}


# --- X-bar Chart ---
xbar_y_min = min(sample_means.min(), xbar_lcl)
xbar_y_max = max(sample_means.max(), xbar_ucl)
xbar_y_pad = (xbar_y_max - xbar_y_min) * 0.15
xbar_chart = pygal.XY(
    **common_config,
    title="spc-xbar-r \u00b7 pygal \u00b7 pyplots.ai",
    x_title="",
    y_title="\u0058\u0304 (mm)",
    margin_bottom=20,
    margin_top=40,
    range=(xbar_y_min - xbar_y_pad, xbar_y_max + xbar_y_pad),
    xrange=(0, n_samples + 1),
    show_legend=True,
    value_formatter=lambda y: f"{y:.3f}" if isinstance(y, (int, float)) else str(y),
)
xbar_chart.x_labels = [float(i) for i in sample_ids]
xbar_chart.x_label_rotation = 0

# Normal points
normal_xbar = [
    {"value": (float(i + 1), float(sample_means[i])), "color": C_NORMAL}
    if not xbar_ooc[i]
    else {"value": (float(i + 1), float(sample_means[i])), "color": C_OOC, "dots_size": 14}
    for i in range(n_samples)
]
xbar_chart.add(
    "Sample Mean", normal_xbar, stroke_style={"width": 4, "linecap": "round", "linejoin": "round"}, show_dots=True
)

# Out-of-control points overlay for legend
ooc_xbar_pts = [(float(i + 1), float(sample_means[i])) for i in range(n_samples) if xbar_ooc[i]]
xbar_chart.add("Out of Control", ooc_xbar_pts, stroke=False, show_dots=True, dots_size=14)

# Center line
xbar_chart.add(
    f"CL = {x_bar_bar:.3f}",
    [(0.5, x_bar_bar), (n_samples + 0.5, x_bar_bar)],
    show_dots=False,
    stroke_style={"width": 4, "linecap": "round"},
)

# UCL and LCL
xbar_chart.add(
    f"UCL = {xbar_ucl:.3f}",
    [(0.5, xbar_ucl), (n_samples + 0.5, xbar_ucl)],
    show_dots=False,
    stroke_style={"width": 3, "dasharray": "16, 8", "linecap": "round"},
)
xbar_chart.add(
    f"LCL = {xbar_lcl:.3f}",
    [(0.5, xbar_lcl), (n_samples + 0.5, xbar_lcl)],
    show_dots=False,
    stroke_style={"width": 3, "dasharray": "16, 8", "linecap": "round"},
)

# Warning limits
xbar_chart.add(
    "+2\u03c3 Warning",
    [(0.5, xbar_uw), (n_samples + 0.5, xbar_uw)],
    show_dots=False,
    stroke_style={"width": 3, "dasharray": "10, 6", "linecap": "round"},
)
xbar_chart.add(
    "-2\u03c3 Warning",
    [(0.5, xbar_lw), (n_samples + 0.5, xbar_lw)],
    show_dots=False,
    stroke_style={"width": 3, "dasharray": "10, 6", "linecap": "round"},
)

# --- R Chart ---
r_y_max = max(sample_ranges.max(), r_ucl)
r_y_pad = r_y_max * 0.15
r_chart = pygal.XY(
    **common_config,
    title="",
    x_title="Sample Number",
    y_title="R (mm)",
    margin_bottom=80,
    margin_top=10,
    range=(0, r_y_max + r_y_pad),
    xrange=(0, n_samples + 1),
    show_legend=True,
    value_formatter=lambda y: f"{y:.3f}" if isinstance(y, (int, float)) else str(y),
)
r_chart.x_labels = [float(i) for i in sample_ids]
r_chart.x_label_rotation = 0

# Range points
range_pts = [
    {"value": (float(i + 1), float(sample_ranges[i])), "color": C_NORMAL}
    if not r_ooc[i]
    else {"value": (float(i + 1), float(sample_ranges[i])), "color": C_OOC, "dots_size": 14}
    for i in range(n_samples)
]
r_chart.add(
    "Sample Range", range_pts, stroke_style={"width": 4, "linecap": "round", "linejoin": "round"}, show_dots=True
)

# Out-of-control R points
ooc_r_pts = [(float(i + 1), float(sample_ranges[i])) for i in range(n_samples) if r_ooc[i]]
if ooc_r_pts:
    r_chart.add("Out of Control", ooc_r_pts, stroke=False, show_dots=True, dots_size=14)

# R center line
r_chart.add(
    f"CL = {r_bar:.3f}",
    [(0.5, r_bar), (n_samples + 0.5, r_bar)],
    show_dots=False,
    stroke_style={"width": 4, "linecap": "round"},
)

# R UCL
r_chart.add(
    f"UCL = {r_ucl:.3f}",
    [(0.5, r_ucl), (n_samples + 0.5, r_ucl)],
    show_dots=False,
    stroke_style={"width": 3, "dasharray": "16, 8", "linecap": "round"},
)

# R LCL (D3=0 for n=5, so LCL = 0)
r_chart.add(
    f"LCL = {r_lcl:.3f}",
    [(0.5, r_lcl), (n_samples + 0.5, r_lcl)],
    show_dots=False,
    stroke_style={"width": 3, "dasharray": "16, 8", "linecap": "round"},
)

# R warning limit
r_chart.add(
    "+2\u03c3 Warning",
    [(0.5, r_uw), (n_samples + 0.5, r_uw)],
    show_dots=False,
    stroke_style={"width": 3, "dasharray": "10, 6", "linecap": "round"},
)

# Render and compose
png_images = []
for chart in [xbar_chart, r_chart]:
    svg_bytes = chart.render()
    png_images.append(cairosvg.svg2png(bytestring=svg_bytes, output_width=4800, output_height=1300))

xbar_img = Image.open(io.BytesIO(png_images[0]))
r_img = Image.open(io.BytesIO(png_images[1]))
combined = Image.new("RGB", (4800, 2700), "white")
combined.paste(xbar_img, (0, 50))
combined.paste(r_img, (0, 1350))

# Subtle divider
draw = ImageDraw.Draw(combined)
draw.line([(140, 1350), (4700, 1350)], fill="#DEE2E6", width=2)

combined.save("plot.png", dpi=(300, 300))
