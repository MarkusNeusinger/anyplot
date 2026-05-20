""" anyplot.ai
maze-circular: Circular Maze Puzzle
Library: altair 6.1.0 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-20
"""

import os
import sys


# Remove this file's directory from sys.path to avoid circular import with the altair package
if sys.path and os.path.exists(os.path.join(sys.path[0] or ".", "altair.py")):
    sys.path = sys.path[1:]

import altair as alt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
WALL_COLOR = "#1A1A17" if THEME == "light" else "#E0DFD8"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
ENTRY_COLOR = "#0072B2"  # Okabe-Ito position 3, theme-independent (same in light and dark)
GOAL_COLOR = "#E69F00"  # Okabe-Ito position 5, theme-independent

# Difficulty: "easy" / "medium" / "hard" — scales sector density (more sectors = harder maze)
DIFFICULTY = os.getenv("ANYPLOT_DIFFICULTY", "medium")
density_map = {"easy": 0.70, "medium": 1.0, "hard": 1.40}
density = density_map.get(DIFFICULTY, 1.0)

# Maze parameters
np.random.seed(42)
num_rings = 7
sectors_per_ring = [1] + [max(4, round((12 + i * 4) * density)) for i in range(num_rings)]
ring_width = 1.0

# Data structures for maze walls
walls = []
for ring in range(num_rings):
    ring_walls = []
    for _sector in range(sectors_per_ring[ring + 1]):
        ring_walls.append({"outer": True, "cw": True})
    walls.append(ring_walls)

# Union-Find for Kruskal's maze generation (inlined, no helper functions)
parent = {}
for ring in range(num_rings):
    for sector in range(sectors_per_ring[ring + 1]):
        parent[(ring, sector)] = (ring, sector)

possible_walls = []
for ring in range(num_rings):
    num_sectors = sectors_per_ring[ring + 1]
    for sector in range(num_sectors):
        next_sector = (sector + 1) % num_sectors
        possible_walls.append(("cw", ring, sector, ring, next_sector))
        if ring < num_rings - 1:
            outer_sectors = sectors_per_ring[ring + 2]
            ratio = outer_sectors / num_sectors
            outer_sector = int(sector * ratio)
            possible_walls.append(("outer", ring, sector, ring + 1, outer_sector))

np.random.shuffle(possible_walls)

for wall_type, r1, s1, r2, s2 in possible_walls:
    cell1, cell2 = (r1, s1), (r2, s2)
    root1 = cell1
    while parent[root1] != root1:
        root1 = parent[root1]
    c = cell1
    while parent[c] != root1:
        parent[c], c = root1, parent[c]

    root2 = cell2
    while parent[root2] != root2:
        root2 = parent[root2]
    c = cell2
    while parent[c] != root2:
        parent[c], c = root2, parent[c]

    if root1 != root2:
        parent[root1] = root2
        if wall_type == "cw":
            walls[r1][s1]["cw"] = False
        else:
            walls[r1][s1]["outer"] = False

# Entry fixed at top (θ ≈ π/2) so START label is always clearly readable
entry_sector = sectors_per_ring[num_rings] // 4

# Generate wall segment coordinates
outer_boundary_data = []  # Outer boundary — rendered thicker for visual emphasis
wall_data = []  # Interior walls
wall_count = 0

theta_vals = np.linspace(0, 2 * np.pi, sectors_per_ring[num_rings] + 1)
entry_theta_start = theta_vals[entry_sector]
entry_theta_end = theta_vals[entry_sector + 1]
outer_r = num_rings * ring_width

# Outer boundary arcs with gap at entry — tracked separately for thicker strokeWidth
if entry_sector > 0:
    theta = np.linspace(0, entry_theta_start, 60)
    x_arr, y_arr = outer_r * np.cos(theta), outer_r * np.sin(theta)
    for i in range(len(x_arr)):
        outer_boundary_data.append({"x": x_arr[i], "y": y_arr[i], "wall_id": f"ob_{wall_count}", "order": i})
    wall_count += 1

if entry_sector < sectors_per_ring[num_rings] - 1:
    theta = np.linspace(entry_theta_end, 2 * np.pi, 60)
    x_arr, y_arr = outer_r * np.cos(theta), outer_r * np.sin(theta)
    for i in range(len(x_arr)):
        outer_boundary_data.append({"x": x_arr[i], "y": y_arr[i], "wall_id": f"ob_{wall_count}", "order": i})
    wall_count += 1

# Concentric ring walls (arcs with gaps at passages)
for ring in range(num_rings - 1):
    r = (ring + 1) * ring_width
    num_sectors = sectors_per_ring[ring + 1]
    ring_theta = np.linspace(0, 2 * np.pi, num_sectors + 1)
    arc_start = None

    for sector in range(num_sectors):
        if walls[ring][sector]["outer"]:
            if arc_start is None:
                arc_start = ring_theta[sector]
        else:
            if arc_start is not None:
                theta = np.linspace(arc_start, ring_theta[sector], 30)
                x_arr, y_arr = r * np.cos(theta), r * np.sin(theta)
                for i in range(len(x_arr)):
                    wall_data.append({"x": x_arr[i], "y": y_arr[i], "wall_id": f"r_{ring}_{wall_count}", "order": i})
                wall_count += 1
                arc_start = None

    if arc_start is not None:
        theta = np.linspace(arc_start, 2 * np.pi, 30)
        x_arr, y_arr = r * np.cos(theta), r * np.sin(theta)
        for i in range(len(x_arr)):
            wall_data.append({"x": x_arr[i], "y": y_arr[i], "wall_id": f"r_{ring}_{wall_count}", "order": i})
        wall_count += 1

# Radial walls (sector dividers with gaps at passages)
for ring in range(num_rings):
    num_sectors = sectors_per_ring[ring + 1]
    r_inner = ring * ring_width if ring > 0 else 0.3
    r_outer = (ring + 1) * ring_width
    radial_theta = np.linspace(0, 2 * np.pi, num_sectors + 1)

    for sector in range(num_sectors):
        if walls[ring][sector]["cw"]:
            theta_val = radial_theta[sector + 1] if sector < num_sectors - 1 else 2 * np.pi
            x1, y1 = r_inner * np.cos(theta_val), r_inner * np.sin(theta_val)
            x2, y2 = r_outer * np.cos(theta_val), r_outer * np.sin(theta_val)
            wid = f"rad_{ring}_{sector}_{wall_count}"
            wall_data.append({"x": x1, "y": y1, "wall_id": wid, "order": 0})
            wall_data.append({"x": x2, "y": y2, "wall_id": wid, "order": 1})
            wall_count += 1

# DataFrames
df_outer = pd.DataFrame(outer_boundary_data)
df_walls = pd.DataFrame(wall_data)

# Goal at center: filled halo + star symbol
goal_halo_df = pd.DataFrame({"x": [0.0], "y": [0.0]})
goal_star_df = pd.DataFrame({"x": [0.0], "y": [0.0], "label": ["★"]})

# Entry label and inward-pointing arrow indicator
entry_angle = (entry_theta_start + entry_theta_end) / 2
entry_label_r = outer_r + 0.90
entry_arrow_r = outer_r + 0.30

entry_df = pd.DataFrame(
    {"x": [entry_label_r * np.cos(entry_angle)], "y": [entry_label_r * np.sin(entry_angle)], "label": ["START"]}
)
arrow_df = pd.DataFrame(
    {"x": [entry_arrow_r * np.cos(entry_angle)], "y": [entry_arrow_r * np.sin(entry_angle)], "label": ["▼"]}
)

max_extent = outer_r + 1.6

# Shared scale domains to guarantee equal-aspect circle
x_scale = alt.Scale(domain=[-max_extent, max_extent])
y_scale = alt.Scale(domain=[-max_extent, max_extent])

# Outer boundary wall lines — thicker for visual boundary emphasis
outer_chart = (
    alt.Chart(df_outer)
    .mark_line(color=WALL_COLOR, strokeWidth=4.0)
    .encode(
        x=alt.X("x:Q", axis=None, scale=x_scale),
        y=alt.Y("y:Q", axis=None, scale=y_scale),
        detail="wall_id:N",
        order="order:O",
    )
)

# Interior wall lines
walls_chart = (
    alt.Chart(df_walls)
    .mark_line(color=WALL_COLOR, strokeWidth=2.5)
    .encode(
        x=alt.X("x:Q", axis=None, scale=x_scale),
        y=alt.Y("y:Q", axis=None, scale=y_scale),
        detail="wall_id:N",
        order="order:O",
    )
)

# Goal halo — subtle filled circle marking the center zone
goal_halo_chart = (
    alt.Chart(goal_halo_df)
    .mark_point(color=GOAL_COLOR, size=350, filled=True, opacity=0.30)
    .encode(x=alt.X("x:Q", axis=None, scale=x_scale), y=alt.Y("y:Q", axis=None, scale=y_scale))
)

# Goal star at center — Unicode ★ for reliable rendering
goal_chart = (
    alt.Chart(goal_star_df)
    .mark_text(fontSize=24, fontWeight="bold", color=GOAL_COLOR)
    .encode(x=alt.X("x:Q", axis=None, scale=x_scale), y=alt.Y("y:Q", axis=None, scale=y_scale), text="label:N")
)

# Inward-pointing arrow at entry gap (▼ points toward center when entry is at top)
arrow_chart = (
    alt.Chart(arrow_df)
    .mark_text(fontSize=14, color=ENTRY_COLOR)
    .encode(x=alt.X("x:Q", axis=None, scale=x_scale), y=alt.Y("y:Q", axis=None, scale=y_scale), text="label:N")
)

# Entry label above the maze
entry_chart = (
    alt.Chart(entry_df)
    .mark_text(fontSize=18, fontWeight="bold", color=ENTRY_COLOR)
    .encode(x=alt.X("x:Q", axis=None, scale=x_scale), y=alt.Y("y:Q", axis=None, scale=y_scale), text="label:N")
)

chart = (
    alt.layer(outer_chart, walls_chart, goal_halo_chart, goal_chart, arrow_chart, entry_chart)
    .properties(width=600, height=600, background=PAGE_BG, title="maze-circular · python · altair · anyplot.ai")
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_axis(grid=False)
    .configure_title(fontSize=16, color=INK)
)

chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")
