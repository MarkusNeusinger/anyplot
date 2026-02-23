"""pyplots.ai
band-basic: Basic Band Plot
Library: pygal 3.1.0 | Python 3.14
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - Soil moisture sensor readings with 95% confidence interval
np.random.seed(42)
n_points = 80
hours = np.linspace(0, 48, n_points)

# Realistic soil moisture pattern: starts high after rain, drops during day,
# recovers slightly at night, then dips to a low before a second rain event
base_trend = 38 - 0.3 * hours + 4.0 * np.sin(2 * np.pi * hours / 24) + 8.0 * np.exp(-((hours - 40) ** 2) / 8)
noise = np.random.randn(n_points) * 0.6
y_raw = base_trend + noise

# Smooth with convolution, padding edges to preserve length
kernel = np.ones(7) / 7
y_smooth = np.convolve(y_raw, kernel, mode="valid")
pad_left = (n_points - len(y_smooth)) // 2
pad_right = n_points - len(y_smooth) - pad_left
y_center = np.concatenate([np.full(pad_left, y_smooth[0]), y_smooth, np.full(pad_right, y_smooth[-1])])

# Confidence interval: wider during dry spell, narrower after rain
uncertainty = 1.2 + 0.8 * np.sin(2 * np.pi * hours / 24) ** 2 + 0.04 * hours
y_lower = y_center - uncertainty
y_upper = y_center + uncertainty

# Custom style — refined palette with low-opacity band
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#2C3E50",
    foreground_strong="#1A252F",
    foreground_subtle="#BDC3C7",
    guide_stroke_color="#E0E0E0",
    colors=("#306998", "#D4880F"),
    opacity=".30",
    opacity_hover=".45",
    stroke_width=4,
    title_font_size=60,
    label_font_size=42,
    major_label_font_size=42,
    legend_font_size=42,
    value_font_size=36,
    value_colors=("transparent",),
    tooltip_font_size=32,
    major_guide_stroke_dasharray="6,3",
)

# Create XY chart
chart = pygal.XY(
    style=custom_style,
    width=4800,
    height=2700,
    title="band-basic \u00b7 pygal \u00b7 pyplots.ai",
    x_title="Time (hours)",
    y_title="Soil Moisture (%)",
    show_dots=False,
    show_x_guides=False,
    show_y_guides=True,
    fill=True,
    stroke=True,
    legend_at_bottom=True,
    truncate_legend=-1,
    x_label_rotation=0,
    range=(min(y_lower) - 1, max(y_upper) + 2),
    x_labels=[0, 6, 12, 18, 24, 30, 36, 42, 48],
    x_labels_major=[0, 12, 24, 36, 48],
    show_minor_x_labels=True,
    show_minor_y_labels=True,
    print_values=False,
    formatter=lambda x: f"{x:.1f}%",
    tooltip_border_radius=6,
    js=[],
)

# Band as closed polygon: upper boundary forward, then lower boundary reversed
band_polygon = [(float(h), float(y)) for h, y in zip(hours, y_upper, strict=True)]
for h, y in zip(reversed(hours), reversed(y_lower), strict=True):
    band_polygon.append((float(h), float(y)))

chart.add("95% Confidence Band", band_polygon, stroke_style={"width": 0.5, "dasharray": "0"}, show_dots=False)

# Central trend line — thicker stroke, no fill, contrasting gold
center_data = [(float(h), float(y)) for h, y in zip(hours, y_center, strict=True)]
chart.add("Sensor Mean", center_data, fill=False, stroke=True, dots_size=0, stroke_style={"width": 8})

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
