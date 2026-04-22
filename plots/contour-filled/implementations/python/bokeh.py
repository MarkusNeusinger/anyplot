""" pyplots.ai
contour-filled: Filled Contour Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 90/100 | Created: 2025-12-30
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import BasicTicker, ColorBar, HoverTool, LinearColorMapper
from bokeh.palettes import Viridis256
from bokeh.plotting import figure
from contourpy import contour_generator


# Data - Terrain elevation surface with multiple peaks
np.random.seed(42)
x = np.linspace(-3, 3, 80)
y = np.linspace(-3, 3, 80)
X, Y = np.meshgrid(x, y)

# Create surface with multiple Gaussian peaks (terrain elevation in meters)
Z = (
    1.5 * np.exp(-((X - 1) ** 2 + (Y - 1) ** 2))
    + 2.0 * np.exp(-((X + 1.5) ** 2 + (Y + 0.5) ** 2) / 1.5)
    + 1.0 * np.exp(-((X - 0.5) ** 2 + (Y + 1.5) ** 2) / 0.8)
    - 0.5 * np.exp(-((X + 0.5) ** 2 + (Y - 1.5) ** 2) / 0.5)
)

# Scale to realistic elevation values (0-2000 meters)
Z = (Z - Z.min()) / (Z.max() - Z.min()) * 2000

# Create figure at 4800x2700 px with interactive tools
p = figure(
    width=4800,
    height=2700,
    title="contour-filled · bokeh · pyplots.ai",
    x_range=(x.min(), x.max()),
    y_range=(y.min(), y.max()),
    tools="pan,wheel_zoom,box_zoom,reset,save",
)

# Explicitly set axis labels after figure creation
p.xaxis.axis_label = "Distance East (km)"
p.yaxis.axis_label = "Distance North (km)"

# Color mapper for the filled surface
color_mapper = LinearColorMapper(palette=Viridis256, low=Z.min(), high=Z.max())

# Draw the filled surface using image
p.image(image=[Z], x=x.min(), y=y.min(), dw=x.max() - x.min(), dh=y.max() - y.min(), color_mapper=color_mapper)

# Overlay contour lines at specific levels for precise identification
n_contour_lines = 12
contour_levels = np.linspace(Z.min(), Z.max(), n_contour_lines + 2)[1:-1]

# Create contour generator
cont_gen = contour_generator(x=X, y=Y, z=Z)

# Draw contour lines with high contrast (white with dark outline effect)
for level in contour_levels:
    lines = cont_gen.lines(level)
    for line in lines:
        # Draw white line for visibility on dark backgrounds
        p.line(line[:, 0], line[:, 1], line_width=4, color="white", alpha=0.9)
        # Draw thinner dark line on top for contrast on light backgrounds
        p.line(line[:, 0], line[:, 1], line_width=1.5, color="#1a1a1a", alpha=0.8)

# Add colorbar with terrain context
color_bar = ColorBar(
    color_mapper=color_mapper,
    ticker=BasicTicker(desired_num_ticks=10),
    label_standoff=25,
    title="Terrain Elevation (m)",
    title_text_font_size="22pt",
    title_standoff=20,
    major_label_text_font_size="18pt",
    width=50,
    padding=40,
)
p.add_layout(color_bar, "right")

# Style text for large canvas
p.title.text_font_size = "28pt"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Grid styling - subtle overlay grid (reduced alpha per review feedback)
p.xgrid.grid_line_color = "white"
p.ygrid.grid_line_color = "white"
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3
p.xgrid.grid_line_width = 2
p.ygrid.grid_line_width = 2
p.xgrid.grid_line_dash = [8, 4]
p.ygrid.grid_line_dash = [8, 4]
p.xgrid.level = "overlay"
p.ygrid.level = "overlay"

# Add hover tool for interactive elevation display
# Create a grid of hover points for better interactivity
hover_x, hover_y, hover_z = [], [], []
step = 4  # Sample every 4th point for responsive hovering
for i in range(0, len(x), step):
    for j in range(0, len(y), step):
        hover_x.append(x[i])
        hover_y.append(y[j])
        hover_z.append(round(Z[j, i], 1))

# Add invisible scatter points for hover detection
hover_renderer = p.scatter(hover_x, hover_y, size=30, fill_alpha=0, line_alpha=0, name="hover_points")
hover_renderer.data_source.data["elevation"] = hover_z

# Configure hover tool to show elevation values
hover = HoverTool(
    renderers=[hover_renderer],
    tooltips=[("Location", "(@x{0.0} km E, @y{0.0} km N)"), ("Elevation", "@elevation{0} m")],
    mode="mouse",
)
p.add_tools(hover)

# Background
p.background_fill_color = None
p.border_fill_color = None

# Save as PNG and HTML
export_png(p, filename="plot.png")

# Also save as HTML for interactive viewing with hover tooltips
output_file("plot.html")
save(p)
