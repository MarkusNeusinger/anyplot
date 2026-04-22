""" pyplots.ai
lollipop-basic: Basic Lollipop Chart
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, NumeralTickFormatter
from bokeh.plotting import figure


# Data - Product sales by category, sorted by value
categories = [
    "Electronics",
    "Clothing",
    "Home & Garden",
    "Sports",
    "Books",
    "Toys",
    "Food",
    "Beauty",
    "Automotive",
    "Office",
]
values = [85000, 72000, 58000, 45000, 42000, 38000, 35000, 28000, 22000, 15000]

# Sort by value (descending) for better readability
sorted_pairs = sorted(zip(categories, values, strict=True), key=lambda x: x[1], reverse=True)
categories = [p[0] for p in sorted_pairs]
values = [p[1] for p in sorted_pairs]

# Create source
source = ColumnDataSource(data={"categories": categories, "values": values, "zeros": [0] * len(values)})

# Create figure with categorical x-axis
p = figure(
    width=4800,
    height=2700,
    x_range=categories,
    title="lollipop-basic · bokeh · pyplots.ai",
    x_axis_label="Product Category",
    y_axis_label="Sales ($)",
)

# Draw stems (thin lines from baseline to value)
p.segment(x0="categories", y0="zeros", x1="categories", y1="values", source=source, line_width=4, color="#306998")

# Draw markers (circles at data values)
p.scatter(x="categories", y="values", source=source, size=25, color="#FFD43B", line_color="#306998", line_width=3)

# Styling for 4800x2700 canvas
p.title.text_font_size = "32pt"
p.xaxis.axis_label_text_font_size = "24pt"
p.yaxis.axis_label_text_font_size = "24pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Rotate x-axis labels for readability
p.xaxis.major_label_orientation = 0.7

# Grid styling - subtle
p.xgrid.grid_line_color = None
p.ygrid.grid_line_alpha = 0.3
p.ygrid.grid_line_dash = "dashed"

# Background
p.background_fill_color = "#fafafa"
p.border_fill_color = "#ffffff"

# Format y-axis with thousands separator
p.yaxis.formatter = NumeralTickFormatter(format="$0,0")

# Save as PNG and HTML
export_png(p, filename="plot.png")
output_file("plot.html")
save(p)
