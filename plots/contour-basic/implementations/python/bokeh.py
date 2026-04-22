""" pyplots.ai
contour-basic: Basic Contour Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import BasicTicker, ColorBar, LinearColorMapper
from bokeh.palettes import Viridis256
from bokeh.plotting import figure
from bokeh.resources import CDN
from contourpy import contour_generator


# Data - create a 2D scalar field using a mathematical function
np.random.seed(42)
x = np.linspace(-3, 3, 50)
y = np.linspace(-3, 3, 50)
X, Y = np.meshgrid(x, y)

# Create a Gaussian peak function with primary and secondary peaks
# This shows contour features: nested rings, gradient directions, multiple maxima
Z = np.exp(-(X**2 + Y**2)) + 0.5 * np.exp(-((X - 1.5) ** 2 + (Y + 1) ** 2) / 0.5)

# Define contour levels for smooth gradient visualization
levels = np.linspace(Z.min(), Z.max(), 12)

# Map levels to colors from Viridis palette (colorblind-safe)
n_levels = len(levels) - 1
color_indices = [int(i * 255 / (n_levels - 1)) if n_levels > 1 else 0 for i in range(n_levels)]
level_colors = [Viridis256[idx] for idx in color_indices]

# Generate filled contours using contourpy
fill_xs = []
fill_ys = []
fill_colors = []

for i in range(len(levels) - 1):
    low_level = levels[i]
    high_level = levels[i + 1]

    # Create filled contour generator
    cont_gen = contour_generator(x=x, y=y, z=Z, fill_type="ChunkCombinedOffset")
    filled = cont_gen.filled(low_level, high_level)

    # ChunkCombinedOffset returns tuple of (points_list, offsets_list) per chunk
    points_list, offsets_list = filled

    # Process each chunk
    for chunk_idx in range(len(points_list)):
        points = points_list[chunk_idx]
        offsets = offsets_list[chunk_idx]

        if points is None or offsets is None:
            continue

        # Extract polygons using offset pairs
        for j in range(len(offsets) - 1):
            start = int(offsets[j])
            end = int(offsets[j + 1])
            polygon = points[start:end]
            if len(polygon) > 2:
                fill_xs.append(polygon[:, 0].tolist())
                fill_ys.append(polygon[:, 1].tolist())
                fill_colors.append(level_colors[i])

# Generate contour lines using contourpy
line_xs = []
line_ys = []

cont_gen_lines = contour_generator(x=x, y=y, z=Z, line_type="SeparateCode")
for level in levels:
    lines, codes = cont_gen_lines.lines(level)
    for line in lines:
        if len(line) > 1:
            line_xs.append(line[:, 0].tolist())
            line_ys.append(line[:, 1].tolist())

# Create Bokeh figure
p = figure(
    width=4800,
    height=2700,
    title="contour-basic · bokeh · pyplots.ai",
    x_axis_label="X Coordinate",
    y_axis_label="Y Coordinate",
    toolbar_location=None,
    tools="",
    x_range=(-3.2, 3.2),
    y_range=(-3.2, 3.2),
)

# Plot filled contours
if fill_xs:
    p.patches(xs=fill_xs, ys=fill_ys, fill_color=fill_colors, line_color=None, fill_alpha=0.9)

# Plot contour lines
if line_xs:
    p.multi_line(xs=line_xs, ys=line_ys, line_color="#333333", line_width=1.5, line_alpha=0.7)

# Add color bar
color_mapper = LinearColorMapper(palette=Viridis256, low=Z.min(), high=Z.max())
color_bar = ColorBar(
    color_mapper=color_mapper,
    ticker=BasicTicker(desired_num_ticks=10),
    label_standoff=16,
    major_label_text_font_size="18pt",
    border_line_color=None,
    location=(0, 0),
    width=40,
    title="Z Value",
    title_text_font_size="20pt",
)
p.add_layout(color_bar, "right")

# Styling for 4800x2700 px
p.title.text_font_size = "28pt"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Grid styling - subtle
p.xgrid.grid_line_color = "#cccccc"
p.ygrid.grid_line_color = "#cccccc"
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = [6, 4]
p.ygrid.grid_line_dash = [6, 4]

# Axis styling
p.axis.axis_line_color = "#666666"
p.axis.major_tick_line_color = "#666666"

# Background
p.background_fill_color = "#fafafa"
p.border_fill_color = "white"
p.outline_line_color = None

# Save PNG
export_png(p, filename="plot.png")

# Save HTML for interactive version
save(p, filename="plot.html", resources=CDN, title="contour-basic · bokeh · pyplots.ai")
