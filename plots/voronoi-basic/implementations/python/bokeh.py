""" pyplots.ai
voronoi-basic: Voronoi Diagram for Spatial Partitioning
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-09
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from scipy.spatial import Voronoi


# Data - seed points for Voronoi diagram
np.random.seed(42)
n_points = 20
x = np.random.uniform(1, 9, n_points)
y = np.random.uniform(1, 9, n_points)
points = np.column_stack([x, y])

# Bounding box for clipping
x_min, x_max = 0, 10
y_min, y_max = 0, 10

# Add mirrored points outside boundaries to handle infinite regions properly
mirrored = []
for px, py in points:
    mirrored.append([2 * x_min - px, py])
    mirrored.append([2 * x_max - px, py])
    mirrored.append([px, 2 * y_min - py])
    mirrored.append([px, 2 * y_max - py])
all_points = np.vstack([points, mirrored])

# Compute Voronoi diagram with mirrored points
vor = Voronoi(all_points)

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="voronoi-basic · bokeh · pyplots.ai",
    x_axis_label="X Coordinate",
    y_axis_label="Y Coordinate",
    x_range=(x_min, x_max),
    y_range=(y_min, y_max),
)

# Color palette for regions
colors = [
    "#306998",
    "#FFD43B",
    "#4ECDC4",
    "#FF6B6B",
    "#95E1D3",
    "#F38181",
    "#AA96DA",
    "#FCBAD3",
    "#A8D8EA",
    "#FFEAA7",
    "#DFE6E9",
    "#74B9FF",
    "#81ECEC",
    "#FDCB6E",
    "#6C5CE7",
    "#A29BFE",
    "#00B894",
    "#00CEC9",
    "#E17055",
    "#D63031",
]


def clip_polygon_to_box(vertices, x_min, x_max, y_min, y_max):
    """Clip polygon to bounding box using Sutherland-Hodgman algorithm."""

    def inside(p, edge):
        if edge == "left":
            return p[0] >= x_min
        elif edge == "right":
            return p[0] <= x_max
        elif edge == "bottom":
            return p[1] >= y_min
        else:
            return p[1] <= y_max

    def intersect(p1, p2, edge):
        x1, y1 = p1
        x2, y2 = p2
        dx, dy = x2 - x1, y2 - y1
        if edge == "left":
            t = (x_min - x1) / dx if dx != 0 else 0
            return [x_min, y1 + t * dy]
        elif edge == "right":
            t = (x_max - x1) / dx if dx != 0 else 0
            return [x_max, y1 + t * dy]
        elif edge == "bottom":
            t = (y_min - y1) / dy if dy != 0 else 0
            return [x1 + t * dx, y_min]
        else:
            t = (y_max - y1) / dy if dy != 0 else 0
            return [x1 + t * dx, y_max]

    polygon = list(vertices)
    for edge in ["left", "right", "bottom", "top"]:
        if not polygon:
            return []
        clipped = []
        for i in range(len(polygon)):
            curr = polygon[i]
            next_v = polygon[(i + 1) % len(polygon)]
            if inside(curr, edge):
                clipped.append(curr)
                if not inside(next_v, edge):
                    clipped.append(intersect(curr, next_v, edge))
            elif inside(next_v, edge):
                clipped.append(intersect(curr, next_v, edge))
        polygon = clipped
    return polygon


# Draw Voronoi regions for original points only
for idx in range(n_points):
    region_idx = vor.point_region[idx]
    region = vor.regions[region_idx]

    if not region or -1 in region:
        continue

    vertices = [vor.vertices[i] for i in region]
    clipped = clip_polygon_to_box(vertices, x_min, x_max, y_min, y_max)

    if len(clipped) >= 3:
        xs = [v[0] for v in clipped]
        ys = [v[1] for v in clipped]
        p.patch(xs, ys, fill_color=colors[idx % len(colors)], fill_alpha=0.5, line_color="#2D3436", line_width=2.5)

# Draw seed points prominently
source = ColumnDataSource(data={"x": x, "y": y})
p.scatter("x", "y", source=source, size=22, color="#306998", line_color="white", line_width=4, alpha=0.95)

# Styling
p.title.text_font_size = "28pt"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.grid.grid_line_alpha = 0.3
p.grid.grid_line_dash = "dashed"
p.outline_line_color = "#2D3436"
p.outline_line_width = 2

# Save outputs
export_png(p, filename="plot.png")
