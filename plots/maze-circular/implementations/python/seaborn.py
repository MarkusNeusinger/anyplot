""" pyplots.ai
maze-circular: Circular Maze Puzzle
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-16
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Configuration
np.random.seed(42)
rings = 7
sectors_per_ring = 12

# Create figure with square aspect for circular maze (3600x3600 at 100dpi = 36x36)
fig, ax = plt.subplots(figsize=(36, 36))

# Total cells = center (1) + rings * sectors
total_cells = 1 + rings * sectors_per_ring

# Union-Find data structure using arrays (KISS - flat script, no classes/functions)
parent = list(range(total_cells))
uf_rank = [0] * total_cells

# Generate all possible walls (edges between adjacent cells)
walls = []

# Radial walls: between ring r and ring r+1
for r in range(rings):
    if r == 0:
        for s in range(sectors_per_ring):
            # cell_id for center is 0, for ring 1 sector s is 1 + s
            walls.append(("radial", 0, s, 0, 1 + s))
    else:
        for s in range(sectors_per_ring):
            # cell_id: 1 + (ring-1)*sectors + sector
            c1 = 1 + (r - 1) * sectors_per_ring + s
            c2 = 1 + r * sectors_per_ring + s
            walls.append(("radial", r, s, c1, c2))

# Circular walls: between adjacent sectors in same ring
for r in range(1, rings + 1):
    for s in range(sectors_per_ring):
        next_s = (s + 1) % sectors_per_ring
        c1 = 1 + (r - 1) * sectors_per_ring + s
        c2 = 1 + (r - 1) * sectors_per_ring + next_s
        walls.append(("circular", r, s, c1, c2))

# Shuffle walls for random maze generation
np.random.shuffle(walls)

# Kruskal's algorithm: remove walls to create spanning tree (exactly one solution)
passages = set()
for wall in walls:
    wall_type, r, s, c1, c2 = wall

    # Find root of c1 with path compression
    root1 = c1
    while parent[root1] != root1:
        root1 = parent[root1]
    x = c1
    while parent[x] != x:
        next_x = parent[x]
        parent[x] = root1
        x = next_x

    # Find root of c2 with path compression
    root2 = c2
    while parent[root2] != root2:
        root2 = parent[root2]
    x = c2
    while parent[x] != x:
        next_x = parent[x]
        parent[x] = root2
        x = next_x

    # Union if different sets
    if root1 != root2:
        if uf_rank[root1] < uf_rank[root2]:
            root1, root2 = root2, root1
        parent[root2] = root1
        if uf_rank[root1] == uf_rank[root2]:
            uf_rank[root1] += 1
        passages.add((wall_type, r, s))

# Build maze grid for seaborn heatmap visualization (higher resolution for smoother walls)
grid_size = 300
maze_grid = np.ones((grid_size, grid_size)) * 0.95  # White background

# Drawing parameters
inner_radius = 0.15
ring_width = (1 - inner_radius) / (rings + 0.5)
wall_color_val = 0.1  # Dark gray for walls

# Grid conversion parameters
grid_center = grid_size // 2
grid_scale = (grid_size - 20) / 2.6

# Draw walls onto grid (increased thickness for higher resolution grid)
wall_thickness = 3

# Draw outer boundary
for i in range(360):
    theta = i * np.pi / 180
    outer_r = inner_radius + (rings + 0.3) * ring_width
    gx = grid_center + int(outer_r * np.cos(theta) * grid_scale)
    gy = grid_center + int(outer_r * np.sin(theta) * grid_scale)
    gx = np.clip(gx, 0, grid_size - 1)
    gy = np.clip(gy, 0, grid_size - 1)
    for dx in range(-wall_thickness, wall_thickness + 1):
        for dy in range(-wall_thickness, wall_thickness + 1):
            nx = np.clip(gx + dx, 0, grid_size - 1)
            ny = np.clip(gy + dy, 0, grid_size - 1)
            maze_grid[ny, nx] = wall_color_val

# Draw concentric ring walls
for r in range(1, rings + 1):
    radius = inner_radius + r * ring_width
    sector_angle = 2 * np.pi / sectors_per_ring
    for s in range(sectors_per_ring):
        if ("circular", r, s) not in passages:
            start_angle = s * sector_angle
            end_angle = start_angle + sector_angle
            for i in range(30):
                theta = start_angle + (end_angle - start_angle) * i / 29
                gx = grid_center + int(radius * np.cos(theta) * grid_scale)
                gy = grid_center + int(radius * np.sin(theta) * grid_scale)
                gx = np.clip(gx, 0, grid_size - 1)
                gy = np.clip(gy, 0, grid_size - 1)
                for dx in range(-wall_thickness, wall_thickness + 1):
                    for dy in range(-wall_thickness, wall_thickness + 1):
                        nx = np.clip(gx + dx, 0, grid_size - 1)
                        ny = np.clip(gy + dy, 0, grid_size - 1)
                        maze_grid[ny, nx] = wall_color_val

# Draw radial walls
for r in range(rings):
    inner_r = inner_radius if r == 0 else inner_radius + r * ring_width
    outer_r_wall = inner_radius + (r + 1) * ring_width
    sector_angle = 2 * np.pi / sectors_per_ring
    for s in range(sectors_per_ring):
        if ("radial", r, s) not in passages:
            angle = s * sector_angle
            for i in range(30):
                rad = inner_r + (outer_r_wall - inner_r) * i / 29
                gx = grid_center + int(rad * np.cos(angle) * grid_scale)
                gy = grid_center + int(rad * np.sin(angle) * grid_scale)
                gx = np.clip(gx, 0, grid_size - 1)
                gy = np.clip(gy, 0, grid_size - 1)
                for dx in range(-wall_thickness, wall_thickness + 1):
                    for dy in range(-wall_thickness, wall_thickness + 1):
                        nx = np.clip(gx + dx, 0, grid_size - 1)
                        ny = np.clip(gy + dy, 0, grid_size - 1)
                        maze_grid[ny, nx] = wall_color_val

# Draw center goal area
center_radius_grid = int(inner_radius * 0.7 * grid_scale)
for dx in range(-center_radius_grid, center_radius_grid + 1):
    for dy in range(-center_radius_grid, center_radius_grid + 1):
        if dx * dx + dy * dy <= center_radius_grid * center_radius_grid:
            maze_grid[grid_center + dy, grid_center + dx] = 0.3

# Entry opening on outer boundary
entry_sector = 0
entry_angle = entry_sector * (2 * np.pi / sectors_per_ring) + (np.pi / sectors_per_ring)
entry_inner_r = inner_radius + rings * ring_width
entry_outer_r = inner_radius + (rings + 0.3) * ring_width
for i in range(30):
    rad = entry_inner_r + (entry_outer_r - entry_inner_r) * i / 29
    gx = grid_center + int(rad * np.cos(entry_angle) * grid_scale)
    gy = grid_center + int(rad * np.sin(entry_angle) * grid_scale)
    gx = np.clip(gx, 0, grid_size - 1)
    gy = np.clip(gy, 0, grid_size - 1)
    for dx in range(-wall_thickness - 2, wall_thickness + 3):
        for dy in range(-wall_thickness - 2, wall_thickness + 3):
            nx = np.clip(gx + dx, 0, grid_size - 1)
            ny = np.clip(gy + dy, 0, grid_size - 1)
            maze_grid[ny, nx] = 0.95  # White to create opening

# Convert to DataFrame for seaborn
maze_df = pd.DataFrame(maze_grid)

# Use seaborn heatmap to display the maze (primary seaborn plotting function)
# Use gray colormap (not gray_r) so low values = dark (walls), high values = light (paths)
sns.heatmap(maze_df, ax=ax, cmap="gray", cbar=False, xticklabels=False, yticklabels=False, square=True, vmin=0, vmax=1)

# Add goal star overlay at center (larger for bigger figure)
ax.text(grid_center, grid_center, "★", fontsize=48, ha="center", va="center", color="#FFD43B", fontweight="bold")

# Add START marker - position it clearly outside the maze
entry_marker_r = inner_radius + (rings + 0.6) * ring_width
start_x = grid_center + int(entry_marker_r * np.cos(entry_angle) * grid_scale)
start_y = grid_center + int(entry_marker_r * np.sin(entry_angle) * grid_scale)
ax.plot(start_x, start_y, "o", color="#306998", markersize=28, zorder=5)
ax.annotate(
    "START",
    xy=(start_x, start_y),
    xytext=(start_x + 25, start_y),
    fontsize=24,
    fontweight="bold",
    ha="left",
    va="center",
    color="#306998",
    bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "#306998", "alpha": 0.9},
)

# Add legend explaining markers - place at upper right for better balance
legend_elements = [
    plt.Line2D([0], [0], marker="o", color="w", markerfacecolor="#306998", markersize=20, label="Entry Point"),
    plt.Line2D([0], [0], marker="*", color="w", markerfacecolor="#FFD43B", markersize=24, label="Goal (Center)"),
]
ax.legend(
    handles=legend_elements,
    loc="upper right",
    fontsize=20,
    framealpha=0.95,
    edgecolor="#333333",
    fancybox=True,
    borderpad=1.0,
)

# Title (larger for bigger figure)
ax.set_title("maze-circular · seaborn · pyplots.ai", fontsize=36, fontweight="bold", pad=30)

plt.tight_layout()
plt.savefig("plot.png", dpi=100, bbox_inches="tight", facecolor="white")
