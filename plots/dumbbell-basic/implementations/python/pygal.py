""" pyplots.ai
dumbbell-basic: Basic Dumbbell Chart
Library: pygal 3.1.0 | Python 3.13.11
Quality: 58/100 | Created: 2025-12-23
"""

import pygal
from pygal.style import Style


# Data - Employee satisfaction scores before and after policy changes
# Includes positive changes, no change, and slight decrease to demonstrate full capability
categories = ["Engineering", "Marketing", "Sales", "HR", "Finance", "Operations", "Customer Support", "Product"]
before = [65, 58, 72, 45, 71, 52, 70, 70]
after = [82, 75, 78, 72, 65, 71, 70, 85]  # Finance decreased (-6), Customer Support unchanged (0)

# Sort by difference (improvement) for better pattern visibility
differences = [a - b for a, b in zip(after, before, strict=True)]
sorted_data = sorted(zip(categories, before, after, differences, strict=True), key=lambda x: x[3], reverse=True)
categories = [item[0] for item in sorted_data]
before = [item[1] for item in sorted_data]
after = [item[2] for item in sorted_data]

# Number of categories
n = len(categories)

# Custom style for 4800x2700 canvas
# Colors: gray for connecting lines (8 series), then blue for before, yellow for after
connector_colors = tuple(["#888888"] * n)  # Gray for each connector line
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#AAAAAA",
    guide_stroke_color="rgba(200, 200, 200, 0.3)",  # Subtle grid with low opacity
    guide_stroke_dasharray="5,5",  # Dashed grid for subtlety
    colors=connector_colors + ("#306998", "#FFD43B"),  # Gray connectors, Blue before, Yellow after
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=42,
    legend_font_size=56,
    value_font_size=36,
    value_label_font_size=36,
    stroke_width=5,  # Default stroke width for connecting lines
)

# Create XY chart for dumbbell visualization
chart = pygal.XY(
    width=4800,
    height=2700,
    title="dumbbell-basic · pygal · pyplots.ai",
    x_title="Satisfaction Score (%)",
    style=custom_style,
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=28,
    dots_size=20,
    stroke=True,  # Enable stroke globally
    show_y_guides=True,
    show_x_guides=True,
    margin=80,
    margin_bottom=120,
    xrange=(30, 100),
    range=(0, n + 1),
    y_labels=[{"label": cat, "value": n - i} for i, cat in enumerate(categories)],
)

# Add connecting lines (gray) - each dumbbell gets its own series with stroke enabled
for i, (_cat, b, a) in enumerate(zip(categories, before, after, strict=True)):
    y_pos = n - i
    # Use explicit stroke and minimal dot size for connecting lines
    chart.add(None, [(b, y_pos), (a, y_pos)], stroke=True, show_dots=False)

# Add "Before" dots (Python Blue) - circles without connecting stroke
before_points = [(b, n - i) for i, b in enumerate(before)]
chart.add("Before Policy Change", before_points, dots_size=25, stroke=False)

# Add "After" dots (Python Yellow) - circles without connecting stroke
after_points = [(a, n - i) for i, a in enumerate(after)]
chart.add("After Policy Change", after_points, dots_size=25, stroke=False)

# Save outputs
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
