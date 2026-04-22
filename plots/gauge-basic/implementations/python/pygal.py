""" pyplots.ai
gauge-basic: Basic Gauge Chart
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import pygal
from pygal.style import Style


# Data - Current sales performance against target
value = 72  # Current value to display
max_value = 100
# Thresholds: 0-30 = Poor (red), 30-70 = Fair (yellow), 70-100 = Good (green)

# Determine zone color based on value position
if value < 30:
    value_color = "#E74C3C"  # Red for poor zone
elif value < 70:
    value_color = "#F1C40F"  # Yellow for fair zone
else:
    value_color = "#2ECC71"  # Green for good zone

# Custom style for 4800x2700 px with large fonts
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#1a1a1a",
    foreground_subtle="#666666",
    colors=(value_color,),
    title_font_size=72,
    label_font_size=54,
    major_label_font_size=54,
    legend_font_size=52,
    value_font_size=72,
    tooltip_font_size=40,
)

# Create SolidGauge chart (semi-circular gauge)
chart = pygal.SolidGauge(
    width=4800,
    height=2700,
    style=custom_style,
    title="Sales Performance · gauge-basic · pygal · pyplots.ai",
    inner_radius=0.60,
    half_pie=True,
    show_legend=True,
    legend_at_bottom=True,
    print_values=True,
    value_formatter=lambda x: f"{x:.0f}%",
    margin=100,
)

# Add single gauge showing current value against max
# Value 72 is in the "Good" zone (70-100)
chart.add(f"Current Sales: {value}% (Good Zone)", [{"value": value, "max_value": max_value}])

# Save outputs
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
