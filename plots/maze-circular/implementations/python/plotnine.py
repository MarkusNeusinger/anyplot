""" pyplots.ai
maze-circular: Circular Maze Puzzle
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-16
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_blank,
    element_text,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    theme,
    theme_void,
)


# Circular maze parameters
np.random.seed(42)
n_rings = 7
sectors_per_ring = [1, 6, 12, 18, 24, 30, 36, 42]  # Increasing sectors outward
difficulty = "medium"
ring_width = 1.0

# Calculate radii for each ring
radii = [i * ring_width for i in range(n_rings + 2)]

# Initialize maze structure
# For each ring, track which radial walls exist and which arc walls exist
# radial_walls[ring][sector] = True means wall exists between this sector and next
# arc_walls[ring][sector] = True means wall exists on outer arc of this sector

radial_walls = []
arc_walls = []

for ring in range(n_rings + 1):
    n_sectors = sectors_per_ring[min(ring, len(sectors_per_ring) - 1)]
    radial_walls.append([True] * n_sectors)
    arc_walls.append([True] * n_sectors)

# Build maze using modified DFS for circular structure
# Cell representation: (ring, sector)
# We work from outside to inside

# Create adjacency and carve passages
visited = set()
parent = {}


# Map cells properly considering sector changes between rings
def get_neighbors(ring, sector):
    """Get neighboring cells with proper sector mapping between rings."""
    neighbors = []
    n_sectors_current = sectors_per_ring[min(ring, len(sectors_per_ring) - 1)]

    # Same ring - adjacent sectors
    prev_sector = (sector - 1) % n_sectors_current
    next_sector = (sector + 1) % n_sectors_current
    neighbors.append((ring, prev_sector, "radial_prev"))
    neighbors.append((ring, next_sector, "radial_next"))

    # Inner ring
    if ring > 0:
        n_sectors_inner = sectors_per_ring[min(ring - 1, len(sectors_per_ring) - 1)]
        inner_sector = int(sector * n_sectors_inner / n_sectors_current)
        neighbors.append((ring - 1, inner_sector, "arc_inner"))

    # Outer ring
    if ring < n_rings:
        n_sectors_outer = sectors_per_ring[min(ring + 1, len(sectors_per_ring) - 1)]
        # Multiple outer sectors may correspond to this sector
        start_outer = int(sector * n_sectors_outer / n_sectors_current)
        end_outer = int((sector + 1) * n_sectors_outer / n_sectors_current)
        for outer_sector in range(start_outer, end_outer):
            neighbors.append((ring + 1, outer_sector % n_sectors_outer, "arc_outer"))

    return neighbors


# DFS maze generation starting from center
start = (0, 0)
stack = [start]
visited.add(start)

while stack:
    current = stack[-1]
    ring, sector = current
    n_sectors = sectors_per_ring[min(ring, len(sectors_per_ring) - 1)]

    # Get unvisited neighbors
    unvisited = []
    for nr, ns, wall_type in get_neighbors(ring, sector):
        if (nr, ns) not in visited:
            unvisited.append((nr, ns, wall_type))

    if unvisited:
        # Choose random neighbor
        next_ring, next_sector, wall_type = unvisited[np.random.randint(len(unvisited))]

        # Remove wall between cells
        if wall_type == "radial_prev":
            radial_walls[ring][sector] = False
        elif wall_type == "radial_next":
            next_s = (sector + 1) % n_sectors
            radial_walls[ring][next_s] = False
        elif wall_type == "arc_inner":
            arc_walls[ring - 1][next_sector] = False
        elif wall_type == "arc_outer":
            arc_walls[ring][sector] = False

        visited.add((next_ring, next_sector))
        stack.append((next_ring, next_sector))
    else:
        stack.pop()

# Create entry point on outer ring
entry_sector = 0
outer_ring = n_rings
n_outer_sectors = sectors_per_ring[min(outer_ring, len(sectors_per_ring) - 1)]

# Generate wall segments for plotting
segments = []

# Outer boundary (full circle except entry)
n_points = 200
for i in range(n_points):
    theta1 = 2 * np.pi * i / n_points
    theta2 = 2 * np.pi * (i + 1) / n_points

    # Leave gap for entry
    entry_angle = 2 * np.pi * entry_sector / n_outer_sectors
    entry_width = 2 * np.pi / n_outer_sectors * 0.8

    if not (entry_angle - entry_width / 2 < (theta1 + theta2) / 2 < entry_angle + entry_width / 2):
        r = radii[n_rings + 1]
        segments.append(
            {"x": r * np.cos(theta1), "y": r * np.sin(theta1), "xend": r * np.cos(theta2), "yend": r * np.sin(theta2)}
        )

# Arc walls (between rings)
for ring in range(n_rings):
    n_sectors = sectors_per_ring[min(ring, len(sectors_per_ring) - 1)]
    r = radii[ring + 1]

    for sector in range(n_sectors):
        if arc_walls[ring][sector]:
            theta1 = 2 * np.pi * sector / n_sectors
            theta2 = 2 * np.pi * (sector + 1) / n_sectors

            # Draw arc as small segments
            n_arc_segments = max(3, int(20 / n_sectors * 6))
            for j in range(n_arc_segments):
                t1 = theta1 + (theta2 - theta1) * j / n_arc_segments
                t2 = theta1 + (theta2 - theta1) * (j + 1) / n_arc_segments
                segments.append(
                    {"x": r * np.cos(t1), "y": r * np.sin(t1), "xend": r * np.cos(t2), "yend": r * np.sin(t2)}
                )

# Radial walls
for ring in range(n_rings + 1):
    n_sectors = sectors_per_ring[min(ring, len(sectors_per_ring) - 1)]
    r_inner = radii[ring]
    r_outer = radii[ring + 1]

    for sector in range(n_sectors):
        if radial_walls[ring][sector]:
            theta = 2 * np.pi * sector / n_sectors
            segments.append(
                {
                    "x": r_inner * np.cos(theta),
                    "y": r_inner * np.sin(theta),
                    "xend": r_outer * np.cos(theta),
                    "yend": r_outer * np.sin(theta),
                }
            )

walls_df = pd.DataFrame(segments)

# Entry and goal markers
# Entry is at the gap in the outer ring (sector 0, so angle near 0)
entry_angle = np.pi / n_outer_sectors  # Middle of sector 0
entry_r = radii[n_rings + 1] + ring_width * 0.6

# Separate dataframes for entry and goal to avoid color mapping issues
entry_df = pd.DataFrame(
    {"x": [entry_r * np.cos(entry_angle)], "y": [entry_r * np.sin(entry_angle)], "label": ["START"]}
)
goal_df = pd.DataFrame({"x": [0], "y": [0], "label": ["GOAL"]})

# Create the plot
plot = (
    ggplot()
    + geom_segment(data=walls_df, mapping=aes(x="x", y="y", xend="xend", yend="yend"), color="black", size=1.2)
    + geom_point(data=goal_df, mapping=aes(x="x", y="y"), color="#306998", size=8)
    + geom_text(
        data=goal_df, mapping=aes(x="x", y="y", label="label"), color="#FFD43B", size=14, fontweight="bold", nudge_y=0.8
    )
    + geom_text(data=entry_df, mapping=aes(x="x", y="y", label="label"), color="#306998", size=14, fontweight="bold")
    + coord_fixed(ratio=1)
    + labs(title="maze-circular · plotnine · pyplots.ai")
    + theme_void()
    + theme(
        figure_size=(12, 12),
        plot_title=element_text(size=24, ha="center", weight="bold"),
        plot_background=element_blank(),
        panel_background=element_blank(),
    )
)

# Save
plot.save("plot.png", dpi=300)
