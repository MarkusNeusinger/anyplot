""" pyplots.ai
line-confidence: Line Plot with Confidence Interval
Library: pygal 3.1.0 | Python 3.13.11
Quality: 58/100 | Created: 2025-12-26
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - Model predictions with 95% confidence interval
np.random.seed(42)

# Time points (e.g., weeks)
x = np.linspace(0, 12, 50)

# Central prediction: exponential growth pattern (e.g., user growth model)
y_center = 1000 + 500 * (1 - np.exp(-0.3 * x)) + np.random.randn(50) * 20
# Smooth the center line
y_center = np.convolve(y_center, np.ones(5) / 5, mode="same")
y_center[0:2] = y_center[2]  # Fix edge effects from convolution
y_center[-2:] = y_center[-3]

# Confidence interval widens over time (increasing uncertainty in predictions)
uncertainty = 30 + 15 * x
y_lower = y_center - uncertainty
y_upper = y_center + uncertainty

# Custom style for 4800x2700 canvas
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    guide_stroke_color="#cccccc",
    colors=(
        "rgba(48, 105, 152, 0.25)",  # Semi-transparent blue for confidence band
        "#306998",  # Solid dark blue for predicted mean line
    ),
    opacity="1",
    opacity_hover="1",
    title_font_size=60,
    label_font_size=42,
    major_label_font_size=42,
    legend_font_size=42,
    value_font_size=36,
)

# Create XY chart
chart = pygal.XY(
    style=custom_style,
    width=4800,
    height=2700,
    title="line-confidence · pygal · pyplots.ai",
    x_title="Time (weeks)",
    y_title="Predicted Users",
    show_dots=False,
    show_x_guides=True,
    show_y_guides=True,
    fill=True,
    legend_at_bottom=True,
    truncate_legend=-1,
    range=(float(y_lower.min() - 50), float(y_upper.max() + 50)),
)

# Create confidence band as a closed polygon:
# Trace upper bound left-to-right, then lower bound right-to-left
# This forms a closed shape that pygal can fill
confidence_band = []

# Forward pass: upper bound (left to right)
for xi, yi in zip(x, y_upper, strict=True):
    confidence_band.append((float(xi), float(yi)))

# Backward pass: lower bound (right to left) - closes the polygon
for xi, yi in zip(reversed(x), reversed(y_lower), strict=True):
    confidence_band.append((float(xi), float(yi)))

# Center line data
center_data = [(float(xi), float(yi)) for xi, yi in zip(x, y_center, strict=True)]

# Add confidence band (filled polygon)
chart.add("95% Confidence Interval", confidence_band, show_dots=False, stroke=False)

# Add center line (solid stroke, no fill)
chart.add("Predicted Mean", center_data, fill=False, stroke=True, show_dots=False, stroke_style={"width": 6})

# Save outputs
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
