"""anyplot.ai
maze-circular: Circular Maze Puzzle
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-20
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

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
ENTRY_COLOR = IMPRINT_PALETTE[2]  # theme-independent, identical in light and dark
GOAL_COLOR = IMPRINT_PALETTE[4]  # theme-independent

# Constants
OUTER = "outer"  # kind of the boundary ring, drawn heavier than the interior walls
INNER = "inner"

# Maze parameters: set these to build another maze
# "easy" / "medium" / "hard" scales the sector density
DIFFICULTY = "medium"  # role: difficulty
RINGS = 7  # rings between the center and the outer boundary
SEED = 42  # fixed seed, so the maze is reproducible

# Wall polylines are drawn from a table with these fields, one wall id per disconnected piece
X = "x"
Y = "y"
WALL = "wall"
ORDER = "order"
KIND = "kind"

# Data: replace this block with your own table of wall polylines, for example df = pd.read_csv("walls.csv")
density = {"easy": 0.70, "medium": 1.0, "hard": 1.40}.get(DIFFICULTY, 1.0)

np.random.seed(SEED)
num_rings = RINGS
sectors_per_ring = [1] + [max(4, round((12 + i * 4) * density)) for i in range(num_rings)]
ring_width = 1.0

# Wall state per cell: True = wall present
walls = [[{"outer": True, "cw": True} for _ in range(sectors_per_ring[ring + 1])] for ring in range(num_rings)]

# Union-Find for Kruskal's maze generation (guarantees exactly one solution)
parent = {(ring, sector): (ring, sector) for ring in range(num_rings) for sector in range(sectors_per_ring[ring + 1])}

possible_walls = []
for ring in range(num_rings):
    num_sectors = sectors_per_ring[ring + 1]
    for sector in range(num_sectors):
        next_sector = (sector + 1) % num_sectors
        possible_walls.append(("cw", ring, sector, ring, next_sector))
        if ring < num_rings - 1:
            outer_sectors = sectors_per_ring[ring + 2]
            outer_sector = int(sector * outer_sectors / num_sectors)
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

# Entry fixed at the top so the START label is always clearly readable
entry_sector = sectors_per_ring[num_rings] // 4
theta_vals = np.linspace(0, 2 * np.pi, sectors_per_ring[num_rings] + 1)
entry_theta_start = theta_vals[entry_sector]
entry_theta_end = theta_vals[entry_sector + 1]
outer_r = num_rings * ring_width

rows = []  # one record per polyline vertex
wall_count = 0


# Outer boundary arcs with a gap at the entry
for start, end in [(0, entry_theta_start), (entry_theta_end, 2 * np.pi)]:
    if end > start:
        theta = np.linspace(start, end, 60)
        for i, (px, py) in enumerate(zip(outer_r * np.cos(theta), outer_r * np.sin(theta), strict=True)):
            rows.append({X: px, Y: py, WALL: f"ob_{wall_count}", ORDER: i, KIND: OUTER})
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
        elif arc_start is not None:
            theta = np.linspace(arc_start, ring_theta[sector], 30)
            for i, (px, py) in enumerate(zip(r * np.cos(theta), r * np.sin(theta), strict=True)):
                rows.append({X: px, Y: py, WALL: f"r_{ring}_{wall_count}", ORDER: i, KIND: INNER})
            wall_count += 1
            arc_start = None

    if arc_start is not None:
        theta = np.linspace(arc_start, 2 * np.pi, 30)
        for i, (px, py) in enumerate(zip(r * np.cos(theta), r * np.sin(theta), strict=True)):
            rows.append({X: px, Y: py, WALL: f"r_{ring}_{wall_count}", ORDER: i, KIND: INNER})
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
            wid = f"rad_{ring}_{sector}_{wall_count}"
            rows.append(
                {X: r_inner * np.cos(theta_val), Y: r_inner * np.sin(theta_val), WALL: wid, ORDER: 0, KIND: INNER}
            )
            rows.append(
                {X: r_outer * np.cos(theta_val), Y: r_outer * np.sin(theta_val), WALL: wid, ORDER: 1, KIND: INNER}
            )
            wall_count += 1

df = pd.DataFrame(rows)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
outer_df = df[df[KIND] == OUTER]

# Geometry derived from df: outer radius, and the entry gap between the two outer arcs
outer_r = np.hypot(outer_df[X], outer_df[Y]).max()
arc_ids = outer_df[WALL].drop_duplicates().tolist()
gap_ends = [
    outer_df[outer_df[WALL] == arc_ids[0]].sort_values(ORDER).iloc[-1],
    outer_df[outer_df[WALL] == arc_ids[-1]].sort_values(ORDER).iloc[0],
]
entry_angle = np.arctan2(sum(p[Y] for p in gap_ends), sum(p[X] for p in gap_ends))
entry_label_r = outer_r + 0.90
entry_arrow_r = outer_r + 0.30
max_extent = outer_r + 1.6

# Shared scale domains guarantee an equal-aspect circle
x_scale = alt.Scale(domain=[-max_extent, max_extent])
y_scale = alt.Scale(domain=[-max_extent, max_extent])
x_enc = alt.X(X, type="quantitative", axis=None, scale=x_scale)
y_enc = alt.Y(Y, type="quantitative", axis=None, scale=y_scale)


def wall_layer(data, width):
    return (
        alt.Chart(data)
        .mark_line(color=WALL_COLOR, strokeWidth=width)
        .encode(
            x=alt.X(X.translate(ESCAPE), type="quantitative", axis=None, scale=x_scale),
            y=alt.Y(Y.translate(ESCAPE), type="quantitative", axis=None, scale=y_scale),
            detail=alt.Detail(WALL.translate(ESCAPE), type="nominal"),
            order=alt.Order(ORDER.translate(ESCAPE), type="ordinal"),
        )
    )


# Outer boundary heavier than the interior walls
outer_chart = wall_layer(outer_df, 4.0)
walls_chart = wall_layer(df[df[KIND] == INNER], 2.5)

# Goal at center: translucent halo + star
center = pd.DataFrame({"x": [0.0], "y": [0.0], "label": ["★"]})
goal_halo_chart = (
    alt.Chart(center).mark_point(color=GOAL_COLOR, size=350, filled=True, opacity=0.30).encode(x=x_enc, y=y_enc)
)
goal_chart = (
    alt.Chart(center)
    .mark_text(fontSize=24, fontWeight="bold", color=GOAL_COLOR)
    .encode(x=x_enc, y=y_enc, text="label:N")
)

# Entry label and inward-pointing arrow (▼ points toward the center when the entry is at the top)
arrow_df = pd.DataFrame(
    {"x": [entry_arrow_r * np.cos(entry_angle)], "y": [entry_arrow_r * np.sin(entry_angle)], "label": ["▼"]}
)
entry_df = pd.DataFrame(
    {"x": [entry_label_r * np.cos(entry_angle)], "y": [entry_label_r * np.sin(entry_angle)], "label": ["START"]}
)
arrow_chart = alt.Chart(arrow_df).mark_text(fontSize=14, color=ENTRY_COLOR).encode(x=x_enc, y=y_enc, text="label:N")
entry_chart = (
    alt.Chart(entry_df)
    .mark_text(fontSize=18, fontWeight="bold", color=ENTRY_COLOR)
    .encode(x=x_enc, y=y_enc, text="label:N")
)

chart = (
    alt.layer(outer_chart, walls_chart, goal_halo_chart, goal_chart, arrow_chart, entry_chart)
    .properties(
        width=600,
        height=600,
        autosize=alt.AutoSizeParams(type="fit", contains="padding"),
        padding=10,
        background=PAGE_BG,
        title="maze-circular · python · altair · anyplot.ai",
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_axis(grid=False)
    .configure_title(fontSize=16, color=INK)
)

chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")
