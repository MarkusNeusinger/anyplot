"""pyplots.ai
histogram-capability: Process Capability Plot with Specification Limits
Library: pygal | Python 3.13
Quality: pending | Created: 2026-03-19
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
n_bins = 25
counts, bin_edges = np.histogram(measurements, bins=n_bins)
bin_width = bin_edges[1] - bin_edges[0]
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

# Normal curve scaled to histogram
x_curve = np.linspace(mean - 4 * sigma, mean + 4 * sigma, 300)
y_curve = stats.norm.pdf(x_curve, mean, sigma) * len(measurements) * bin_width

# Style
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#e0e0e0",
    colors=("#306998", "#1a5276", "#c0392b", "#c0392b", "#27ae60", "#888888"),
    title_font_size=72,
    label_font_size=44,
    major_label_font_size=40,
    legend_font_size=36,
    value_font_size=28,
    stroke_width=4,
    opacity=0.75,
    opacity_hover=0.90,
    font_family="'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
)

# Chart
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="histogram-capability · pygal · pyplots.ai",
    x_title="Shaft Diameter (mm)",
    y_title="Frequency",
    show_dots=False,
    fill=False,
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
    xrange=(min(lsl - 3 * sigma, measurements.min() - sigma), max(usl + 3 * sigma, measurements.max() + sigma)),
    range=(0, max(counts) * 1.25),
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

# Histogram bars as step-like XY series
hist_points = []
for i in range(len(counts)):
    left = float(bin_edges[i])
    right = float(bin_edges[i + 1])
    height = float(counts[i])
    hist_points.append((left, 0.0))
    hist_points.append((left, height))
    hist_points.append((right, height))
    hist_points.append((right, 0.0))

chart.add("Measurements", hist_points, fill=True, stroke_style={"width": 2})

# Normal distribution curve
curve_points = [(float(x), float(y)) for x, y in zip(x_curve, y_curve, strict=True)]
chart.add(f"Normal fit (Cp={cp:.2f}, Cpk={cpk:.2f})", curve_points, stroke_style={"width": 5, "linecap": "round"})

# LSL vertical line
y_max = float(max(counts) * 1.2)
chart.add("LSL (9.95)", [(float(lsl), 0.0), (float(lsl), y_max)], stroke_style={"width": 5, "dasharray": "15,8"})

# USL vertical line
chart.add("USL (10.05)", [(float(usl), 0.0), (float(usl), y_max)], stroke_style={"width": 5, "dasharray": "15,8"})

# Target vertical line
chart.add(
    "Target (10.00)", [(float(target), 0.0), (float(target), y_max)], stroke_style={"width": 4, "dasharray": "8,6"}
)

# Mean vertical line
chart.add(
    f"Mean ({mean:.3f})", [(float(mean), 0.0), (float(mean), y_max)], stroke_style={"width": 3, "dasharray": "4,4"}
)

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
