""" pyplots.ai
radar-basic: Basic Radar Chart
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, Legend, LegendItem
from bokeh.plotting import figure


# Data - Employee performance comparison
categories = ["Communication", "Technical Skills", "Teamwork", "Problem Solving", "Leadership", "Creativity"]
employee_a = [85, 90, 75, 88, 70, 82]
employee_b = [70, 75, 90, 72, 85, 78]

n_categories = len(categories)

# Calculate angles for each axis (evenly distributed around circle)
angles = np.linspace(0, 2 * np.pi, n_categories, endpoint=False).tolist()

# Close the polygon by repeating the first point
angles_closed = angles + [angles[0]]
values_a_closed = employee_a + [employee_a[0]]
values_b_closed = employee_b + [employee_b[0]]


# Convert polar to cartesian coordinates
x_a = [v * np.cos(a) for v, a in zip(values_a_closed, angles_closed, strict=True)]
y_a = [v * np.sin(a) for v, a in zip(values_a_closed, angles_closed, strict=True)]
x_b = [v * np.cos(a) for v, a in zip(values_b_closed, angles_closed, strict=True)]
y_b = [v * np.sin(a) for v, a in zip(values_b_closed, angles_closed, strict=True)]

# Create figure (square for radar chart)
p = figure(
    width=3600,
    height=3600,
    title="radar-basic · bokeh · pyplots.ai",
    x_range=(-150, 150),
    y_range=(-140, 140),
    tools="",
    toolbar_location=None,
)

# Draw grid circles at 20, 40, 60, 80, 100
for r in [20, 40, 60, 80, 100]:
    theta = np.linspace(0, 2 * np.pi, 100)
    x_circle = r * np.cos(theta)
    y_circle = r * np.sin(theta)
    p.line(x_circle, y_circle, line_color="#cccccc", line_width=2, line_alpha=0.6)

# Draw axis lines from center to each category
for angle in angles:
    x_end = 100 * np.cos(angle)
    y_end = 100 * np.sin(angle)
    p.line([0, x_end], [0, y_end], line_color="#cccccc", line_width=2, line_alpha=0.6)

# Add axis labels at outer edge
for angle, cat in zip(angles, categories, strict=True):
    # Position labels slightly outside the outer circle
    label_radius = 115
    x_label = label_radius * np.cos(angle)
    y_label = label_radius * np.sin(angle)

    # Adjust text alignment based on position
    if abs(np.cos(angle)) < 0.1:  # Top or bottom
        text_align = "center"
    elif np.cos(angle) > 0:
        text_align = "left"
    else:
        text_align = "right"

    p.text(
        x=[x_label],
        y=[y_label],
        text=[cat],
        text_font_size="22pt",
        text_align=text_align,
        text_baseline="middle",
        text_color="#333333",
    )

# Draw filled polygons for each employee
source_a = ColumnDataSource(data={"x": x_a, "y": y_a})
source_b = ColumnDataSource(data={"x": x_b, "y": y_b})

# Employee A - Python Blue
patch_a = p.patch("x", "y", source=source_a, fill_color="#306998", fill_alpha=0.25, line_color="#306998", line_width=4)
scatter_a = p.scatter("x", "y", source=source_a, size=20, color="#306998")

# Employee B - Python Yellow (darker outline for visibility)
patch_b = p.patch("x", "y", source=source_b, fill_color="#FFD43B", fill_alpha=0.25, line_color="#B8960A", line_width=4)
scatter_b = p.scatter("x", "y", source=source_b, size=20, color="#B8960A")

# Add legend
legend = Legend(
    items=[
        LegendItem(label="Employee A", renderers=[patch_a, scatter_a]),
        LegendItem(label="Employee B", renderers=[patch_b, scatter_b]),
    ],
    location="top_right",
)
legend.label_text_font_size = "22pt"
legend.glyph_height = 35
legend.glyph_width = 35
legend.spacing = 12
legend.background_fill_alpha = 0.8
p.add_layout(legend)

# Style the plot
p.title.text_font_size = "32pt"
p.title.align = "center"
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False
p.outline_line_color = None
p.background_fill_color = "white"

# Save outputs
export_png(p, filename="plot.png")
output_file("plot.html")
save(p)
