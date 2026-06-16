""" anyplot.ai
voronoi-basic: Voronoi Diagram for Spatial Partitioning
Library: pygal 3.1.0 | Python 3.13.13
Quality: 73/100 | Updated: 2026-05-17
"""

import os
import xml.etree.ElementTree as ET

import cairosvg
import numpy as np
from scipy.spatial import Voronoi


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477")

np.random.seed(42)
points = np.random.uniform(0.5, 10.5, size=(25, 2))

vor = Voronoi(points)

WIDTH = 4800
HEIGHT = 2700
margin_left = 400
margin_right = 200
margin_top = 300
margin_bottom = 250

plot_width = WIDTH - margin_left - margin_right
plot_height = HEIGHT - margin_top - margin_bottom

x_min, x_max = 0.5, 10.5
y_min, y_max = 0.5, 10.5


def data_to_svg(x, y):
    svg_x = margin_left + (x - x_min) / (x_max - x_min) * plot_width
    svg_y = margin_top + (y_max - y) / (y_max - y_min) * plot_height
    return svg_x, svg_y


def voronoi_finite_polygons_2d(vor, radius=None):
    if vor.points.shape[1] != 2:
        raise ValueError("Requires 2D input")

    new_regions = []
    new_vertices = vor.vertices.tolist()

    center = vor.points.mean(axis=0)
    if radius is None:
        radius = vor.points.ptp().max() * 2

    all_ridges = {}
    for (p1, p2), (v1, v2) in zip(vor.ridge_points, vor.ridge_vertices, strict=True):
        all_ridges.setdefault(p1, []).append((p2, v1, v2))
        all_ridges.setdefault(p2, []).append((p1, v1, v2))

    for p1, region in enumerate(vor.point_region):
        vertices = vor.regions[region]

        if all(v >= 0 for v in vertices):
            new_regions.append(vertices)
            continue

        ridges = all_ridges[p1]
        new_region = [v for v in vertices if v >= 0]

        for p2, v1, v2 in ridges:
            if v2 < 0:
                v1, v2 = v2, v1
            if v1 >= 0:
                continue

            t = vor.points[p2] - vor.points[p1]
            t /= np.linalg.norm(t)
            n = np.array([-t[1], t[0]])

            midpoint = vor.points[[p1, p2]].mean(axis=0)
            direction = np.sign(np.dot(midpoint - center, n)) * n
            far_point = vor.vertices[v2] + direction * radius

            new_region.append(len(new_vertices))
            new_vertices.append(far_point.tolist())

        vs = np.asarray([new_vertices[v] for v in new_region])
        c = vs.mean(axis=0)
        angles = np.arctan2(vs[:, 1] - c[1], vs[:, 0] - c[0])
        new_region = np.array(new_region)[np.argsort(angles)].tolist()

        new_regions.append(new_region)

    return new_regions, np.asarray(new_vertices)


def clip_polygon_to_box(vertices, x_min, x_max, y_min, y_max):
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
        else:
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


regions, vertices = voronoi_finite_polygons_2d(vor, radius=20)

svg_ns = "http://www.w3.org/2000/svg"
ET.register_namespace("", svg_ns)

svg_root = ET.Element("svg", xmlns=svg_ns, width=str(WIDTH), height=str(HEIGHT), viewBox=f"0 0 {WIDTH} {HEIGHT}")
svg_root.set("style", f"background-color: {PAGE_BG};")

title_elem = ET.SubElement(svg_root, "text")
title_elem.set("x", str(WIDTH / 2))
title_elem.set("y", "150")
title_elem.set("text-anchor", "middle")
title_elem.set("fill", INK)
title_elem.set("font-size", "28")
title_elem.set("font-family", "sans-serif")
title_elem.set("font-weight", "500")
title_elem.text = "voronoi-basic · pygal · anyplot.ai"

x_label = ET.SubElement(svg_root, "text")
x_label.set("x", str(margin_left + plot_width / 2))
x_label.set("y", str(HEIGHT - 80))
x_label.set("text-anchor", "middle")
x_label.set("fill", INK)
x_label.set("font-size", "22")
x_label.set("font-family", "sans-serif")
x_label.text = "X Coordinate (units)"

y_label = ET.SubElement(svg_root, "text")
y_label.set("x", "110")
y_label.set("y", str(margin_top + plot_height / 2))
y_label.set("text-anchor", "middle")
y_label.set("fill", INK)
y_label.set("font-size", "22")
y_label.set("font-family", "sans-serif")
y_label.set("transform", f"rotate(-90, 110, {margin_top + plot_height / 2})")
y_label.text = "Y Coordinate (units)"

plot_bg = ET.SubElement(svg_root, "rect")
plot_bg.set("x", str(margin_left))
plot_bg.set("y", str(margin_top))
plot_bg.set("width", str(plot_width))
plot_bg.set("height", str(plot_height))
plot_bg.set("fill", PAGE_BG)
plot_bg.set("stroke", INK_SOFT)
plot_bg.set("stroke-width", "2")

defs = ET.SubElement(svg_root, "defs")
clip_path = ET.SubElement(defs, "clipPath", id="plot-area")
clip_rect = ET.SubElement(clip_path, "rect")
clip_rect.set("x", str(margin_left))
clip_rect.set("y", str(margin_top))
clip_rect.set("width", str(plot_width))
clip_rect.set("height", str(plot_height))

grid_g = ET.SubElement(svg_root, "g")
grid_g.set("class", "grid")

grid_color = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

for x_val in np.arange(1, 11, 1):
    sx, _ = data_to_svg(x_val, 0)
    _, sy_top = data_to_svg(0, y_max)
    _, sy_bot = data_to_svg(0, y_min)
    line = ET.SubElement(grid_g, "line")
    line.set("x1", f"{sx:.1f}")
    line.set("y1", f"{sy_top:.1f}")
    line.set("x2", f"{sx:.1f}")
    line.set("y2", f"{sy_bot:.1f}")
    line.set("stroke", INK_SOFT)
    line.set("stroke-width", "1")
    line.set("opacity", "0.15")

for y_val in np.arange(1, 11, 1):
    _, sy = data_to_svg(0, y_val)
    sx_left, _ = data_to_svg(x_min, 0)
    sx_right, _ = data_to_svg(x_max, 0)
    line = ET.SubElement(grid_g, "line")
    line.set("x1", f"{sx_left:.1f}")
    line.set("y1", f"{sy:.1f}")
    line.set("x2", f"{sx_right:.1f}")
    line.set("y2", f"{sy:.1f}")
    line.set("stroke", INK_SOFT)
    line.set("stroke-width", "1")
    line.set("opacity", "0.15")

for x_val in range(1, 11, 2):
    sx, _ = data_to_svg(x_val, 0)
    tick_label = ET.SubElement(svg_root, "text")
    tick_label.set("x", f"{sx:.1f}")
    tick_label.set("y", str(margin_top + plot_height + 60))
    tick_label.set("text-anchor", "middle")
    tick_label.set("fill", INK_SOFT)
    tick_label.set("font-size", "18")
    tick_label.set("font-family", "sans-serif")
    tick_label.text = str(x_val)

for y_val in range(1, 11, 2):
    _, sy = data_to_svg(0, y_val)
    tick_label = ET.SubElement(svg_root, "text")
    tick_label.set("x", str(margin_left - 40))
    tick_label.set("y", f"{sy + 8:.1f}")
    tick_label.set("text-anchor", "end")
    tick_label.set("fill", INK_SOFT)
    tick_label.set("font-size", "18")
    tick_label.set("font-family", "sans-serif")
    tick_label.text = str(y_val)

cells_g = ET.SubElement(svg_root, "g")
cells_g.set("class", "voronoi-cells")
cells_g.set("clip-path", "url(#plot-area)")

for i, region in enumerate(regions):
    if not region or len(region) < 3:
        continue

    poly_verts = [vertices[v] for v in region]
    clipped = clip_polygon_to_box(poly_verts, x_min, x_max, y_min, y_max)

    if len(clipped) < 3:
        continue

    svg_points = [data_to_svg(x, y) for x, y in clipped]
    points_str = " ".join([f"{x:.1f},{y:.1f}" for x, y in svg_points])

    polygon = ET.SubElement(cells_g, "polygon")
    polygon.set("points", points_str)
    color = IMPRINT[i % len(IMPRINT)]
    polygon.set("fill", color)
    polygon.set("fill-opacity", "0.6")
    polygon.set("stroke", INK_SOFT)
    polygon.set("stroke-width", "2")

    title = ET.SubElement(polygon, "title")
    title.text = f"Region {i + 1}: ({vor.points[i][0]:.2f}, {vor.points[i][1]:.2f})"

points_g = ET.SubElement(svg_root, "g")
points_g.set("class", "seed-points")

for i, (px, py) in enumerate(vor.points):
    sx, sy = data_to_svg(px, py)

    outer = ET.SubElement(points_g, "circle")
    outer.set("cx", f"{sx:.1f}")
    outer.set("cy", f"{sy:.1f}")
    outer.set("r", "16")
    outer.set("fill", PAGE_BG)
    outer.set("stroke", INK_SOFT)
    outer.set("stroke-width", "2")

    inner = ET.SubElement(points_g, "circle")
    inner.set("cx", f"{sx:.1f}")
    inner.set("cy", f"{sy:.1f}")
    inner.set("r", "12")
    color = IMPRINT[i % len(IMPRINT)]
    inner.set("fill", color)

    title = ET.SubElement(inner, "title")
    title.text = f"Point {i + 1}: ({px:.2f}, {py:.2f})"

svg_output = ET.tostring(svg_root, encoding="unicode")
with open(f"plot-{THEME}.html", "w") as f:
    f.write(svg_output)

cairosvg.svg2png(bytestring=svg_output.encode("utf-8"), write_to=f"plot-{THEME}.png")
