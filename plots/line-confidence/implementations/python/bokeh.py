""" pyplots.ai
line-confidence: Line Plot with Confidence Interval
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, Legend
from bokeh.plotting import figure


# Data - Simulating model predictions with 95% confidence interval
np.random.seed(42)
x = np.linspace(0, 10, 50)

# True underlying function with some curvature
y_true = 2 + 0.5 * x + 0.1 * x**2

# Add noise to create observed "predictions"
y = y_true + np.random.normal(0, 0.5, len(x))

# Confidence interval (widens slightly over prediction horizon)
uncertainty = 0.8 + 0.15 * x
y_lower = y - 1.96 * uncertainty
y_upper = y + 1.96 * uncertainty

# Create ColumnDataSource
source = ColumnDataSource(data={"x": x, "y": y, "y_lower": y_lower, "y_upper": y_upper})

# Create figure (4800 x 2700 px for 16:9 aspect ratio)
p = figure(
    width=4800,
    height=2700,
    title="line-confidence · bokeh · pyplots.ai",
    x_axis_label="Time (units)",
    y_axis_label="Predicted Value",
)

# Style the plot - scaled for large canvas
p.title.text_font_size = "36pt"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "22pt"

# Add confidence band using varea
band = p.varea(x="x", y1="y_lower", y2="y_upper", source=source, fill_color="#306998", fill_alpha=0.3)

# Add central trend line
line = p.line(x="x", y="y", source=source, line_color="#306998", line_width=5)

# Add legend inside the plot area
legend = Legend(items=[("Prediction", [line]), ("95% Confidence Interval", [band])], location="top_left")
legend.label_text_font_size = "22pt"
legend.glyph_height = 30
legend.glyph_width = 30
legend.spacing = 15
legend.padding = 20
legend.background_fill_alpha = 0.8
p.add_layout(legend)

# Grid styling
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = "dashed"
p.ygrid.grid_line_dash = "dashed"

# Background
p.background_fill_color = "#fafafa"
p.border_fill_color = None

# Save as PNG
export_png(p, filename="plot.png")

# Also save as HTML for interactive version
output_file("plot.html")
save(p)
