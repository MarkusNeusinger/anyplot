""" pyplots.ai
band-basic: Basic Band Plot
Library: pygal 3.1.0 | Python 3.14
Quality: 78/100 | Updated: 2026-02-23
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - Time series with 95% confidence interval
np.random.seed(42)
n_points = 50
x = np.linspace(0, 10, n_points)
# Central trend line (quadratic curve with noise)
y_raw = 2 + 0.5 * x + 0.1 * x**2 + np.random.randn(n_points) * 0.3
# Smooth with valid-mode convolution, then pad edges to preserve length
kernel = np.ones(5) / 5
y_smooth = np.convolve(y_raw, kernel, mode="valid")
# Pad edges with first/last smoothed values to match original length
pad_left = (n_points - len(y_smooth)) // 2
pad_right = n_points - len(y_smooth) - pad_left
y_center = np.concatenate([np.full(pad_left, y_smooth[0]), y_smooth, np.full(pad_right, y_smooth[-1])])
# Confidence interval widens with x (increasing uncertainty)
uncertainty = 0.5 + 0.15 * x
y_lower = y_center - uncertainty
y_upper = y_center + uncertainty

# Custom style for 4800x2700 canvas
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    guide_stroke_color="#AAAAAA",
    colors=("#306998", "#E8A317"),
    opacity=".65",
    opacity_hover=".75",
    stroke_width=5,
    title_font_size=60,
    label_font_size=42,
    major_label_font_size=42,
    legend_font_size=42,
    value_font_size=36,
)

# Create XY chart with fill enabled for area rendering
chart = pygal.XY(
    style=custom_style,
    width=4800,
    height=2700,
    title="band-basic \u00b7 pygal \u00b7 pyplots.ai",
    x_title="Time (s)",
    y_title="Measurement Value",
    show_dots=False,
    show_x_guides=True,
    show_y_guides=True,
    fill=True,
    stroke=True,
    legend_at_bottom=True,
    truncate_legend=-1,
)

# Create band as a closed polygon: upper boundary forward, then lower backward
band_polygon = [(float(xi), float(yi)) for xi, yi in zip(x, y_upper, strict=True)]
for xi, yi in zip(reversed(x), reversed(y_lower), strict=True):
    band_polygon.append((float(xi), float(yi)))

chart.add("Confidence Band", band_polygon, stroke_style={"width": 0.1}, show_dots=False)

# Add center line (no fill, just stroke)
center_data = [(float(xi), float(yi)) for xi, yi in zip(x, y_center, strict=True)]
chart.add("Central Trend", center_data, fill=False, stroke=True, dots_size=0, stroke_style={"width": 6})

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
