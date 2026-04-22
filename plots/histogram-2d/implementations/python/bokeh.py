""" pyplots.ai
histogram-2d: 2D Histogram Heatmap
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import ColorBar, LinearColorMapper
from bokeh.palettes import Viridis256
from bokeh.plotting import figure, output_file, save


# Data - bivariate normal distribution with correlation
np.random.seed(42)
n_points = 5000
mean = [0, 0]
cov = [[1, 0.7], [0.7, 1]]  # Correlation of 0.7
data = np.random.multivariate_normal(mean, cov, n_points)
x = data[:, 0]
y = data[:, 1]

# Compute 2D histogram
bins = 40
hist, x_edges, y_edges = np.histogram2d(x, y, bins=bins)

# Create plot (4800 x 2700 px for 16:9)
p = figure(
    width=4800,
    height=2700,
    title="histogram-2d · bokeh · pyplots.ai",
    x_axis_label="X Value",
    y_axis_label="Y Value",
    x_range=(x_edges[0], x_edges[-1]),
    y_range=(y_edges[0], y_edges[-1]),
)

# Color mapper for heatmap
color_mapper = LinearColorMapper(palette=Viridis256, low=0, high=hist.max())

# Use image glyph for 2D histogram (transposed for correct orientation)
p.image(
    image=[hist.T],
    x=x_edges[0],
    y=y_edges[0],
    dw=x_edges[-1] - x_edges[0],
    dh=y_edges[-1] - y_edges[0],
    color_mapper=color_mapper,
)

# Add color bar with proper sizing
color_bar = ColorBar(
    color_mapper=color_mapper,
    width=50,
    location=(0, 0),
    title="Count",
    title_text_font_size="28pt",
    major_label_text_font_size="22pt",
    title_standoff=15,
)
p.add_layout(color_bar, "right")

# Style text sizes for large canvas (4800x2700)
p.title.text_font_size = "36pt"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "22pt"

# Axis line and tick styling
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2
p.xaxis.major_tick_line_width = 2
p.yaxis.major_tick_line_width = 2

# Grid styling - disabled for heatmap
p.xgrid.grid_line_alpha = 0.0
p.ygrid.grid_line_alpha = 0.0

# Background styling
p.background_fill_color = None
p.border_fill_color = "white"

# Save PNG
export_png(p, filename="plot.png")

# Save HTML for interactivity
output_file("plot.html", title="histogram-2d · bokeh · pyplots.ai")
save(p)
