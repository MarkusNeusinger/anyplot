""" pyplots.ai
bar-diverging: Diverging Bar Chart
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

from bokeh.io import export_png
from bokeh.models import ColumnDataSource, Span
from bokeh.plotting import figure, save


# Data - Customer satisfaction survey responses (Net Promoter Score style)
categories = [
    "Product Quality",
    "Customer Service",
    "Delivery Speed",
    "Website Experience",
    "Price Value",
    "Return Policy",
    "Mobile App",
    "Warranty Service",
    "Tech Support",
    "Packaging",
]

# Net satisfaction scores: positive = more promoters, negative = more detractors
values = [45, 32, -15, 28, -8, 52, -22, 18, -35, 12]

# Sort by value for better pattern recognition
sorted_data = sorted(zip(categories, values, strict=True), key=lambda x: x[1])
categories_sorted = [item[0] for item in sorted_data]
values_sorted = [item[1] for item in sorted_data]

# Assign colors based on positive/negative values
colors = ["#306998" if v >= 0 else "#FFD43B" for v in values_sorted]

# Create ColumnDataSource
source = ColumnDataSource(data={"category": categories_sorted, "value": values_sorted, "color": colors})

# Create figure with horizontal bars (better for long category labels)
p = figure(
    width=4800,
    height=2700,
    y_range=categories_sorted,
    x_range=(-60, 70),
    title="bar-diverging · bokeh · pyplots.ai",
    x_axis_label="Net Satisfaction Score",
    y_axis_label="Category",
)

# Draw horizontal bars from 0
p.hbar(y="category", right="value", left=0, height=0.7, color="color", source=source, alpha=0.9)

# Add vertical line at zero baseline
zero_line = Span(location=0, dimension="height", line_color="#333333", line_width=2, line_dash="solid")
p.add_layout(zero_line)

# Style the plot
p.title.text_font_size = "28pt"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Grid styling - subtle
p.xgrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = "dashed"
p.ygrid.grid_line_alpha = 0.0

# Remove unnecessary elements
p.outline_line_color = None

# Background
p.background_fill_color = "#ffffff"

# Save as PNG
export_png(p, filename="plot.png")

# Also save as HTML for interactive version
save(p, filename="plot.html", title="bar-diverging · bokeh · pyplots.ai")
