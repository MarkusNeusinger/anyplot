""" pyplots.ai
errorbar-basic: Basic Error Bar Plot
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import pygal
from pygal.style import Style


# Data - experimental measurements with associated uncertainties
categories = ["Control", "Treatment A", "Treatment B", "Treatment C", "Treatment D", "Treatment E"]
means = [25.3, 38.7, 42.1, 35.8, 48.2, 31.5]
# Asymmetric errors: Treatment C and D have notably different lower/upper bounds
err_lower = [2.1, 3.5, 2.8, 6.5, 4.8, 2.5]
err_upper = [2.1, 3.5, 2.8, 2.8, 2.2, 2.5]

# Custom style for 4800x2700 output
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998",),
    title_font_size=56,
    label_font_size=40,
    major_label_font_size=36,
    legend_font_size=36,
    value_font_size=28,
    stroke_width=5,
)

# Create XY chart for error bars
chart = pygal.XY(
    style=custom_style,
    width=4800,
    height=2700,
    dots_size=20,
    title="errorbar-basic · pygal · pyplots.ai",
    x_title="Experimental Group",
    y_title="Response Value (units)",
    show_legend=False,
    range=(0, max(m + e for m, e in zip(means, err_upper, strict=True)) * 1.15),
    xrange=(-0.5, len(categories) - 0.5),
    show_x_guides=False,
    show_y_guides=True,
    margin_right=50,
)

# Set category labels on x-axis
chart.x_labels = categories
chart.x_labels_major = categories

cap_width = 0.12  # Width of error bar caps in x-axis units

# Add mean points (markers only, no connecting lines)
mean_points = [(i, m) for i, m in enumerate(means)]
chart.add("Mean", mean_points, stroke=False, dots_size=22)

# Add error bars with caps for each data point
for i in range(len(means)):
    low = means[i] - err_lower[i]
    high = means[i] + err_upper[i]

    # Vertical error bar line
    chart.add(None, [(i, low), (i, high)], stroke=True, show_dots=False)

    # Bottom cap (horizontal line)
    chart.add(None, [(i - cap_width, low), (i + cap_width, low)], stroke=True, show_dots=False)

    # Top cap (horizontal line)
    chart.add(None, [(i - cap_width, high), (i + cap_width, high)], stroke=True, show_dots=False)

# Save outputs
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
