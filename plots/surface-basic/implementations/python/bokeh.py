""" pyplots.ai
surface-basic: Basic 3D Surface Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColorBar, LinearColorMapper, Range1d
from bokeh.palettes import Viridis256
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data - create a smooth surface z = sin(x) * cos(y)
np.random.seed(42)

# Grid setup - 40x40 for smooth surface
n_points = 40
x = np.linspace(-3, 3, n_points)
y = np.linspace(-3, 3, n_points)
X, Y = np.meshgrid(x, y)

# Surface function: combination of sin and cos for interesting terrain
Z = np.sin(X) * np.cos(Y)

# 3D to 2D projection using isometric-like view (elevation=25°, azimuth=45°)
elev_rad = np.radians(25)
azim_rad = np.radians(45)

# Rotation around z-axis (azimuth)
X_rot = X * np.cos(azim_rad) - Y * np.sin(azim_rad)
Y_rot = X * np.sin(azim_rad) + Y * np.cos(azim_rad)

# Rotation around x-axis (elevation) and project to 2D
X_proj = X_rot
Z_proj = Y_rot * np.sin(elev_rad) + Z * np.cos(elev_rad)

# Prepare quads for surface rendering (filled patches)
# Collect quads with their z-values for color mapping and depth sorting
quads = []
for i in range(n_points - 1):
    for j in range(n_points - 1):
        # Four corners of each quad
        xs = [X_proj[i, j], X_proj[i, j + 1], X_proj[i + 1, j + 1], X_proj[i + 1, j]]
        ys = [Z_proj[i, j], Z_proj[i, j + 1], Z_proj[i + 1, j + 1], Z_proj[i + 1, j]]

        # Average z for color (original Z, not projected)
        avg_z = (Z[i, j] + Z[i, j + 1] + Z[i + 1, j + 1] + Z[i + 1, j]) / 4

        # Depth for sorting (average Y_rot for painter's algorithm)
        depth = (Y_rot[i, j] + Y_rot[i, j + 1] + Y_rot[i + 1, j + 1] + Y_rot[i + 1, j]) / 4

        quads.append((depth, xs, ys, avg_z))

# Sort by depth (back to front - painter's algorithm)
quads.sort(key=lambda q: q[0], reverse=True)

# Extract sorted data
quad_xs = [q[1] for q in quads]
quad_ys = [q[2] for q in quads]
quad_colors = [q[3] for q in quads]

# Color mapping using Viridis colormap
z_min, z_max = Z.min(), Z.max()
color_mapper = LinearColorMapper(palette=Viridis256, low=z_min, high=z_max)

# Map z values to colors
colors = []
for z_val in quad_colors:
    # Normalize to 0-255 index
    idx = int((z_val - z_min) / (z_max - z_min) * 255)
    idx = max(0, min(255, idx))
    colors.append(Viridis256[idx])

# Create Bokeh figure
p = figure(width=4800, height=2700, title="surface-basic · bokeh · pyplots.ai", toolbar_location=None, tools="")

# Draw surface patches with subtle edges
p.patches(xs=quad_xs, ys=quad_ys, fill_color=colors, line_color="#306998", line_alpha=0.3, line_width=0.5, alpha=0.9)

# Set appropriate ranges with padding
x_min = min(min(xs) for xs in quad_xs)
x_max = max(max(xs) for xs in quad_xs)
y_min = min(min(ys) for ys in quad_ys)
y_max = max(max(ys) for ys in quad_ys)

x_pad = (x_max - x_min) * 0.15
y_pad = (y_max - y_min) * 0.15

p.x_range = Range1d(x_min - x_pad, x_max + x_pad)
p.y_range = Range1d(y_min - y_pad, y_max + y_pad)

# Hide default axes for cleaner 3D projection look
p.xaxis.visible = False
p.yaxis.visible = False

# Add text annotations for 3D axes labels
p.text(
    x=[x_max + x_pad * 0.4],
    y=[(y_min + y_max) / 2],
    text=["X"],
    text_font_size="28pt",
    text_color="#666666",
    text_align="center",
)
p.text(
    x=[x_min - x_pad * 0.3],
    y=[y_min - y_pad * 0.3],
    text=["Y"],
    text_font_size="28pt",
    text_color="#666666",
    text_align="center",
)
p.text(
    x=[x_min - x_pad * 0.5],
    y=[y_max + y_pad * 0.3],
    text=["Z"],
    text_font_size="28pt",
    text_color="#666666",
    text_align="center",
)

# Add color bar for z-value scale
color_bar = ColorBar(
    color_mapper=color_mapper,
    width=60,
    location=(0, 0),
    title="Z Value",
    title_text_font_size="22pt",
    major_label_text_font_size="18pt",
    margin=20,
    padding=10,
)
p.add_layout(color_bar, "right")

# Title styling for large canvas
p.title.text_font_size = "32pt"

# Grid styling - subtle
p.xgrid.grid_line_color = "#cccccc"
p.ygrid.grid_line_color = "#cccccc"
p.xgrid.grid_line_alpha = 0.2
p.ygrid.grid_line_alpha = 0.2
p.xgrid.grid_line_dash = [6, 4]
p.ygrid.grid_line_dash = [6, 4]

# Background styling
p.background_fill_color = "#fafafa"
p.border_fill_color = "white"
p.outline_line_color = None
p.min_border_right = 200

# Save PNG
export_png(p, filename="plot.png")

# Save HTML for interactive version
save(p, filename="plot.html", resources=CDN, title="surface-basic · bokeh · pyplots.ai")
