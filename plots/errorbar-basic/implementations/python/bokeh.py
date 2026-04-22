""" pyplots.ai
errorbar-basic: Basic Error Bar Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, TeeHead, Whisker
from bokeh.plotting import figure


# Data - experimental measurements with associated uncertainties
np.random.seed(42)
categories = ["Control", "Treatment A", "Treatment B", "Treatment C", "Treatment D", "Treatment E"]
means = np.array([25.3, 38.7, 42.1, 35.8, 48.2, 31.5])

# Asymmetric errors to demonstrate feature (some treatments have larger lower uncertainty)
lower_errors = np.array([2.1, 3.5, 2.8, 6.5, 4.8, 2.5])
upper_errors = np.array([2.1, 3.5, 2.8, 2.8, 2.2, 2.5])

# Calculate upper and lower bounds for whiskers
upper = means + upper_errors
lower = means - lower_errors

# Create ColumnDataSource
source = ColumnDataSource(data={"categories": categories, "means": means, "upper": upper, "lower": lower})

# Create figure with categorical x-axis
p = figure(
    width=4800,
    height=2700,
    x_range=categories,
    title="errorbar-basic · bokeh · pyplots.ai",
    x_axis_label="Experimental Group",
    y_axis_label="Response Value (units)",
)

# Add error bars using Whisker with TeeHead caps
whisker = Whisker(
    base="categories",
    upper="upper",
    lower="lower",
    source=source,
    line_color="#306998",
    line_width=4,
    upper_head=TeeHead(size=20, line_color="#306998", line_width=4),
    lower_head=TeeHead(size=20, line_color="#306998", line_width=4),
)
p.add_layout(whisker)

# Add scatter points for the mean values
p.scatter(x="categories", y="means", source=source, size=20, color="#306998", alpha=0.9)

# Styling for 4800x2700 px
p.title.text_font_size = "36pt"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "22pt"

# Grid styling
p.ygrid.grid_line_alpha = 0.3
p.ygrid.grid_line_dash = "dashed"
p.xgrid.grid_line_color = None

# Set y-axis range with padding
p.y_range.start = 0
p.y_range.end = max(upper) * 1.15

# Save outputs
export_png(p, filename="plot.png")
output_file("plot.html", title="errorbar-basic · bokeh · pyplots.ai")
save(p)
