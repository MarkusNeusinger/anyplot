""" pyplots.ai
slope-basic: Basic Slope Chart (Slopegraph)
Library: pygal 3.1.0 | Python 3.13.11
Quality: 86/100 | Created: 2025-12-23
"""

import pygal
from pygal.style import Style


# Data - Sales figures comparing Q1 vs Q4 for 10 products
products = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
q1_sales = [85, 72, 95, 45, 68, 52, 78, 62, 88, 40]
q4_sales = [92, 58, 102, 75, 65, 71, 82, 48, 95, 55]

# Colorblind-friendly colors for increase vs decrease (spec requirement)
COLOR_INCREASE = "#2166AC"  # Blue - value went up
COLOR_DECREASE = "#D6604D"  # Orange-red - value went down

# Separate products by direction for proper color grouping
increasing = []
decreasing = []
for i, p in enumerate(products):
    if q4_sales[i] >= q1_sales[i]:
        increasing.append((p, q1_sales[i], q4_sales[i]))
    else:
        decreasing.append((p, q1_sales[i], q4_sales[i]))

# Build color tuple: increasing (blue) then decreasing (orange)
series_colors = tuple([COLOR_INCREASE] * len(increasing) + [COLOR_DECREASE] * len(decreasing))

# Custom style for 4800x2700 px with clean legend (2 grouped entries)
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=series_colors,
    title_font_size=72,
    label_font_size=44,
    major_label_font_size=48,
    legend_font_size=48,
    value_font_size=36,
    stroke_width=5,
    value_label_font_size=32,
)

# Create slope chart using Line chart with only 2 x-axis points
chart = pygal.Line(
    width=4800,
    height=2700,
    title="slope-basic · pygal · pyplots.ai",
    x_title="Time Period",
    y_title="Sales (units)",
    style=custom_style,
    show_dots=True,
    dots_size=16,
    stroke_style={"width": 5},
    show_y_guides=True,
    show_x_guides=False,
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=32,
    truncate_legend=-1,
    interpolate=None,
    margin=120,
    print_values=False,
    print_labels=False,
    range=(30, 110),
)

# X-axis labels (two time points)
chart.x_labels = ["Q1 2024", "Q4 2024"]

# Add series - first entry in each group shows in legend, rest use None to hide
for i, (p, start, end) in enumerate(increasing):
    chart.add(
        "Increasing" if i == 0 else None,
        [{"value": start, "label": f"Product {p}: {start}"}, {"value": end, "label": f"Product {p}: {end}"}],
    )

for i, (p, start, end) in enumerate(decreasing):
    chart.add(
        "Decreasing" if i == 0 else None,
        [{"value": start, "label": f"Product {p}: {start}"}, {"value": end, "label": f"Product {p}: {end}"}],
    )

# Save as PNG and HTML (HTML provides interactive hover labels)
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
