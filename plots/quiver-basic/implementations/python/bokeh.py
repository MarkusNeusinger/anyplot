""" pyplots.ai
quiver-basic: Basic Quiver Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure


# Data - Create a circular rotation flow field: u = -y, v = x
np.random.seed(42)
grid_size = 15
x_range = np.linspace(-2, 2, grid_size)
y_range = np.linspace(-2, 2, grid_size)
X, Y = np.meshgrid(x_range, y_range)
x = X.flatten()
y = Y.flatten()

# Vector components: circular rotation pattern
u = -y.copy()
v = x.copy()

# Normalize and scale arrows for visibility
magnitude = np.sqrt(u**2 + v**2)
magnitude[magnitude == 0] = 1  # Avoid division by zero at origin
scale = 0.18  # Arrow length scale
u_norm = u / magnitude * scale
v_norm = v / magnitude * scale

# Calculate arrow endpoints
x_end = x + u_norm
y_end = y + v_norm

# Calculate arrowhead points
# Arrowhead is a triangle at the end of each segment
arrowhead_length = 0.06
arrowhead_width = 0.035

# Unit vectors for each arrow
dx = u_norm / np.sqrt(u_norm**2 + v_norm**2 + 1e-10)
dy = v_norm / np.sqrt(u_norm**2 + v_norm**2 + 1e-10)

# Perpendicular vectors for arrowhead wings
perp_x = -dy
perp_y = dx

# Arrowhead vertices (triangle)
arrow_x1 = x_end - arrowhead_length * dx + arrowhead_width * perp_x
arrow_y1 = y_end - arrowhead_length * dy + arrowhead_width * perp_y
arrow_x2 = x_end - arrowhead_length * dx - arrowhead_width * perp_x
arrow_y2 = y_end - arrowhead_length * dy - arrowhead_width * perp_y

# Color by magnitude for additional insight
colors = ["#306998"] * len(x)  # Python Blue for all arrows

# Create figure (4800 × 2700 px)
p = figure(
    width=4800,
    height=2700,
    title="quiver-basic · bokeh · pyplots.ai",
    x_axis_label="X Position",
    y_axis_label="Y Position",
    x_range=(-2.5, 2.5),
    y_range=(-2.5, 2.5),
)

# Styling for large canvas
p.title.text_font_size = "28pt"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Draw arrow shafts (segments)
segment_source = ColumnDataSource(data={"x0": x, "y0": y, "x1": x_end, "y1": y_end, "color": colors})
p.segment(x0="x0", y0="y0", x1="x1", y1="y1", source=segment_source, line_width=3, line_color="color")

# Draw arrowheads (triangles using patches)
# Build triangle coordinates for each arrow
xs = [[x_end[i], arrow_x1[i], arrow_x2[i]] for i in range(len(x))]
ys = [[y_end[i], arrow_y1[i], arrow_y2[i]] for i in range(len(y))]

patch_source = ColumnDataSource(data={"xs": xs, "ys": ys, "color": colors})
p.patches(xs="xs", ys="ys", source=patch_source, fill_color="color", line_color="color")

# Grid styling - subtle
p.grid.grid_line_alpha = 0.3
p.grid.grid_line_dash = [6, 4]

# Save outputs
export_png(p, filename="plot.png")
output_file("plot.html", title="quiver-basic · bokeh · pyplots.ai")
save(p)
