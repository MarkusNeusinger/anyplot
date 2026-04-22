""" pyplots.ai
density-rug: Density Plot with Rug Marks
Library: pygal 3.1.0 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-09
"""

import numpy as np
import pygal
from pygal.style import Style
from scipy.stats import gaussian_kde


# Data - bimodal distribution to show interesting density shape
np.random.seed(42)
values = np.concatenate(
    [
        np.random.normal(loc=35, scale=8, size=60),  # First mode
        np.random.normal(loc=65, scale=10, size=90),  # Second mode
    ]
)

# Calculate KDE
kde = gaussian_kde(values)
x_range = np.linspace(values.min() - 10, values.max() + 10, 200)
density = kde(x_range)

# Scale density for visibility
density_scaled = density / density.max()

# Custom style for pyplots (scaled for 4800x2700 canvas)
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998", "#FFD43B"),  # Python Blue for KDE, Yellow for rug
    title_font_size=56,
    label_font_size=36,
    major_label_font_size=32,
    legend_font_size=32,
    value_font_size=28,
    stroke_width=4,
    opacity=".7",
    opacity_hover=".9",
)

# Create XY chart for continuous data
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="density-rug · pygal · pyplots.ai",
    x_title="Value",
    y_title="Density (normalized)",
    show_legend=True,
    legend_at_bottom=True,
    stroke=True,
    fill=True,
    show_dots=False,
    show_x_guides=True,
    show_y_guides=True,
    range=(0, 1.15),
    include_x_axis=True,
    truncate_legend=-1,
)

# Add KDE curve as line with fill
kde_points = [(float(x), float(y)) for x, y in zip(x_range, density_scaled, strict=True)]
chart.add("KDE Density Curve", kde_points, stroke_style={"width": 5})

# Add rug marks as tick marks along the x-axis at y=0
# Position marks at y=0 and use dots as visual markers for each data point
# In pygal, this is the closest approximation to traditional rug marks
sorted_values = np.sort(values)
rug_points = [(float(v), 0.0) for v in sorted_values]

# Use small dots at the axis line to represent rug marks
# This is pygal's best approximation of rug tick marks
chart.add("Rug Marks", rug_points, stroke=False, show_dots=True, fill=False, dots_size=10)

# Save as PNG and HTML
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
