""" pyplots.ai
rose-basic: Basic Rose Chart
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure


# Data - Monthly rainfall (mm) showing seasonal patterns
np.random.seed(42)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
values = [85, 70, 65, 45, 30, 20, 15, 25, 40, 60, 75, 90]

n = len(months)

# Calculate wedge angles (equal slices, starting from top/north)
angle_width = 2 * np.pi / n
start_angles = np.array([np.pi / 2 - angle_width / 2 - i * angle_width for i in range(n)])
end_angles = start_angles - angle_width

# Normalize values to radius (max value = 1.0 for full radius)
max_val = max(values)
radii = [v / max_val for v in values]

# Colors - gradient from Python Yellow to Python Blue based on value
colors = ["#306998" if v >= 60 else "#4A89B8" if v >= 40 else "#7AB3D8" if v >= 25 else "#FFD43B" for v in values]

source = ColumnDataSource(
    data={
        "start_angle": start_angles,
        "end_angle": end_angles,
        "radius": radii,
        "months": months,
        "values": values,
        "colors": colors,
    }
)

# Create figure with matching x/y ranges for circular shape
p = figure(
    width=4800,
    height=2700,
    title="Monthly Rainfall · rose-basic · bokeh · pyplots.ai",
    x_range=(-1.3, 1.3),
    y_range=(-1.2, 1.1),
    tools="",
    toolbar_location=None,
)

# Draw wedges (rose petals)
p.wedge(
    x=0,
    y=0,
    radius="radius",
    start_angle="end_angle",
    end_angle="start_angle",
    source=source,
    fill_color="colors",
    fill_alpha=0.8,
    line_color="white",
    line_width=2,
)

# Add radial gridlines (concentric circles)
for r in [0.25, 0.5, 0.75, 1.0]:
    theta = np.linspace(0, 2 * np.pi, 100)
    p.line(r * np.cos(theta), r * np.sin(theta), line_color="gray", line_alpha=0.3, line_width=1, line_dash="dashed")

# Add radial lines from center
for i in range(n):
    angle = np.pi / 2 - i * angle_width
    p.line([0, 1.05 * np.cos(angle)], [0, 1.05 * np.sin(angle)], line_color="gray", line_alpha=0.2, line_width=1)

# Add month labels around the outside
label_radius = 1.12
for i, month in enumerate(months):
    angle = np.pi / 2 - i * angle_width
    x = label_radius * np.cos(angle)
    y = label_radius * np.sin(angle)
    p.text(
        x=[x],
        y=[y],
        text=[month],
        text_align="center",
        text_baseline="middle",
        text_font_size="18pt",
        text_color="#333333",
    )

# Add value scale labels on right side
p.text(x=[1.05], y=[0.25], text=["25%"], text_font_size="14pt", text_color="gray", text_align="left")
p.text(x=[1.05], y=[0.5], text=["50%"], text_font_size="14pt", text_color="gray", text_align="left")
p.text(x=[1.05], y=[0.75], text=["75%"], text_font_size="14pt", text_color="gray", text_align="left")
p.text(x=[1.05], y=[1.0], text=["100%"], text_font_size="14pt", text_color="gray", text_align="left")

# Styling
p.title.text_font_size = "28pt"
p.title.align = "center"
p.background_fill_color = "white"
p.border_fill_color = "white"
p.outline_line_color = None

# Hide axes (not needed for rose chart)
p.axis.visible = False
p.grid.visible = False

# Save as PNG and HTML
export_png(p, filename="plot.png")
output_file("plot.html")
save(p)
