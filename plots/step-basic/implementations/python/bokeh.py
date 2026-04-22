""" pyplots.ai
step-basic: Basic Step Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

from bokeh.io import export_png, output_file
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure, save


# Data - Monthly cumulative sales showing discrete jumps
months = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
cumulative_sales = [15, 28, 42, 55, 71, 89, 102, 118, 135, 156, 172, 195]

source = ColumnDataSource(data={"month": months, "sales": cumulative_sales})

# Create figure (4800 × 2700 px)
p = figure(
    width=4800,
    height=2700,
    title="step-basic · bokeh · pyplots.ai",
    x_axis_label="Month",
    y_axis_label="Cumulative Sales (units)",
    tools="",
    toolbar_location=None,
)

# Step plot using step glyph (post mode - value applies until next change)
p.step(x="month", y="sales", source=source, line_width=4, color="#306998", mode="after")

# Add markers at data points to show where changes occur
p.scatter(x="month", y="sales", source=source, size=18, color="#FFD43B", line_color="#306998", line_width=3)

# Styling for 4800x2700 px
p.title.text_font_size = "48pt"
p.xaxis.axis_label_text_font_size = "36pt"
p.yaxis.axis_label_text_font_size = "36pt"
p.xaxis.major_label_text_font_size = "28pt"
p.yaxis.major_label_text_font_size = "28pt"

# Grid styling
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = "dashed"
p.ygrid.grid_line_dash = "dashed"

# Background
p.background_fill_color = "#fafafa"

# Save as PNG
export_png(p, filename="plot.png")

# Save as HTML for interactivity
output_file("plot.html")
save(p)
