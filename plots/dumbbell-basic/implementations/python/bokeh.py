""" pyplots.ai
dumbbell-basic: Basic Dumbbell Chart
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure


# Data - Employee satisfaction scores before and after policy changes
categories = [
    "Engineering",
    "Marketing",
    "Sales",
    "Customer Support",
    "Human Resources",
    "Finance",
    "Operations",
    "Research & Development",
]
start_values = [62, 58, 71, 55, 68, 72, 60, 65]  # Before policy changes
end_values = [78, 74, 82, 70, 85, 80, 73, 88]  # After policy changes

# Sort by difference for better visualization
differences = [e - s for s, e in zip(start_values, end_values, strict=True)]
sorted_data = sorted(zip(categories, start_values, end_values, differences, strict=True), key=lambda x: x[3])
categories = [d[0] for d in sorted_data]
start_values = [d[1] for d in sorted_data]
end_values = [d[2] for d in sorted_data]

# Create figure with categorical y-axis (horizontal orientation)
p = figure(
    width=4800,
    height=2700,
    y_range=categories,
    title="dumbbell-basic · bokeh · pyplots.ai",
    x_axis_label="Satisfaction Score",
    y_axis_label="Department",
)

# Create connecting lines (thin and subtle)
for i, cat in enumerate(categories):
    p.line(x=[start_values[i], end_values[i]], y=[cat, cat], line_width=4, line_color="#888888", line_alpha=0.6)

# Data sources for dots
source_start = ColumnDataSource(data={"x": start_values, "y": categories, "label": ["Before"] * len(categories)})
source_end = ColumnDataSource(data={"x": end_values, "y": categories, "label": ["After"] * len(categories)})

# Plot start dots (Before - Python Blue)
p.scatter(x="x", y="y", source=source_start, size=25, color="#306998", alpha=0.9, legend_label="Before Policy Changes")

# Plot end dots (After - Python Yellow)
p.scatter(x="x", y="y", source=source_end, size=25, color="#FFD43B", alpha=0.9, legend_label="After Policy Changes")

# Styling for 4800x2700 px
p.title.text_font_size = "36pt"
p.xaxis.axis_label_text_font_size = "24pt"
p.yaxis.axis_label_text_font_size = "24pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Grid styling (subtle)
p.xgrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = "dashed"
p.ygrid.grid_line_alpha = 0.3
p.ygrid.grid_line_dash = "dashed"

# Legend styling
p.legend.label_text_font_size = "18pt"
p.legend.location = "bottom_right"
p.legend.background_fill_alpha = 0.7

# Set x-axis range with padding
p.x_range.start = 45
p.x_range.end = 95

# Save outputs
export_png(p, filename="plot.png")
output_file("plot.html")
save(p)
