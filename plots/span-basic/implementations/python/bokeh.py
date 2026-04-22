""" pyplots.ai
span-basic: Basic Span Plot (Highlighted Region)
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import BoxAnnotation, ColumnDataSource, Label
from bokeh.plotting import figure


# Data - Monthly revenue over 2 years with spans highlighting key periods
np.random.seed(42)
months = np.arange(1, 25)
base_revenue = 100 + np.linspace(0, 50, 24) + 15 * np.sin(np.linspace(0, 4 * np.pi, 24))
noise = np.random.randn(24) * 8
revenue = base_revenue + noise

# Create ColumnDataSource
source = ColumnDataSource(data={"x": months, "y": revenue})

# Create figure (4800 × 2700 px)
p = figure(
    width=4800,
    height=2700,
    title="span-basic · bokeh · pyplots.ai",
    x_axis_label="Month",
    y_axis_label="Revenue (thousands $)",
)

# Add vertical span - highlight Q4 of Year 1 (months 10-12)
vertical_span = BoxAnnotation(
    left=10, right=12, fill_alpha=0.25, fill_color="#306998", line_color="#306998", line_width=2, line_alpha=0.5
)
p.add_layout(vertical_span)

# Add horizontal span - highlight target revenue range (120-140)
horizontal_span = BoxAnnotation(
    bottom=120, top=140, fill_alpha=0.2, fill_color="#FFD43B", line_color="#FFD43B", line_width=2, line_alpha=0.5
)
p.add_layout(horizontal_span)

# Plot line with markers
p.line(x="x", y="y", source=source, line_width=4, line_color="#306998", legend_label="Monthly Revenue")
p.scatter(x="x", y="y", source=source, size=16, fill_color="#306998", line_color="white", line_width=2)

# Add labels for spans
vertical_label = Label(
    x=10.2, y=102, text="Q4 Peak Season", text_font_size="24pt", text_color="#1a4d7c", text_font_style="bold"
)
p.add_layout(vertical_label)

horizontal_label = Label(
    x=17, y=125, text="Target Range", text_font_size="28pt", text_color="#B8860B", text_font_style="bold"
)
p.add_layout(horizontal_label)

# Style text sizes for 4800x2700 px
p.title.text_font_size = "48pt"
p.xaxis.axis_label_text_font_size = "36pt"
p.yaxis.axis_label_text_font_size = "36pt"
p.xaxis.major_label_text_font_size = "28pt"
p.yaxis.major_label_text_font_size = "28pt"

# Grid styling
p.grid.grid_line_alpha = 0.3
p.grid.grid_line_dash = "dashed"

# Legend styling
p.legend.label_text_font_size = "28pt"
p.legend.location = "bottom_right"
p.legend.background_fill_alpha = 0.7

# Save as PNG and HTML
export_png(p, filename="plot.png")

output_file("plot.html")
save(p)
