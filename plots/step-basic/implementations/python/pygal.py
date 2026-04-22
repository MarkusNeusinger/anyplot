""" pyplots.ai
step-basic: Basic Step Plot
Library: pygal 3.1.0 | Python 3.13.11
Quality: 90/100 | Created: 2025-12-23
"""

import pygal
from pygal.style import Style


# Data - Monthly cumulative sales (in thousands)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
cumulative_sales = [45, 92, 128, 165, 198, 256, 312, 378, 425, 489, 562, 635]

# Create step data by duplicating points for stair-step effect (post-style)
# Each value extends horizontally until the next month
# Use only the actual month labels to avoid x-axis spacing issues
step_x_labels = []
step_values = []

for i, (month, value) in enumerate(zip(months, cumulative_sales, strict=True)):
    # Add the current data point with visible marker
    step_x_labels.append(month)
    step_values.append({"value": value, "node": {"r": 14}})
    # Add intermediate point at same Y before next X (except for last point)
    if i < len(months) - 1:
        # Use a non-breaking space for intermediate labels to maintain spacing
        step_x_labels.append("\u200b")  # Zero-width space - invisible but preserves grid
        step_values.append({"value": value, "node": {"r": 0}})

# Custom style for 4800x2700 canvas with enhanced sizing
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333",
    foreground_strong="#000",
    foreground_subtle="#555",
    colors=("#306998",),
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=44,
    legend_font_size=56,
    value_font_size=40,
)

# Create line chart configured for step visualization
chart = pygal.Line(
    width=4800,
    height=2700,
    title="step-basic · pygal · pyplots.ai",
    x_title="Month",
    y_title="Cumulative Sales ($K)",
    style=custom_style,
    show_dots=True,
    dots_size=14,
    stroke_style={"width": 8},
    show_y_guides=True,
    show_x_guides=False,
    x_label_rotation=0,
    legend_at_bottom=True,
    legend_at_bottom_columns=1,
    truncate_legend=-1,
    show_legend=True,
    margin_bottom=120,
)

# Add data
chart.x_labels = step_x_labels
chart.add("Cumulative Sales", step_values)

# Save outputs
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
