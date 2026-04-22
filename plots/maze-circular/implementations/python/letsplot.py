""" pyplots.ai
maze-circular: Circular Maze Puzzle
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-16
"""

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Maze parameters
np.random.seed(42)
num_rings = 7
sectors_per_ring = [1]  # Center has 1 sector, each ring has more sectors
for ring in range(1, num_rings + 1):
    sectors_per_ring.append(max(6, ring * 4))  # Increasing sectors per ring

# Build adjacency graph for cells
# Each cell is (ring, sector) where ring 0 is center
cells = [(0, 0)]  # Center cell
for ring in range(1, num_rings + 1):
    for sector in range(sectors_per_ring[ring]):
        cells.append((ring, sector))

# Find neighbors for each cell
neighbors = {cell: [] for cell in cells}

# Center connects to all sectors in ring 1
for sector in range(sectors_per_ring[1]):
    neighbors[(0, 0)].append((1, sector))
    neighbors[(1, sector)].append((0, 0))

# Connections within same ring (adjacent sectors)
for ring in range(1, num_rings + 1):
    n_sectors = sectors_per_ring[ring]
    for sector in range(n_sectors):
        next_sector = (sector + 1) % n_sectors
        neighbors[(ring, sector)].append((ring, next_sector))
        neighbors[(ring, next_sector)].append((ring, sector))

# Connections between adjacent rings (radial passages)
for ring in range(1, num_rings):
    inner_sectors = sectors_per_ring[ring]
    outer_sectors = sectors_per_ring[ring + 1]
    ratio = outer_sectors / inner_sectors
    for inner_sector in range(inner_sectors):
        outer_start = int(inner_sector * ratio)
        outer_end = int((inner_sector + 1) * ratio)
        for outer_sector in range(outer_start, outer_end):
            neighbors[(ring, inner_sector)].append((ring + 1, outer_sector))
            neighbors[(ring + 1, outer_sector)].append((ring, inner_sector))

# DFS maze generation
visited = set()
passages = set()  # Edges in the spanning tree
stack = [(0, 0)]
visited.add((0, 0))

while stack:
    current = stack[-1]
    unvisited_neighbors = [n for n in neighbors[current] if n not in visited]

    if unvisited_neighbors:
        next_cell = unvisited_neighbors[np.random.randint(len(unvisited_neighbors))]
        visited.add(next_cell)
        passages.add((current, next_cell))
        passages.add((next_cell, current))
        stack.append(next_cell)
    else:
        stack.pop()

# Geometry parameters
ring_width = 1.0
center_radius = 0.5
entrance_sector = 0
n_arc_points = 50

# Collect wall segments as lines
wall_segments = []

# Draw arc walls (circular walls between rings)
for ring in range(1, num_rings + 1):
    outer_r = center_radius + ring * ring_width if ring > 0 else center_radius
    n_sectors = sectors_per_ring[ring]

    for sector in range(n_sectors):
        # Check if there's a passage to the outer ring
        if ring < num_rings:
            has_passage = False
            outer_sectors_count = sectors_per_ring[ring + 1]
            ratio = outer_sectors_count / n_sectors
            outer_start = int(sector * ratio)
            outer_end = int((sector + 1) * ratio)
            for outer_sector in range(outer_start, outer_end):
                if ((ring, sector), (ring + 1, outer_sector)) in passages:
                    has_passage = True
                    break
            if has_passage:
                continue  # Don't draw outer wall - there's a passage

        # Skip entrance opening on outer wall
        if ring == num_rings and sector == entrance_sector:
            continue

        # Draw arc for outer wall of this sector
        theta_start = 2 * np.pi * sector / n_sectors - np.pi / 2
        theta_end = 2 * np.pi * (sector + 1) / n_sectors - np.pi / 2
        theta_vals = np.linspace(theta_start, theta_end, n_arc_points)
        for i in range(len(theta_vals) - 1):
            x1, y1 = outer_r * np.cos(theta_vals[i]), outer_r * np.sin(theta_vals[i])
            x2, y2 = outer_r * np.cos(theta_vals[i + 1]), outer_r * np.sin(theta_vals[i + 1])
            wall_segments.append({"x": x1, "y": y1, "xend": x2, "yend": y2})

# Draw radial walls (between sectors in same ring)
for ring in range(1, num_rings + 1):
    n_sectors = sectors_per_ring[ring]
    inner_r = center_radius + (ring - 1) * ring_width if ring > 1 else center_radius
    outer_r = center_radius + ring * ring_width

    for sector in range(n_sectors):
        next_sector = (sector + 1) % n_sectors
        if ((ring, sector), (ring, next_sector)) in passages:
            continue  # Don't draw wall - there's a passage

        theta = 2 * np.pi * (sector + 1) / n_sectors - np.pi / 2
        x1, y1 = inner_r * np.cos(theta), inner_r * np.sin(theta)
        x2, y2 = outer_r * np.cos(theta), outer_r * np.sin(theta)
        wall_segments.append({"x": x1, "y": y1, "xend": x2, "yend": y2})

# Draw inner walls for ring 1 connecting to center
inner_r = center_radius
for sector in range(sectors_per_ring[1]):
    if ((0, 0), (1, sector)) not in passages:
        n_inner_sectors = sectors_per_ring[1]
        theta_start = 2 * np.pi * sector / n_inner_sectors - np.pi / 2
        theta_end = 2 * np.pi * (sector + 1) / n_inner_sectors - np.pi / 2
        theta_vals = np.linspace(theta_start, theta_end, n_arc_points // 2)
        for i in range(len(theta_vals) - 1):
            x1, y1 = inner_r * np.cos(theta_vals[i]), inner_r * np.sin(theta_vals[i])
            x2, y2 = inner_r * np.cos(theta_vals[i + 1]), inner_r * np.sin(theta_vals[i + 1])
            wall_segments.append({"x": x1, "y": y1, "xend": x2, "yend": y2})

df_walls = pd.DataFrame(wall_segments)

# Markers for start and goal
outer_r = center_radius + num_rings * ring_width
entrance_n_sectors = sectors_per_ring[num_rings]
entrance_theta = (
    2 * np.pi * entrance_sector / entrance_n_sectors + 2 * np.pi * (entrance_sector + 1) / entrance_n_sectors
) / 2 - np.pi / 2
start_x = (outer_r + 0.8) * np.cos(entrance_theta)
start_y = (outer_r + 0.8) * np.sin(entrance_theta)

df_markers = pd.DataFrame(
    {"x": [start_x, 0], "y": [start_y, 0], "label": ["START", "GOAL"], "color": ["#306998", "#DC2626"]}
)

# Create plot
plot_radius = outer_r + 1.5
plot = (
    ggplot()
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=df_walls, color="black", size=1.5)
    + geom_text(
        aes(x="x", y="y", label="label", color="color"), data=df_markers, size=8, fontface="bold", show_legend=False
    )
    + scale_color_identity()
    + coord_fixed(ratio=1, xlim=(-plot_radius, plot_radius), ylim=(-plot_radius, plot_radius))
    + theme_void()
    + theme(plot_title=element_text(size=24, hjust=0.5), plot_margin=[40, 40, 40, 40])
    + labs(title="maze-circular \u00b7 letsplot \u00b7 pyplots.ai")
    + ggsize(1200, 1200)
)

# Save as PNG and HTML
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
