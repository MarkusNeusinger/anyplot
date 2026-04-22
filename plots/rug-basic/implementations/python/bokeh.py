""" pyplots.ai
rug-basic: Basic Rug Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 78/100 | Created: 2025-12-23
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, Range1d
from bokeh.plotting import figure


# Data - bimodal distribution of API response times (ms) to show clustering patterns
np.random.seed(42)
cluster1 = np.random.normal(85, 12, 60)  # Fast responses (~85ms)
cluster2 = np.random.normal(180, 20, 40)  # Slower responses (~180ms)
values = np.concatenate([cluster1, cluster2])

# Rug tick configuration
# Ticks positioned at the bottom, small relative to plot area (~5% of visible height)
tick_base = 0.0
tick_height = 0.05

# Create ColumnDataSource for rug ticks
source = ColumnDataSource(
    data={"x": values, "y0": np.full(len(values), tick_base), "y1": np.full(len(values), tick_height)}
)

# Create figure (4800 x 2700 px) - reduced height to emphasize horizontal distribution
p = figure(
    width=4800,
    height=1200,
    title="rug-basic · bokeh · pyplots.ai",
    x_axis_label="Response Time (ms)",
    y_axis_label="",
    toolbar_location=None,
)

# Draw rug ticks as vertical segments at the bottom margin
# Line width increased for visibility at 4800px width
p.segment(x0="x", y0="y0", x1="x", y1="y1", source=source, line_color="#306998", line_width=6, line_alpha=0.6)

# Configure axis ranges - y range tightly fits tick height to minimize whitespace
p.x_range = Range1d(values.min() - 10, values.max() + 10)
p.y_range = Range1d(-0.01, 0.08)

# Hide y-axis (not meaningful for rug plot)
p.yaxis.visible = False

# Styling for 4800px width
p.title.text_font_size = "28pt"
p.xaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"

# Remove all grid lines for clean rug appearance
p.xgrid.visible = False
p.ygrid.visible = False

# Background
p.background_fill_color = "#fafafa"

# Save outputs
export_png(p, filename="plot.png")
output_file("plot.html")
save(p)
