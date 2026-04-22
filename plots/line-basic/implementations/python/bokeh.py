""" pyplots.ai
line-basic: Basic Line Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure


# Data - Daily temperature readings for a month
np.random.seed(42)
days = np.arange(1, 32)

# Temperature with seasonal pattern and random variation
base_temp = 20 + 8 * np.sin(np.linspace(0, np.pi, 31))  # Warm mid-month
noise = np.random.randn(31) * 2
temperature = base_temp + noise

# Create ColumnDataSource
source = ColumnDataSource(data={"day": days, "temperature": temperature})

# Create figure (4800 × 2700 px)
p = figure(
    width=4800,
    height=2700,
    title="line-basic · bokeh · pyplots.ai",
    x_axis_label="Day of Month",
    y_axis_label="Temperature (°C)",
)

# Plot line with markers for visibility
p.line(x="day", y="temperature", source=source, line_width=5, line_color="#306998")
p.scatter(x="day", y="temperature", source=source, size=16, fill_color="#306998", line_color="white", line_width=3)

# Style text sizes for 4800x2700 px
p.title.text_font_size = "42pt"
p.xaxis.axis_label_text_font_size = "32pt"
p.yaxis.axis_label_text_font_size = "32pt"
p.xaxis.major_label_text_font_size = "24pt"
p.yaxis.major_label_text_font_size = "24pt"

# Grid styling - subtle dashed lines
p.grid.grid_line_alpha = 0.3
p.grid.grid_line_dash = "dashed"

# Background styling
p.background_fill_color = "#fafafa"
p.border_fill_color = "white"

# Axis styling
p.axis.axis_line_width = 2
p.axis.axis_line_color = "#333333"
p.axis.major_tick_line_width = 2
p.axis.minor_tick_line_width = 1

# Remove toolbar for cleaner static image
p.toolbar_location = None

# Save as PNG and HTML
export_png(p, filename="plot.png")

output_file("plot.html")
save(p)
