""" pyplots.ai
maze-circular: Circular Maze Puzzle
Library: altair 6.0.0 | Python 3.13.11
Quality: 80/100 | Created: 2026-01-16
"""

import altair as alt
import numpy as np
import pandas as pd


# Maze parameters
np.random.seed(42)
num_rings = 7
sectors_per_ring = [1] + [12 + i * 4 for i in range(num_rings)]
ring_width = 1.0

# Data structures for maze
walls = []
for ring in range(num_rings):
    ring_walls = []
    for _sector in range(sectors_per_ring[ring + 1]):
        ring_walls.append({"outer": True, "cw": True})
    walls.append(ring_walls)

# Union-Find using dictionaries (inlined - no helper functions)
parent = {}
for ring in range(num_rings):
    for sector in range(sectors_per_ring[ring + 1]):
        parent[(ring, sector)] = (ring, sector)

# Generate maze using randomized Kruskal's algorithm
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
    # Inline find with path compression
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

    # Inline union
    if root1 != root2:
        parent[root1] = root2
        if wall_type == "cw":
            walls[r1][s1]["cw"] = False
        else:
            walls[r1][s1]["outer"] = False

# Entry point
entry_sector = np.random.randint(0, sectors_per_ring[num_rings])

# Generate wall segments for plotting
wall_data = []
wall_count = 0

# Draw outer boundary (except entry)
theta_vals = np.linspace(0, 2 * np.pi, sectors_per_ring[num_rings] + 1)
entry_theta_start = theta_vals[entry_sector]
entry_theta_end = theta_vals[entry_sector + 1]
outer_r = num_rings * ring_width

# Outer boundary arc segments (inline add_arc)
if entry_sector > 0:
    theta = np.linspace(0, entry_theta_start, 30)
    x = outer_r * np.cos(theta)
    y = outer_r * np.sin(theta)
    for i in range(len(x)):
        wall_data.append({"x": x[i], "y": y[i], "wall_id": f"outer_bound_{wall_count}", "order": i})
    wall_count += 1

if entry_sector < sectors_per_ring[num_rings] - 1:
    theta = np.linspace(entry_theta_end, 2 * np.pi, 30)
    x = outer_r * np.cos(theta)
    y = outer_r * np.sin(theta)
    for i in range(len(x)):
        wall_data.append({"x": x[i], "y": y[i], "wall_id": f"outer_bound_{wall_count}", "order": i})
    wall_count += 1

# Draw ring walls (concentric circles with gaps)
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
                # Inline add_arc
                theta = np.linspace(arc_start, ring_theta[sector], 30)
                x = r * np.cos(theta)
                y = r * np.sin(theta)
                for i in range(len(x)):
                    wall_data.append({"x": x[i], "y": y[i], "wall_id": f"ring_{ring}_{wall_count}", "order": i})
                wall_count += 1
                arc_start = None

    if arc_start is not None:
        theta = np.linspace(arc_start, 2 * np.pi, 30)
        x = r * np.cos(theta)
        y = r * np.sin(theta)
        for i in range(len(x)):
            wall_data.append({"x": x[i], "y": y[i], "wall_id": f"ring_{ring}_{wall_count}", "order": i})
        wall_count += 1

# Draw radial walls (sector dividers with gaps)
for ring in range(num_rings):
    num_sectors = sectors_per_ring[ring + 1]
    r_inner = ring * ring_width if ring > 0 else 0.3
    r_outer = (ring + 1) * ring_width
    radial_theta = np.linspace(0, 2 * np.pi, num_sectors + 1)

    for sector in range(num_sectors):
        if walls[ring][sector]["cw"]:
            theta_val = radial_theta[(sector + 1) % num_sectors] if sector < num_sectors - 1 else 2 * np.pi
            # Inline add_radial
            x1, y1 = r_inner * np.cos(theta_val), r_inner * np.sin(theta_val)
            x2, y2 = r_outer * np.cos(theta_val), r_outer * np.sin(theta_val)
            wall_data.append({"x": x1, "y": y1, "wall_id": f"radial_{ring}_{sector}_{wall_count}", "order": 0})
            wall_data.append({"x": x2, "y": y2, "wall_id": f"radial_{ring}_{sector}_{wall_count}", "order": 1})
            wall_count += 1

# Create center goal marker - use mark_point with star shape (Altair's native star support)
goal_df = pd.DataFrame({"x": [0], "y": [0]})

# Entry marker - position and compute angle for text rotation
entry_angle = (entry_theta_start + entry_theta_end) / 2
entry_r = num_rings * ring_width + 0.8
entry_x = entry_r * np.cos(entry_angle)
entry_y = entry_r * np.sin(entry_angle)

# Keep START text horizontal for universal readability regardless of entry position

entry_data = pd.DataFrame({"x": [entry_x], "y": [entry_y], "label": ["START"]})

# Convert wall data to DataFrame
df_walls = pd.DataFrame(wall_data)

# Calculate domain bounds to ensure perfect circle (equal x/y scales)
max_extent = num_rings * ring_width + 1.5  # Extra padding for START label

# Create wall lines chart with fixed scale domains for circular appearance
base = (
    alt.Chart(df_walls)
    .mark_line(color="black", strokeWidth=3)
    .encode(
        x=alt.X("x:Q", axis=None, scale=alt.Scale(domain=[-max_extent, max_extent])),
        y=alt.Y("y:Q", axis=None, scale=alt.Scale(domain=[-max_extent, max_extent])),
        detail="wall_id:N",
        order="order:O",
    )
)

# Center goal - use Vega-Lite's built-in star shape via mark_point
# Increased size to 40000 for better visibility relative to maze size
goal = (
    alt.Chart(goal_df)
    .mark_point(
        shape="M0,0.5L0.191,0.181L0.5,0.181L0.236,-0.045L0.309,-0.405L0,-0.191L-0.309,-0.405L-0.236,-0.045L-0.5,0.181L-0.191,0.181Z",
        size=40000,
        fill="#FFD43B",
        stroke="#333333",
        strokeWidth=3,
        filled=True,
    )
    .encode(x=alt.X("x:Q", axis=None), y=alt.Y("y:Q", axis=None))
)

# Entry marker - horizontal text for best readability
entry = (
    alt.Chart(entry_data)
    .mark_text(fontSize=22, fontWeight="bold", color="#306998")
    .encode(x="x:Q", y="y:Q", text="label:N")
)

# Combine layers with square aspect ratio for perfect circle
chart = (
    alt.layer(base, goal, entry)
    .properties(width=900, height=900, title=alt.Title("maze-circular · altair · pyplots.ai", fontSize=28))
    .configure_view(strokeWidth=0)
    .configure_axis(grid=False)
)

# Save outputs
chart.save("plot.png", scale_factor=4.0)
chart.save("plot.html")
