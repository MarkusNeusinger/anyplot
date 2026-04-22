""" pyplots.ai
band-basic: Basic Band Plot
Library: pygal 3.1.0 | Python 3.14
Quality: 89/100 | Updated: 2026-02-23
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

# Explicit y-axis labels at clean intervals for precise grid control
y_lo = 4 * (int(min(y_lower)) // 4)
y_hi = 4 * (int(max(y_upper)) // 4 + 1)
y_label_values = list(range(y_lo, y_hi + 1, 4))

# Custom style — sans-serif typography, polished palette, refined visual hierarchy
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#2C3E50",
    foreground_strong="#1A252F",
    foreground_subtle="#BDC3C7",
    guide_stroke_color="#F0F0F0",
    guide_stroke_dasharray="2,8",
    major_guide_stroke_color="#E8E8E8",
    major_guide_stroke_dasharray="4,6",
    colors=("#306998", "#B8860B", "#7F8C8D"),
    opacity=".20",
    opacity_hover=".35",
    stroke_opacity="1",
    stroke_opacity_hover="1",
    stroke_width=4,
    title_font_size=60,
    label_font_size=42,
    major_label_font_size=42,
    legend_font_size=40,
    value_font_size=36,
    value_colors=("transparent",),
    tooltip_font_size=32,
    font_family='Helvetica, Arial, "DejaVu Sans", sans-serif',
)

# Create XY chart with fine-tuned layout and pygal-specific configuration
chart = pygal.XY(
    style=custom_style,
    width=4800,
    height=2700,
    explicit_size=True,
    title="band-basic \u00b7 pygal \u00b7 pyplots.ai",
    x_title="Time (hours)",
    y_title="Soil Moisture (%)",
    show_dots=False,
    show_x_guides=False,
    show_y_guides=True,
    fill=True,
    stroke=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    legend_box_size=28,
    truncate_legend=-1,
    x_label_rotation=0,
    range=(y_lo - 1, y_hi + 1),
    y_labels=y_label_values,
    x_labels=[0, 6, 12, 18, 24, 30, 36, 42, 48],
    x_labels_major=[0, 12, 24, 36, 48],
    show_minor_x_labels=True,
    show_minor_y_labels=False,
    print_values=False,
    x_value_formatter=lambda x: f"{x:.0f}h",
    value_formatter=lambda x: f"{x:.1f}%",
    tooltip_border_radius=8,
    margin_top=30,
    margin_bottom=50,
    margin_left=30,
    margin_right=50,
    spacing=18,
    js=[],
)

# Band as closed polygon: upper boundary forward, then lower boundary reversed
band_polygon = [(float(h), float(y)) for h, y in zip(hours, y_upper, strict=True)]
for h, y in zip(reversed(hours), reversed(y_lower), strict=True):
    band_polygon.append((float(h), float(y)))

chart.add(
    "95% Confidence Band",
    band_polygon,
    stroke_style={"width": 0.5, "color": "#306998", "opacity": 0.15},
    show_dots=False,
)

# Central trend line — bold stroke with rounded SVG caps for smooth rendering
center_data = [(float(h), float(y)) for h, y in zip(hours, y_center, strict=True)]
chart.add(
    "Sensor Mean",
    center_data,
    fill=False,
    stroke=True,
    dots_size=0,
    stroke_style={"width": 48, "linecap": "round", "linejoin": "round"},
)

# Wilting point reference — threshold below which plants cannot extract moisture
chart.add(
    "Wilting Point (25%)",
    [(0.0, 25.0), (48.0, 25.0)],
    fill=False,
    stroke=True,
    dots_size=0,
    formatter=lambda x: f"{x:.0f}%",
    stroke_style={"width": 5, "dasharray": "16,10", "linecap": "round"},
)

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
