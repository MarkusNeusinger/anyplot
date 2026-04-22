""" pyplots.ai
sparkline-basic: Basic Sparkline
Library: pygal 3.1.0 | Python 3.13.11
Quality: 78/100 | Created: 2025-12-23
"""

import pygal
from pygal.style import Style


# Data - simulated daily sales trend with balanced variation
# 30 data points with clear ups and downs, no dominant trend
values = [
    65,
    72,
    80,
    85,
    78,
    70,
    60,
    52,
    45,
    50,
    58,
    68,
    82,
    95,
    105,
    100,
    88,
    75,
    65,
    58,
    62,
    70,
    78,
    85,
    80,
    72,
    65,
    60,
    55,
    58,
]

# Find min/max indices for highlighting
min_val = min(values)
max_val = max(values)
min_idx = values.index(min_val)
max_idx = values.index(max_val)

# Custom style for sparkline - minimal and clean
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="transparent",
    foreground_strong="transparent",
    foreground_subtle="transparent",
    colors=("#306998", "#43A047", "#E53935"),  # Blue line, green max, red min
    title_font_size=72,
    label_font_size=1,
    major_label_font_size=1,
    legend_font_size=1,
    value_font_size=1,
    tooltip_font_size=1,
    stroke_width=8,
    opacity=1.0,
    opacity_hover=1.0,
)

# Compact sparkline aspect ratio (4:1) as per spec
chart = pygal.Line(
    width=4800,
    height=1200,
    style=custom_style,
    show_x_labels=False,
    show_y_labels=False,
    show_x_guides=False,
    show_y_guides=False,
    show_legend=False,
    show_dots=False,
    fill=True,
    interpolate="cubic",
    margin=80,
    title="sparkline-basic · pygal · pyplots.ai",
    dots_size=20,
)

# Add main sparkline data without dots
chart.add("", values)

# Create max point series - only the max point has a value, rest are None
max_series = [None] * len(values)
max_series[max_idx] = max_val
chart.add("", max_series, stroke=False, show_dots=True, fill=False)

# Create min point series - only the min point has a value, rest are None
min_series = [None] * len(values)
min_series[min_idx] = min_val
chart.add("", min_series, stroke=False, show_dots=True, fill=False)

# Save outputs
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
