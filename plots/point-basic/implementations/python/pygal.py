""" pyplots.ai
point-basic: Point Estimate Plot
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import pygal
from pygal.style import Style


# Data: Treatment effects with 95% confidence intervals
categories = ["Treatment A", "Treatment B", "Treatment C", "Treatment D", "Control"]
estimates = [2.4, 1.8, 3.2, 0.9, 0.0]
lower_bounds = [1.6, 0.9, 2.5, -0.2, -0.5]
upper_bounds = [3.2, 2.7, 3.9, 2.0, 0.5]

# Custom style for 4800x2700 canvas
ci_color = "#306998"
point_color = "#FFD43B"
ref_color = "#888888"

custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#999999",
    colors=(ref_color, ci_color, ci_color, ci_color, ci_color, ci_color, point_color),
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=42,
    legend_font_size=42,
    value_font_size=36,
    stroke_width=6,
    guide_stroke_color="#e0e0e0",
)

# Create XY chart for point estimates with confidence intervals
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="point-basic · pygal · pyplots.ai",
    x_title="Effect Size",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    show_y_guides=True,
    show_x_guides=True,
    dots_size=30,
    stroke=False,
    margin_left=120,
    margin_right=120,
    margin_top=150,
    margin_bottom=180,
    xrange=(-1.5, 4.5),
    range=(0, 6),
)

# Map categories to y-values (numeric) - reversed for top-to-bottom display
y_positions = list(range(len(categories), 0, -1))

# Add reference line at zero first (so it appears behind other elements)
ref_line = [(0, 0.3), (0, 5.7)]
chart.add("Reference (x=0)", ref_line, stroke=True, show_dots=False, stroke_width=3)

# Add each CI as a separate series (to avoid connecting lines)
for i, (low, high, y) in enumerate(zip(lower_bounds, upper_bounds, y_positions, strict=True)):
    ci_data = [(low, y), (high, y)]
    # First CI gets label, others are hidden from legend using None
    if i == 0:
        chart.add("95% CI", ci_data, stroke=True, show_dots=False, stroke_width=8)
    else:
        chart.add(None, ci_data, stroke=True, show_dots=False, stroke_width=8)

# Add point estimates (on top of CI lines)
point_data = [(est, y) for est, y in zip(estimates, y_positions, strict=True)]
chart.add("Point Estimate", point_data, dots_size=32, stroke=False)

# Custom y-axis labels with category names - use major labels
chart.y_labels_major = [5, 4, 3, 2, 1]
chart.y_labels = [
    {"value": 5, "label": "Treatment A"},
    {"value": 4, "label": "Treatment B"},
    {"value": 3, "label": "Treatment C"},
    {"value": 2, "label": "Treatment D"},
    {"value": 1, "label": "Control"},
]

# Save as PNG and HTML
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
