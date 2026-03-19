""" pyplots.ai
histogram-capability: Process Capability Plot with Specification Limits
Library: pygal 3.1.0 | Python 3.14.3
Quality: 82/100 | Created: 2026-03-19
"""

import numpy as np
import pygal
from pygal.style import Style
from scipy import stats


# Data - Shaft diameter measurements (mm)
np.random.seed(42)
lsl = 9.95
usl = 10.05
target = 10.00
measurements = np.random.normal(loc=10.002, scale=0.012, size=200)

# Statistics
mean = np.mean(measurements)
sigma = np.std(measurements, ddof=1)
cp = (usl - lsl) / (6 * sigma)
cpk = min((usl - mean) / (3 * sigma), (mean - lsl) / (3 * sigma))

# Histogram bins
n_bins = 20
counts, bin_edges = np.histogram(measurements, bins=n_bins)
bin_width = bin_edges[1] - bin_edges[0]

# Normal curve - use fewer, wider bars for a clean envelope look
n_curve_pts = 60
x_curve = np.linspace(mean - 4 * sigma, mean + 4 * sigma, n_curve_pts)
y_curve = stats.norm.pdf(x_curve, mean, sigma) * len(measurements) * bin_width
dx_curve = x_curve[1] - x_curve[0]

# Style - colorblind-safe palette with distinct colors per series
# Order: histogram(blue), curve(purple), LSL(orange), USL(orange), target(teal), mean(gray)
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#e0e0e0",
    colors=("#306998", "#8e44ad", "#d35400", "#d35400", "#16a085", "#555555"),
    title_font_size=64,
    label_font_size=44,
    major_label_font_size=40,
    legend_font_size=38,
    value_font_size=28,
    stroke_width=4,
    opacity=0.80,
    opacity_hover=0.90,
    font_family="'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
)

# Chart
y_ceil = float(max(counts) * 1.3)
chart = pygal.Histogram(
    width=4800,
    height=2700,
    style=custom_style,
    title="histogram-capability · pygal · pyplots.ai  |  Cp = {:.2f}  ·  Cpk = {:.2f}".format(cp, cpk),
    x_title="Shaft Diameter (mm)",
    y_title="Frequency",
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=28,
    show_y_guides=True,
    show_x_guides=False,
    truncate_label=-1,
    truncate_legend=-1,
    margin_top=40,
    margin_right=60,
    margin_bottom=30,
    margin_left=20,
    x_value_formatter=lambda x: f"{x:.3f}",
    y_value_formatter=lambda y: f"{y:.0f}",
    xrange=(lsl - 3 * sigma, usl + 3 * sigma),
    range=(0, y_ceil),
    css=[
        "file://style.css",
        "inline:.plot .background {fill: white !important; stroke: none !important;}",
        "inline:.graph > .background {fill: white !important; stroke: none !important;}",
        "inline:.axis .guides .line {stroke: #e0e0e0 !important; stroke-width: 0.8px;}",
        "inline:.axis.x > path.line {stroke: none !important;}",
        "inline:.axis.y > path.line {stroke: none !important;}",
        "inline:text.title {font-weight: 600 !important; fill: #222222 !important;}",
        "inline:.legends text {font-weight: 400 !important; fill: #444444 !important;}",
    ],
    js=[],
)

# Histogram bars using pygal.Histogram native format: (height, start, end)
hist_data = [(float(counts[i]), float(bin_edges[i]), float(bin_edges[i + 1])) for i in range(len(counts))]
chart.add("Measurements", hist_data)

# Normal distribution curve - fewer wider bars for smooth envelope appearance
curve_data = [(float(y), float(x), float(x + dx_curve)) for x, y in zip(x_curve, y_curve, strict=True)]
chart.add("Normal fit", curve_data, stroke_style={"width": 3, "linecap": "round"})

# LSL vertical line - wide bar for visibility
line_width = 0.0008
chart.add(
    "LSL (9.95)",
    [(y_ceil, float(lsl - line_width), float(lsl + line_width))],
    stroke_style={"width": 8, "dasharray": "18,8"},
)

# USL vertical line
chart.add(
    "USL (10.05)",
    [(y_ceil, float(usl - line_width), float(usl + line_width))],
    stroke_style={"width": 8, "dasharray": "18,8"},
)

# Target vertical line - teal, distinct from orange spec limits
chart.add(
    "Target (10.00)",
    [(y_ceil, float(target - line_width), float(target + line_width))],
    stroke_style={"width": 6, "dasharray": "12,6"},
)

# Mean vertical line - dark gray, dotted pattern
chart.add(
    f"Mean ({mean:.3f})",
    [(y_ceil, float(mean - line_width / 2), float(mean + line_width / 2))],
    stroke_style={"width": 4, "dasharray": "4,8"},
)

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
