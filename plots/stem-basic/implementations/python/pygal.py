""" pyplots.ai
stem-basic: Basic Stem Plot
Library: pygal 3.1.0 | Python 3.13.11
Quality: 86/100 | Created: 2025-12-23
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - discrete signal samples demonstrating impulse response
np.random.seed(42)
n_points = 30
x = np.arange(n_points)
# Create a decaying oscillation pattern (typical impulse response)
y = np.exp(-x / 8) * np.sin(x * 0.8) * 2 + np.random.randn(n_points) * 0.1

# Custom style for 4800×2700 px canvas with larger fonts
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998",),  # Single color for consistency
    title_font_size=84,
    label_font_size=56,
    major_label_font_size=48,
    legend_font_size=48,
    value_font_size=40,
    stroke_width=10,  # Thicker stem lines for visibility
)

# Create XY chart for stem plot
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="stem-basic · pygal · pyplots.ai",
    x_title="Sample Index (n)",
    y_title="Amplitude (a.u.)",  # Use parentheses instead of brackets for better rendering
    show_legend=False,
    show_dots=True,
    stroke=True,
    dots_size=30,  # Larger dots for better marker visibility
    stroke_style={"width": 10},  # Thicker stem lines
    show_x_guides=False,
    show_y_guides=True,
)

# Build all stems as coordinate pairs for a single series
# Each stem goes from (x, 0) to (x, y), with None separator between stems
stem_data = []
for i in range(n_points):
    xi = float(x[i])
    yi = float(y[i])
    stem_data.append((xi, 0))
    stem_data.append((xi, yi))
    stem_data.append(None)  # Separator between stems

# Add all stems as a single series for consistent coloring
chart.add("", stem_data, show_dots=True, dots_size=30, stroke_style={"width": 10})

# Save as PNG and HTML
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
