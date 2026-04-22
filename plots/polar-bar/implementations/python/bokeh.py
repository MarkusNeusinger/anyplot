""" pyplots.ai
polar-bar: Polar Bar Chart (Wind Rose)
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import ColumnDataSource, Label, Title
from bokeh.palettes import Blues8
from bokeh.plotting import figure


# Data - Wind frequency by direction (8 compass points)
np.random.seed(42)
directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
# Simulating wind pattern: prevailing winds from SW and W
frequencies = np.array([12, 8, 10, 6, 9, 18, 22, 14])

# Convert directions to angles (0° = North, clockwise)
# In Bokeh, angles are counterclockwise from East, so we need to convert
n_dirs = len(directions)
angles = np.linspace(0, 2 * np.pi, n_dirs, endpoint=False)
# Bokeh: 0 = East, pi/2 = North, counterclockwise
start_angles = np.pi / 2 - angles - np.pi / n_dirs
end_angles = np.pi / 2 - angles + np.pi / n_dirs

# Normalize frequencies for bar length
max_freq = frequencies.max()
radii = frequencies / max_freq * 0.75  # Scale to 75% of plot radius

# Colors - Python Blue palette
colors = [Blues8[min(7, max(0, 7 - int((f / max_freq) * 7)))] for f in frequencies]

# Create figure (square for polar plot)
p = figure(width=3600, height=3600, x_range=(-1.05, 1.05), y_range=(-1.05, 1.05), tools="", toolbar_location=None)

# Remove axes and grid for polar appearance
p.axis.visible = False
p.grid.visible = False
p.outline_line_color = None
p.background_fill_color = "#fafafa"

# Title styling
p.title = Title(text="polar-bar · bokeh · pyplots.ai", text_font_size="42pt", text_color="#306998", align="center")

# Draw concentric reference circles
circle_radii = [0.25, 0.50, 0.75]
for r in circle_radii:
    p.circle(x=0, y=0, radius=r, fill_color=None, line_color="#aaaaaa", line_width=2, line_dash="dashed")

# Draw outer circle
p.circle(x=0, y=0, radius=0.85, fill_color=None, line_color="#888888", line_width=2)

# Draw radial lines for each direction
for i in range(n_dirs):
    angle = np.pi / 2 - angles[i]
    x_end = np.cos(angle) * 0.85
    y_end = np.sin(angle) * 0.85
    p.line([0, x_end], [0, y_end], line_color="#cccccc", line_width=1.5)

# Draw wedges (polar bars)
source = ColumnDataSource(
    data={
        "x": [0] * n_dirs,
        "y": [0] * n_dirs,
        "radius": radii.tolist(),
        "start_angle": start_angles.tolist(),
        "end_angle": end_angles.tolist(),
        "color": colors,
        "direction": directions,
        "frequency": frequencies.tolist(),
    }
)

p.wedge(
    x="x",
    y="y",
    radius="radius",
    start_angle="start_angle",
    end_angle="end_angle",
    fill_color="color",
    fill_alpha=0.9,
    line_color="#306998",
    line_width=3,
    source=source,
)

# Add direction labels around the plot
label_radius = 0.93
for i, direction in enumerate(directions):
    angle = np.pi / 2 - angles[i]
    x_label = np.cos(angle) * label_radius
    y_label = np.sin(angle) * label_radius

    label = Label(
        x=x_label,
        y=y_label,
        text=direction,
        text_font_size="32pt",
        text_font_style="bold",
        text_color="#306998",
        text_align="center",
        text_baseline="middle",
    )
    p.add_layout(label)

# Add frequency scale labels at reference circles
for r in circle_radii:
    freq_val = int(r / 0.75 * max_freq)
    label = Label(
        x=0.03,
        y=r + 0.015,
        text=f"{freq_val}%",
        text_font_size="20pt",
        text_color="#666666",
        text_align="left",
        text_baseline="bottom",
    )
    p.add_layout(label)

# Save as PNG
export_png(p, filename="plot.png")
