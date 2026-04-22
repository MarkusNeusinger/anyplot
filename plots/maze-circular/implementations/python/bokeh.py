""" pyplots.ai
maze-circular: Circular Maze Puzzle
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-16
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import Label
from bokeh.plotting import figure


# Parameters
np.random.seed(42)
rings = 7
sectors_per_ring = [8, 12, 16, 20, 24, 28, 32]  # Increasing sectors for outer rings
wall_color = "#1a1a1a"
background_color = "#ffffff"
wall_width = 4
entry_color = "#306998"
goal_color = "#FFD43B"

# Build maze structure using recursive backtracking
# Each cell is (ring, sector), walls track connections between cells
cells = {}
for r in range(rings):
    n_sectors = sectors_per_ring[r]
    for s in range(n_sectors):
        cells[(r, s)] = {"visited": False, "walls": {"inner": True, "outer": True, "cw": True, "ccw": True}}


# Get neighbors for a cell
def get_neighbors(ring, sector):
    neighbors = []
    n_sectors = sectors_per_ring[ring]

    # Same ring neighbors (clockwise and counter-clockwise)
    ccw_sector = (sector - 1) % n_sectors
    cw_sector = (sector + 1) % n_sectors
    neighbors.append(((ring, ccw_sector), "ccw", "cw"))
    neighbors.append(((ring, cw_sector), "cw", "ccw"))

    # Inner ring neighbor
    if ring > 0:
        inner_sectors = sectors_per_ring[ring - 1]
        inner_sector = int(sector * inner_sectors / n_sectors)
        neighbors.append(((ring - 1, inner_sector), "inner", "outer"))

    # Outer ring neighbor
    if ring < rings - 1:
        outer_sectors = sectors_per_ring[ring + 1]
        ratio = outer_sectors / n_sectors
        outer_sector = int(sector * ratio)
        neighbors.append(((ring + 1, outer_sector), "outer", "inner"))

    return neighbors


# Recursive backtracking maze generation
stack = [(0, 0)]  # Start from center
cells[(0, 0)]["visited"] = True

while stack:
    current = stack[-1]
    ring, sector = current

    # Get unvisited neighbors
    neighbors = get_neighbors(ring, sector)
    unvisited = [(n, wall, opp_wall) for n, wall, opp_wall in neighbors if n in cells and not cells[n]["visited"]]

    if unvisited:
        # Choose random neighbor
        next_cell, wall_to_remove, opp_wall = unvisited[np.random.randint(len(unvisited))]

        # Remove walls between current and next
        cells[current]["walls"][wall_to_remove] = False
        cells[next_cell]["walls"][opp_wall] = False

        # Mark visited and add to stack
        cells[next_cell]["visited"] = True
        stack.append(next_cell)
    else:
        stack.pop()

# Create entry point on outer ring
outer_ring = rings - 1
entry_sector = 0
cells[(outer_ring, entry_sector)]["walls"]["outer"] = False

# Create figure (square for circular maze)
p = figure(
    width=3600,
    height=3600,
    title="maze-circular · bokeh · pyplots.ai",
    x_range=(-1.2, 1.2),
    y_range=(-1.2, 1.2),
    background_fill_color=background_color,
    toolbar_location=None,
    match_aspect=True,
)

# Remove axes and grid
p.axis.visible = False
p.grid.visible = False
p.outline_line_color = None

# Title styling
p.title.text_font_size = "36pt"
p.title.align = "center"


# Helper function to draw arc
def draw_arc(radius, start_angle, end_angle, n_points=50):
    angles = np.linspace(start_angle, end_angle, n_points)
    xs = radius * np.cos(angles)
    ys = radius * np.sin(angles)
    return xs, ys


# Draw maze walls
ring_radii = np.linspace(0.12, 0.95, rings + 1)  # Inner to outer

# Draw circular walls (arcs) and radial walls
for r in range(rings):
    n_sectors = sectors_per_ring[r]
    sector_angle = 2 * np.pi / n_sectors
    inner_radius = ring_radii[r]
    outer_radius = ring_radii[r + 1]

    for s in range(n_sectors):
        start_angle = s * sector_angle
        end_angle = (s + 1) * sector_angle

        # Draw outer arc wall if present
        if cells[(r, s)]["walls"]["outer"]:
            xs, ys = draw_arc(outer_radius, start_angle, end_angle)
            p.line(xs, ys, line_width=wall_width, line_color=wall_color)

        # Draw radial wall (clockwise side) if present
        if cells[(r, s)]["walls"]["cw"]:
            x1 = inner_radius * np.cos(end_angle)
            y1 = inner_radius * np.sin(end_angle)
            x2 = outer_radius * np.cos(end_angle)
            y2 = outer_radius * np.sin(end_angle)
            p.line([x1, x2], [y1, y2], line_width=wall_width, line_color=wall_color)

# Draw outer boundary (with gap for entry)
outer_boundary_radius = ring_radii[-1]
entry_start = entry_sector * (2 * np.pi / sectors_per_ring[outer_ring])
entry_end = (entry_sector + 1) * (2 * np.pi / sectors_per_ring[outer_ring])

# Draw outer boundary in two arcs (leaving gap for entry)
xs1, ys1 = draw_arc(outer_boundary_radius, entry_end, entry_start + 2 * np.pi, n_points=180)
p.line(xs1, ys1, line_width=wall_width + 2, line_color=wall_color)

# Draw inner boundary circle (around center)
theta = np.linspace(0, 2 * np.pi, 100)
p.line(ring_radii[0] * np.cos(theta), ring_radii[0] * np.sin(theta), line_width=wall_width, line_color=wall_color)

# Draw center goal
center_radius = ring_radii[0] * 0.65
p.patch(
    center_radius * np.cos(theta),
    center_radius * np.sin(theta),
    fill_color=goal_color,
    line_color=wall_color,
    line_width=3,
)

# Add GOAL star
goal_label = Label(
    x=0, y=-0.01, text="★", text_font_size="28pt", text_align="center", text_baseline="middle", text_color=wall_color
)
p.add_layout(goal_label)

# Draw entry marker (triangle pointing inward)
entry_angle = (entry_start + entry_end) / 2
entry_x = 1.03 * np.cos(entry_angle)
entry_y = 1.03 * np.sin(entry_angle)
p.scatter(
    [entry_x],
    [entry_y],
    marker="triangle",
    size=35,
    fill_color=entry_color,
    line_color=wall_color,
    angle=entry_angle - np.pi / 2,
)

# Add START label
start_label = Label(
    x=entry_x * 1.12,
    y=entry_y * 1.12,
    text="START",
    text_font_size="20pt",
    text_align="center",
    text_baseline="middle",
    text_color=entry_color,
    text_font_style="bold",
)
p.add_layout(start_label)

# Save outputs
export_png(p, filename="plot.png")

output_file("plot.html", title="Circular Maze Puzzle")
save(p)
