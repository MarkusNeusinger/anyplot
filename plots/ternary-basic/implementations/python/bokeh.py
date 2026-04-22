""" pyplots.ai
ternary-basic: Basic Ternary Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 94/100 | Created: 2025-12-17
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, Label
from bokeh.plotting import figure


# Data - Soil composition samples (Sand, Silt, Clay)
np.random.seed(42)
n_points = 50

# Generate random compositions that sum to 100%
raw = np.random.dirichlet(alpha=[2, 2, 2], size=n_points) * 100
sand = raw[:, 0]
silt = raw[:, 1]
clay = raw[:, 2]


# Convert ternary coordinates to Cartesian (equilateral triangle)
def ternary_to_cartesian(a, b, c):
    """Convert ternary coordinates (a, b, c) to Cartesian (x, y).
    Triangle vertices: bottom-left (1,0,0), bottom-right (0,1,0), top (0,0,1)
    """
    total = a + b + c
    b_norm = b / total
    c_norm = c / total
    x = 0.5 * (2 * b_norm + c_norm)
    y = (np.sqrt(3) / 2) * c_norm
    return x, y


# Convert data points
x_data, y_data = ternary_to_cartesian(sand, silt, clay)

# Triangle vertices (in Cartesian coordinates)
# Vertex A (Sand, 100%) at bottom-left: (0, 0)
# Vertex B (Silt, 100%) at bottom-right: (1, 0)
# Vertex C (Clay, 100%) at top: (0.5, sqrt(3)/2)
tri_x = [0, 1, 0.5, 0]
tri_y = [0, 0, np.sqrt(3) / 2, 0]

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="Soil Composition · ternary-basic · bokeh · pyplots.ai",
    x_range=(-0.15, 1.15),
    y_range=(-0.15, 1.05),
    tools="",
    toolbar_location=None,
)

# Remove default axes
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False

# Draw triangle outline
p.line(tri_x, tri_y, line_width=3, color="black")

# Draw grid lines at 20% intervals
grid_color = "#888888"
grid_alpha = 0.4
grid_width = 1.5

for pct in [20, 40, 60, 80]:
    frac = pct / 100

    # Lines parallel to each side
    # Parallel to BC (constant A) - horizontal lines from A vertex perspective
    a1, b1, c1 = frac, 1 - frac, 0
    a2, b2, c2 = frac, 0, 1 - frac
    x1, y1 = ternary_to_cartesian(a1, b1, c1)
    x2, y2 = ternary_to_cartesian(a2, b2, c2)
    p.line([x1, x2], [y1, y2], line_width=grid_width, color=grid_color, alpha=grid_alpha)

    # Parallel to AC (constant B) - lines from B vertex perspective
    a1, b1, c1 = 1 - frac, frac, 0
    a2, b2, c2 = 0, frac, 1 - frac
    x1, y1 = ternary_to_cartesian(a1, b1, c1)
    x2, y2 = ternary_to_cartesian(a2, b2, c2)
    p.line([x1, x2], [y1, y2], line_width=grid_width, color=grid_color, alpha=grid_alpha)

    # Parallel to AB (constant C) - lines from C vertex perspective
    a1, b1, c1 = 1 - frac, 0, frac
    a2, b2, c2 = 0, 1 - frac, frac
    x1, y1 = ternary_to_cartesian(a1, b1, c1)
    x2, y2 = ternary_to_cartesian(a2, b2, c2)
    p.line([x1, x2], [y1, y2], line_width=grid_width, color=grid_color, alpha=grid_alpha)

# Add tick labels along each edge
tick_font_size = "16pt"
tick_offset = 0.04

for pct in [0, 20, 40, 60, 80, 100]:
    frac = pct / 100

    # Sand axis (bottom edge, left to right = decreasing Sand)
    x_tick, y_tick = ternary_to_cartesian(1 - frac, frac, 0)
    label = Label(
        x=x_tick,
        y=y_tick - tick_offset,
        text=f"{int(100 - pct)}",
        text_font_size=tick_font_size,
        text_align="center",
        text_baseline="top",
    )
    p.add_layout(label)

    # Silt axis (right edge, bottom to top = decreasing Silt)
    x_tick, y_tick = ternary_to_cartesian(0, 1 - frac, frac)
    label = Label(
        x=x_tick + tick_offset * 0.8,
        y=y_tick + tick_offset * 0.5,
        text=f"{int(100 - pct)}",
        text_font_size=tick_font_size,
        text_align="left",
        text_baseline="middle",
    )
    p.add_layout(label)

    # Clay axis (left edge, top to bottom = decreasing Clay)
    x_tick, y_tick = ternary_to_cartesian(frac, 0, 1 - frac)
    label = Label(
        x=x_tick - tick_offset * 0.8,
        y=y_tick + tick_offset * 0.5,
        text=f"{int(100 - pct)}",
        text_font_size=tick_font_size,
        text_align="right",
        text_baseline="middle",
    )
    p.add_layout(label)

# Add vertex labels
label_font_size = "24pt"
label_offset = 0.08

# Sand (bottom-left vertex)
sand_label = Label(
    x=0 - label_offset,
    y=0 - label_offset,
    text="Sand",
    text_font_size=label_font_size,
    text_font_style="bold",
    text_align="center",
    text_baseline="top",
)
p.add_layout(sand_label)

# Silt (bottom-right vertex)
silt_label = Label(
    x=1 + label_offset,
    y=0 - label_offset,
    text="Silt",
    text_font_size=label_font_size,
    text_font_style="bold",
    text_align="center",
    text_baseline="top",
)
p.add_layout(silt_label)

# Clay (top vertex)
clay_label = Label(
    x=0.5,
    y=np.sqrt(3) / 2 + label_offset,
    text="Clay",
    text_font_size=label_font_size,
    text_font_style="bold",
    text_align="center",
    text_baseline="bottom",
)
p.add_layout(clay_label)

# Plot data points
source = ColumnDataSource(data={"x": x_data, "y": y_data, "sand": sand, "silt": silt, "clay": clay})

p.scatter(x="x", y="y", source=source, size=20, color="#306998", alpha=0.7, line_color="#1a3d5c", line_width=2)

# Style title
p.title.text_font_size = "32pt"
p.title.align = "center"

# Remove outline
p.outline_line_color = None

# Save outputs
export_png(p, filename="plot.png")
output_file("plot.html", title="Ternary Basic - Bokeh")
save(p)
