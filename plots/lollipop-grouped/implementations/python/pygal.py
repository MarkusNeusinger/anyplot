""" pyplots.ai
lollipop-grouped: Grouped Lollipop Chart
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-09
"""

import pygal
from pygal.style import Style


# Data: Quarterly revenue (in millions) by product line across regions
categories = ["North", "South", "East", "West"]
series_names = ["Electronics", "Furniture", "Apparel"]
series_values = [
    [42, 35, 48, 31],  # Electronics
    [28, 32, 25, 38],  # Furniture
    [15, 22, 18, 26],  # Apparel
]
colors = ["#306998", "#FFD43B", "#2ecc71"]

# Build color list: each lollipop gets its series color
# Order: all Electronics lollipops, all Furniture, all Apparel
all_colors = []
for color in colors:
    all_colors.extend([color] * len(categories))

# Custom style for 4800x2700 canvas
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=tuple(all_colors),
    title_font_size=48,
    label_font_size=32,
    major_label_font_size=28,
    legend_font_size=28,
    value_font_size=20,
)

# Create XY chart for lollipop visualization
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="lollipop-grouped · pygal · pyplots.ai",
    x_title="Region",
    y_title="Revenue ($ millions)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    show_y_guides=True,
    show_x_guides=False,
    dots_size=22,
    stroke_width=6,
    margin=80,
    range=(0, 55),
    xrange=(0.3, 4.7),
    show_minor_x_labels=False,
    truncate_legend=-1,
)

# Position offsets for grouped lollipops within each category
offsets = [-0.2, 0, 0.2]

# Add each lollipop as its own series (prevents connecting lines)
for series_idx, (name, values) in enumerate(zip(series_names, series_values, strict=True)):
    for cat_idx, val in enumerate(values):
        x_pos = cat_idx + 1 + offsets[series_idx]
        # Each lollipop is a separate series: stem from 0 to value
        lollipop_data = [
            {"value": (x_pos, 0), "node": {"r": 0}},  # Base (no dot)
            {"value": (x_pos, val), "node": {"r": 22}},  # Top (large dot)
        ]
        # Only first lollipop of each series shows in legend
        show_label = name if cat_idx == 0 else None
        chart.add(show_label, lollipop_data, stroke_style={"width": 6})

# Custom x-axis labels at category positions
chart.x_labels = [1, 2, 3, 4]
chart.x_labels_major = [1, 2, 3, 4]


# Map numeric labels to category names using formatter
def x_label_formatter(x):
    labels = {1: "North", 2: "South", 3: "East", 4: "West"}
    return labels.get(int(x), str(x)) if x == int(x) else ""


chart.x_value_formatter = x_label_formatter

# Save as PNG and HTML
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
