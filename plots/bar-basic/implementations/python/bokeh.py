""" pyplots.ai
bar-basic: Basic Bar Chart
Library: bokeh 3.8.2 | Python 3.14
Quality: 90/100 | Created: 2025-12-23
"""

from bokeh.io import export_png
from bokeh.models import ColumnDataSource, LabelSet, NumeralTickFormatter
from bokeh.plotting import figure, output_file, save


# Data - Quarterly revenue by department (varied, non-monotonic pattern)
categories = ["Engineering", "Marketing", "Sales", "Support", "Design", "Operations"]
values = [38200, 21500, 45800, 14300, 27600, 19100]
labels = [f"${v / 1000:.1f}K" for v in values]

# Create ColumnDataSource
source = ColumnDataSource(data={"categories": categories, "values": values, "labels": labels})

# Create figure with categorical x-axis (4800 x 2700 px)
p = figure(
    x_range=categories,
    width=4800,
    height=2700,
    title="bar-basic \u00b7 bokeh \u00b7 pyplots.ai",
    x_axis_label="Department",
    y_axis_label="Revenue ($)",
    toolbar_location=None,
)

# Create bars with white edge for definition
p.vbar(
    x="categories", top="values", source=source, width=0.7, color="#306998", alpha=0.9, line_color="white", line_width=2
)

# Add formatted value labels above bars
labels_glyph = LabelSet(
    x="categories",
    y="values",
    text="labels",
    level="glyph",
    x_offset=0,
    y_offset=8,
    source=source,
    text_font_size="28pt",
    text_color="#333333",
    text_align="center",
)
p.add_layout(labels_glyph)

# Styling for 4800x2700 px
p.title.text_font_size = "36pt"
p.title.align = "center"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "24pt"
p.yaxis.major_label_text_font_size = "24pt"

# Clean L-shaped frame: remove top and right spines
p.outline_line_color = None
p.xaxis.axis_line_color = "#333333"
p.yaxis.axis_line_color = "#333333"
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2

# Remove tick marks, keep labels
p.xaxis.major_tick_line_color = None
p.yaxis.major_tick_line_color = None
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

# Grid styling - y-axis only, subtle solid lines
p.xgrid.grid_line_color = None
p.ygrid.grid_line_alpha = 0.2
p.ygrid.grid_line_dash = "solid"

# Format y-axis with dollar amounts
p.yaxis.formatter = NumeralTickFormatter(format="$0,0")

# Y-axis starts at 0, add headroom for labels
p.y_range.start = 0
p.y_range.end = max(values) * 1.15

# Background
p.background_fill_color = "#FFFFFF"

# Save as PNG
export_png(p, filename="plot.png")

# Save as HTML for interactivity
output_file("plot.html")
save(p)
