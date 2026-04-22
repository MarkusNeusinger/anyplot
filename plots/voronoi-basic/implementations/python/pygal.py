""" pyplots.ai
voronoi-basic: Voronoi Diagram for Spatial Partitioning
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-09
"""

import xml.etree.ElementTree as ET

import cairosvg
import numpy as np
import pygal
from pygal.style import Style
from scipy.spatial import Voronoi


# Data: Generate seed points representing facility locations
np.random.seed(42)

# Create clustered distribution simulating facility placement
# Cluster 1: Urban center
x1 = np.random.randn(7) * 1.2 + 3.5
y1 = np.random.randn(7) * 1.2 + 3.5

# Cluster 2: Industrial zone
x2 = np.random.randn(6) * 1.0 + 7.5
y2 = np.random.randn(6) * 1.0 + 3.5

# Cluster 3: Suburban area
x3 = np.random.randn(7) * 1.3 + 5.5
y3 = np.random.randn(7) * 1.3 + 7.5

# Combine all points
points_x = np.concatenate([x1, x2, x3])
points_y = np.concatenate([y1, y2, y3])
points = np.column_stack([points_x, points_y])

# Clip to bounding region
x_min, x_max = 0.5, 10.5
y_min, y_max = 0.5, 10.5
points[:, 0] = np.clip(points[:, 0], x_min + 0.5, x_max - 0.5)
points[:, 1] = np.clip(points[:, 1], y_min + 0.5, y_max - 0.5)

# Compute Voronoi diagram
vor = Voronoi(points)

# Chart dimensions
WIDTH = 4800
HEIGHT = 2700

# Plotting area within chart (leaving margins for title and labels)
margin_left = 350
margin_right = 150
margin_top = 200
margin_bottom = 200

plot_width = WIDTH - margin_left - margin_right
plot_height = HEIGHT - margin_top - margin_bottom


def data_to_svg(x, y):
    """Convert data coordinates to SVG coordinates."""
    svg_x = margin_left + (x - x_min) / (x_max - x_min) * plot_width
    svg_y = margin_top + (y_max - y) / (y_max - y_min) * plot_height
    return svg_x, svg_y


def voronoi_finite_polygons_2d(vor, radius=None):
    """
    Reconstruct infinite Voronoi regions in a 2D diagram to finite regions.
    Adapted from scipy documentation.
    """
    if vor.points.shape[1] != 2:
        raise ValueError("Requires 2D input")

    new_regions = []
    new_vertices = vor.vertices.tolist()

    center = vor.points.mean(axis=0)
    if radius is None:
        radius = vor.points.ptp().max() * 2

    # Construct a map containing all ridges for a given point
    all_ridges = {}
    for (p1, p2), (v1, v2) in zip(vor.ridge_points, vor.ridge_vertices, strict=True):
        all_ridges.setdefault(p1, []).append((p2, v1, v2))
        all_ridges.setdefault(p2, []).append((p1, v1, v2))

    # Reconstruct infinite regions
    for p1, region in enumerate(vor.point_region):
        vertices = vor.regions[region]

        if all(v >= 0 for v in vertices):
            # Finite region
            new_regions.append(vertices)
            continue

        # Reconstruct a non-finite region
        ridges = all_ridges[p1]
        new_region = [v for v in vertices if v >= 0]

        for p2, v1, v2 in ridges:
            if v2 < 0:
                v1, v2 = v2, v1
            if v1 >= 0:
                # Finite ridge
                continue

            # Compute the missing endpoint of an infinite ridge
            t = vor.points[p2] - vor.points[p1]  # tangent
            t /= np.linalg.norm(t)
            n = np.array([-t[1], t[0]])  # normal

            midpoint = vor.points[[p1, p2]].mean(axis=0)
            direction = np.sign(np.dot(midpoint - center, n)) * n
            far_point = vor.vertices[v2] + direction * radius

            new_region.append(len(new_vertices))
            new_vertices.append(far_point.tolist())

        # Sort region counterclockwise
        vs = np.asarray([new_vertices[v] for v in new_region])
        c = vs.mean(axis=0)
        angles = np.arctan2(vs[:, 1] - c[1], vs[:, 0] - c[0])
        new_region = np.array(new_region)[np.argsort(angles)].tolist()

        new_regions.append(new_region)

    return new_regions, np.asarray(new_vertices)


def clip_polygon_to_box(vertices, x_min, x_max, y_min, y_max):
    """Clip polygon vertices to bounding box using Sutherland-Hodgman algorithm."""

    def inside_edge(p, edge):
        x, y = p
        if edge == "left":
            return x >= x_min
        if edge == "right":
            return x <= x_max
        if edge == "bottom":
            return y >= y_min
        if edge == "top":
            return y <= y_max

    def intersect(p1, p2, edge):
        x1, y1 = p1
        x2, y2 = p2
        dx = x2 - x1
        dy = y2 - y1

        if edge == "left":
            t = (x_min - x1) / (dx + 1e-12)
        elif edge == "right":
            t = (x_max - x1) / (dx + 1e-12)
        elif edge == "bottom":
            t = (y_min - y1) / (dy + 1e-12)
        else:  # top
            t = (y_max - y1) / (dy + 1e-12)

        return (x1 + t * dx, y1 + t * dy)

    output = list(vertices)

    for edge in ["left", "right", "bottom", "top"]:
        if len(output) == 0:
            break
        input_list = output
        output = []

        for i in range(len(input_list)):
            current = input_list[i]
            prev = input_list[i - 1]

            if inside_edge(current, edge):
                if not inside_edge(prev, edge):
                    output.append(intersect(prev, current, edge))
                output.append(current)
            elif inside_edge(prev, edge):
                output.append(intersect(prev, current, edge))

    return output


# Get finite polygons from Voronoi diagram
regions, vertices = voronoi_finite_polygons_2d(vor, radius=20)

# Color palette (colorblind-safe, distinguishable)
colors = [
    "#306998",  # Python Blue
    "#FFD43B",  # Python Yellow
    "#5DA5DA",  # Blue
    "#FAA43A",  # Orange
    "#60BD68",  # Green
    "#B276B2",  # Purple
    "#F15854",  # Red
    "#4D4D4D",  # Gray
    "#DECF3F",  # Yellow-green
    "#F17CB0",  # Pink
    "#B2912F",  # Brown
    "#8DD3C7",  # Teal
    "#BEBADA",  # Lavender
    "#FB8072",  # Salmon
    "#80B1D3",  # Light blue
    "#FDB462",  # Light orange
    "#FCCDE5",  # Light pink
    "#D9D9D9",  # Light gray
    "#BC80BD",  # Light purple
    "#CCEBC5",  # Light green
]

# Custom style using pygal
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#222222",
    foreground_subtle="#666666",
    colors=tuple(colors),
    title_font_size=72,
    label_font_size=48,
    legend_font_size=36,
    major_label_font_size=40,
    value_font_size=36,
    font_family="sans-serif",
)

# Use pygal config for consistent settings
config = pygal.Config()
config.width = WIDTH
config.height = HEIGHT
config.style = custom_style

# Build SVG
svg_ns = "http://www.w3.org/2000/svg"
ET.register_namespace("", svg_ns)

svg_root = ET.Element("svg", xmlns=svg_ns, width=str(WIDTH), height=str(HEIGHT), viewBox=f"0 0 {WIDTH} {HEIGHT}")
svg_root.set("style", f"background-color: {custom_style.background};")

# Add title
title_elem = ET.SubElement(svg_root, "text")
title_elem.set("x", str(WIDTH / 2))
title_elem.set("y", "100")
title_elem.set("text-anchor", "middle")
title_elem.set("fill", custom_style.foreground_strong)
title_elem.set("font-size", str(custom_style.title_font_size))
title_elem.set("font-family", custom_style.font_family)
title_elem.set("font-weight", "bold")
title_elem.text = "voronoi-basic \u00b7 pygal \u00b7 pyplots.ai"

# Add axis labels
x_label = ET.SubElement(svg_root, "text")
x_label.set("x", str(margin_left + plot_width / 2))
x_label.set("y", str(HEIGHT - 60))
x_label.set("text-anchor", "middle")
x_label.set("fill", custom_style.foreground_strong)
x_label.set("font-size", str(custom_style.label_font_size))
x_label.set("font-family", custom_style.font_family)
x_label.text = "X Coordinate (km)"

y_label = ET.SubElement(svg_root, "text")
y_label.set("x", "80")
y_label.set("y", str(margin_top + plot_height / 2))
y_label.set("text-anchor", "middle")
y_label.set("fill", custom_style.foreground_strong)
y_label.set("font-size", str(custom_style.label_font_size))
y_label.set("font-family", custom_style.font_family)
y_label.set("transform", f"rotate(-90, 80, {margin_top + plot_height / 2})")
y_label.text = "Y Coordinate (km)"

# Create plot background
plot_bg = ET.SubElement(svg_root, "rect")
plot_bg.set("x", str(margin_left))
plot_bg.set("y", str(margin_top))
plot_bg.set("width", str(plot_width))
plot_bg.set("height", str(plot_height))
plot_bg.set("fill", "#fafafa")
plot_bg.set("stroke", "#cccccc")
plot_bg.set("stroke-width", "2")

# Create clipping path for plot area
defs = ET.SubElement(svg_root, "defs")
clip_path = ET.SubElement(defs, "clipPath", id="plot-area")
clip_rect = ET.SubElement(clip_path, "rect")
clip_rect.set("x", str(margin_left))
clip_rect.set("y", str(margin_top))
clip_rect.set("width", str(plot_width))
clip_rect.set("height", str(plot_height))

# Add grid lines (inside clip region)
grid_g = ET.SubElement(svg_root, "g")
grid_g.set("class", "grid")

# X grid lines
for x_val in range(1, 11, 1):
    sx, _ = data_to_svg(x_val, 0)
    _, sy_top = data_to_svg(0, y_max)
    _, sy_bot = data_to_svg(0, y_min)
    line = ET.SubElement(grid_g, "line")
    line.set("x1", f"{sx:.1f}")
    line.set("y1", f"{sy_top:.1f}")
    line.set("x2", f"{sx:.1f}")
    line.set("y2", f"{sy_bot:.1f}")
    line.set("stroke", "#dddddd")
    line.set("stroke-width", "2")
    line.set("stroke-dasharray", "8,8")

# Y grid lines
for y_val in range(1, 11, 1):
    _, sy = data_to_svg(0, y_val)
    sx_left, _ = data_to_svg(x_min, 0)
    sx_right, _ = data_to_svg(x_max, 0)
    line = ET.SubElement(grid_g, "line")
    line.set("x1", f"{sx_left:.1f}")
    line.set("y1", f"{sy:.1f}")
    line.set("x2", f"{sx_right:.1f}")
    line.set("y2", f"{sy:.1f}")
    line.set("stroke", "#dddddd")
    line.set("stroke-width", "2")
    line.set("stroke-dasharray", "8,8")

# X tick labels
for x_val in range(1, 11, 2):
    sx, _ = data_to_svg(x_val, 0)
    tick_label = ET.SubElement(svg_root, "text")
    tick_label.set("x", f"{sx:.1f}")
    tick_label.set("y", str(margin_top + plot_height + 50))
    tick_label.set("text-anchor", "middle")
    tick_label.set("fill", custom_style.foreground)
    tick_label.set("font-size", str(custom_style.major_label_font_size))
    tick_label.set("font-family", custom_style.font_family)
    tick_label.text = str(x_val)

# Y tick labels
for y_val in range(1, 11, 2):
    _, sy = data_to_svg(0, y_val)
    tick_label = ET.SubElement(svg_root, "text")
    tick_label.set("x", str(margin_left - 20))
    tick_label.set("y", f"{sy + 12:.1f}")
    tick_label.set("text-anchor", "end")
    tick_label.set("fill", custom_style.foreground)
    tick_label.set("font-size", str(custom_style.major_label_font_size))
    tick_label.set("font-family", custom_style.font_family)
    tick_label.text = str(y_val)

# Group for Voronoi cells
cells_g = ET.SubElement(svg_root, "g")
cells_g.set("class", "voronoi-cells")
cells_g.set("clip-path", "url(#plot-area)")

# Draw Voronoi cells
for i, region in enumerate(regions):
    if not region or len(region) < 3:
        continue

    # Get polygon vertices
    poly_verts = [vertices[v] for v in region]

    # Clip to bounding box
    clipped = clip_polygon_to_box(poly_verts, x_min, x_max, y_min, y_max)

    if len(clipped) < 3:
        continue

    # Convert to SVG coordinates
    svg_points = [data_to_svg(x, y) for x, y in clipped]
    points_str = " ".join([f"{x:.1f},{y:.1f}" for x, y in svg_points])

    polygon = ET.SubElement(cells_g, "polygon")
    polygon.set("points", points_str)
    polygon.set("fill", colors[i % len(colors)])
    polygon.set("fill-opacity", "0.6")
    polygon.set("stroke", "#333333")
    polygon.set("stroke-width", "3")

    # Tooltip
    title = ET.SubElement(polygon, "title")
    title.text = f"Region {i + 1}: Center ({vor.points[i][0]:.1f}, {vor.points[i][1]:.1f})"

# Draw seed points on top
points_g = ET.SubElement(svg_root, "g")
points_g.set("class", "seed-points")

for i, (px, py) in enumerate(vor.points):
    sx, sy = data_to_svg(px, py)
    # Outer circle (white border)
    outer = ET.SubElement(points_g, "circle")
    outer.set("cx", f"{sx:.1f}")
    outer.set("cy", f"{sy:.1f}")
    outer.set("r", "18")
    outer.set("fill", "white")
    outer.set("stroke", "#333333")
    outer.set("stroke-width", "3")

    # Inner circle (colored)
    inner = ET.SubElement(points_g, "circle")
    inner.set("cx", f"{sx:.1f}")
    inner.set("cy", f"{sy:.1f}")
    inner.set("r", "12")
    inner.set("fill", colors[i % len(colors)])
    inner.set("stroke", "#333333")
    inner.set("stroke-width", "2")

    # Tooltip
    title = ET.SubElement(inner, "title")
    title.text = f"Point {i + 1}: ({px:.1f}, {py:.1f})"

# Add legend
legend_g = ET.SubElement(svg_root, "g")
legend_g.set("class", "legend")
legend_x = WIDTH - 400
legend_y = margin_top + 50

legend_bg = ET.SubElement(legend_g, "rect")
legend_bg.set("x", str(legend_x - 20))
legend_bg.set("y", str(legend_y - 30))
legend_bg.set("width", "280")
legend_bg.set("height", "200")
legend_bg.set("fill", "white")
legend_bg.set("fill-opacity", "0.9")
legend_bg.set("stroke", "#cccccc")
legend_bg.set("stroke-width", "2")
legend_bg.set("rx", "10")

legend_title = ET.SubElement(legend_g, "text")
legend_title.set("x", str(legend_x))
legend_title.set("y", str(legend_y))
legend_title.set("fill", custom_style.foreground_strong)
legend_title.set("font-size", "36")
legend_title.set("font-family", custom_style.font_family)
legend_title.set("font-weight", "bold")
legend_title.text = "Legend"

# Cell symbol
cell_sym = ET.SubElement(legend_g, "rect")
cell_sym.set("x", str(legend_x))
cell_sym.set("y", str(legend_y + 30))
cell_sym.set("width", "40")
cell_sym.set("height", "30")
cell_sym.set("fill", colors[0])
cell_sym.set("fill-opacity", "0.6")
cell_sym.set("stroke", "#333333")
cell_sym.set("stroke-width", "2")

cell_label = ET.SubElement(legend_g, "text")
cell_label.set("x", str(legend_x + 55))
cell_label.set("y", str(legend_y + 52))
cell_label.set("fill", custom_style.foreground)
cell_label.set("font-size", "32")
cell_label.set("font-family", custom_style.font_family)
cell_label.text = "Voronoi Cell"

# Point symbol
point_outer = ET.SubElement(legend_g, "circle")
point_outer.set("cx", str(legend_x + 20))
point_outer.set("cy", str(legend_y + 100))
point_outer.set("r", "14")
point_outer.set("fill", "white")
point_outer.set("stroke", "#333333")
point_outer.set("stroke-width", "2")

point_inner = ET.SubElement(legend_g, "circle")
point_inner.set("cx", str(legend_x + 20))
point_inner.set("cy", str(legend_y + 100))
point_inner.set("r", "9")
point_inner.set("fill", colors[0])
point_inner.set("stroke", "#333333")
point_inner.set("stroke-width", "1")

point_label = ET.SubElement(legend_g, "text")
point_label.set("x", str(legend_x + 55))
point_label.set("y", str(legend_y + 108))
point_label.set("fill", custom_style.foreground)
point_label.set("font-size", "32")
point_label.set("font-family", custom_style.font_family)
point_label.text = "Seed Point"

# Count label
count_label = ET.SubElement(legend_g, "text")
count_label.set("x", str(legend_x))
count_label.set("y", str(legend_y + 150))
count_label.set("fill", custom_style.foreground_subtle)
count_label.set("font-size", "28")
count_label.set("font-family", custom_style.font_family)
count_label.text = f"n = {len(vor.points)} points"

# Write SVG to file (interactive output)
svg_output = ET.tostring(svg_root, encoding="unicode")
with open("plot.html", "w") as f:
    f.write(svg_output)

# Render to PNG via cairosvg
cairosvg.svg2png(bytestring=svg_output.encode("utf-8"), write_to="plot.png")
