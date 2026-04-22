""" pyplots.ai
lollipop-basic: Basic Lollipop Chart
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import pygal
from pygal.style import Style


# Data - Product sales by category (sorted by value for better readability)
categories = ["Smartphones", "Laptops", "Tablets", "Headphones", "Smartwatches", "Cameras", "Speakers", "Gaming"]
values = [892, 654, 478, 312, 287, 198, 156, 134]

# Sort by value descending (already sorted in this example)
sorted_data = sorted(zip(categories, values, strict=True), key=lambda x: x[1], reverse=True)
categories = [item[0] for item in sorted_data]
values = [item[1] for item in sorted_data]

# Custom style for 4800x2700 canvas with visible stroke
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998",) * len(categories),  # Python Blue for all series
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=42,
    legend_font_size=42,
    value_font_size=36,
    value_label_font_size=36,
    stroke_width=8,  # Line width in style
)

# Create horizontal lollipop chart using XY
# Categories on y-axis, values on x-axis (horizontal orientation)
n = len(categories)
chart = pygal.XY(
    width=4800,
    height=2700,
    title="lollipop-basic · pygal · pyplots.ai",
    x_title="Sales (units)",
    style=custom_style,
    show_legend=False,
    dots_size=24,
    stroke=True,  # Enable stroke/lines
    show_y_guides=True,
    show_x_guides=True,
    margin=100,
    xrange=(0, max(values) * 1.1),
    range=(0.5, n + 0.5),
    y_labels=[{"label": cat, "value": n - i} for i, cat in enumerate(categories)],
)

# Add lollipop data - each is a line from x=0 to value
for i, (cat, val) in enumerate(zip(categories, values, strict=True)):
    y_pos = n - i
    # Hide dot at baseline (r=0), show large dot at value end
    chart.add(cat, [{"value": (0, y_pos), "node": {"r": 0}}, {"value": (val, y_pos)}])

# Save outputs
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
