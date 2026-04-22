""" pyplots.ai
maze-circular: Circular Maze Puzzle
Library: pygal 3.1.0 | Python 3.13.11
Quality: 52/100 | Created: 2026-01-16
"""

import numpy as np
import pygal
from pygal.style import Style


# Set seed for reproducibility
np.random.seed(42)

# Maze parameters
num_rings = 6
num_sectors = 12

# Calculate radii
inner_radius = 0.15
outer_radius = 0.85
radii = np.linspace(inner_radius, outer_radius, num_rings + 1)[1:]

# Build cells: each cell is (ring, sector)
all_cells = [(r, s) for r in range(num_rings) for s in range(num_sectors)]

# Build edges between adjacent cells
edges = []
for ring in range(num_rings):
    for sector in range(num_sectors):
        next_s = (sector + 1) % num_sectors
        edges.append(frozenset([(ring, sector), (ring, next_s)]))
        if ring < num_rings - 1:
            edges.append(frozenset([(ring, sector), (ring + 1, sector)]))

edges = list(set(edges))

# Kruskal's algorithm for maze generation
parent = {cell: cell for cell in all_cells}


def find(c):
    while parent[c] != c:
        parent[c] = parent[parent[c]]
        c = parent[c]
    return c


def union(a, b):
    ra, rb = find(a), find(b)
    if ra != rb:
        parent[ra] = rb
        return True
    return False


np.random.shuffle(edges)
passages = set()
for edge in edges:
    cells = list(edge)
    if union(cells[0], cells[1]):
        passages.add(edge)

# Entry at sector 0
entry_sector = 0

# Colors
wall_color = "#222222"
entry_color = "#1565C0"
goal_color = "#D32F2F"

custom_style = Style(
    background="#FFFFFF",
    plot_background="#FFFFFF",
    foreground="#333333",
    foreground_strong="#000000",
    foreground_subtle="#666666",
    colors=(wall_color,),
    title_font_size=84,
    stroke_width=6,
)

chart = pygal.XY(
    width=3600,
    height=3600,
    style=custom_style,
    title="maze-circular · pygal · pyplots.ai",
    show_legend=False,
    show_dots=False,
    stroke=True,
    show_x_guides=False,
    show_y_guides=False,
    show_x_labels=False,
    show_y_labels=False,
    xrange=(-1.1, 1.1),
    range=(-1.1, 1.1),
    explicit_size=True,
    fill=False,
    margin=80,
)


def arc_pts(radius, a1, a2, n=30):
    """Generate arc points."""
    angles = np.linspace(a1, a2, n)
    return [(radius * np.cos(a), radius * np.sin(a)) for a in angles]


# Entry angles
entry_a1 = 2 * np.pi * entry_sector / num_sectors
entry_a2 = 2 * np.pi * (entry_sector + 1) / num_sectors

# Wall stroke config
wall_stroke = {"width": 7, "linecap": "round", "linejoin": "round"}

# 1. Outer boundary (with entry gap) - draw as single continuous arc
outer_arc = arc_pts(radii[-1], entry_a2, entry_a1 + 2 * np.pi, 80)
chart.add("", outer_arc, stroke_style=wall_stroke)

# 2. Inner circle (goal area boundary) - complete circle
inner_arc = arc_pts(inner_radius, 0, 2 * np.pi + 0.01, 60)
chart.add("", inner_arc, stroke_style=wall_stroke)

# 3. Ring walls - combine consecutive wall segments into continuous arcs
for ring in range(num_rings - 1):
    r = radii[ring]
    # Find continuous wall segments
    wall_sectors = []
    for sector in range(num_sectors):
        if frozenset([(ring, sector), (ring + 1, sector)]) not in passages:
            wall_sectors.append(sector)

    # Group consecutive sectors into continuous arcs
    if wall_sectors:
        groups = []
        current_group = [wall_sectors[0]]
        for i in range(1, len(wall_sectors)):
            if wall_sectors[i] == wall_sectors[i - 1] + 1:
                current_group.append(wall_sectors[i])
            else:
                groups.append(current_group)
                current_group = [wall_sectors[i]]
        groups.append(current_group)

        # Check if first and last groups wrap around
        if len(groups) > 1 and groups[0][0] == 0 and groups[-1][-1] == num_sectors - 1:
            groups[-1].extend(groups[0])
            groups = groups[1:]

        # Draw each continuous arc
        for group in groups:
            start_sector = group[0]
            end_sector = group[-1]
            a1 = 2 * np.pi * start_sector / num_sectors
            a2 = 2 * np.pi * (end_sector + 1) / num_sectors
            pts_per_sector = 8
            arc_points = arc_pts(r, a1, a2, len(group) * pts_per_sector + 1)
            chart.add("", arc_points, stroke_style=wall_stroke)

# 4. Radial walls - draw as single line segments
radial_walls = []
for ring in range(num_rings):
    r_in = radii[ring - 1] if ring > 0 else inner_radius
    r_out = radii[ring]
    for sector in range(num_sectors):
        prev_s = (sector - 1) % num_sectors
        if frozenset([(ring, sector), (ring, prev_s)]) not in passages:
            angle = 2 * np.pi * sector / num_sectors
            x1, y1 = r_in * np.cos(angle), r_in * np.sin(angle)
            x2, y2 = r_out * np.cos(angle), r_out * np.sin(angle)
            radial_walls.append((angle, r_in, r_out))

# Group consecutive radial walls at same angle into longer lines
angle_groups = {}
for angle, r_in, r_out in radial_walls:
    key = round(angle, 6)
    if key not in angle_groups:
        angle_groups[key] = []
    angle_groups[key].append((r_in, r_out))

for angle_key, segments in angle_groups.items():
    # Sort by inner radius
    segments.sort(key=lambda x: x[0])
    # Merge overlapping or adjacent segments
    merged = []
    for r_in, r_out in segments:
        if merged and abs(merged[-1][1] - r_in) < 0.01:
            merged[-1] = (merged[-1][0], r_out)
        else:
            merged.append((r_in, r_out))

    # Draw merged segments
    for r_in, r_out in merged:
        angle = float(angle_key)
        x1, y1 = r_in * np.cos(angle), r_in * np.sin(angle)
        x2, y2 = r_out * np.cos(angle), r_out * np.sin(angle)
        chart.add("", [(x1, y1), (x2, y2)], stroke_style=wall_stroke)

# Entry arrow - blue, prominent
mid_angle = (entry_a1 + entry_a2) / 2
arrow_start = radii[-1] + 0.18
arrow_end = radii[-1] + 0.03
tip_x = arrow_end * np.cos(mid_angle)
tip_y = arrow_end * np.sin(mid_angle)
base_x = arrow_start * np.cos(mid_angle)
base_y = arrow_start * np.sin(mid_angle)

arrow_stroke = {"width": 10, "linecap": "round", "linejoin": "round"}
chart.add("", [(base_x, base_y), (tip_x, tip_y)], stroke_style={**arrow_stroke, "color": entry_color})

# Arrow head
wing_len = 0.07
wing_angle = 0.5
wing1_x = tip_x + wing_len * np.cos(mid_angle + np.pi - wing_angle)
wing1_y = tip_y + wing_len * np.sin(mid_angle + np.pi - wing_angle)
wing2_x = tip_x + wing_len * np.cos(mid_angle + np.pi + wing_angle)
wing2_y = tip_y + wing_len * np.sin(mid_angle + np.pi + wing_angle)
chart.add(
    "", [(wing1_x, wing1_y), (tip_x, tip_y), (wing2_x, wing2_y)], stroke_style={**arrow_stroke, "color": entry_color}
)

# Goal star - red, at center (filled polygon via closed path)
star_outer = 0.09
star_inner = 0.035
star_pts = []
for i in range(10):
    a = i * np.pi / 5 - np.pi / 2
    r = star_outer if i % 2 == 0 else star_inner
    star_pts.append((r * np.cos(a), r * np.sin(a)))
star_pts.append(star_pts[0])  # Close the star
chart.add("", star_pts, stroke_style={"width": 6, "color": goal_color})

# Render PNG output only
chart.render_to_png("plot.png")
