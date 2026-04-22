""" pyplots.ai
bar-horizontal: Horizontal Bar Chart
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 94/100 | Created: 2025-12-25
"""

from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure


# Data - Top Programming Languages by Developer Popularity (%)
categories = ["JavaScript", "Python", "TypeScript", "Java", "C#", "C++", "PHP", "Go", "Rust", "Kotlin"]
values = [65.6, 49.3, 38.5, 33.3, 28.7, 22.4, 18.2, 14.3, 13.1, 9.2]

# Sort by value (smallest to largest for bottom-to-top display)
sorted_data = sorted(zip(categories, values, strict=True), key=lambda x: x[1])
categories_sorted = [x[0] for x in sorted_data]
values_sorted = [x[1] for x in sorted_data]

# Create data source
source = ColumnDataSource(data={"categories": categories_sorted, "values": values_sorted})

# Create figure with categorical y-axis (4800 × 2700 px)
p = figure(
    width=4800,
    height=2700,
    y_range=categories_sorted,
    x_axis_label="Developer Popularity (%)",
    title="bar-horizontal · bokeh · pyplots.ai",
    toolbar_location=None,
)

# Draw horizontal bars
p.hbar(
    y="categories",
    right="values",
    height=0.7,
    source=source,
    color="#306998",
    line_color="#1e4a6e",
    line_width=2,
    alpha=0.9,
)

# Style title
p.title.text_font_size = "36pt"
p.title.align = "center"

# Style axes for large canvas
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "24pt"
p.yaxis.major_label_text_font_size = "24pt"
p.xaxis.axis_label_standoff = 20
p.yaxis.axis_label_standoff = 20

# Configure grid
p.xgrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = "dashed"
p.ygrid.grid_line_alpha = 0

# Set x-axis range starting from 0
p.x_range.start = 0
p.x_range.end = 75

# Add padding on left for category labels
p.min_border_left = 200

# Export to PNG
export_png(p, filename="plot.png")

# Save as HTML for interactivity
output_file("plot.html")
save(p)
