""" pyplots.ai
frequency-polygon-basic: Frequency Polygon for Distribution Comparison
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-09
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - Three groups of measurements (e.g., plant heights by soil type)
np.random.seed(42)

# Generate three distributions with different characteristics
group_a = np.random.normal(loc=45, scale=8, size=200)  # Sandy soil - lower mean
group_b = np.random.normal(loc=55, scale=10, size=200)  # Loamy soil - medium mean, wider spread
group_c = np.random.normal(loc=60, scale=6, size=200)  # Clay soil - higher mean, narrow spread

# Define bins for frequency calculation
bins = np.linspace(20, 85, 15)
bin_midpoints = (bins[:-1] + bins[1:]) / 2

# Calculate frequencies for each group
freq_a, _ = np.histogram(group_a, bins=bins)
freq_b, _ = np.histogram(group_b, bins=bins)
freq_c, _ = np.histogram(group_c, bins=bins)

# Extend lines to zero at both ends to close the polygon shape
# Convert to Python native types for JSON serialization
midpoints_extended = [float(bins[0])] + [float(m) for m in bin_midpoints] + [float(bins[-1])]
freq_a_extended = [0] + [int(f) for f in freq_a] + [0]
freq_b_extended = [0] + [int(f) for f in freq_b] + [0]
freq_c_extended = [0] + [int(f) for f in freq_c] + [0]

# Custom style for large canvas (4800x2700)
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998", "#FFD43B", "#48a868"),  # Python Blue, Python Yellow, Green
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=42,
    legend_font_size=42,
    value_font_size=36,
    opacity=0.9,
    opacity_hover=1.0,
    guide_stroke_width=1,
    major_guide_stroke_width=1,
    guide_stroke_dasharray="3,3",
    font_family="sans-serif",
)

# Create XY chart for frequency polygon
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="frequency-polygon-basic · pygal · pyplots.ai",
    x_title="Plant Height (cm)",
    y_title="Frequency",
    show_x_guides=False,
    show_y_guides=True,
    dots_size=12,
    stroke_style={"width": 6},
    legend_at_bottom=True,
    legend_box_size=36,
    truncate_legend=-1,
    show_dots=True,
    fill=False,
    x_label_rotation=0,
    range=(0, int(max(max(freq_a), max(freq_b), max(freq_c))) + 5),
    xrange=(15, 90),
)

# Add data series - each point is (x, y) tuple
chart.add("Sandy Soil", list(zip(midpoints_extended, freq_a_extended, strict=True)))
chart.add("Loamy Soil", list(zip(midpoints_extended, freq_b_extended, strict=True)))
chart.add("Clay Soil", list(zip(midpoints_extended, freq_c_extended, strict=True)))

# Save as PNG and HTML
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
