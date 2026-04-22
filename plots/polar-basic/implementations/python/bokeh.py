""" pyplots.ai
polar-basic: Basic Polar Chart
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure


# Data - Hourly temperature readings (24-hour cycle)
np.random.seed(42)
hours = np.arange(24)
theta = hours * (2 * np.pi / 24)  # Convert hours to radians (0-2π)

# Temperature pattern: peak around 14:00, low around 04:00
base_temp = 15 + 8 * np.sin(theta - np.pi / 2)  # Shifted sine wave
temperature = base_temp + np.random.randn(24) * 1.5
radius = temperature - temperature.min() + 2  # Normalize to positive radius

# Convert polar to Cartesian (bokeh doesn't have native polar support)
# Rotate so 0h (midnight) is at top (subtract pi/2 to rotate 90 degrees CCW)
x = radius * np.cos(theta + np.pi / 2)
y = radius * np.sin(theta + np.pi / 2)

source = ColumnDataSource(data={"x": x, "y": y, "radius": radius, "theta": theta, "hour": hours, "temp": temperature})

# Create figure (square for polar chart)
p = figure(width=3600, height=3600, title="polar-basic · bokeh · pyplots.ai", match_aspect=True)

# Draw polar grid manually
max_radius = np.ceil(radius.max()) + 1.5
grid_radii = np.linspace(0, max_radius, 5)[1:]  # Skip 0

# Radial gridlines (concentric circles)
for r in grid_radii:
    circle_theta = np.linspace(0, 2 * np.pi, 100)
    cx = r * np.cos(circle_theta)
    cy = r * np.sin(circle_theta)
    p.line(cx, cy, line_color="#cccccc", line_width=2, line_alpha=0.4)

# Angular gridlines (spokes) at 3-hour intervals
for hour in [0, 3, 6, 9, 12, 15, 18, 21]:
    angle = hour * (2 * np.pi / 24) + np.pi / 2  # Rotate so 0h is at top
    p.line(
        [0, max_radius * np.cos(angle)],
        [0, max_radius * np.sin(angle)],
        line_color="#cccccc",
        line_width=2,
        line_alpha=0.4,
    )

# Add hour labels around the edge
label_radius = max_radius + 1.8
for hour in [0, 3, 6, 9, 12, 15, 18, 21]:
    angle = hour * (2 * np.pi / 24) + np.pi / 2
    lx = label_radius * np.cos(angle)
    ly = label_radius * np.sin(angle)
    label = f"{hour:02d}:00"
    p.text(
        x=[lx],
        y=[ly],
        text=[label],
        text_align="center",
        text_baseline="middle",
        text_font_size="22pt",
        text_color="#555555",
    )

# Connect points with line (in order)
p.line(x="x", y="y", source=source, line_color="#306998", line_width=4, line_alpha=0.8)

# Close the loop by connecting last point to first
p.line([x[-1], x[0]], [y[-1], y[0]], line_color="#306998", line_width=4, line_alpha=0.8)

# Plot data points
p.scatter(x="x", y="y", source=source, size=22, color="#306998", alpha=0.9)

# Add center point marker
p.scatter([0], [0], size=10, color="#555555", alpha=0.5)

# Styling
p.title.text_font_size = "32pt"
p.title.align = "center"
p.background_fill_color = "#fafafa"

# Hide axes (we have our own polar grid)
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False
p.outline_line_color = None

# Save outputs
export_png(p, filename="plot.png")
output_file("plot.html", title="polar-basic · bokeh · pyplots.ai")
save(p)
