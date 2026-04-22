""" pyplots.ai
errorbar-asymmetric: Asymmetric Error Bars Plot
Library: pygal 3.1.0 | Python 3.13.11
Quality: 88/100 | Created: 2025-12-30
"""

import pygal
from pygal.style import Style


# Data - Material strength testing (MPa) with asymmetric confidence intervals
materials = ["Steel", "Aluminum", "Titanium", "Copper", "Brass", "Bronze"]
# Central values (median strength)
y_values = [250, 150, 450, 200, 180, 220]
# Asymmetric errors - showing realistic variation in error distribution
# Some materials have larger lower errors (conservative bounds), others have larger upper errors
error_lower = [35, 12, 20, 25, 8, 18]  # 10th percentile distance from median
error_upper = [20, 28, 50, 15, 22, 30]  # 90th percentile distance from median
# Now Steel and Copper have larger lower than upper (conservative), others have larger upper

# Cap width for horizontal lines at error bar ends (in x-axis units)
# Wider caps for clear visibility as proper horizontal lines (approx 1/3 of spacing between bars)
cap_width = 0.35

# Custom style for 4800x2700 canvas with larger fonts
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998", "#306998", "#306998", "#306998", "#306998", "#306998", "#306998"),
    title_font_size=84,
    label_font_size=52,
    major_label_font_size=48,
    legend_font_size=52,
    value_font_size=42,
    stroke_width=7,
    opacity=1.0,
    transition="0s",
)

# Create XY chart for error bar visualization
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="errorbar-asymmetric · pygal · pyplots.ai",
    x_title="Material",
    y_title="Tensile Strength (MPa)",
    show_legend=True,
    legend_at_bottom=False,
    legend_box_size=28,
    show_y_guides=True,
    show_x_guides=False,
    print_values=False,
    margin=120,
    stroke=True,
    dots_size=8,
    range=(80, 550),
    xrange=(0, 7),
    x_labels=["", "Steel", "Aluminum", "Titanium", "Copper", "Brass", "Bronze"],
    x_labels_major_every=1,
    show_minor_x_labels=False,
)

# Add each error bar with proper caps (horizontal lines at ends)
for i in range(len(materials)):
    x_pos = i + 1
    y_center = y_values[i]
    y_low = y_center - error_lower[i]
    y_high = y_center + error_upper[i]

    # Vertical error bar segment
    bar_data = [(x_pos, y_low), (x_pos, y_high)]

    # Bottom cap (horizontal line)
    bottom_cap = [(x_pos - cap_width, y_low), (x_pos + cap_width, y_low)]

    # Top cap (horizontal line)
    top_cap = [(x_pos - cap_width, y_high), (x_pos + cap_width, y_high)]

    # Only first bar gets legend entry
    if i == 0:
        chart.add("10th-90th Percentile Range", bar_data, stroke=True, show_dots=False, stroke_style={"width": 7})
    else:
        chart.add(None, bar_data, stroke=True, show_dots=False, stroke_style={"width": 7})

    # Add caps as visible horizontal lines (thicker stroke for clarity as proper T-caps)
    chart.add(None, bottom_cap, stroke=True, show_dots=False, stroke_style={"width": 12})
    chart.add(None, top_cap, stroke=True, show_dots=False, stroke_style={"width": 12})

# Add central points as main series (on top of error bars)
central_data = [(i + 1, y_values[i]) for i in range(len(materials))]
chart.add("Median Strength", central_data, stroke=False, dots_size=24)

# Render to files
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
