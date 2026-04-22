""" pyplots.ai
rug-basic: Basic Rug Plot
Library: pygal 3.1.0 | Python 3.13.11
Quality: 85/100 | Created: 2025-12-23
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - Response times (in milliseconds) showing realistic clustering patterns
np.random.seed(42)
values = np.concatenate(
    [
        np.random.normal(150, 20, 60),  # Main cluster of typical responses
        np.random.normal(250, 30, 25),  # Slower responses
        np.random.normal(400, 15, 10),  # Occasional outliers
        np.random.uniform(50, 100, 5),  # Very fast responses
    ]
)
values = np.clip(values, 30, 500)  # Realistic bounds
values = np.sort(values)  # Sort for better visual ordering

# Custom style - keep text readable, minimize distracting elements
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998",),  # Python Blue
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=42,
    legend_font_size=42,
    value_font_size=36,
    opacity=0.85,
    opacity_hover=1.0,
    tooltip_font_size=36,
)

# Create XY chart for rug plot visualization
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="rug-basic · pygal · pyplots.ai",
    x_title="Response Time (ms)",
    y_title=None,
    show_legend=False,
    show_dots=False,
    stroke=True,
    stroke_style={"width": 10},
    show_x_guides=False,
    show_y_guides=False,
    show_y_labels=False,
    print_values=False,
    explicit_size=True,
    margin=80,
    margin_top=180,
    margin_bottom=280,
    margin_left=80,
    margin_right=80,
    tooltip_border_radius=10,
    xrange=(30, 450),
    range=(0, 1),
)

# Rug ticks - uniform height filling 90% of vertical canvas
tick_bottom = 0.05
tick_top = 0.95

# Add rug ticks with interactive tooltips showing exact values
for val in values:
    x = float(val)
    chart.add(f"{val:.1f} ms", [(x, tick_bottom), (x, tick_top)], stroke_style={"width": 10}, show_dots=False)

# Save outputs - HTML preserves pygal's SVG interactivity with hover tooltips
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
