""" pyplots.ai
scatter-color-mapped: Color-Mapped Scatter Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColorBar, ColumnDataSource, LinearColorMapper
from bokeh.palettes import Viridis256
from bokeh.plotting import figure
from bokeh.resources import CDN
from bokeh.transform import linear_cmap


# Data
np.random.seed(42)
n_points = 150
x = np.random.randn(n_points) * 10 + 50
y = 0.6 * x + np.random.randn(n_points) * 8 + 20
intensity = np.sqrt((x - 50) ** 2 + (y - 50) ** 2) + np.random.randn(n_points) * 3

source = ColumnDataSource(data={"x": x, "y": y, "intensity": intensity})

# Create color mapper
color_mapper = LinearColorMapper(palette=Viridis256, low=intensity.min(), high=intensity.max())

# Create figure (4800 x 2700 px)
p = figure(
    width=4800,
    height=2700,
    title="scatter-color-mapped · bokeh · pyplots.ai",
    x_axis_label="X Value",
    y_axis_label="Y Value",
)

# Plot scatter with color mapping
p.scatter(
    x="x",
    y="y",
    source=source,
    size=30,
    fill_color=linear_cmap("intensity", palette=Viridis256, low=intensity.min(), high=intensity.max()),
    line_color=None,
    fill_alpha=0.8,
)

# Add colorbar
color_bar = ColorBar(
    color_mapper=color_mapper,
    title="Intensity",
    title_text_font_size="22pt",
    title_standoff=20,
    major_label_text_font_size="18pt",
    label_standoff=12,
    width=50,
    padding=40,
)
p.add_layout(color_bar, "right")

# Styling for large canvas
p.title.text_font_size = "32pt"
p.xaxis.axis_label_text_font_size = "24pt"
p.yaxis.axis_label_text_font_size = "24pt"
p.xaxis.major_label_text_font_size = "20pt"
p.yaxis.major_label_text_font_size = "20pt"

# Grid styling
p.grid.grid_line_alpha = 0.3
p.grid.grid_line_dash = [6, 4]

# Background
p.background_fill_color = "#fafafa"

# Save PNG and HTML
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="scatter-color-mapped · bokeh · pyplots.ai")
