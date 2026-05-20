"""anyplot.ai
maze-circular: Circular Maze Puzzle
Library: seaborn | Python 3.13
Quality: pending | Created: 2026-05-20
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1 — entry marker

sns.set_theme(
    style="white",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "text.color": INK,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Maze parameters
np.random.seed(42)
rings = 7
sectors_per_ring = 12
total_cells = 1 + rings * sectors_per_ring
sector_angle = 2 * np.pi / sectors_per_ring

# Union-Find
parent = list(range(total_cells))
uf_rank = [0] * total_cells

# Build wall list
walls = []
for r in range(rings):
    if r == 0:
        for s in range(sectors_per_ring):
            walls.append(("radial", 0, s, 0, 1 + s))
    else:
        for s in range(sectors_per_ring):
            c1 = 1 + (r - 1) * sectors_per_ring + s
            c2 = 1 + r * sectors_per_ring + s
            walls.append(("radial", r, s, c1, c2))

for r in range(1, rings + 1):
    for s in range(sectors_per_ring):
        next_s = (s + 1) % sectors_per_ring
        c1 = 1 + (r - 1) * sectors_per_ring + s
        c2 = 1 + (r - 1) * sectors_per_ring + next_s
        walls.append(("circular", r, s, c1, c2))

np.random.shuffle(walls)

# Kruskal's spanning tree — removes walls to create exactly one solvable path
passages = set()
for wall in walls:
    wall_type, r, s, c1, c2 = wall

    root1 = c1
    while parent[root1] != root1:
        root1 = parent[root1]
    x = c1
    while parent[x] != x:
        next_x = parent[x]
        parent[x] = root1
        x = next_x

    root2 = c2
    while parent[root2] != root2:
        root2 = parent[root2]
    x = c2
    while parent[x] != x:
        next_x = parent[x]
        parent[x] = root2
        x = next_x

    if root1 != root2:
        if uf_rank[root1] < uf_rank[root2]:
            root1, root2 = root2, root1
        parent[root2] = root1
        if uf_rank[root1] == uf_rank[root2]:
            uf_rank[root1] += 1
        passages.add((wall_type, r, s))

# Render maze into a 2D grid (0=path/PAGE_BG, 1=wall/INK)
grid_size = 300
maze_grid = np.zeros((grid_size, grid_size))

inner_radius = 0.15
ring_width = (1 - inner_radius) / (rings + 0.5)
wall_thickness = 3
grid_center = grid_size // 2
grid_scale = (grid_size - 20) / 2.6

# Outer boundary
for i in range(360):
    theta = i * np.pi / 180
    outer_r = inner_radius + (rings + 0.3) * ring_width
    gx = np.clip(grid_center + int(outer_r * np.cos(theta) * grid_scale), 0, grid_size - 1)
    gy = np.clip(grid_center + int(outer_r * np.sin(theta) * grid_scale), 0, grid_size - 1)
    for dx in range(-wall_thickness, wall_thickness + 1):
        for dy in range(-wall_thickness, wall_thickness + 1):
            maze_grid[np.clip(gy + dy, 0, grid_size - 1), np.clip(gx + dx, 0, grid_size - 1)] = 1.0

# Concentric ring walls
for r in range(1, rings + 1):
    radius = inner_radius + r * ring_width
    for s in range(sectors_per_ring):
        if ("circular", r, s) not in passages:
            for i in range(30):
                theta = s * sector_angle + sector_angle * i / 29
                gx = np.clip(grid_center + int(radius * np.cos(theta) * grid_scale), 0, grid_size - 1)
                gy = np.clip(grid_center + int(radius * np.sin(theta) * grid_scale), 0, grid_size - 1)
                for dx in range(-wall_thickness, wall_thickness + 1):
                    for dy in range(-wall_thickness, wall_thickness + 1):
                        maze_grid[np.clip(gy + dy, 0, grid_size - 1), np.clip(gx + dx, 0, grid_size - 1)] = 1.0

# Radial walls
for r in range(rings):
    inner_r = inner_radius if r == 0 else inner_radius + r * ring_width
    outer_r_wall = inner_radius + (r + 1) * ring_width
    for s in range(sectors_per_ring):
        if ("radial", r, s) not in passages:
            angle = s * sector_angle
            for i in range(30):
                rad = inner_r + (outer_r_wall - inner_r) * i / 29
                gx = np.clip(grid_center + int(rad * np.cos(angle) * grid_scale), 0, grid_size - 1)
                gy = np.clip(grid_center + int(rad * np.sin(angle) * grid_scale), 0, grid_size - 1)
                for dx in range(-wall_thickness, wall_thickness + 1):
                    for dy in range(-wall_thickness, wall_thickness + 1):
                        maze_grid[np.clip(gy + dy, 0, grid_size - 1), np.clip(gx + dx, 0, grid_size - 1)] = 1.0

# Entry opening on outer boundary
entry_angle = sector_angle / 2  # mid-point of sector 0
entry_inner_r = inner_radius + rings * ring_width
entry_outer_r = inner_radius + (rings + 0.3) * ring_width
for i in range(30):
    rad = entry_inner_r + (entry_outer_r - entry_inner_r) * i / 29
    gx = np.clip(grid_center + int(rad * np.cos(entry_angle) * grid_scale), 0, grid_size - 1)
    gy = np.clip(grid_center + int(rad * np.sin(entry_angle) * grid_scale), 0, grid_size - 1)
    for dx in range(-wall_thickness - 2, wall_thickness + 3):
        for dy in range(-wall_thickness - 2, wall_thickness + 3):
            maze_grid[np.clip(gy + dy, 0, grid_size - 1), np.clip(gx + dx, 0, grid_size - 1)] = 0.0

# Theme-adaptive colormap: 0=path(PAGE_BG), 1=wall(INK)
maze_cmap = LinearSegmentedColormap.from_list("maze", [PAGE_BG, INK])

# Plot — square canvas: 2400×2400 px (6in × 400dpi)
fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

sns.heatmap(
    maze_grid, ax=ax, cmap=maze_cmap, cbar=False, xticklabels=False, yticklabels=False, square=True, vmin=0, vmax=1
)

# Goal: star at center
ax.text(
    grid_center, grid_center, "★", fontsize=16, ha="center", va="center", color="#E69F00", fontweight="bold", zorder=5
)

# Entry: branded circle marker + label
entry_marker_r = inner_radius + (rings + 0.6) * ring_width
start_x = grid_center + int(entry_marker_r * np.cos(entry_angle) * grid_scale)
start_y = grid_center + int(entry_marker_r * np.sin(entry_angle) * grid_scale)
ax.plot(start_x, start_y, "o", color=BRAND, markersize=6, zorder=5)
ax.annotate(
    "START",
    xy=(start_x, start_y),
    xytext=(start_x - 20, start_y + 16),
    fontsize=7,
    fontweight="bold",
    ha="right",
    va="top",
    color=BRAND,
    bbox={"boxstyle": "round,pad=0.3", "facecolor": ELEVATED_BG, "edgecolor": BRAND, "alpha": 0.9},
    arrowprops={"arrowstyle": "-", "color": BRAND, "lw": 0.5},
)

# Legend
legend_elements = [
    plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=BRAND, markersize=6, label="Entry Point"),
    plt.Line2D([0], [0], marker="*", color="w", markerfacecolor="#E69F00", markersize=8, label="Goal (Center)"),
]
ax.legend(
    handles=legend_elements,
    loc="upper right",
    fontsize=8,
    framealpha=0.95,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
    fancybox=True,
    borderpad=0.8,
)

ax.set_title("maze-circular · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=10)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, bbox_inches="tight", facecolor=PAGE_BG)
