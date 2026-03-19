"""pyplots.ai
histogram-capability: Process Capability Plot with Specification Limits
Library: pygal 3.1.0 | Python 3.14.3
Quality: 81/100 | Created: 2026-03-19
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

# Normal curve scaled to histogram
x_curve = np.linspace(mean - 4 * sigma, mean + 4 * sigma, 300)
y_curve = stats.norm.pdf(x_curve, mean, sigma) * len(measurements) * bin_width

# Style - colorblind-safe palette (no red-green distinction)
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#e0e0e0",
    colors=("#306998", "#1a5276", "#d35400", "#d35400", "#2980b9", "#7f8c8d"),
    title_font_size=64,
    label_font_size=44,
    major_label_font_size=40,
    legend_font_size=38,
    value_font_size=28,
    stroke_width=4,
    opacity=0.75,
    opacity_hover=0.90,
    font_family="'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
)

# Chart - using pygal.Histogram for idiomatic histogram rendering
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
    xrange=(lsl - 2.5 * sigma, usl + 2.5 * sigma),
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

# Histogram bars using pygal.Histogram native format: (height, start, end)
hist_data = [(float(counts[i]), float(bin_edges[i]), float(bin_edges[i + 1])) for i in range(len(counts))]
chart.add("Measurements", hist_data)

# Normal distribution curve - as XY overlay using secondary series
# pygal.Histogram also accepts (height, x, x) for point-width bars to approximate a curve
curve_data = []
dx = x_curve[1] - x_curve[0]
for x, y in zip(x_curve, y_curve, strict=True):
    curve_data.append((float(y), float(x), float(x + dx)))
chart.add("Normal fit", curve_data, stroke_style={"width": 5, "linecap": "round"})

# LSL vertical line - orange for colorblind safety
y_max = float(max(counts) * 1.2)
chart.add("LSL (9.95)", [(y_max, float(lsl), float(lsl + 0.0001))], stroke_style={"width": 6, "dasharray": "18,8"})

# USL vertical line - orange (same series color)
chart.add("USL (10.05)", [(y_max, float(usl), float(usl + 0.0001))], stroke_style={"width": 6, "dasharray": "18,8"})

# Target vertical line - blue, distinct from orange spec limits
chart.add(
    "Target (10.00)", [(y_max, float(target), float(target + 0.0001))], stroke_style={"width": 5, "dasharray": "10,5"}
)

# Mean vertical line - gray, different dash pattern for clear distinction
chart.add(
    f"Mean ({mean:.3f})", [(y_max, float(mean), float(mean + 0.0001))], stroke_style={"width": 3, "dasharray": "3,6"}
)

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
