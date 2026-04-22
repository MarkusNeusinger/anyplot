""" pyplots.ai
scatter-marginal: Scatter Plot with Marginal Distributions
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import numpy as np
from bokeh.io import export_png
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure


# Data - bivariate normal with correlation
np.random.seed(42)
n_points = 200
x = np.random.randn(n_points) * 15 + 50
y = x * 0.6 + np.random.randn(n_points) * 10 + 20

source = ColumnDataSource(data={"x": x, "y": y})

# Colors
python_blue = "#306998"
python_yellow = "#FFD43B"

# Calculate dimensions for 4800x2700 total with marginal plots
# Main scatter: ~80% of each dimension, marginals: ~20%
main_width = 3800
main_height = 2100
marginal_width = 3800  # Same as main for alignment
marginal_height = 550
side_marginal_width = 950
side_marginal_height = 2100

# Histogram bins
n_bins = 30
x_hist, x_edges = np.histogram(x, bins=n_bins)
y_hist, y_edges = np.histogram(y, bins=n_bins)

# Main scatter plot
p_scatter = figure(
    width=main_width,
    height=main_height,
    x_axis_label="X Value",
    y_axis_label="Y Value",
    title="scatter-marginal · bokeh · pyplots.ai",
)

p_scatter.scatter(x="x", y="y", source=source, size=18, color=python_blue, alpha=0.65, line_color=None)

# Style main scatter
p_scatter.title.text_font_size = "28pt"
p_scatter.xaxis.axis_label_text_font_size = "22pt"
p_scatter.yaxis.axis_label_text_font_size = "22pt"
p_scatter.xaxis.major_label_text_font_size = "18pt"
p_scatter.yaxis.major_label_text_font_size = "18pt"
p_scatter.grid.grid_line_alpha = 0.3
p_scatter.grid.grid_line_dash = [6, 4]

# Top marginal histogram (X distribution)
p_top = figure(
    width=main_width,
    height=marginal_height,
    x_range=p_scatter.x_range,  # Align with scatter
    title=None,
)
p_top.quad(
    top=x_hist,
    bottom=0,
    left=x_edges[:-1],
    right=x_edges[1:],
    fill_color=python_yellow,
    line_color=python_blue,
    alpha=0.7,
)
p_top.xaxis.visible = False
p_top.yaxis.axis_label = "Count"
p_top.yaxis.axis_label_text_font_size = "18pt"
p_top.yaxis.major_label_text_font_size = "14pt"
p_top.grid.grid_line_alpha = 0.3
p_top.min_border_bottom = 0
p_top.min_border_left = p_scatter.min_border_left

# Right marginal histogram (Y distribution)
p_right = figure(
    width=side_marginal_width,
    height=main_height,
    y_range=p_scatter.y_range,  # Align with scatter
    title=None,
)
p_right.quad(
    top=y_edges[1:],
    bottom=y_edges[:-1],
    left=0,
    right=y_hist,
    fill_color=python_yellow,
    line_color=python_blue,
    alpha=0.7,
)
p_right.yaxis.visible = False
p_right.xaxis.axis_label = "Count"
p_right.xaxis.axis_label_text_font_size = "18pt"
p_right.xaxis.major_label_text_font_size = "14pt"
p_right.grid.grid_line_alpha = 0.3
p_right.min_border_left = 0
p_right.min_border_bottom = p_scatter.min_border_bottom

# Empty corner placeholder
p_corner = figure(width=side_marginal_width, height=marginal_height, toolbar_location=None)
p_corner.outline_line_color = None
p_corner.xaxis.visible = False
p_corner.yaxis.visible = False
p_corner.grid.visible = False

# Remove toolbars for clean look
p_scatter.toolbar_location = None
p_top.toolbar_location = None
p_right.toolbar_location = None

# Layout: top marginal + corner on top row, scatter + right marginal on bottom row
layout = column(row(p_top, p_corner), row(p_scatter, p_right))

# Save
export_png(layout, filename="plot.png")
