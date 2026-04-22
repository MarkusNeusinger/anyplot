""" pyplots.ai
point-basic: Point Estimate Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, Span, TeeHead, Whisker
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data - Effect sizes for different treatment groups with 95% confidence intervals
np.random.seed(42)
categories = ["Treatment A", "Treatment B", "Treatment C", "Treatment D", "Treatment E", "Control"]
estimates = np.array([2.5, 1.8, 3.2, -0.5, 1.2, 0.0])
# Generate confidence intervals with varying widths
ci_widths = np.array([0.8, 1.2, 0.6, 0.9, 1.5, 0.4])
lower = estimates - ci_widths
upper = estimates + ci_widths

# Create ColumnDataSource
source = ColumnDataSource(data={"categories": categories, "estimates": estimates, "lower": lower, "upper": upper})

# Create figure with categorical y-axis (horizontal orientation for readability)
p = figure(
    width=4800,
    height=2700,
    y_range=categories[::-1],  # Reverse order so first category is at top
    title="point-basic · bokeh · pyplots.ai",
    x_axis_label="Effect Size",
    y_axis_label="Treatment Group",
)

# Add reference line at zero (null hypothesis)
zero_line = Span(location=0, dimension="height", line_color="#888888", line_width=3, line_dash="dashed")
p.add_layout(zero_line)

# Add error bars using Whisker with TeeHead caps (horizontal)
whisker = Whisker(
    source=source,
    base="categories",
    lower="lower",
    upper="upper",
    dimension="width",
    line_color="#306998",
    line_width=6,
    upper_head=TeeHead(size=30, line_color="#306998", line_width=6),
    lower_head=TeeHead(size=30, line_color="#306998", line_width=6),
)
p.add_layout(whisker)

# Plot points (estimates) with larger markers for visibility
p.scatter(x="estimates", y="categories", source=source, size=40, color="#306998", fill_color="#FFD43B", line_width=4)

# Styling for large canvas
p.title.text_font_size = "36pt"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "22pt"

# Grid styling
p.xgrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = "dashed"
p.ygrid.grid_line_alpha = 0.3
p.ygrid.grid_line_dash = "dashed"

# Remove toolbar and outline for cleaner look
p.toolbar_location = None
p.outline_line_color = None

# Save as PNG and HTML
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="point-basic · bokeh · pyplots.ai")
