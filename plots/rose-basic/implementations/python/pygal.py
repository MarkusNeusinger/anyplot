""" pyplots.ai
rose-basic: Basic Rose Chart
Library: pygal 3.1.0 | Python 3.13.11
Quality: 58/100 | Created: 2025-12-23
"""

import pygal
from pygal.style import Style


# Data: Monthly rainfall (mm) - Pacific Northwest pattern with seasonal variation
# Clear cycle: wet winters (Nov-Feb), dry summers (Jun-Aug)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
rainfall = [145, 115, 95, 65, 45, 35, 20, 25, 50, 90, 135, 155]

# Custom style for 3600x3600 square canvas
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998",),  # Single blue for cohesive look
    title_font_size=72,
    label_font_size=44,
    major_label_font_size=40,
    legend_font_size=40,
    value_font_size=36,
    stroke_width=3,
    opacity=0.75,
    opacity_hover=0.9,
)

# Pygal Radar chart: best approximation for rose/coxcomb in pygal
# - Equal angular spacing around center (like rose chart)
# - Radial distance proportional to values (like rose chart)
# - Limitation: connected polygon instead of discrete wedges
chart = pygal.Radar(
    width=3600,
    height=3600,
    style=custom_style,
    title="rose-basic · pygal · pyplots.ai",
    fill=True,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    margin=120,
    dots_size=10,
    show_dots=True,
    range=(0, 170),
)

# Add month labels around the radar
chart.x_labels = months

# Single series with rainfall values - radius proportional to value
chart.add("Monthly Rainfall (mm)", rainfall)

# Save outputs
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
