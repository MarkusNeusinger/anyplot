""" pyplots.ai
line-stepwise: Step Line Plot
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import pygal
from pygal.style import Style


# Data - Server response time stepping over 24 hours
hours = list(range(0, 25))  # 0-24 hours

# Response time that steps discretely (server load changes)
response_times = [50]  # Start at 50ms
for i in range(1, 25):
    # Discrete jumps at certain hours (morning rush, lunch, evening)
    if i == 8:  # Morning rush
        response_times.append(120)
    elif i == 12:  # Lunch peak
        response_times.append(180)
    elif i == 14:  # Post lunch
        response_times.append(100)
    elif i == 18:  # Evening rush
        response_times.append(200)
    elif i == 21:  # Night decrease
        response_times.append(80)
    elif i == 23:  # Late night
        response_times.append(40)
    else:
        response_times.append(response_times[-1])  # Stay constant

# Create step data by duplicating points for horizontal-then-vertical transitions
# For step-post style: horizontal segment at old value, then vertical jump
step_x_labels = []
step_values = []
for i, (h, v) in enumerate(zip(hours, response_times, strict=True)):
    if i == 0:
        step_x_labels.append(str(h))
        step_values.append(v)
    else:
        # Add point at new x with OLD y value (horizontal segment)
        step_x_labels.append(str(h))
        step_values.append(response_times[i - 1])
        # Add point at same x with NEW y value (vertical segment)
        step_x_labels.append("")  # Empty label to avoid clutter
        step_values.append(v)

# Custom style for pyplots
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998",),  # Python Blue
    title_font_size=56,
    label_font_size=36,
    major_label_font_size=32,
    legend_font_size=32,
    value_font_size=28,
    stroke_width=5,
)

# Create line chart
chart = pygal.Line(
    width=4800,
    height=2700,
    style=custom_style,
    title="line-stepwise · pygal · pyplots.ai",
    x_title="Hour of Day",
    y_title="Response Time (ms)",
    show_dots=False,  # Hide dots for cleaner step appearance
    fill=False,
    show_x_guides=False,
    show_y_guides=True,
    show_legend=False,
    truncate_label=-1,
    show_minor_x_labels=True,
    x_label_rotation=0,
)

# X-axis labels
chart.x_labels = step_x_labels

# Add step data
chart.add("Server Response", step_values)

# Save outputs
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
