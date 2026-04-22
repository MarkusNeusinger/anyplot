""" pyplots.ai
gauge-basic: Basic Gauge Chart
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import Label
from bokeh.plotting import figure


# Data
value = 72
min_value = 0
max_value = 100
thresholds = [30, 70]

# Gauge parameters
start_angle = np.pi  # 180 degrees (left side)
end_angle = 0  # 0 degrees (right side)
center_x = 0
center_y = 0
outer_radius = 0.9
inner_radius = 0.6
needle_length = 0.85

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="gauge-basic · bokeh · pyplots.ai",
    x_range=(-1.2, 1.2),
    y_range=(-0.3, 1.2),
    tools="",
    toolbar_location=None,
)

# Remove axes and grid
p.axis.visible = False
p.grid.visible = False
p.outline_line_color = None

# Title styling
p.title.text_font_size = "36pt"
p.title.align = "center"

# Colors for zones (red, yellow, green)
zone_colors = ["#E74C3C", "#FFD43B", "#27AE60"]

# Draw arc segments for each zone
zones = [min_value] + thresholds + [max_value]
for i in range(len(zones) - 1):
    zone_start = zones[i]
    zone_end = zones[i + 1]

    # Convert value range to angle range
    angle_start = start_angle - (zone_start - min_value) / (max_value - min_value) * np.pi
    angle_end = start_angle - (zone_end - min_value) / (max_value - min_value) * np.pi

    # Create wedge for this zone
    num_points = 50
    angles = np.linspace(angle_start, angle_end, num_points)

    # Outer arc points
    outer_x = center_x + outer_radius * np.cos(angles)
    outer_y = center_y + outer_radius * np.sin(angles)

    # Inner arc points (reversed for closed polygon)
    inner_x = center_x + inner_radius * np.cos(angles[::-1])
    inner_y = center_y + inner_radius * np.sin(angles[::-1])

    # Combine to form closed polygon
    xs = np.concatenate([outer_x, inner_x])
    ys = np.concatenate([outer_y, inner_y])

    p.patch(xs, ys, fill_color=zone_colors[i], line_color="white", line_width=2)

# Draw tick marks and labels
tick_values = [0, 25, 50, 75, 100]
for tick_val in tick_values:
    tick_angle = start_angle - (tick_val - min_value) / (max_value - min_value) * np.pi

    # Tick line (outer)
    tick_outer_x = center_x + (outer_radius + 0.02) * np.cos(tick_angle)
    tick_outer_y = center_y + (outer_radius + 0.02) * np.sin(tick_angle)
    tick_inner_x = center_x + (outer_radius + 0.08) * np.cos(tick_angle)
    tick_inner_y = center_y + (outer_radius + 0.08) * np.sin(tick_angle)

    p.line([tick_outer_x, tick_inner_x], [tick_outer_y, tick_inner_y], line_color="#2C3E50", line_width=4)

    # Tick label
    label_x = center_x + (outer_radius + 0.18) * np.cos(tick_angle)
    label_y = center_y + (outer_radius + 0.18) * np.sin(tick_angle)

    label = Label(
        x=label_x,
        y=label_y,
        text=str(tick_val),
        text_font_size="24pt",
        text_color="#2C3E50",
        text_align="center",
        text_baseline="middle",
    )
    p.add_layout(label)

# Draw needle
needle_angle = start_angle - (value - min_value) / (max_value - min_value) * np.pi
needle_x = center_x + needle_length * np.cos(needle_angle)
needle_y = center_y + needle_length * np.sin(needle_angle)

# Needle triangle
needle_width = 0.04
perp_angle = needle_angle + np.pi / 2
base_x1 = center_x + needle_width * np.cos(perp_angle)
base_y1 = center_y + needle_width * np.sin(perp_angle)
base_x2 = center_x - needle_width * np.cos(perp_angle)
base_y2 = center_y - needle_width * np.sin(perp_angle)

p.patch(
    [base_x1, needle_x, base_x2], [base_y1, needle_y, base_y2], fill_color="#306998", line_color="#1A3A5C", line_width=2
)

# Center circle
p.circle(center_x, center_y, radius=0.08, fill_color="#306998", line_color="#1A3A5C", line_width=3)

# Value display
value_label = Label(
    x=center_x,
    y=-0.18,
    text=str(value),
    text_font_size="48pt",
    text_color="#306998",
    text_align="center",
    text_baseline="middle",
    text_font_style="bold",
)
p.add_layout(value_label)

# Save as PNG
export_png(p, filename="plot.png")

# Save as HTML for interactivity
output_file("plot.html")
save(p)
