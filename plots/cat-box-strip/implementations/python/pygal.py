""" pyplots.ai
cat-box-strip: Box Plot with Strip Overlay
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - Plant growth measurements (cm) under different light conditions
np.random.seed(42)
categories = ["Full Sun", "Partial Shade", "Full Shade", "Artificial"]
data = {
    "Full Sun": np.random.normal(45, 8, 35),
    "Partial Shade": np.random.normal(38, 10, 40),
    "Full Shade": np.random.normal(25, 6, 30),
    "Artificial": np.random.normal(35, 12, 38),
}

# Add realistic variation and some outliers
data["Full Sun"] = np.append(data["Full Sun"], [68, 72, 28])
data["Partial Shade"] = np.append(data["Partial Shade"], [65, 15])
data["Full Shade"] = np.append(data["Full Shade"], [42, 10])
data["Artificial"] = np.append(data["Artificial"], [70, 12])

# Group colors - distinct for each category (colorblind-safe)
group_colors = ["#306998", "#FFD43B", "#4CAF50", "#E07B39"]

# Build color sequence: 6 elements per box (box, median, 2 whiskers, 2 caps) + 1 strip = 7 per category
# But we draw all boxes first (6*4=24), then all strips (4)
# So color sequence needs: 6 of color1, 6 of color2, 6 of color3, 6 of color4, then 1 each for strips
color_sequence = []
for c in group_colors:
    color_sequence.extend([c] * 6)  # 6 box elements per category
for c in group_colors:
    color_sequence.append(c)  # 1 strip series per category

# Custom style for 4800x2700 px canvas
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#999999",
    guide_stroke_color="#e0e0e0",
    colors=tuple(color_sequence),
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    opacity=0.6,
    opacity_hover=0.8,
)

# Create XY chart for combined box plot with strip overlay
# X-axis = Category position, Y-axis = Plant Height (cm)
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="cat-box-strip · pygal · pyplots.ai",
    x_title="Light Condition",
    y_title="Plant Height (cm)",
    show_legend=False,
    stroke=True,
    fill=True,
    dots_size=0,
    show_x_guides=False,
    show_y_guides=True,
    xrange=(0, 5),
    range=(0, 80),
    margin=80,
    explicit_size=True,
)

# Layout parameters
box_width = 0.25
cap_width = 0.15

# Pre-compute all components
strip_data = []
box_data = []

for i, (category, values) in enumerate(data.items()):
    center_x = i + 1  # X position for this group (1, 2, 3, 4)
    values = np.array(values)
    color = group_colors[i]

    # --- Box Plot Statistics ---
    median = float(np.median(values))
    q1 = float(np.percentile(values, 25))
    q3 = float(np.percentile(values, 75))
    iqr = q3 - q1
    whisker_low = float(max(values.min(), q1 - 1.5 * iqr))
    whisker_high = float(min(values.max(), q3 + 1.5 * iqr))
    box_data.append((center_x, median, q1, q3, whisker_low, whisker_high, color))

    # --- Strip Points with Jitter ---
    np.random.seed(42 + i)
    jitter = np.random.uniform(-0.12, 0.12, len(values))
    strip_points = [(center_x + j, float(v)) for j, v in zip(jitter, values, strict=True)]
    strip_data.append((category, strip_points, color))

# First, draw box plots (so strip points appear on top)
for center_x, median, q1, q3, whisker_low, whisker_high, _color in box_data:
    # IQR box (filled rectangle)
    quartile_box = [
        (center_x - box_width, q1),
        (center_x - box_width, q3),
        (center_x + box_width, q3),
        (center_x + box_width, q1),
        (center_x - box_width, q1),
    ]
    chart.add("", quartile_box, stroke=True, fill=True, show_dots=False, stroke_style={"width": 6})

    # Median line (horizontal line within box)
    median_line = [(center_x - box_width * 1.1, median), (center_x + box_width * 1.1, median)]
    chart.add("", median_line, stroke=True, fill=False, show_dots=False, stroke_style={"width": 10})

    # Whiskers (vertical lines from box to caps)
    whisker_bottom = [(center_x, q1), (center_x, whisker_low)]
    whisker_top = [(center_x, q3), (center_x, whisker_high)]
    chart.add("", whisker_bottom, stroke=True, fill=False, show_dots=False, stroke_style={"width": 6})
    chart.add("", whisker_top, stroke=True, fill=False, show_dots=False, stroke_style={"width": 6})

    # Whisker caps (horizontal lines at ends)
    cap_bottom = [(center_x - cap_width, whisker_low), (center_x + cap_width, whisker_low)]
    cap_top = [(center_x - cap_width, whisker_high), (center_x + cap_width, whisker_high)]
    chart.add("", cap_bottom, stroke=True, fill=False, show_dots=False, stroke_style={"width": 6})
    chart.add("", cap_top, stroke=True, fill=False, show_dots=False, stroke_style={"width": 6})

# Add strip points on top with transparency
for _category, strip_points, _color in strip_data:
    chart.add("", strip_points, stroke=False, fill=False, dots_size=18)

# X-axis labels for categories
chart.x_labels = [
    {"value": 0, "label": ""},
    {"value": 1, "label": "Full Sun"},
    {"value": 2, "label": "Partial Shade"},
    {"value": 3, "label": "Full Shade"},
    {"value": 4, "label": "Artificial"},
    {"value": 5, "label": ""},
]

# Save outputs
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
