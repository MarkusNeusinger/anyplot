""" pyplots.ai
histogram-stepwise: Step Histogram
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data - Two distributions for comparison
np.random.seed(42)
data1 = np.random.normal(loc=50, scale=12, size=500)  # Temperature readings (°C)
data2 = np.random.normal(loc=65, scale=10, size=500)  # Second sensor readings

# Compute histogram bins and counts
bins = np.linspace(15, 100, 35)  # Common bins for both distributions
counts1, edges1 = np.histogram(data1, bins=bins)
counts2, edges2 = np.histogram(data2, bins=bins)

# Create step coordinates for step histogram (outline only)
x1 = np.repeat(edges1, 2)[1:-1]
y1 = np.repeat(counts1, 2)
x2 = np.repeat(edges2, 2)[1:-1]
y2 = np.repeat(counts2, 2)

# Create figure (4800 x 2700 px)
p = figure(
    width=4800,
    height=2700,
    title="histogram-stepwise · bokeh · pyplots.ai",
    x_axis_label="Temperature (°C)",
    y_axis_label="Frequency",
)

# Plot step histograms (outline only, no fill)
p.line(x1, y1, line_width=5, color="#306998", alpha=0.9, legend_label="Sensor A")
p.line(x2, y2, line_width=5, color="#FFD43B", alpha=0.9, legend_label="Sensor B")

# Styling for large canvas
p.title.text_font_size = "36pt"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "22pt"

# Grid styling
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = "dashed"
p.ygrid.grid_line_dash = "dashed"

# Legend styling
p.legend.label_text_font_size = "22pt"
p.legend.location = "top_right"
p.legend.background_fill_alpha = 0.8
p.legend.border_line_width = 2
p.legend.padding = 15
p.legend.spacing = 10

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="histogram-stepwise · bokeh · pyplots.ai")
