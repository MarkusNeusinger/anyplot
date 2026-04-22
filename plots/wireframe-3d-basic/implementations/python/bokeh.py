""" pyplots.ai
wireframe-3d-basic: Basic 3D Wireframe Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 90/100 | Created: 2025-12-24
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import Label, Range1d
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data - create a ripple surface z = sin(sqrt(x^2 + y^2))
np.random.seed(42)

# Grid setup - 30x30 for clear wireframe
n_points = 30
x = np.linspace(-4, 4, n_points)
y = np.linspace(-4, 4, n_points)
X, Y = np.meshgrid(x, y)

# Ripple function
R = np.sqrt(X**2 + Y**2)
Z = np.sin(R)

# 3D to 2D projection (elevation=30, azimuth=45)
elev_rad = np.radians(30)
azim_rad = np.radians(45)

# Rotation around z-axis (azimuth)
X_rot = X * np.cos(azim_rad) - Y * np.sin(azim_rad)
Y_rot = X * np.sin(azim_rad) + Y * np.cos(azim_rad)

# Rotation around x-axis (elevation) and project
X_proj = X_rot
Z_proj = Y_rot * np.sin(elev_rad) + Z * np.cos(elev_rad)

# Collect wireframe lines
# Lines along x-direction (rows)
x_lines_xs = []
x_lines_ys = []
for i in range(n_points):
    x_lines_xs.append(X_proj[i, :].tolist())
    x_lines_ys.append(Z_proj[i, :].tolist())

# Lines along y-direction (columns)
y_lines_xs = []
y_lines_ys = []
for j in range(n_points):
    y_lines_xs.append(X_proj[:, j].tolist())
    y_lines_ys.append(Z_proj[:, j].tolist())

# Combine all lines
all_xs = x_lines_xs + y_lines_xs
all_ys = x_lines_ys + y_lines_ys

# Create Bokeh figure
p = figure(width=4800, height=2700, title="wireframe-3d-basic · bokeh · pyplots.ai", toolbar_location=None, tools="")

# Hide default axes since we're doing custom 3D axis visualization
p.xaxis.visible = False
p.yaxis.visible = False

# Draw wireframe using multi_line with Python Blue
p.multi_line(xs=all_xs, ys=all_ys, line_color="#306998", line_width=3, line_alpha=0.85)

# Set appropriate ranges with padding for axes and labels
x_min, x_max = min(min(xs) for xs in all_xs), max(max(xs) for xs in all_xs)
y_min, y_max = min(min(ys) for ys in all_ys), max(max(ys) for ys in all_ys)

x_pad = (x_max - x_min) * 0.20
y_pad = (y_max - y_min) * 0.25

p.x_range = Range1d(x_min - x_pad, x_max + x_pad)
p.y_range = Range1d(y_min - y_pad * 1.2, y_max + y_pad)

# Custom 3D axis lines positioned at the projected origin of the wireframe data
# Project 3D origin (0,0,0) to 2D using same transformation
origin_3d_x, origin_3d_y, origin_3d_z = 0, 0, 0
origin_x_rot = origin_3d_x * np.cos(azim_rad) - origin_3d_y * np.sin(azim_rad)
origin_y_rot = origin_3d_x * np.sin(azim_rad) + origin_3d_y * np.cos(azim_rad)
origin_x = origin_x_rot
origin_y = origin_y_rot * np.sin(elev_rad) + origin_3d_z * np.cos(elev_rad)

# Axis styling
axis_color = "#333333"
axis_width = 6
axis_length = 2.5

# Project 3D axis endpoints to 2D using same transformation
# X-axis: point (axis_length, 0, 0) in 3D
x_end_x_rot = axis_length * np.cos(azim_rad) - 0 * np.sin(azim_rad)
x_end_y_rot = axis_length * np.sin(azim_rad) + 0 * np.cos(azim_rad)
x_axis_end_x = x_end_x_rot
x_axis_end_y = x_end_y_rot * np.sin(elev_rad) + 0 * np.cos(elev_rad)

# Y-axis: point (0, axis_length, 0) in 3D
y_end_x_rot = 0 * np.cos(azim_rad) - axis_length * np.sin(azim_rad)
y_end_y_rot = 0 * np.sin(azim_rad) + axis_length * np.cos(azim_rad)
y_axis_end_x = y_end_x_rot
y_axis_end_y = y_end_y_rot * np.sin(elev_rad) + 0 * np.cos(elev_rad)

# Z-axis: point (0, 0, axis_length) in 3D
z_axis_end_x = origin_x
z_axis_end_y = origin_y + axis_length * np.cos(elev_rad)

# Draw axis lines from projected origin
p.line(x=[origin_x, x_axis_end_x], y=[origin_y, x_axis_end_y], line_color=axis_color, line_width=axis_width)
p.line(x=[origin_x, y_axis_end_x], y=[origin_y, y_axis_end_y], line_color=axis_color, line_width=axis_width)
p.line(x=[origin_x, z_axis_end_x], y=[origin_y, z_axis_end_y], line_color=axis_color, line_width=axis_width)

# Add axis labels using Label annotations for reliable rendering
x_label = Label(
    x=x_axis_end_x + 0.3,
    y=x_axis_end_y - 0.2,
    text="X",
    text_font_size="72pt",
    text_color="#222222",
    text_font_style="bold",
)
p.add_layout(x_label)

y_label = Label(
    x=y_axis_end_x - 0.5,
    y=y_axis_end_y + 0.2,
    text="Y",
    text_font_size="72pt",
    text_color="#222222",
    text_font_style="bold",
)
p.add_layout(y_label)

z_label = Label(
    x=z_axis_end_x + 0.3,
    y=z_axis_end_y + 0.1,
    text="Z",
    text_font_size="72pt",
    text_color="#222222",
    text_font_style="bold",
)
p.add_layout(z_label)

# Add axis arrows (small triangles at the end of each axis)
arrow_size = 0.15
# X-axis arrow
x_dir = np.array([x_axis_end_x - origin_x, x_axis_end_y - origin_y])
x_dir = x_dir / np.linalg.norm(x_dir)
x_perp = np.array([-x_dir[1], x_dir[0]])
p.patch(
    x=[
        x_axis_end_x,
        x_axis_end_x - arrow_size * x_dir[0] + arrow_size * 0.5 * x_perp[0],
        x_axis_end_x - arrow_size * x_dir[0] - arrow_size * 0.5 * x_perp[0],
    ],
    y=[
        x_axis_end_y,
        x_axis_end_y - arrow_size * x_dir[1] + arrow_size * 0.5 * x_perp[1],
        x_axis_end_y - arrow_size * x_dir[1] - arrow_size * 0.5 * x_perp[1],
    ],
    fill_color=axis_color,
    line_color=axis_color,
)

# Y-axis arrow
y_dir = np.array([y_axis_end_x - origin_x, y_axis_end_y - origin_y])
y_dir = y_dir / np.linalg.norm(y_dir)
y_perp = np.array([-y_dir[1], y_dir[0]])
p.patch(
    x=[
        y_axis_end_x,
        y_axis_end_x - arrow_size * y_dir[0] + arrow_size * 0.5 * y_perp[0],
        y_axis_end_x - arrow_size * y_dir[0] - arrow_size * 0.5 * y_perp[0],
    ],
    y=[
        y_axis_end_y,
        y_axis_end_y - arrow_size * y_dir[1] + arrow_size * 0.5 * y_perp[1],
        y_axis_end_y - arrow_size * y_dir[1] - arrow_size * 0.5 * y_perp[1],
    ],
    fill_color=axis_color,
    line_color=axis_color,
)

# Z-axis arrow
z_dir = np.array([z_axis_end_x - origin_x, z_axis_end_y - origin_y])
z_dir = z_dir / np.linalg.norm(z_dir)
z_perp = np.array([-z_dir[1], z_dir[0]])
p.patch(
    x=[
        z_axis_end_x,
        z_axis_end_x - arrow_size * z_dir[0] + arrow_size * 0.5 * z_perp[0],
        z_axis_end_x - arrow_size * z_dir[0] - arrow_size * 0.5 * z_perp[0],
    ],
    y=[
        z_axis_end_y,
        z_axis_end_y - arrow_size * z_dir[1] + arrow_size * 0.5 * z_perp[1],
        z_axis_end_y - arrow_size * z_dir[1] - arrow_size * 0.5 * z_perp[1],
    ],
    fill_color=axis_color,
    line_color=axis_color,
)

# Add formula annotation in bottom right
formula_label = Label(
    x=x_max - 0.5,
    y=y_min - y_pad * 0.5,
    text="z = sin(sqrt(x² + y²))",
    text_font_size="48pt",
    text_color="#555555",
    text_font_style="italic",
)
p.add_layout(formula_label)

# Styling for 4800x2700 px - larger title for high-res canvas
p.title.text_font_size = "56pt"
p.title.text_font_style = "bold"

# Disable grid for cleaner 3D appearance
p.xgrid.visible = False
p.ygrid.visible = False

# Background
p.background_fill_color = "#f8f9fa"
p.border_fill_color = "white"
p.outline_line_color = None

# Save PNG
export_png(p, filename="plot.png")

# Save HTML for interactive version
save(p, filename="plot.html", resources=CDN, title="wireframe-3d-basic · bokeh · pyplots.ai")
