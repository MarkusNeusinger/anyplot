""" pyplots.ai
maze-circular: Circular Maze Puzzle
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 93/100 | Created: 2026-01-16
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Arc


np.random.seed(42)

# Maze parameters
rings = 7
sectors_per_ring = [8, 12, 16, 20, 24, 28, 32]  # More sectors in outer rings
inner_radius = 0.5
ring_width = 0.15

# Initialize maze structure: walls[ring][sector] indicates radial wall after sector
# passages[ring][sector] indicates passage to outer ring at sector position
radial_walls = []
ring_passages = []

for r in range(rings):
    num_sectors = sectors_per_ring[r]
    radial_walls.append([True] * num_sectors)
    ring_passages.append([False] * num_sectors)

# Generate maze using modified Prim's algorithm for circular structure
# Start from center and carve outward ensuring connectivity

# Track which cells are connected to the maze
connected = [[False] * sectors_per_ring[r] for r in range(rings)]
connected[0][0] = True  # Start with center ring, sector 0

# Frontier cells (ring, sector, connection_type, source_ring, source_sector)
frontier = []

# Add initial frontier from ring 0
for s in range(sectors_per_ring[0]):
    if s > 0:
        frontier.append((0, s, "radial", 0, s - 1))
    frontier.append((1, s * sectors_per_ring[1] // sectors_per_ring[0], "ring", 0, s))

while frontier:
    idx = np.random.randint(len(frontier))
    r, s, conn_type, src_r, src_s = frontier.pop(idx)

    if connected[r][s]:
        continue

    connected[r][s] = True

    # Create the passage
    if conn_type == "radial":
        radial_walls[r][min(s, src_s)] = False
    else:  # ring passage
        ring_passages[src_r][src_s] = True

    num_sectors = sectors_per_ring[r]

    # Add neighbors to frontier
    # Radial neighbors (same ring)
    next_s = (s + 1) % num_sectors
    if not connected[r][next_s]:
        frontier.append((r, next_s, "radial", r, s))
    prev_s = (s - 1) % num_sectors
    if not connected[r][prev_s]:
        frontier.append((r, prev_s, "radial", r, s))

    # Outer ring neighbor
    if r < rings - 1:
        outer_sectors = sectors_per_ring[r + 1]
        ratio = outer_sectors / num_sectors
        for outer_s in range(int(s * ratio), int((s + 1) * ratio)):
            if not connected[r + 1][outer_s % outer_sectors]:
                frontier.append((r + 1, outer_s % outer_sectors, "ring", r, s))

    # Inner ring neighbor
    if r > 0:
        inner_sectors = sectors_per_ring[r - 1]
        inner_s = int(s * inner_sectors / num_sectors)
        if not connected[r - 1][inner_s]:
            frontier.append((r - 1, inner_s, "radial", r - 1, inner_s))

# Create entry point on outer ring
entry_sector = np.random.randint(sectors_per_ring[-1])

# Create figure
fig, ax = plt.subplots(figsize=(12, 12))
ax.set_aspect("equal")
ax.set_xlim(-1.7, 1.7)
ax.set_ylim(-1.7, 1.7)
ax.axis("off")

wall_color = "black"
wall_width = 2.5

# Draw outer boundary (with entry gap)
outer_r = inner_radius + rings * ring_width
entry_angle_start = entry_sector * 360 / sectors_per_ring[-1]
entry_angle_end = (entry_sector + 1) * 360 / sectors_per_ring[-1]

# Draw outer arc in two parts (leaving entry gap)
if entry_angle_start > 0:
    arc1 = Arc(
        (0, 0),
        2 * outer_r,
        2 * outer_r,
        angle=0,
        theta1=entry_angle_end,
        theta2=entry_angle_start + 360,
        color=wall_color,
        linewidth=wall_width,
    )
    ax.add_patch(arc1)

# Draw ring walls (concentric circles with gaps for passages)
for r in range(rings):
    ring_r = inner_radius + r * ring_width
    num_sectors = sectors_per_ring[r]
    sector_angle = 360 / num_sectors

    # Draw arcs where there are no passages to outer ring
    for s in range(num_sectors):
        if not ring_passages[r][s]:
            theta1 = s * sector_angle
            theta2 = (s + 1) * sector_angle
            arc = Arc(
                (0, 0),
                2 * (ring_r + ring_width),
                2 * (ring_r + ring_width),
                angle=0,
                theta1=theta1,
                theta2=theta2,
                color=wall_color,
                linewidth=wall_width,
            )
            ax.add_patch(arc)

# Draw radial walls
for r in range(rings):
    num_sectors = sectors_per_ring[r]
    sector_angle = 360 / num_sectors
    r_inner = inner_radius + r * ring_width
    r_outer = r_inner + ring_width

    for s in range(num_sectors):
        if radial_walls[r][s]:
            angle = np.radians((s + 1) * sector_angle)
            x1, y1 = r_inner * np.cos(angle), r_inner * np.sin(angle)
            x2, y2 = r_outer * np.cos(angle), r_outer * np.sin(angle)
            ax.plot([x1, x2], [y1, y2], color=wall_color, linewidth=wall_width)

# Draw center goal
center_circle = plt.Circle((0, 0), inner_radius * 0.6, fill=True, facecolor="#FFD43B", edgecolor="black", linewidth=2)
ax.add_patch(center_circle)
ax.text(0, 0, "GOAL", ha="center", va="center", fontsize=14, fontweight="bold", color="black")

# Draw entry marker
entry_angle = np.radians((entry_sector + 0.5) * 360 / sectors_per_ring[-1])
entry_x = (outer_r + 0.08) * np.cos(entry_angle)
entry_y = (outer_r + 0.08) * np.sin(entry_angle)
ax.annotate("START", xy=(entry_x, entry_y), fontsize=12, fontweight="bold", ha="center", va="center", color="#306998")

# Draw inner boundary (center circle)
inner_circle = Arc(
    (0, 0), 2 * inner_radius, 2 * inner_radius, angle=0, theta1=0, theta2=360, color=wall_color, linewidth=wall_width
)
ax.add_patch(inner_circle)

# Title
ax.set_title("maze-circular · matplotlib · pyplots.ai", fontsize=24, pad=20)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
